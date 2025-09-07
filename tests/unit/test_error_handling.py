"""Comprehensive error handling tests for the video transcriber pipeline."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

# Mock speech_recognition module since it may not be installed
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

from src.models.video_file import VideoFile
from src.services.audio_extractor import AudioExtractor
from src.services.transcriber import Transcriber, TranscriberError
from src.services.summarizer import Summarizer
from src.utils.config import Config
from src.utils.file_handler import FileHandler
from src.utils.validators import ValidationError


class TestErrorHandling(unittest.TestCase):
    """Test cases for comprehensive error handling scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        self.nonexistent_video_path = "/nonexistent/path/video.mp4"
        self.invalid_format_path = os.path.join(self.temp_dir, "test.txt")
        
        # Create test files
        with open(self.test_video_path, 'wb') as f:
            f.write(b"fake video content")
        with open(self.invalid_format_path, 'w') as f:
            f.write("not a video file")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    # Video File Error Handling Tests
    
    def test_video_file_nonexistent_file_error(self):
        """Test VideoFile handles non-existent files gracefully."""
        video = VideoFile(self.nonexistent_video_path)
        
        self.assertFalse(video.validate())
        self.assertIsNone(video.size)
        self.assertFalse(video.get_metadata()['exists'])
        self.assertFalse(video.get_metadata()['is_valid'])
    
    def test_video_file_invalid_format_error(self):
        """Test VideoFile handles invalid file formats gracefully."""
        video = VideoFile(self.invalid_format_path)
        
        self.assertFalse(video.validate())
        self.assertIsNotNone(video.size)  # File exists but invalid format
        self.assertTrue(video.get_metadata()['exists'])
        self.assertFalse(video.get_metadata()['is_valid'])
    
    def test_video_file_directory_path_error(self):
        """Test VideoFile handles directory paths gracefully."""
        video = VideoFile(self.temp_dir)
        
        self.assertFalse(video.validate())
        # Directory size may return 0 or small number, not None
        self.assertIsNotNone(video.size)
    
    def test_video_file_permission_error(self):
        """Test VideoFile handles permission errors gracefully."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('os.path.getsize', side_effect=PermissionError("Access denied")):
                    video = VideoFile(self.test_video_path)
                    self.assertIsNone(video.size)
    
    # Audio Extractor Error Handling Tests
    
    @patch('src.services.audio_extractor.get_config')
    def test_audio_extractor_nonexistent_video_error(self, mock_get_config):
        """Test AudioExtractor handles non-existent video files gracefully."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        extractor = AudioExtractor()
        result = extractor.extract_audio(self.nonexistent_video_path)
        
        self.assertIsNone(result)
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.subprocess.run')
    def test_audio_extractor_ffmpeg_not_found_error(self, mock_subprocess, mock_get_config):
        """Test AudioExtractor handles missing ffmpeg gracefully."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        mock_subprocess.side_effect = FileNotFoundError("ffmpeg not found")
        
        extractor = AudioExtractor()
        result = extractor.extract_audio(self.test_video_path)
        
        self.assertIsNone(result)
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.subprocess.run')
    def test_audio_extractor_ffmpeg_timeout_error(self, mock_subprocess, mock_get_config):
        """Test AudioExtractor handles ffmpeg timeout gracefully."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired(cmd=['ffmpeg'], timeout=300)
        
        extractor = AudioExtractor()
        result = extractor.extract_audio(self.test_video_path)
        
        self.assertIsNone(result)
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.FileHandler.ensure_directory_exists')
    def test_audio_extractor_temp_directory_creation_error(self, mock_ensure_dir, mock_get_config):
        """Test AudioExtractor handles temp directory creation failure."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = "/invalid/temp/path"
        mock_get_config.return_value = mock_config
        
        mock_ensure_dir.return_value = False
        
        # Should still create extractor but with failed directory creation
        extractor = AudioExtractor()
        self.assertIsNotNone(extractor)
    
    # Transcriber Error Handling Tests
    
    def test_transcriber_unsupported_audio_format_error(self):
        """Test Transcriber handles unsupported audio formats gracefully."""
        transcriber = Transcriber()
        
        # Create unsupported audio format file
        unsupported_file = os.path.join(self.temp_dir, "test.mp3")
        with open(unsupported_file, 'wb') as f:
            f.write(b"fake audio content")
        
        with self.assertRaises(TranscriberError):
            transcriber.transcribe(unsupported_file)
    
    def test_transcriber_nonexistent_audio_file_error(self):
        """Test Transcriber handles non-existent audio files gracefully."""
        transcriber = Transcriber()
        
        with self.assertRaises(TranscriberError):
            transcriber.transcribe("/nonexistent/audio.wav")
    
    @patch('src.services.transcriber.sr.Recognizer')
    def test_transcriber_speech_recognition_api_error(self, mock_recognizer):
        """Test Transcriber handles speech recognition API errors gracefully."""
        # Create valid audio file
        valid_audio = os.path.join(self.temp_dir, "test.wav")
        with open(valid_audio, 'wb') as f:
            f.write(b"fake wav content")
        
        # Mock speech recognition request error
        mock_instance = mock_recognizer.return_value
        mock_instance.recognize_google.side_effect = Exception("API request failed")
        
        transcriber = Transcriber()
        
        with self.assertRaises(TranscriberError):
            transcriber.transcribe(valid_audio)
    
    @patch('src.services.transcriber.sr.AudioFile')
    def test_transcriber_audio_file_read_error(self, mock_audio_file):
        """Test Transcriber handles audio file read errors gracefully."""
        valid_audio = os.path.join(self.temp_dir, "test.wav")
        with open(valid_audio, 'wb') as f:
            f.write(b"fake wav content")
        
        # Mock audio file read error
        mock_audio_file.side_effect = Exception("Cannot read audio file")
        
        transcriber = Transcriber()
        
        with self.assertRaises(TranscriberError):
            transcriber.transcribe(valid_audio)
    
    # Summarizer Error Handling Tests
    
    def test_summarizer_no_api_key_error(self):
        """Test Summarizer handles missing API key gracefully."""
        with patch('src.services.summarizer.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_chatgpt_api_key.return_value = None
            mock_get_config.return_value = mock_config
            
            summarizer = Summarizer()
            result = summarizer.generate_summary("test text")
            
            self.assertIsNone(result)
    
    def test_summarizer_invalid_api_key_error(self):
        """Test Summarizer handles invalid API key gracefully."""
        summarizer = Summarizer(api_key="invalid-key")
        
        with patch('src.services.summarizer.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
            mock_post.return_value = mock_response
            
            result = summarizer.generate_summary("test text")
            
            self.assertIsNone(result)
    
    @patch('src.services.summarizer.requests.post')
    def test_summarizer_network_error(self, mock_post):
        """Test Summarizer handles network errors gracefully."""
        summarizer = Summarizer(api_key="sk-test-key")
        
        # Mock network error
        mock_post.side_effect = Exception("Network connection error")
        
        result = summarizer.generate_summary("test text")
        
        self.assertIsNone(result)
    
    @patch('src.services.summarizer.requests.post')
    def test_summarizer_rate_limit_error(self, mock_post):
        """Test Summarizer handles rate limit errors gracefully."""
        summarizer = Summarizer(api_key="sk-test-key")
        
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        mock_post.return_value = mock_response
        
        result = summarizer.generate_summary("test text")
        
        self.assertIsNone(result)
    
    @patch('src.services.summarizer.requests.post')
    def test_summarizer_malformed_response_error(self, mock_post):
        """Test Summarizer handles malformed API responses gracefully."""
        summarizer = Summarizer(api_key="sk-test-key")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response format"}
        mock_post.return_value = mock_response
        
        result = summarizer.generate_summary("test text")
        
        self.assertIsNone(result)
    
    def test_summarizer_empty_text_input_error(self):
        """Test Summarizer handles empty text input gracefully."""
        summarizer = Summarizer(api_key="sk-test-key")
        
        result = summarizer.generate_summary("")
        
        self.assertIsNone(result)
    
    # File System Error Handling Tests
    
    def test_file_handler_permission_denied_error(self):
        """Test FileHandler handles permission denied errors gracefully."""
        # Try to write to a read-only location (simulated)
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = FileHandler.write_text_file("/protected/file.txt", "test content")
            self.assertFalse(result)
    
    def test_file_handler_disk_full_error(self):
        """Test FileHandler handles disk full errors gracefully."""
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            result = FileHandler.write_text_file(os.path.join(self.temp_dir, "test.txt"), "test content")
            self.assertFalse(result)
    
    def test_file_handler_directory_creation_permission_error(self):
        """Test FileHandler handles directory creation permission errors gracefully."""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            result = FileHandler.ensure_directory_exists("/protected/new/directory")
            self.assertFalse(result)
    
    def test_file_handler_corrupted_file_read_error(self):
        """Test FileHandler handles corrupted file read errors gracefully."""
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')):
            result = FileHandler.read_text_file(self.test_video_path)
            self.assertIsNone(result)
    
    # Configuration Error Handling Tests
    
    @patch('os.path.exists')
    def test_config_file_not_found_error(self, mock_exists):
        """Test Config handles missing config file gracefully."""
        mock_exists.return_value = False
        
        # Should create config without crashing
        config = Config()
        self.assertIsNotNone(config)
        self.assertIsNone(config.get_chatgpt_api_key())
    
    def test_config_file_corrupted_error(self):
        """Test Config handles corrupted config file gracefully."""
        corrupted_config_path = os.path.join(self.temp_dir, "corrupted_config.txt")
        with open(corrupted_config_path, 'w') as f:
            f.write("invalid=config=format=with=too=many=equals\n")
            f.write("malformed line without equals\n")
            f.write("=empty_key\n")
        
        # Should handle corrupted config gracefully
        config = Config(config_file=corrupted_config_path)
        self.assertIsNotNone(config)
    
    @patch('builtins.open')
    def test_config_save_permission_error(self, mock_open):
        """Test Config handles config save permission errors gracefully."""
        mock_open.side_effect = PermissionError("Permission denied")
        
        config = Config()
        config.set_chatgpt_api_key("sk-test-key")  # Should not crash
        
        # Verify it handled the error gracefully
        self.assertIsNotNone(config)
    
    # Integration Pipeline Error Handling Tests
    
    def test_pipeline_cascade_failure_scenario(self):
        """Test how pipeline handles cascade failure scenarios."""
        # Simulate a scenario where multiple components fail
        with patch('src.services.audio_extractor.subprocess.run', side_effect=FileNotFoundError("ffmpeg not found")):
            with patch('src.services.transcriber.sr.Recognizer') as mock_recognizer:
                mock_instance = mock_recognizer.return_value
                mock_instance.recognize_google.side_effect = Exception("API failed")
                
                with patch('src.services.summarizer.requests.post', side_effect=Exception("Network error")):
                    # Each component should handle its own errors gracefully
                    
                    # Audio extraction should fail gracefully
                    extractor = AudioExtractor()
                    audio_path = extractor.extract_audio(self.test_video_path)
                    self.assertIsNone(audio_path)
                    
                    # Transcription should fail gracefully
                    transcriber = Transcriber()
                    with self.assertRaises((TranscriberError, ValidationError)):
                        transcriber.transcribe("/fake/audio.wav")
                    
                    # Summarization should fail gracefully
                    summarizer = Summarizer(api_key="sk-test-key")
                    summary = summarizer.generate_summary("test text")
                    self.assertIsNone(summary)
    
    def test_cleanup_on_failure_scenario(self):
        """Test that temporary files are cleaned up even when failures occur."""
        with patch('src.services.audio_extractor.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.get_temp_directory.return_value = self.temp_dir
            mock_get_config.return_value = mock_config
            
            extractor = AudioExtractor()
            # Manually add temp files to simulate partial processing
            fake_temp_file = os.path.join(self.temp_dir, "fake_temp.wav")
            with open(fake_temp_file, 'w') as f:
                f.write("fake temp content")
            
            extractor._temp_files.append(fake_temp_file)
            
            # Cleanup should work even if some files fail to delete
            with patch('src.services.audio_extractor.FileHandler.delete_file', 
                      side_effect=[True, Exception("Delete failed"), True]):
                extractor.cleanup_temp_files()
                
                # Temp files list should still be cleared
                self.assertEqual(extractor._temp_files, [])


if __name__ == '__main__':
    unittest.main()