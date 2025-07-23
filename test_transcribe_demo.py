#!/usr/bin/env python3
"""
Basic tests for transcribe_demo.py improvements.
"""

import argparse
import sys
import unittest
from unittest.mock import patch
from queue import Queue

# Import functions from transcribe_demo
sys.path.insert(0, '.')


class TestTranscribeDemoImprovements(unittest.TestCase):
    """Test suite for transcribe_demo improvements."""

    def test_validate_arguments_valid(self):
        """Test argument validation with valid arguments."""
        from transcribe_demo import validate_arguments
        
        args = argparse.Namespace(
            energy_threshold=1000,
            record_timeout=2.0,
            phrase_timeout=3.0
        )
        # Should not raise any exception
        try:
            validate_arguments(args)
        except Exception as e:
            self.fail(f"validate_arguments raised {e} unexpectedly")

    def test_validate_arguments_negative_energy(self):
        """Test argument validation with negative energy threshold."""
        from transcribe_demo import validate_arguments
        
        args = argparse.Namespace(
            energy_threshold=-100,
            record_timeout=2.0,
            phrase_timeout=3.0
        )
        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        self.assertIn("Energy threshold must be non-negative", str(context.exception))

    def test_validate_arguments_zero_timeout(self):
        """Test argument validation with zero timeout values."""
        from transcribe_demo import validate_arguments
        
        args = argparse.Namespace(
            energy_threshold=1000,
            record_timeout=0,
            phrase_timeout=3.0
        )
        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        self.assertIn("Record timeout must be positive", str(context.exception))

    def test_process_audio_queue_empty(self):
        """Test processing empty audio queue."""
        from transcribe_demo import process_audio_queue
        
        queue = Queue()
        result = process_audio_queue(queue)
        self.assertIsNone(result)

    def test_process_audio_queue_with_data(self):
        """Test processing audio queue with data."""
        from transcribe_demo import process_audio_queue
        
        queue = Queue()
        test_data1 = b'test_audio_data_1'
        test_data2 = b'test_audio_data_2'
        queue.put(test_data1)
        queue.put(test_data2)
        
        result = process_audio_queue(queue)
        self.assertEqual(result, test_data1 + test_data2)
        self.assertTrue(queue.empty())

    @patch('subprocess.run')
    def test_clear_console_unix(self, mock_run):
        """Test console clearing on Unix systems."""
        from transcribe_demo import clear_console
        
        with patch('os.name', 'posix'):
            clear_console()
            mock_run.assert_called_once_with(['clear'], check=True, capture_output=True)

    @patch('subprocess.run')
    def test_clear_console_windows(self, mock_run):
        """Test console clearing on Windows systems."""
        from transcribe_demo import clear_console
        
        with patch('os.name', 'nt'):
            clear_console()
            mock_run.assert_called_once_with(['cls'], shell=True, check=True, capture_output=True)

    @patch('subprocess.run')
    @patch('builtins.print')
    def test_clear_console_fallback(self, mock_print, mock_run):
        """Test console clearing fallback when subprocess fails."""
        from transcribe_demo import clear_console
        
        mock_run.side_effect = FileNotFoundError()
        
        clear_console()
        
        # Should print newlines as fallback
        mock_print.assert_called_once_with('\n' * 50)


class TestConstants(unittest.TestCase):
    """Test that constants are properly defined."""

    def test_constants_exist(self):
        """Test that all expected constants are defined."""
        from transcribe_demo import (
            DEFAULT_ENERGY_THRESHOLD,
            DEFAULT_RECORD_TIMEOUT,
            DEFAULT_PHRASE_TIMEOUT,
            DEFAULT_MODEL,
            SAMPLE_RATE,
            AUDIO_NORMALIZATION_FACTOR,
            SLEEP_INTERVAL,
            CONSOLE_CLEAR_FALLBACK_LINES
        )
        
        # Check that constants have expected values
        self.assertEqual(DEFAULT_ENERGY_THRESHOLD, 1000)
        self.assertEqual(DEFAULT_RECORD_TIMEOUT, 2.0)
        self.assertEqual(DEFAULT_PHRASE_TIMEOUT, 3.0)
        self.assertEqual(DEFAULT_MODEL, "medium")
        self.assertEqual(SAMPLE_RATE, 16000)
        self.assertEqual(AUDIO_NORMALIZATION_FACTOR, 32768.0)
        self.assertEqual(SLEEP_INTERVAL, 0.25)
        self.assertEqual(CONSOLE_CLEAR_FALLBACK_LINES, 50)


if __name__ == '__main__':
    unittest.main()