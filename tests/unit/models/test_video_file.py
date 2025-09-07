"""Unit tests for VideoFile model."""

import os
import tempfile
import unittest
from pathlib import Path

from src.models.video_file import VideoFile


class TestVideoFile(unittest.TestCase):
    """Test cases for VideoFile model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory and files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_video_file = os.path.join(self.temp_dir, "test_video.mp4")
        self.temp_invalid_file = os.path.join(self.temp_dir, "test_file.txt")
        
        # Create actual test files
        with open(self.temp_video_file, 'w') as f:
            f.write("fake video content")
        with open(self.temp_invalid_file, 'w') as f:
            f.write("not a video file")
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files and directory
        if os.path.exists(self.temp_video_file):
            os.remove(self.temp_video_file)
        if os.path.exists(self.temp_invalid_file):
            os.remove(self.temp_invalid_file)
        os.rmdir(self.temp_dir)
    
    def test_init_with_valid_path(self):
        """Test VideoFile initialization with valid path."""
        video = VideoFile(self.temp_video_file)
        self.assertEqual(video.path, self.temp_video_file)
        self.assertEqual(video.filename, "test_video.mp4")
    
    def test_init_with_nonexistent_path(self):
        """Test VideoFile initialization with non-existent path."""
        nonexistent_path = "/nonexistent/path/video.mp4"
        video = VideoFile(nonexistent_path)
        self.assertEqual(video.path, nonexistent_path)
        self.assertEqual(video.filename, "video.mp4")
    
    def test_size_property_existing_file(self):
        """Test size property returns correct file size for existing file."""
        video = VideoFile(self.temp_video_file)
        expected_size = len("fake video content")
        self.assertEqual(video.size, expected_size)
    
    def test_size_property_nonexistent_file(self):
        """Test size property returns None for non-existent file."""
        video = VideoFile("/nonexistent/path/video.mp4")
        self.assertIsNone(video.size)
    
    def test_duration_property_placeholder(self):
        """Test duration property returns None (placeholder implementation)."""
        video = VideoFile(self.temp_video_file)
        self.assertIsNone(video.duration)
    
    def test_validate_existing_valid_video_file(self):
        """Test validate method returns True for existing valid video file."""
        video = VideoFile(self.temp_video_file)
        self.assertTrue(video.validate())
    
    def test_validate_existing_invalid_extension(self):
        """Test validate method returns False for file with invalid extension."""
        video = VideoFile(self.temp_invalid_file)
        self.assertFalse(video.validate())
    
    def test_validate_nonexistent_file(self):
        """Test validate method returns False for non-existent file."""
        video = VideoFile("/nonexistent/path/video.mp4")
        self.assertFalse(video.validate())
    
    def test_validate_directory_path(self):
        """Test validate method returns False for directory path."""
        video = VideoFile(self.temp_dir)
        self.assertFalse(video.validate())
    
    def test_validate_various_video_extensions(self):
        """Test validate method works with various video extensions."""
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        
        for ext in valid_extensions:
            temp_file = os.path.join(self.temp_dir, f"test{ext}")
            with open(temp_file, 'w') as f:
                f.write("test content")
            
            video = VideoFile(temp_file)
            self.assertTrue(video.validate(), f"Extension {ext} should be valid")
            
            os.remove(temp_file)
    
    def test_validate_case_insensitive_extensions(self):
        """Test validate method is case insensitive for extensions."""
        temp_file = os.path.join(self.temp_dir, "test.MP4")
        with open(temp_file, 'w') as f:
            f.write("test content")
        
        video = VideoFile(temp_file)
        self.assertTrue(video.validate())
        
        os.remove(temp_file)
    
    def test_get_metadata_existing_file(self):
        """Test get_metadata returns correct metadata for existing file."""
        video = VideoFile(self.temp_video_file)
        metadata = video.get_metadata()
        
        expected_metadata = {
            'path': self.temp_video_file,
            'filename': 'test_video.mp4',
            'size': len("fake video content"),
            'duration': None,
            'exists': True,
            'is_valid': True
        }
        
        self.assertEqual(metadata, expected_metadata)
    
    def test_get_metadata_nonexistent_file(self):
        """Test get_metadata returns correct metadata for non-existent file."""
        nonexistent_path = "/nonexistent/path/video.mp4"
        video = VideoFile(nonexistent_path)
        metadata = video.get_metadata()
        
        expected_metadata = {
            'path': nonexistent_path,
            'filename': 'video.mp4',
            'size': None,
            'duration': None,
            'exists': False,
            'is_valid': False
        }
        
        self.assertEqual(metadata, expected_metadata)


if __name__ == '__main__':
    unittest.main()