"""
Unit tests for the Transcriber service.
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock, mock_open

# Mock speech_recognition module since it may not be installed yet
class MockUnknownValueError(Exception):
    pass

class MockRequestError(Exception):
    pass

mock_sr = MagicMock()
mock_sr.Recognizer = MagicMock
mock_sr.AudioFile = MagicMock
mock_sr.UnknownValueError = MockUnknownValueError
mock_sr.RequestError = MockRequestError
sys.modules['speech_recognition'] = mock_sr

from src.services.transcriber import Transcriber, TranscriberError
from src.models.transcription import Transcription
from src.utils.validators import ValidationError


class TestTranscriber(unittest.TestCase):
    """Test cases for the Transcriber service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.transcriber = Transcriber()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test audio file paths
        self.valid_wav_file = os.path.join(self.temp_dir, "test_audio.wav")
        self.valid_flac_file = os.path.join(self.temp_dir, "test_audio.flac")
        self.invalid_format_file = os.path.join(self.temp_dir, "test_audio.mp3")
        
        # Create dummy files
        for file_path in [self.valid_wav_file, self.valid_flac_file, self.invalid_format_file]:
            with open(file_path, 'wb') as f:
                f.write(b"dummy audio content for testing")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test Transcriber initialization."""
        # Test default initialization
        transcriber = Transcriber()
        self.assertEqual(transcriber.language, "en-US")
        self.assertIsNotNone(transcriber.recognizer)
        
        # Test initialization with custom language
        transcriber_custom = Transcriber(language="es-ES")
        self.assertEqual(transcriber_custom.language, "es-ES")
    
    def test_set_language(self):
        """Test setting language."""
        # Test valid language
        self.transcriber.set_language("fr-FR")
        self.assertEqual(self.transcriber.language, "fr-FR")
        
        # Test empty language
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.set_language("")
        self.assertIn("Language must be a non-empty string", str(context.exception))
        
        # Test None language
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.set_language(None)
        self.assertIn("Language must be a non-empty string", str(context.exception))
        
        # Test non-string language
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.set_language(123)
        self.assertIn("Language must be a non-empty string", str(context.exception))
    
    def test_get_current_language(self):
        """Test getting current language."""
        self.assertEqual(self.transcriber.get_current_language(), "en-US")
        
        self.transcriber.set_language("de-DE")
        self.assertEqual(self.transcriber.get_current_language(), "de-DE")
    
    def test_get_supported_formats(self):
        """Test getting supported audio formats."""
        formats = self.transcriber.get_supported_formats()
        expected_formats = ['.wav', '.flac', '.aiff', '.aif']
        
        self.assertEqual(formats, expected_formats)
        self.assertIsInstance(formats, list)
    
    def test_configure_recognizer(self):
        """Test configuring speech recognizer settings."""
        # Test setting energy threshold
        self.transcriber.configure_recognizer(energy_threshold=5000)
        self.assertEqual(self.transcriber.recognizer.energy_threshold, 5000)
        
        # Test setting pause threshold
        self.transcriber.configure_recognizer(pause_threshold=1.0)
        self.assertEqual(self.transcriber.recognizer.pause_threshold, 1.0)
        
        # Test setting multiple parameters
        self.transcriber.configure_recognizer(
            energy_threshold=3000,
            dynamic_energy_threshold=False,
            phrase_threshold=0.5
        )
        self.assertEqual(self.transcriber.recognizer.energy_threshold, 3000)
        self.assertFalse(self.transcriber.recognizer.dynamic_energy_threshold)
        self.assertEqual(self.transcriber.recognizer.phrase_threshold, 0.5)
    
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_validation_error(self, mock_validate):
        """Test transcribe method with file validation error."""
        mock_validate.side_effect = ValidationError("File does not exist")
        
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertIn("Audio file validation failed", str(context.exception))
        self.assertIn("File does not exist", str(context.exception))
    
    def test_transcribe_unsupported_format(self):
        """Test transcribe method with unsupported audio format."""
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe(self.invalid_format_file)
        
        self.assertIn("Unsupported audio format: .mp3", str(context.exception))
        self.assertIn("Supported formats:", str(context.exception))
    
    @patch('src.services.transcriber.sr.AudioFile')
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_success(self, mock_validate, mock_audio_file):
        """Test successful transcription."""
        # Setup mocks
        mock_validate.return_value = None
        
        mock_source = MagicMock()
        mock_audio_file.return_value.__enter__ = MagicMock(return_value=mock_source)
        mock_audio_file.return_value.__exit__ = MagicMock(return_value=None)
        
        mock_audio_data = MagicMock()
        self.transcriber.recognizer.record = MagicMock(return_value=mock_audio_data)
        self.transcriber.recognizer.adjust_for_ambient_noise = MagicMock()
        self.transcriber.recognizer.recognize_google = MagicMock(return_value="Hello world")
        
        # Test transcription
        result = self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertEqual(result, "Hello world")
        mock_validate.assert_called_once_with(self.valid_wav_file)
        mock_audio_file.assert_called_once_with(self.valid_wav_file)
        self.transcriber.recognizer.adjust_for_ambient_noise.assert_called_once()
        self.transcriber.recognizer.record.assert_called_once_with(mock_source)
        self.transcriber.recognizer.recognize_google.assert_called_once_with(
            mock_audio_data, language="en-US"
        )
    
    @patch('src.services.transcriber.sr.AudioFile')
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_no_speech_detected(self, mock_validate, mock_audio_file):
        """Test transcription when no speech is detected."""
        # Setup mocks
        mock_validate.return_value = None
        
        mock_source = MagicMock()
        mock_audio_file.return_value.__enter__ = MagicMock(return_value=mock_source)
        mock_audio_file.return_value.__exit__ = MagicMock(return_value=None)
        
        mock_audio_data = MagicMock()
        self.transcriber.recognizer.record = MagicMock(return_value=mock_audio_data)
        self.transcriber.recognizer.adjust_for_ambient_noise = MagicMock()
        self.transcriber.recognizer.recognize_google = MagicMock(return_value="")
        
        # Test transcription with empty result
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertIn("No speech detected in audio file", str(context.exception))
    
    @patch('src.services.transcriber.sr.AudioFile')
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_unknown_value_error(self, mock_validate, mock_audio_file):
        """Test transcription with UnknownValueError."""
        # Setup mocks
        mock_validate.return_value = None
        
        mock_source = MagicMock()
        mock_audio_file.return_value.__enter__ = MagicMock(return_value=mock_source)
        mock_audio_file.return_value.__exit__ = MagicMock(return_value=None)
        
        mock_audio_data = MagicMock()
        self.transcriber.recognizer.record = MagicMock(return_value=mock_audio_data)
        self.transcriber.recognizer.adjust_for_ambient_noise = MagicMock()
        self.transcriber.recognizer.recognize_google = MagicMock(
            side_effect=mock_sr.UnknownValueError()
        )
        
        # Test transcription with unclear audio
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertIn("Could not understand audio", str(context.exception))
    
    @patch('src.services.transcriber.sr.AudioFile')
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_request_error(self, mock_validate, mock_audio_file):
        """Test transcription with RequestError."""
        # Setup mocks
        mock_validate.return_value = None
        
        mock_source = MagicMock()
        mock_audio_file.return_value.__enter__ = MagicMock(return_value=mock_source)
        mock_audio_file.return_value.__exit__ = MagicMock(return_value=None)
        
        mock_audio_data = MagicMock()
        self.transcriber.recognizer.record = MagicMock(return_value=mock_audio_data)
        self.transcriber.recognizer.adjust_for_ambient_noise = MagicMock()
        self.transcriber.recognizer.recognize_google = MagicMock(
            side_effect=mock_sr.RequestError("Network error")
        )
        
        # Test transcription with network error
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertIn("Speech recognition service error", str(context.exception))
        self.assertIn("Network error", str(context.exception))
    
    @patch('src.services.transcriber.sr.AudioFile')
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_generic_error(self, mock_validate, mock_audio_file):
        """Test transcription with generic error."""
        # Setup mocks
        mock_validate.return_value = None
        mock_audio_file.side_effect = IOError("File read error")
        
        # Test transcription with file read error
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertIn("Failed to process audio file", str(context.exception))
        self.assertIn("File read error", str(context.exception))
    
    @patch.object(Transcriber, 'transcribe')
    def test_transcribe_to_model_success(self, mock_transcribe):
        """Test successful transcription to model."""
        mock_transcribe.return_value = "Hello world test transcription"
        
        result = self.transcriber.transcribe_to_model(self.valid_wav_file)
        
        self.assertIsInstance(result, Transcription)
        self.assertEqual(result.text, "Hello world test transcription")
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(result.language, "en-US")
        mock_transcribe.assert_called_once_with(self.valid_wav_file)
    
    @patch.object(Transcriber, 'transcribe')
    def test_transcribe_to_model_error(self, mock_transcribe):
        """Test transcription to model with error."""
        mock_transcribe.side_effect = TranscriberError("Transcription failed")
        
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe_to_model(self.valid_wav_file)
        
        self.assertIn("Transcription failed", str(context.exception))
    
    @patch.object(Transcriber, 'transcribe')
    def test_transcribe_to_model_generic_error(self, mock_transcribe):
        """Test transcription to model with generic error."""
        mock_transcribe.side_effect = ValueError("Some other error")
        
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe_to_model(self.valid_wav_file)
        
        self.assertIn("Failed to create transcription model", str(context.exception))
        self.assertIn("Some other error", str(context.exception))
    
    def test_different_audio_formats(self):
        """Test validation with different supported audio formats."""
        supported_files = [
            ("test.wav", True),
            ("test.flac", True),
            ("test.aiff", True),
            ("test.aif", True),
            ("test.WAV", True),  # Case insensitive
            ("test.FLAC", True),
            ("test.mp3", False),  # Unsupported
            ("test.m4a", False),  # Unsupported
            ("test.ogg", False),  # Unsupported
        ]
        
        for filename, should_be_valid in supported_files:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(b"dummy content")
            
            with self.subTest(filename=filename):
                if should_be_valid:
                    # Should not raise exception for format validation
                    # (but may raise other exceptions in actual transcription)
                    try:
                        self.transcriber.transcribe(file_path)
                    except TranscriberError as e:
                        # Only format errors should be tested here
                        self.assertNotIn("Unsupported audio format", str(e))
                else:
                    # Should raise format error
                    with self.assertRaises(TranscriberError) as context:
                        self.transcriber.transcribe(file_path)
                    self.assertIn("Unsupported audio format", str(context.exception))
    
    def test_transcriber_error_inheritance(self):
        """Test that TranscriberError is properly inherited from Exception."""
        self.assertTrue(issubclass(TranscriberError, Exception))
        
        # Test raising and catching
        with self.assertRaises(TranscriberError):
            raise TranscriberError("Test error")


if __name__ == '__main__':
    unittest.main()