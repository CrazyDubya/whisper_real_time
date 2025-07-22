#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from queue import Queue, Empty
from sys import platform
from time import sleep
from typing import List, Optional

import numpy as np
import speech_recognition as sr
import torch
import whisper

# Constants
DEFAULT_ENERGY_THRESHOLD = 1000
DEFAULT_RECORD_TIMEOUT = 2.0
DEFAULT_PHRASE_TIMEOUT = 3.0
DEFAULT_MODEL = "medium"
SAMPLE_RATE = 16000
AUDIO_NORMALIZATION_FACTOR = 32768.0
SLEEP_INTERVAL = 0.25
CONSOLE_CLEAR_FALLBACK_LINES = 50

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def clear_console() -> None:
    """Safely clear the console screen."""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['cls'], shell=True, check=True, capture_output=True)
        else:  # Unix/Linux/MacOS
            subprocess.run(['clear'], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        # Fallback: print newlines if clear command fails
        print('\n' * CONSOLE_CLEAR_FALLBACK_LINES)


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if args.energy_threshold < 0:
        raise ValueError("Energy threshold must be non-negative")
    if args.record_timeout <= 0:
        raise ValueError("Record timeout must be positive")
    if args.phrase_timeout <= 0:
        raise ValueError("Phrase timeout must be positive")


def get_microphone_source(mic_name: Optional[str] = None) -> sr.Microphone:
    """Get the appropriate microphone source with error handling."""
    if 'linux' in platform:
        if not mic_name or mic_name == 'list':
            print("Available microphone devices are: ")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"Microphone with name \"{name}\" found")
            sys.exit(0)
        else:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in name:
                    try:
                        return sr.Microphone(sample_rate=SAMPLE_RATE, device_index=index)
                    except OSError as e:
                        raise RuntimeError(f"Failed to initialize microphone '{name}': {e}")
            raise ValueError(f"Microphone '{mic_name}' not found")
    else:
        try:
            return sr.Microphone(sample_rate=SAMPLE_RATE)
        except OSError as e:
            raise RuntimeError(f"Failed to initialize default microphone: {e}")


def load_whisper_model(model_name: str, non_english: bool = False) -> whisper.Whisper:
    """Load Whisper model with error handling."""
    model = model_name
    if model_name != "large" and not non_english:
        model = model + ".en"
    
    try:
        logging.info(f"Loading Whisper model: {model}")
        audio_model = whisper.load_model(model)
        logging.info("Model loaded successfully")
        return audio_model
    except Exception as e:
        raise RuntimeError(f"Error loading model '{model}': {e}")


def process_audio_queue(data_queue: Queue) -> Optional[bytes]:
    """Process audio data from queue using thread-safe operations."""
    audio_data_list = []
    while not data_queue.empty():
        try:
            audio_data_list.append(data_queue.get_nowait())
        except Empty:
            break
    
    return b''.join(audio_data_list) if audio_data_list else None


def convert_audio_to_numpy(audio_data: bytes) -> np.ndarray:
    """Convert audio bytes to numpy array for Whisper processing."""
    return np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / AUDIO_NORMALIZATION_FACTOR


def display_transcription(transcription: List[str]) -> None:
    """Display the current transcription with console clearing."""
    clear_console()
    for line in transcription:
        if line.strip():  # Only print non-empty lines
            print(line)
    print('', end='', flush=True)


