"""
Unit tests for the Transcriber service.
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock, mock_open

# Mock whisper module for testing
mock_whisper = MagicMock()
mock_whisper.available_models = MagicMock(return_value=['tiny', 'base', 'small', 'medium', 'large', 'turbo'])
mock_whisper.load_model = MagicMock()
sys.modules['whisper'] = mock_whisper

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
        self.valid_mp3_file = os.path.join(self.temp_dir, "test_audio.mp3")
        
        # Create dummy files
        for file_path in [self.valid_wav_file, self.valid_flac_file, self.valid_mp3_file]:
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
        self.assertEqual(transcriber.model_name, "turbo")
        self.assertIsNone(transcriber.language)
        self.assertIsNone(transcriber.model)  # Model not loaded yet
        
        # Test initialization with custom parameters
        transcriber_custom = Transcriber(model_name="base", language="es")
        self.assertEqual(transcriber_custom.model_name, "base")
        self.assertEqual(transcriber_custom.language, "es")
    
    def test_set_language(self):
        """Test setting language."""
        # Test valid language
        self.transcriber.set_language("fr")
        self.assertEqual(self.transcriber.language, "fr")
        
        # Test None language (auto-detection)
        self.transcriber.set_language(None)
        self.assertIsNone(self.transcriber.language)
        
        # Test empty string (should work as None)
        self.transcriber.set_language("")
        self.assertEqual(self.transcriber.language, "")
    
    def test_get_current_language(self):
        """Test getting current language."""
        self.assertIsNone(self.transcriber.get_current_language())  # Default is None (auto-detect)
        
        self.transcriber.set_language("de")
        self.assertEqual(self.transcriber.get_current_language(), "de")
    
    def test_get_supported_formats(self):
        """Test getting supported audio formats."""
        formats = self.transcriber.get_supported_formats()
        expected_formats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.opus', '.aac', '.aiff', '.wma']
        
        self.assertEqual(formats, expected_formats)
        self.assertIsInstance(formats, list)
    
    def test_set_model(self):
        """Test setting Whisper model."""
        # Test valid model
        self.transcriber.set_model("base")
        self.assertEqual(self.transcriber.model_name, "base")
        self.assertIsNone(self.transcriber.model)  # Should reset model
        
        # Test invalid model
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.set_model("invalid_model")
        self.assertIn("Invalid model name", str(context.exception))
    
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_validation_error(self, mock_validate):
        """Test transcribe method with file validation error."""
        mock_validate.side_effect = ValidationError("File does not exist")
        
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertIn("Audio file validation failed", str(context.exception))
        self.assertIn("File does not exist", str(context.exception))
    
    def test_get_model_name(self):
        """Test getting model name."""
        self.assertEqual(self.transcriber.get_model_name(), "turbo")
        
        self.transcriber.set_model("base")
        self.assertEqual(self.transcriber.get_model_name(), "base")
    
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_success(self, mock_validate):
        """Test successful transcription with Whisper."""
        # Setup mocks
        mock_validate.return_value = None
        
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'Hello world',
            'language': 'en'
        }
        mock_whisper.load_model.return_value = mock_model
        
        # Test transcription
        result = self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertEqual(result, "Hello world")
        mock_validate.assert_called_once_with(self.valid_wav_file)
        mock_whisper.load_model.assert_called_once_with("turbo")
        mock_model.transcribe.assert_called_once()
    
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_no_speech_detected(self, mock_validate):
        """Test transcription when no speech is detected."""
        # Setup mocks
        mock_validate.return_value = None
        
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': '  ',  # Empty/whitespace text
            'language': 'en'
        }
        mock_whisper.load_model.return_value = mock_model
        
        # Test transcription with empty result
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertIn("No speech detected in audio file", str(context.exception))
    
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_whisper_error(self, mock_validate):
        """Test transcription with Whisper error."""
        # Setup mocks
        mock_validate.return_value = None
        
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = Exception("Whisper processing error")
        mock_whisper.load_model.return_value = mock_model
        
        # Test transcription with Whisper error
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertIn("Failed to transcribe audio", str(context.exception))
        self.assertIn("Whisper processing error", str(context.exception))
    
    @patch('src.services.transcriber.validate_file_exists')
    def test_load_model(self, mock_validate):
        """Test model loading."""
        # Setup mocks
        mock_validate.return_value = None
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'Test transcription',
            'language': 'en'
        }
        mock_whisper.load_model.return_value = mock_model
        
        # First call should load the model
        result = self.transcriber.transcribe(self.valid_wav_file)
        self.assertEqual(result, "Test transcription")
        self.assertIsNotNone(self.transcriber.model)
        
        # Second call should reuse the model
        mock_whisper.load_model.reset_mock()
        result2 = self.transcriber.transcribe(self.valid_wav_file)
        mock_whisper.load_model.assert_not_called()  # Should not load again
    
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_generic_error(self, mock_validate):
        """Test transcription with generic error."""
        # Setup validation error
        mock_validate.side_effect = ValidationError("File does not exist")
        
        # Test transcription with validation error
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe(self.valid_wav_file)
        
        self.assertIn("Audio file validation failed", str(context.exception))
        self.assertIn("File does not exist", str(context.exception))
    
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_to_model_success(self, mock_validate):
        """Test successful transcription to model."""
        # Setup mocks
        mock_validate.return_value = None
        
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'Hello world test transcription',
            'language': 'en',
            'segments': [{
                'avg_logprob': -0.5
            }]
        }
        mock_whisper.load_model.return_value = mock_model
        
        result = self.transcriber.transcribe_to_model(self.valid_wav_file)
        
        self.assertIsInstance(result, Transcription)
        self.assertEqual(result.text, "Hello world test transcription")
        self.assertEqual(result.language, "en")
        self.assertGreater(result.confidence, 0)  # Should have calculated confidence
    
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_to_model_error(self, mock_validate):
        """Test transcription to model with error."""
        # Setup validation error
        mock_validate.side_effect = ValidationError("File validation failed")
        
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe_to_model(self.valid_wav_file)
        
        self.assertIn("Audio file validation failed", str(context.exception))
        self.assertIn("File validation failed", str(context.exception))
    
    @patch('src.services.transcriber.validate_file_exists')
    def test_transcribe_to_model_generic_error(self, mock_validate):
        """Test transcription to model with generic error."""
        # Setup mocks
        mock_validate.return_value = None
        
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = ValueError("Some other error")
        mock_whisper.load_model.return_value = mock_model
        
        with self.assertRaises(TranscriberError) as context:
            self.transcriber.transcribe_to_model(self.valid_wav_file)
        
        self.assertIn("Failed to create transcription model", str(context.exception))
        self.assertIn("Some other error", str(context.exception))
    
    def test_different_audio_formats(self):
        """Test that Whisper supports many audio formats."""
        supported_files = [
            "test.wav",
            "test.mp3", 
            "test.flac",
            "test.m4a",
            "test.ogg",
            "test.opus",
            "test.aac",
            "test.aiff",
            "test.wma"
        ]
        
        formats = self.transcriber.get_supported_formats()
        
        for filename in supported_files:
            extension = os.path.splitext(filename)[1]
            with self.subTest(extension=extension):
                self.assertIn(extension, formats, f"Format {extension} should be supported by Whisper")
    
    def test_transcriber_error_inheritance(self):
        """Test that TranscriberError is properly inherited from Exception."""
        self.assertTrue(issubclass(TranscriberError, Exception))
        
        # Test raising and catching
        with self.assertRaises(TranscriberError):
            raise TranscriberError("Test error")


if __name__ == '__main__':
    unittest.main()