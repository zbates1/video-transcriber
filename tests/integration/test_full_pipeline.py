"""Integration tests for the full video transcription pipeline."""

import os
import tempfile
import unittest
from unittest.mock import patch, Mock
import json

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Mock external dependencies before importing
from unittest.mock import MagicMock
sys.modules['speech_recognition'] = MagicMock()
sys.modules['pydub'] = MagicMock()
sys.modules['pyaudio'] = MagicMock()

from src.main import VideoTranscriberCLI
from src.models.video_file import VideoFile
from src.models.transcription import Transcription
from src.models.summary import Summary


class TestFullPipeline(unittest.TestCase):
    """Integration tests for the complete video transcription pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        
        # Create a mock video file (just an empty file with .mp4 extension)
        with open(self.test_video_path, 'wb') as f:
            # Write minimal MP4 header-like data
            f.write(b'\x00\x00\x00\x20ftypmp42')
            f.write(b'\x00' * 500)  # Pad with zeros to make it look like a video file
        
        # Initialize CLI
        self.cli = VideoTranscriberCLI()
        
        # Mock API key for testing
        self.mock_api_key = "sk-test-key-for-integration-testing"
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.services.audio_extractor.AudioExtractor.extract_audio')
    @patch('src.services.audio_extractor.AudioExtractor.cleanup_temp_files')
    @patch('src.services.transcriber.Transcriber.transcribe_to_model')
    @patch('src.services.summarizer.requests.post')
    def test_full_pipeline_with_summary(self, mock_requests, mock_transcribe, mock_cleanup, mock_extract):
        """Test complete pipeline including summary generation."""
        # Setup mocks
        mock_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        mock_extract.return_value = mock_audio_path
        mock_cleanup.return_value = None
        
        # Mock transcription
        mock_transcription = Transcription(
            text="This is a test transcription of the video content.",
            confidence=0.95
        )
        mock_transcribe.return_value = mock_transcription
        
        # Mock successful API response for summary
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test summary of the transcribed content."
                    }
                }
            ]
        }
        mock_requests.return_value = mock_response
        
        # Run the pipeline
        results = self.cli.run(
            video_path=self.test_video_path,
            output_dir=self.output_dir,
            api_key=self.mock_api_key
        )
        
        # Verify results
        self.assertTrue(results["success"])
        self.assertEqual(results["video_file"], self.test_video_path)
        self.assertEqual(results["output_directory"], self.output_dir)
        self.assertIsNotNone(results["transcription_file"])
        self.assertIsNotNone(results["summary_file"])
        self.assertEqual(results["transcription_word_count"], mock_transcription.get_word_count())
        self.assertEqual(results["transcription_confidence"], 0.95)
        
        # Verify files were created
        self.assertTrue(os.path.exists(results["transcription_file"]))
        self.assertTrue(os.path.exists(results["summary_file"]))
        
        # Verify file contents
        with open(results["transcription_file"], 'r', encoding='utf-8') as f:
            transcription_content = f.read()
            self.assertIn("This is a test transcription", transcription_content)
        
        with open(results["summary_file"], 'r', encoding='utf-8') as f:
            summary_content = f.read()
            self.assertIn("This is a test summary", summary_content)
        
        # Verify service methods were called
        mock_extract.assert_called_once_with(self.test_video_path)
        mock_transcribe.assert_called_once_with(mock_audio_path)
        mock_cleanup.assert_called_once()
        mock_requests.assert_called_once()
    
    @patch('src.services.audio_extractor.AudioExtractor.extract_audio')
    @patch('src.services.audio_extractor.AudioExtractor.cleanup_temp_files')
    @patch('src.services.transcriber.Transcriber.transcribe_to_model')
    def test_full_pipeline_without_summary(self, mock_transcribe, mock_cleanup, mock_extract):
        """Test pipeline without summary generation (no API key)."""
        # Setup mocks
        mock_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        mock_extract.return_value = mock_audio_path
        mock_cleanup.return_value = None
        
        # Mock transcription
        mock_transcription = Transcription(
            text="This is a test transcription without summary.",
            confidence=0.88
        )
        mock_transcribe.return_value = mock_transcription
        
        # Run the pipeline without API key
        results = self.cli.run(
            video_path=self.test_video_path,
            output_dir=self.output_dir,
            api_key=None
        )
        
        # Verify results
        self.assertTrue(results["success"])
        self.assertEqual(results["video_file"], self.test_video_path)
        self.assertEqual(results["output_directory"], self.output_dir)
        self.assertIsNotNone(results["transcription_file"])
        self.assertIsNone(results["summary_file"])
        self.assertEqual(results["transcription_word_count"], mock_transcription.get_word_count())
        
        # Verify transcription file was created but not summary
        self.assertTrue(os.path.exists(results["transcription_file"]))
        
        # Verify service methods were called appropriately
        mock_extract.assert_called_once_with(self.test_video_path)
        mock_transcribe.assert_called_once_with(mock_audio_path)
        mock_cleanup.assert_called_once()
    
    @patch('src.services.audio_extractor.AudioExtractor.extract_audio')
    def test_pipeline_audio_extraction_failure(self, mock_extract):
        """Test pipeline behavior when audio extraction fails."""
        # Mock audio extraction failure
        mock_extract.side_effect = RuntimeError("FFmpeg not found")
        
        # Run the pipeline
        results = self.cli.run(
            video_path=self.test_video_path,
            output_dir=self.output_dir,
            api_key=None
        )
        
        # Verify failure handling
        self.assertFalse(results["success"])
        self.assertEqual(results["video_file"], self.test_video_path)
        self.assertIn("error", results)
        self.assertIn("Audio extraction failed", results["error"])
    
    @patch('src.services.audio_extractor.AudioExtractor.extract_audio')
    @patch('src.services.audio_extractor.AudioExtractor.cleanup_temp_files')
    @patch('src.services.transcriber.Transcriber.transcribe_to_model')
    def test_pipeline_transcription_failure(self, mock_transcribe, mock_cleanup, mock_extract):
        """Test pipeline behavior when transcription fails."""
        # Setup mocks
        mock_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        mock_extract.return_value = mock_audio_path
        mock_cleanup.return_value = None
        
        # Mock transcription failure
        mock_transcribe.side_effect = RuntimeError("Speech recognition failed")
        
        # Run the pipeline
        results = self.cli.run(
            video_path=self.test_video_path,
            output_dir=self.output_dir,
            api_key=None
        )
        
        # Verify failure handling
        self.assertFalse(results["success"])
        self.assertEqual(results["video_file"], self.test_video_path)
        self.assertIn("error", results)
        self.assertIn("Transcription failed", results["error"])
        
        # Verify cleanup still happens
        mock_cleanup.assert_called_once()
    
    def test_pipeline_invalid_video_file(self):
        """Test pipeline behavior with invalid video file."""
        invalid_video_path = os.path.join(self.temp_dir, "not_a_video.txt")
        
        # Create a text file instead of video
        with open(invalid_video_path, 'w') as f:
            f.write("This is not a video file")
        
        # Run the pipeline
        results = self.cli.run(
            video_path=invalid_video_path,
            output_dir=self.output_dir,
            api_key=None
        )
        
        # Verify failure handling
        self.assertFalse(results["success"])
        self.assertEqual(results["video_file"], invalid_video_path)
        self.assertIn("error", results)
        self.assertIn("Invalid video file", results["error"])
    
    def test_pipeline_nonexistent_video_file(self):
        """Test pipeline behavior with non-existent video file."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.mp4")
        
        # Run the pipeline
        results = self.cli.run(
            video_path=nonexistent_path,
            output_dir=self.output_dir,
            api_key=None
        )
        
        # Verify failure handling
        self.assertFalse(results["success"])
        self.assertEqual(results["video_file"], nonexistent_path)
        self.assertIn("error", results)
        self.assertIn("Invalid video file", results["error"])
    
    @patch('src.services.audio_extractor.AudioExtractor.extract_audio')
    @patch('src.services.audio_extractor.AudioExtractor.cleanup_temp_files')
    @patch('src.services.transcriber.Transcriber.transcribe_to_model')
    @patch('src.services.summarizer.requests.post')
    def test_pipeline_summary_generation_failure(self, mock_requests, mock_transcribe, mock_cleanup, mock_extract):
        """Test pipeline behavior when summary generation fails but transcription succeeds."""
        # Setup mocks
        mock_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        mock_extract.return_value = mock_audio_path
        mock_cleanup.return_value = None
        
        # Mock transcription
        mock_transcription = Transcription(
            text="This is a test transcription for failed summary.",
            confidence=0.92
        )
        mock_transcribe.return_value = mock_transcription
        
        # Mock failed API response for summary
        mock_response = Mock()
        mock_response.status_code = 401  # Unauthorized
        mock_requests.return_value = mock_response
        
        # Run the pipeline
        results = self.cli.run(
            video_path=self.test_video_path,
            output_dir=self.output_dir,
            api_key=self.mock_api_key
        )
        
        # Verify results - should succeed with transcription only
        self.assertTrue(results["success"])
        self.assertEqual(results["video_file"], self.test_video_path)
        self.assertIsNotNone(results["transcription_file"])
        self.assertIsNone(results["summary_file"])  # Summary should fail gracefully
        
        # Verify transcription file was still created
        self.assertTrue(os.path.exists(results["transcription_file"]))
    
    @patch('src.services.audio_extractor.AudioExtractor.extract_audio')
    @patch('src.services.audio_extractor.AudioExtractor.cleanup_temp_files') 
    @patch('src.services.transcriber.Transcriber.transcribe_to_model')
    def test_pipeline_creates_output_directory(self, mock_transcribe, mock_cleanup, mock_extract):
        """Test that pipeline creates output directory if it doesn't exist."""
        # Setup mocks
        mock_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        mock_extract.return_value = mock_audio_path
        mock_cleanup.return_value = None
        
        # Mock transcription
        mock_transcription = Transcription(
            text="Test transcription for directory creation.",
            confidence=0.90
        )
        mock_transcribe.return_value = mock_transcription
        
        # Use a non-existent output directory
        non_existent_output = os.path.join(self.temp_dir, "new_output", "subdir")
        
        # Run the pipeline
        results = self.cli.run(
            video_path=self.test_video_path,
            output_dir=non_existent_output,
            api_key=None
        )
        
        # Verify the pipeline succeeded
        self.assertTrue(results["success"])
        
        # Verify the output directory was created
        self.assertTrue(os.path.exists(non_existent_output))
        self.assertTrue(os.path.exists(results["transcription_file"]))


class TestVideoFileIntegration(unittest.TestCase):
    """Integration tests for VideoFile model with real file operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_video_file_with_real_mp4_file(self):
        """Test VideoFile model with a real MP4-like file."""
        video_path = os.path.join(self.temp_dir, "test_real.mp4")
        
        # Create a more realistic MP4 file structure
        with open(video_path, 'wb') as f:
            # Write MP4 file signature and basic structure
            f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42mp41')
            f.write(b'\x00' * 1000)  # Add some content
        
        # Test VideoFile model
        video_file = VideoFile(video_path)
        
        # Verify properties
        self.assertEqual(video_file.path, video_path)
        self.assertEqual(video_file.filename, "test_real.mp4")
        self.assertIsNotNone(video_file.size)
        self.assertGreater(video_file.size, 0)
        
        # Verify validation
        self.assertTrue(video_file.validate())
        
        # Verify metadata
        metadata = video_file.get_metadata()
        self.assertEqual(metadata['path'], video_path)
        self.assertEqual(metadata['filename'], "test_real.mp4")
        self.assertTrue(metadata['exists'])
        self.assertTrue(metadata['is_valid'])


if __name__ == '__main__':
    unittest.main()