"""
Unit tests for the main CLI entry point.
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Mock the speech_recognition module
mock_sr = MagicMock()
sys.modules['speech_recognition'] = mock_sr

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import VideoTranscriberCLI, main
from models.transcription import Transcription
from models.summary import Summary
from utils.validators import ValidationError


class TestVideoTranscriberCLI(unittest.TestCase):
    """Test cases for the VideoTranscriberCLI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        self.output_dir = os.path.join(self.temp_dir, "output")
        
        # Create test video file
        with open(self.test_video_path, 'wb') as f:
            f.write(b"fake video content for testing")
        
        # Create CLI instance with mocked dependencies
        with patch.multiple(
            'main',
            Config=MagicMock,
            FileHandler=MagicMock,
            AudioExtractor=MagicMock,
            Transcriber=MagicMock,
            Summarizer=MagicMock
        ):
            self.cli = VideoTranscriberCLI()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('main.validate_video_file')
    @patch('main.validate_output_directory')
    @patch('main.VideoFile')
    def test_run_success_with_summary(self, mock_video_file, mock_validate_output, mock_validate_video):
        """Test successful pipeline run with summary generation."""
        # Setup validation mocks
        mock_validate_video.return_value = (True, "")
        mock_validate_output.return_value = None
        
        # Setup VideoFile mock
        mock_video = MagicMock()
        mock_video.filename = "test_video.mp4"
        mock_video_file.return_value = mock_video
        
        # Setup service mocks
        self.cli.audio_extractor.extract_audio.return_value = "/tmp/audio.wav"
        self.cli.audio_extractor.cleanup_temp_files.return_value = None
        
        # Setup transcription mock
        mock_transcription = MagicMock(spec=Transcription)
        mock_transcription.text = "This is the transcribed text"
        mock_transcription.get_word_count.return_value = 5
        mock_transcription.confidence = 0.95
        mock_transcription.save_to_file.return_value = None
        self.cli.transcriber.transcribe_to_model.return_value = mock_transcription
        
        # Setup summary mock
        mock_summary = MagicMock(spec=Summary)
        mock_summary.get_compression_ratio.return_value = 3.5
        mock_summary.save_to_file.return_value = None
        self.cli.summarizer.generate_summary.return_value = mock_summary
        
        # Run pipeline
        with patch('main.validate_api_key'):
            result = self.cli.run(self.test_video_path, self.output_dir, "test-api-key")
        
        # Verify results
        self.assertTrue(result["success"])
        self.assertEqual(result["video_file"], self.test_video_path)
        self.assertEqual(result["transcription_word_count"], 5)
        self.assertEqual(result["transcription_confidence"], 0.95)
        self.assertIn("test_video_transcription.txt", result["transcription_file"])
        self.assertIn("test_video_summary.txt", result["summary_file"])
        
        # Verify service calls
        self.cli.audio_extractor.extract_audio.assert_called_once_with(self.test_video_path)
        self.cli.transcriber.transcribe_to_model.assert_called_once_with("/tmp/audio.wav")
        self.cli.summarizer.generate_summary.assert_called_once_with("This is the transcribed text", "test-api-key")
        self.cli.audio_extractor.cleanup_temp_files.assert_called_once()
    
    @patch('main.validate_video_file')
    @patch('main.validate_output_directory')
    @patch('main.VideoFile')
    def test_run_success_without_summary(self, mock_video_file, mock_validate_output, mock_validate_video):
        """Test successful pipeline run without summary generation."""
        # Setup validation mocks
        mock_validate_video.return_value = (True, "")
        mock_validate_output.return_value = None
        
        # Setup VideoFile mock
        mock_video = MagicMock()
        mock_video.filename = "test_video.mp4"
        mock_video_file.return_value = mock_video
        
        # Setup service mocks
        self.cli.audio_extractor.extract_audio.return_value = "/tmp/audio.wav"
        self.cli.audio_extractor.cleanup_temp_files.return_value = None
        
        # Setup transcription mock
        mock_transcription = MagicMock(spec=Transcription)
        mock_transcription.text = "This is the transcribed text"
        mock_transcription.get_word_count.return_value = 5
        mock_transcription.confidence = 0.95
        mock_transcription.save_to_file.return_value = None
        self.cli.transcriber.transcribe_to_model.return_value = mock_transcription
        
        # Run pipeline without API key
        result = self.cli.run(self.test_video_path, self.output_dir)
        
        # Verify results
        self.assertTrue(result["success"])
        self.assertEqual(result["video_file"], self.test_video_path)
        self.assertIsNone(result["summary_file"])
        
        # Verify summarizer was not called
        self.cli.summarizer.generate_summary.assert_not_called()
    
    @patch('main.validate_video_file')
    def test_run_invalid_video_file(self, mock_validate_video):
        """Test pipeline with invalid video file."""
        mock_validate_video.return_value = (False, "File does not exist")
        
        result = self.cli.run("nonexistent.mp4", self.output_dir)
        
        self.assertFalse(result["success"])
        self.assertIn("Invalid video file", result["error"])
        self.assertIn("File does not exist", result["error"])
    
    @patch('main.validate_video_file')
    @patch('main.validate_output_directory')
    @patch('main.VideoFile')
    def test_run_audio_extraction_failure(self, mock_video_file, mock_validate_output, mock_validate_video):
        """Test pipeline with audio extraction failure."""
        # Setup validation mocks
        mock_validate_video.return_value = (True, "")
        mock_validate_output.return_value = None
        
        # Setup VideoFile mock
        mock_video = MagicMock()
        mock_video.filename = "test_video.mp4"
        mock_video_file.return_value = mock_video
        
        # Make audio extraction fail
        self.cli.audio_extractor.extract_audio.side_effect = RuntimeError("FFmpeg not found")
        
        result = self.cli.run(self.test_video_path, self.output_dir)
        
        self.assertFalse(result["success"])
        self.assertIn("Audio extraction failed", result["error"])
        self.assertIn("FFmpeg not found", result["error"])
    
    @patch('main.validate_video_file')
    @patch('main.validate_output_directory')
    @patch('main.VideoFile')
    def test_run_transcription_failure(self, mock_video_file, mock_validate_output, mock_validate_video):
        """Test pipeline with transcription failure."""
        # Setup validation mocks
        mock_validate_video.return_value = (True, "")
        mock_validate_output.return_value = None
        
        # Setup VideoFile mock
        mock_video = MagicMock()
        mock_video.filename = "test_video.mp4"
        mock_video_file.return_value = mock_video
        
        # Setup successful audio extraction
        self.cli.audio_extractor.extract_audio.return_value = "/tmp/audio.wav"
        self.cli.audio_extractor.cleanup_temp_files.return_value = None
        
        # Make transcription fail
        from services.transcriber import TranscriberError
        self.cli.transcriber.transcribe_to_model.side_effect = TranscriberError("No speech detected")
        
        result = self.cli.run(self.test_video_path, self.output_dir)
        
        self.assertFalse(result["success"])
        self.assertIn("Transcription failed", result["error"])
        self.assertIn("No speech detected", result["error"])
        
        # Verify cleanup was still called
        self.cli.audio_extractor.cleanup_temp_files.assert_called_once()
    
    @patch('main.validate_video_file')
    @patch('main.validate_output_directory')
    @patch('main.VideoFile')
    @patch('main.validate_api_key')
    def test_run_summary_failure_continues(self, mock_validate_api, mock_video_file, mock_validate_output, mock_validate_video):
        """Test that pipeline continues when summary generation fails."""
        # Setup validation mocks
        mock_validate_video.return_value = (True, "")
        mock_validate_output.return_value = None
        mock_validate_api.return_value = None
        
        # Setup VideoFile mock
        mock_video = MagicMock()
        mock_video.filename = "test_video.mp4"
        mock_video_file.return_value = mock_video
        
        # Setup successful services
        self.cli.audio_extractor.extract_audio.return_value = "/tmp/audio.wav"
        self.cli.audio_extractor.cleanup_temp_files.return_value = None
        
        mock_transcription = MagicMock(spec=Transcription)
        mock_transcription.text = "This is the transcribed text"
        mock_transcription.get_word_count.return_value = 5
        mock_transcription.confidence = 0.95
        mock_transcription.save_to_file.return_value = None
        self.cli.transcriber.transcribe_to_model.return_value = mock_transcription
        
        # Make summary generation fail
        self.cli.summarizer.generate_summary.side_effect = RuntimeError("API rate limit exceeded")
        
        result = self.cli.run(self.test_video_path, self.output_dir, "test-api-key")
        
        # Should still succeed with transcription
        self.assertTrue(result["success"])
        self.assertIsNone(result["summary_file"])
        self.assertIn("transcription.txt", result["transcription_file"])
    
    @patch('main.validate_output_directory')
    def test_run_output_directory_validation_failure(self, mock_validate_output):
        """Test pipeline with output directory validation failure."""
        mock_validate_output.side_effect = ValidationError("Permission denied")
        
        result = self.cli.run(self.test_video_path, "/root/restricted")
        
        self.assertFalse(result["success"])
        self.assertIn("Permission denied", result["error"])
    
    @patch('main.validate_video_file')
    @patch('main.validate_output_directory')
    @patch('main.VideoFile')
    def test_cleanup_on_failure(self, mock_video_file, mock_validate_output, mock_validate_video):
        """Test that cleanup is called even when pipeline fails."""
        # Setup validation mocks
        mock_validate_video.return_value = (True, "")
        mock_validate_output.return_value = None
        
        # Setup VideoFile mock
        mock_video = MagicMock()
        mock_video.filename = "test_video.mp4"
        mock_video_file.return_value = mock_video
        
        # Setup successful audio extraction
        self.cli.audio_extractor.extract_audio.return_value = "/tmp/audio.wav"
        self.cli.audio_extractor.cleanup_temp_files.return_value = None
        
        # Make transcription fail
        self.cli.transcriber.transcribe_to_model.side_effect = RuntimeError("Transcription error")
        
        result = self.cli.run(self.test_video_path, self.output_dir)
        
        self.assertFalse(result["success"])
        # Verify cleanup was called despite failure
        self.cli.audio_extractor.cleanup_temp_files.assert_called_once()
    
    @patch('main.validate_video_file')
    @patch('main.validate_output_directory')
    @patch('main.VideoFile')
    def test_cleanup_failure_warning(self, mock_video_file, mock_validate_output, mock_validate_video):
        """Test handling of cleanup failure."""
        # Setup validation mocks
        mock_validate_video.return_value = (True, "")
        mock_validate_output.return_value = None
        
        # Setup VideoFile mock
        mock_video = MagicMock()
        mock_video.filename = "test_video.mp4"
        mock_video_file.return_value = mock_video
        
        # Setup successful services
        self.cli.audio_extractor.extract_audio.return_value = "/tmp/audio.wav"
        mock_transcription = MagicMock(spec=Transcription)
        mock_transcription.text = "Text"
        mock_transcription.get_word_count.return_value = 1
        mock_transcription.confidence = 0.9
        mock_transcription.save_to_file.return_value = None
        self.cli.transcriber.transcribe_to_model.return_value = mock_transcription
        
        # Make cleanup fail
        self.cli.audio_extractor.cleanup_temp_files.side_effect = OSError("File locked")
        
        # Should still succeed despite cleanup failure
        result = self.cli.run(self.test_video_path, self.output_dir)
        
        self.assertTrue(result["success"])  # Pipeline should still succeed


