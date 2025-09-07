"""Unit tests for AudioExtractor service."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from src.services.audio_extractor import AudioExtractor


class TestAudioExtractor(unittest.TestCase):
    """Test cases for AudioExtractor service."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory and files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_video_file = os.path.join(self.temp_dir, "test_video.mp4")
        self.temp_audio_file = os.path.join(self.temp_dir, "test_audio.wav")
        
        # Create fake video file
        with open(self.temp_video_file, 'wb') as f:
            f.write(b"fake video content")
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files and directory
        if os.path.exists(self.temp_video_file):
            os.remove(self.temp_video_file)
        if os.path.exists(self.temp_audio_file):
            os.remove(self.temp_audio_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    @patch('src.services.audio_extractor.get_config')
    def test_init_creates_temp_directory(self, mock_get_config):
        """Test AudioExtractor initialization creates temp directory."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        with patch('src.services.audio_extractor.FileHandler.ensure_directory_exists') as mock_ensure_dir:
            extractor = AudioExtractor()
            
            mock_ensure_dir.assert_called_once_with(self.temp_dir)
            self.assertEqual(extractor._temp_directory, self.temp_dir)
            self.assertEqual(extractor._temp_files, [])
    
    @patch('src.services.audio_extractor.get_config')
    def test_extract_audio_nonexistent_file(self, mock_get_config):
        """Test extract_audio returns None for non-existent file."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        extractor = AudioExtractor()
        result = extractor.extract_audio("/nonexistent/video.mp4")
        
        self.assertIsNone(result)
    
    @patch('src.services.audio_extractor.get_config')
    def test_extract_audio_directory_path(self, mock_get_config):
        """Test extract_audio returns None for directory path."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        extractor = AudioExtractor()
        result = extractor.extract_audio(self.temp_dir)
        
        self.assertIsNone(result)
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.subprocess.run')
    @patch('src.services.audio_extractor.FileHandler.create_unique_filename')
    def test_extract_audio_success(self, mock_unique_filename, mock_subprocess, mock_get_config):
        """Test successful audio extraction."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        expected_audio_path = os.path.join(self.temp_dir, "test_video_audio.wav")
        mock_unique_filename.return_value = expected_audio_path
        
        # Mock successful subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Create the expected output file
        with open(expected_audio_path, 'w') as f:
            f.write("fake audio content")
        
        extractor = AudioExtractor()
        result = extractor.extract_audio(self.temp_video_file)
        
        self.assertEqual(result, expected_audio_path)
        self.assertIn(expected_audio_path, extractor._temp_files)
        
        # Verify ffmpeg command was called correctly
        expected_cmd = [
            'ffmpeg',
            '-i', self.temp_video_file,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',
            expected_audio_path
        ]
        mock_subprocess.assert_called_once_with(
            expected_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Clean up
        os.remove(expected_audio_path)
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.subprocess.run')
    def test_extract_audio_ffmpeg_failure(self, mock_subprocess, mock_get_config):
        """Test extract_audio handles ffmpeg failure gracefully."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        # Mock failed subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        extractor = AudioExtractor()
        result = extractor.extract_audio(self.temp_video_file)
        
        self.assertIsNone(result)
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.subprocess.run')
    def test_extract_audio_timeout(self, mock_subprocess, mock_get_config):
        """Test extract_audio handles timeout gracefully."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        # Mock timeout exception
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired(cmd=['ffmpeg'], timeout=300)
        
        extractor = AudioExtractor()
        result = extractor.extract_audio(self.temp_video_file)
        
        self.assertIsNone(result)
    
    @patch('src.services.audio_extractor.get_config')
    def test_cleanup_temp_files_empty_list(self, mock_get_config):
        """Test cleanup_temp_files with empty file list."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        extractor = AudioExtractor()
        extractor.cleanup_temp_files()
        
        self.assertEqual(extractor._temp_files, [])
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.FileHandler.delete_file')
    def test_cleanup_temp_files_success(self, mock_delete_file, mock_get_config):
        """Test successful cleanup of temporary files."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        mock_delete_file.return_value = True
        
        extractor = AudioExtractor()
        test_files = ["/tmp/file1.wav", "/tmp/file2.wav"]
        extractor._temp_files = test_files.copy()
        
        extractor.cleanup_temp_files()
        
        # Verify all files were attempted to be deleted
        expected_calls = [call(file_path) for file_path in test_files]
        mock_delete_file.assert_has_calls(expected_calls, any_order=True)
        
        # Verify temp files list is cleared
        self.assertEqual(extractor._temp_files, [])
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.FileHandler.delete_file')
    def test_cleanup_temp_files_partial_failure(self, mock_delete_file, mock_get_config):
        """Test cleanup continues even if some file deletions fail."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        # Mock one successful deletion and one failure
        mock_delete_file.side_effect = [True, Exception("Delete failed"), True]
        
        extractor = AudioExtractor()
        test_files = ["/tmp/file1.wav", "/tmp/file2.wav", "/tmp/file3.wav"]
        extractor._temp_files = test_files.copy()
        
        extractor.cleanup_temp_files()
        
        # Verify all files were attempted to be deleted
        expected_calls = [call(file_path) for file_path in test_files]
        mock_delete_file.assert_has_calls(expected_calls, any_order=True)
        
        # Verify temp files list is still cleared despite failures
        self.assertEqual(extractor._temp_files, [])
    
    @patch('src.services.audio_extractor.get_config')
    def test_get_temp_files(self, mock_get_config):
        """Test get_temp_files returns copy of internal list."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        extractor = AudioExtractor()
        test_files = ["/tmp/file1.wav", "/tmp/file2.wav"]
        extractor._temp_files = test_files.copy()
        
        result = extractor.get_temp_files()
        
        self.assertEqual(result, test_files)
        # Verify it's a copy, not the same object
        self.assertIsNot(result, extractor._temp_files)
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.subprocess.run')
    def test_is_ffmpeg_available_true(self, mock_subprocess, mock_get_config):
        """Test is_ffmpeg_available returns True when ffmpeg is available."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        extractor = AudioExtractor()
        result = extractor.is_ffmpeg_available()
        
        self.assertTrue(result)
        mock_subprocess.assert_called_once_with(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=10
        )
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.subprocess.run')
    def test_is_ffmpeg_available_false(self, mock_subprocess, mock_get_config):
        """Test is_ffmpeg_available returns False when ffmpeg is not available."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        mock_subprocess.side_effect = FileNotFoundError("ffmpeg not found")
        
        extractor = AudioExtractor()
        result = extractor.is_ffmpeg_available()
        
        self.assertFalse(result)
    
    @patch('src.services.audio_extractor.get_config')
    @patch('src.services.audio_extractor.subprocess.run')
    @patch('src.services.audio_extractor.FileHandler.get_file_size')
    def test_get_audio_info_success(self, mock_get_file_size, mock_subprocess, mock_get_config):
        """Test get_audio_info returns correct audio information."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        mock_get_file_size.return_value = 1024
        
        # Mock successful ffprobe execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''
        {
            "streams": [{
                "sample_rate": "16000",
                "channels": 1,
                "codec_name": "pcm_s16le"
            }],
            "format": {
                "duration": "30.5"
            }
        }
        '''
        mock_subprocess.return_value = mock_result
        
        # Create test audio file
        with open(self.temp_audio_file, 'w') as f:
            f.write("fake audio content")
        
        extractor = AudioExtractor()
        result = extractor.get_audio_info(self.temp_audio_file)
        
        expected_info = {
            'duration': 30.5,
            'sample_rate': 16000,
            'channels': 1,
            'codec': 'pcm_s16le',
            'size': 1024
        }
        
        self.assertEqual(result, expected_info)
        
        # Clean up
        os.remove(self.temp_audio_file)
    
    @patch('src.services.audio_extractor.get_config')
    def test_get_audio_info_nonexistent_file(self, mock_get_config):
        """Test get_audio_info returns None for non-existent file."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        extractor = AudioExtractor()
        result = extractor.get_audio_info("/nonexistent/audio.wav")
        
        self.assertIsNone(result)
    
    @patch('src.services.audio_extractor.get_config')
    def test_context_manager_cleanup(self, mock_get_config):
        """Test context manager automatically cleans up temp files."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        with patch.object(AudioExtractor, 'cleanup_temp_files') as mock_cleanup:
            with AudioExtractor() as extractor:
                # Add some fake temp files
                extractor._temp_files = ["/tmp/test.wav"]
            
            # Verify cleanup was called on exit
            mock_cleanup.assert_called_once()
    
    @patch('src.services.audio_extractor.get_config')
    def test_context_manager_cleanup_with_exception(self, mock_get_config):
        """Test context manager cleans up even when exception occurs."""
        mock_config = MagicMock()
        mock_config.get_temp_directory.return_value = self.temp_dir
        mock_get_config.return_value = mock_config
        
        with patch.object(AudioExtractor, 'cleanup_temp_files') as mock_cleanup:
            try:
                with AudioExtractor() as extractor:
                    extractor._temp_files = ["/tmp/test.wav"]
                    raise ValueError("Test exception")
            except ValueError:
                pass
            
            # Verify cleanup was called despite exception
            mock_cleanup.assert_called_once()


if __name__ == '__main__':
    unittest.main()