def main():
    """Main function to run the real-time whisper transcription."""
    parser = argparse.ArgumentParser(
        description="Real-time speech transcription using OpenAI Whisper"
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=DEFAULT_ENERGY_THRESHOLD,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=DEFAULT_RECORD_TIMEOUT,
                        help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=DEFAULT_PHRASE_TIMEOUT,
                        help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)
    parser.add_argument("--output_file", help="Optional file to save transcription")
    parser.add_argument("--show_confidence", action='store_true',
                        help="Show confidence scores with transcription")
    
    if 'linux' in platform:
        parser.add_argument("--default_microphone", default='pulse',
                            help="Default microphone name for SpeechRecognition. "
                                 "Run this with 'list' to view available Microphones.", type=str)
    args = parser.parse_args()

    # Validate arguments
    try:
        validate_arguments(args)
    except ValueError as e:
        logging.error(f"Argument validation failed: {e}")
        sys.exit(1)

    # Initialize components
    phrase_time = None
    data_queue = Queue()
    transcription: List[str] = ['']

    # Setup audio recorder
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    recorder.dynamic_energy_threshold = False

    # Get microphone source
    try:
        if 'linux' in platform:
            source = get_microphone_source(args.default_microphone)
        else:
            source = get_microphone_source()
    except (ValueError, RuntimeError) as e:
        logging.error(f"Microphone initialization failed: {e}")
        sys.exit(1)

    # Load Whisper model
    try:
        audio_model = load_whisper_model(args.model, args.non_english)
    except RuntimeError as e:
        logging.error(str(e))
        sys.exit(1)

    # Adjust for ambient noise
    try:
        with source:
            logging.info("Adjusting for ambient noise...")
            recorder.adjust_for_ambient_noise(source)
            logging.info("Ambient noise adjustment complete")
    except Exception as e:
        logging.error(f"Error adjusting for ambient noise: {e}")
        sys.exit(1)

    def record_callback(_, audio: sr.AudioData) -> None:
        """Threaded callback function to receive audio data when recordings finish."""
        data = audio.get_raw_data()
        data_queue.put(data)

    # Start background recording
    stop_listening = recorder.listen_in_background(
        source, record_callback, phrase_time_limit=args.record_timeout
    )

    print("Model loaded. Starting transcription...")
    logging.info("Real-time transcription started")

    try:
        while True:
            try:
                now = datetime.utcnow()
                
                # Process audio data if available
                if not data_queue.empty():
                    phrase_complete = False
                    
                    # Check if enough time has passed for phrase completion
                    if phrase_time and now - phrase_time > timedelta(seconds=args.phrase_timeout):
                        phrase_complete = True
                    
                    phrase_time = now
                    
                    # Get audio data from queue
                    audio_data = process_audio_queue(data_queue)
                    
                    if not audio_data:
                        sleep(SLEEP_INTERVAL)
                        continue
                    
                    # Convert audio to numpy array
                    audio_np = convert_audio_to_numpy(audio_data)
                    
                    # Transcribe audio
                    result = audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    text = result['text'].strip()
                    
                    if text:  # Only process non-empty transcriptions
                        # Format text with confidence if requested
                        if args.show_confidence and 'segments' in result:
                            avg_confidence = np.mean([seg.get('no_speech_prob', 0) for seg in result['segments']])
                            confidence_percentage = (1 - avg_confidence) * 100
                            text = f"{text} [Confidence: {confidence_percentage:.1f}%]"
                        
                        # Update transcription
                        if phrase_complete:
                            transcription.append(text)
                        else:
                            transcription[-1] = text
                        
                        # Display updated transcription
                        display_transcription(transcription)
                        
                        # Save to file if specified
                        if args.output_file:
                            try:
                                with open(args.output_file, 'w', encoding='utf-8') as f:
                                    f.write('\n'.join(line for line in transcription if line.strip()))
                            except IOError as e:
                                logging.warning(f"Failed to write to output file: {e}")
                
                else:
                    sleep(SLEEP_INTERVAL)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"Error during transcription: {e}")
                continue
                
    finally:
        # Cleanup
        stop_listening(wait_for_stop=False)
        
        # Final transcription output
        print("\n\nFinal Transcription:")
        for line in transcription:
            if line.strip():
                print(line)
        
        if args.output_file:
            try:
                with open(args.output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(line for line in transcription if line.strip()))
                print(f"\nTranscription saved to: {args.output_file}")
            except IOError as e:
                logging.error(f"Failed to save final transcription: {e}")
        
        logging.info("Transcription session ended")

if __name__ == "__main__":
    main()