class TestMainFunction(unittest.TestCase):
    """Test cases for the main function."""
    
    @patch('main.VideoTranscriberCLI')
    @patch('sys.argv', ['main.py', 'test.mp4'])
    def test_main_success(self, mock_cli_class):
        """Test main function with successful pipeline."""
        mock_cli = MagicMock()
        mock_cli.run.return_value = {"success": True}
        
        # Mock parse_arguments to return expected values
        mock_args = MagicMock()
        mock_args.video_path = 'test.mp4'
        mock_args.output_dir = 'output'
        mock_args.api_key = None
        mock_args.language = 'en-US'
        mock_cli.parse_arguments.return_value = mock_args
        
        mock_cli_class.return_value = mock_cli
        
        with self.assertRaises(SystemExit) as context:
            main()
        
        self.assertEqual(context.exception.code, 0)
        mock_cli.transcriber.set_language.assert_called_once_with("en-US")
    
    @patch('main.VideoTranscriberCLI')
    @patch('sys.argv', ['main.py', 'test.mp4', '--language', 'es-ES'])
    def test_main_custom_language(self, mock_cli_class):
        """Test main function with custom language."""
        mock_cli = MagicMock()
        mock_cli.run.return_value = {"success": True}
        
        # Mock parse_arguments to return expected values
        mock_args = MagicMock()
        mock_args.video_path = 'test.mp4'
        mock_args.output_dir = 'output'
        mock_args.api_key = None
        mock_args.language = 'es-ES'
        mock_cli.parse_arguments.return_value = mock_args
        
        mock_cli_class.return_value = mock_cli
        
        with self.assertRaises(SystemExit) as context:
            main()
        
        self.assertEqual(context.exception.code, 0)
        mock_cli.transcriber.set_language.assert_called_once_with("es-ES")
    
    @patch('main.VideoTranscriberCLI')
    @patch('sys.argv', ['main.py', 'test.mp4'])
    def test_main_failure(self, mock_cli_class):
        """Test main function with pipeline failure."""
        mock_cli = MagicMock()
        mock_cli.run.return_value = {"success": False}
        mock_cli_class.return_value = mock_cli
        
        with self.assertRaises(SystemExit) as context:
            main()
        
        self.assertEqual(context.exception.code, 1)
    
    @patch('main.VideoTranscriberCLI')
    @patch('sys.argv', ['main.py', 'test.mp4', '--api-key', 'sk-test123'])
    @patch.dict('os.environ', {}, clear=True)
    def test_main_api_key_from_args(self, mock_cli_class):
        """Test main function with API key from command line."""
        mock_cli = MagicMock()
        mock_cli.run.return_value = {"success": True}
        
        # Mock parse_arguments to return expected values
        mock_args = MagicMock()
        mock_args.video_path = 'test.mp4'
        mock_args.output_dir = 'output'
        mock_args.api_key = 'sk-test123'
        mock_args.language = 'en-US'
        mock_cli.parse_arguments.return_value = mock_args
        
        mock_cli_class.return_value = mock_cli
        
        with self.assertRaises(SystemExit):
            main()
        
        # Verify API key was passed from command line argument
        mock_cli.run.assert_called_once()
        call_args = mock_cli.run.call_args
        self.assertEqual(call_args[1]['api_key'], 'sk-test123')
    
    @patch('main.VideoTranscriberCLI')
    @patch('sys.argv', ['main.py', 'test.mp4'])
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-env123'})
    def test_main_api_key_from_env(self, mock_cli_class):
        """Test main function with API key from environment."""
        mock_cli = MagicMock()
        mock_cli.run.return_value = {"success": True}
        
        # Mock parse_arguments to return expected values
        mock_args = MagicMock()
        mock_args.video_path = 'test.mp4'
        mock_args.output_dir = 'output'
        mock_args.api_key = None  # From args
        mock_args.language = 'en-US'
        mock_cli.parse_arguments.return_value = mock_args
        
        mock_cli_class.return_value = mock_cli
        
        with self.assertRaises(SystemExit):
            main()
        
        # Verify API key was taken from environment
        mock_cli.run.assert_called_once()
        call_args = mock_cli.run.call_args
        self.assertEqual(call_args[1]['api_key'], 'sk-env123')


