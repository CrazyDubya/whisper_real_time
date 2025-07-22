# Real Time Whisper Transcription

![Demo gif](demo.gif)

This is an enhanced version of real-time speech-to-text transcription using OpenAI's Whisper model. It provides comprehensive improvements in security, performance, code quality, and features while maintaining the core real-time audio processing functionality.

## Features

### Core Functionality
- Real-time speech transcription using OpenAI Whisper
- Support for multiple Whisper model sizes (tiny, base, small, medium, large)
- Cross-platform support (Windows, macOS, Linux)
- Automatic microphone detection and configuration

### Enhanced Features
- **Configuration file support** - Use `config.ini` for persistent settings
- **Output file support** - Save transcriptions to text files
- **Confidence scores** - Display transcription confidence levels
- **Comprehensive logging** - Detailed logging with configurable levels
- **Input validation** - Robust argument and parameter validation
- **Error handling** - Graceful handling of audio device and model loading errors

### Security & Performance Improvements
- **Secure console clearing** - Replaced `os.system()` with safe `subprocess.run()`
- **Thread-safe queue operations** - Fixed race conditions in audio processing
- **Optimized audio processing** - Improved queue management and buffer handling
- **Resource cleanup** - Proper cleanup of audio resources on exit

### Code Quality Enhancements
- **Type hints** - Full type annotation support
- **Modular architecture** - Refactored into focused, reusable functions
- **Named constants** - Replaced magic numbers with descriptive constants
- **Comprehensive documentation** - Detailed docstrings and comments

## Installation

To install dependencies simply run:
```bash
pip install -r requirements.txt
```

Whisper also requires the command-line tool [`ffmpeg`](https://ffmpeg.org/) to be installed on your system, which is available from most package managers:

```bash
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```

## Usage

### Basic Usage
```bash
python transcribe_demo.py
```

### Advanced Usage
```bash
# Use a specific model
python transcribe_demo.py --model small

# Save output to file with confidence scores
python transcribe_demo.py --output_file transcript.txt --show_confidence

# Adjust microphone sensitivity
python transcribe_demo.py --energy_threshold 500

# Use configuration file
python transcribe_demo.py --config my_config.ini

# List available microphones (Linux)
python transcribe_demo.py --default_microphone list
```

### Configuration File

Create a `config.ini` file to set default values:

```ini
[DEFAULT]
model = medium
energy_threshold = 1000
record_timeout = 2.0
phrase_timeout = 3.0
output_file = 
show_confidence = false
log_level = INFO
```

### Command Line Options

- `--model`: Whisper model size (tiny, base, small, medium, large)
- `--non_english`: Don't use English-specific model
- `--energy_threshold`: Microphone sensitivity (higher = less sensitive)
- `--record_timeout`: Real-time recording interval in seconds
- `--phrase_timeout`: Pause detection threshold in seconds
- `--output_file`: Save transcription to file
- `--show_confidence`: Display confidence scores
- `--config`: Path to configuration file
- `--default_microphone`: Microphone name (Linux only)

## Architecture

The codebase has been refactored into a modular architecture:

- **Configuration Management**: `load_config()`, `setup_logging()`
- **Audio Processing**: `get_microphone_source()`, `process_audio_queue()`
- **Transcription**: `load_whisper_model()`, `convert_audio_to_numpy()`
- **Display**: `clear_console()`, `display_transcription()`
- **Validation**: `validate_arguments()`

## Testing

Run the test suite to validate functionality:

```bash
python test_transcribe_demo.py
```

Validate improvements:

```bash
python validate_improvements.py
```

## Improvements Summary

This enhanced version includes 15+ comprehensive improvements:

### Security Fixes
- ✅ Replaced `os.system()` with secure `subprocess.run()`
- ✅ Added input validation for all parameters
- ✅ Secure error handling for audio device access

### Bug Resolutions
- ✅ Fixed Python version compatibility
- ✅ Resolved queue race conditions
- ✅ Added comprehensive error handling
- ✅ Proper resource cleanup

### Performance Optimizations
- ✅ Thread-safe queue operations
- ✅ Optimized audio buffer processing
- ✅ Named constants for better performance
- ✅ Reduced CPU usage with adaptive sleep

### Code Quality Enhancements
- ✅ Full type hints and documentation
- ✅ Modular function architecture (9 functions)
- ✅ Logging system with configurable levels
- ✅ Consistent naming conventions

### Architectural Improvements
- ✅ Separation of concerns
- ✅ Configuration management system
- ✅ Reusable, testable components
- ✅ Cross-platform compatibility

### Feature Additions
- ✅ Configuration file support
- ✅ Output file functionality
- ✅ Confidence score display
- ✅ Enhanced CLI interface

## Requirements

See `requirements.txt` for the complete list of dependencies. Main requirements:
- Python 3.7+
- OpenAI Whisper
- PyAudio
- SpeechRecognition
- NumPy
- PyTorch

For more information on Whisper, see: https://github.com/openai/whisper

## License

The code in this repository is public domain.