class TestArgumentParsing(unittest.TestCase):
    """Test cases for command line argument parsing."""
    
    def setUp(self):
        """Set up CLI instance for testing."""
        with patch.multiple(
            'main',
            Config=MagicMock,
            FileHandler=MagicMock,
            AudioExtractor=MagicMock,
            Transcriber=MagicMock,
            Summarizer=MagicMock
        ):
            self.cli = VideoTranscriberCLI()
    
    @patch('sys.argv', ['main.py', 'test.mp4'])
    def test_parse_minimal_args(self):
        """Test parsing minimal required arguments."""
        args = self.cli.parse_arguments()
        
        self.assertEqual(args.video_path, 'test.mp4')
        self.assertEqual(args.output_dir, 'output')
        self.assertIsNone(args.api_key)
        self.assertEqual(args.language, 'en-US')
        self.assertFalse(args.verbose)
    
    @patch('sys.argv', ['main.py', 'video.mp4', '--output-dir', 'transcripts/', '--api-key', 'sk-123', '--language', 'fr-FR', '--verbose'])
    def test_parse_all_args(self):
        """Test parsing all arguments."""
        args = self.cli.parse_arguments()
        
        self.assertEqual(args.video_path, 'video.mp4')
        self.assertEqual(args.output_dir, 'transcripts/')
        self.assertEqual(args.api_key, 'sk-123')
        self.assertEqual(args.language, 'fr-FR')
        self.assertTrue(args.verbose)
    
    @patch('sys.argv', ['main.py', 'video.mp4', '-o', 'out/', '-k', 'sk-456', '-l', 'de-DE', '-v'])
    def test_parse_short_args(self):
        """Test parsing short argument forms."""
        args = self.cli.parse_arguments()
        
        self.assertEqual(args.video_path, 'video.mp4')
        self.assertEqual(args.output_dir, 'out/')
        self.assertEqual(args.api_key, 'sk-456')
        self.assertEqual(args.language, 'de-DE')
        self.assertTrue(args.verbose)


if __name__ == '__main__':
    unittest.main()