"""
Unit tests for the validators utility module.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from src.utils.validators import (
    ValidationError,
    validate_file_exists,
    validate_video_format,
    validate_video_file,
    validate_output_directory,
    validate_api_key,
    get_file_info,
    is_valid_file_path
)


class TestValidators(unittest.TestCase):
    """Test cases for the validators module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.valid_mp4_file = os.path.join(self.temp_dir, "test_video.mp4")
        self.invalid_format_file = os.path.join(self.temp_dir, "test_video.avi")
        self.empty_file = os.path.join(self.temp_dir, "empty.mp4")
        
        # Create valid MP4 file with some content
        with open(self.valid_mp4_file, 'wb') as f:
            f.write(b"fake mp4 content for testing")
        
        # Create file with invalid format
        with open(self.invalid_format_file, 'wb') as f:
            f.write(b"fake avi content")
        
        # Create empty file
        with open(self.empty_file, 'wb') as f:
            pass  # Empty file
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_validate_file_exists_success(self):
        """Test successful file existence validation."""
        # Should not raise exception for existing file
        try:
            validate_file_exists(self.valid_mp4_file)
        except ValidationError:
            self.fail("validate_file_exists raised ValidationError for existing file")
    
    def test_validate_file_exists_nonexistent(self):
        """Test validation failure for non-existent file."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.mp4")
        
        with self.assertRaises(ValidationError) as context:
            validate_file_exists(nonexistent_file)
        
        self.assertIn("File does not exist", str(context.exception))
    
    def test_validate_file_exists_empty_path(self):
        """Test validation failure for empty path."""
        with self.assertRaises(ValidationError) as context:
            validate_file_exists("")
        
        self.assertIn("File path cannot be empty", str(context.exception))
    
    def test_validate_file_exists_directory(self):
        """Test validation failure when path is a directory."""
        with self.assertRaises(ValidationError) as context:
            validate_file_exists(self.temp_dir)
        
        self.assertIn("Path is not a file", str(context.exception))
    
    def test_validate_video_format_success(self):
        """Test successful video format validation."""
        # Should not raise exception for MP4 file
        try:
            validate_video_format(self.valid_mp4_file)
        except ValidationError:
            self.fail("validate_video_format raised ValidationError for MP4 file")
    
    def test_validate_video_format_failure(self):
        """Test video format validation failure."""
        with self.assertRaises(ValidationError) as context:
            validate_video_format(self.invalid_format_file)
        
        self.assertIn("Unsupported video format", str(context.exception))
        self.assertIn(".avi", str(context.exception))
    
    def test_validate_video_format_custom_formats(self):
        """Test video format validation with custom allowed formats."""
        # Should pass with AVI in allowed formats
        try:
            validate_video_format(self.invalid_format_file, ['.avi', '.mp4'])
        except ValidationError:
            self.fail("validate_video_format failed with custom allowed formats")
        
        # Should fail with only MOV allowed
        with self.assertRaises(ValidationError):
            validate_video_format(self.valid_mp4_file, ['.mov'])
    
    def test_validate_video_file_success(self):
        """Test comprehensive video file validation success."""
        is_valid, error_msg = validate_video_file(self.valid_mp4_file)
        
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
    
    def test_validate_video_file_nonexistent(self):
        """Test video file validation with non-existent file."""
        nonexistent = os.path.join(self.temp_dir, "nonexistent.mp4")
        is_valid, error_msg = validate_video_file(nonexistent)
        
        self.assertFalse(is_valid)
        self.assertIn("File does not exist", error_msg)
    
    def test_validate_video_file_wrong_format(self):
        """Test video file validation with wrong format."""
        is_valid, error_msg = validate_video_file(self.invalid_format_file)
        
        self.assertFalse(is_valid)
        self.assertIn("Unsupported video format", error_msg)
    
    def test_validate_video_file_empty(self):
        """Test video file validation with empty file."""
        is_valid, error_msg = validate_video_file(self.empty_file)
        
        self.assertFalse(is_valid)
        self.assertIn("File is empty", error_msg)
    
    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    def test_validate_video_file_not_readable(self, mock_file):
        """Test video file validation with unreadable file."""
        is_valid, error_msg = validate_video_file(self.valid_mp4_file)
        
        self.assertFalse(is_valid)
        self.assertIn("File is not readable", error_msg)
    
    def test_validate_output_directory_success(self):
        """Test successful output directory validation."""
        output_dir = os.path.join(self.temp_dir, "output")
        
        try:
            validate_output_directory(output_dir)
            # Verify directory was created
            self.assertTrue(os.path.exists(output_dir))
            self.assertTrue(os.path.isdir(output_dir))
        except ValidationError:
            self.fail("validate_output_directory failed for valid directory")
    
    def test_validate_output_directory_empty_path(self):
        """Test output directory validation with empty path."""
        with self.assertRaises(ValidationError) as context:
            validate_output_directory("")
        
        self.assertIn("Output path cannot be empty", str(context.exception))
    
    @patch('os.access', return_value=False)
    @patch('pathlib.Path.mkdir')
    def test_validate_output_directory_not_writable(self, mock_mkdir, mock_access):
        """Test output directory validation when directory is not writable."""
        output_dir = os.path.join(self.temp_dir, "readonly_output")
        
        with self.assertRaises(ValidationError) as context:
            validate_output_directory(output_dir)
        
        self.assertIn("not writable", str(context.exception))
    
    def test_validate_api_key_success(self):
        """Test successful API key validation."""
        valid_key = "sk-1234567890abcdef"
        
        try:
            validate_api_key(valid_key)
        except ValidationError:
            self.fail("validate_api_key failed for valid API key")
    
    def test_validate_api_key_empty(self):
        """Test API key validation with empty key."""
        with self.assertRaises(ValidationError) as context:
            validate_api_key("")
        
        self.assertIn("API key cannot be empty", str(context.exception))
    
    def test_validate_api_key_none(self):
        """Test API key validation with None."""
        with self.assertRaises(ValidationError) as context:
            validate_api_key(None)
        
        self.assertIn("API key cannot be empty", str(context.exception))
    
    def test_validate_api_key_not_string(self):
        """Test API key validation with non-string input."""
        with self.assertRaises(ValidationError) as context:
            validate_api_key(12345)
        
        self.assertIn("API key must be a string", str(context.exception))
    
    def test_validate_api_key_too_short(self):
        """Test API key validation with too short key."""
        with self.assertRaises(ValidationError) as context:
            validate_api_key("short")
        
        self.assertIn("API key appears to be too short", str(context.exception))
    
    def test_get_file_info_existing_file(self):
        """Test getting file info for existing file."""
        info = get_file_info(self.valid_mp4_file)
        
        self.assertTrue(info["exists"])
        self.assertTrue(info["is_file"])
        self.assertGreater(info["size"], 0)
        self.assertEqual(info["extension"], ".mp4")
        self.assertIn("test_video.mp4", info["name"])
        self.assertTrue(info["readable"])
    
    def test_get_file_info_nonexistent_file(self):
        """Test getting file info for non-existent file."""
        nonexistent = os.path.join(self.temp_dir, "nonexistent.mp4")
        info = get_file_info(nonexistent)
        
        self.assertFalse(info["exists"])
    
    def test_get_file_info_directory(self):
        """Test getting file info for directory."""
        info = get_file_info(self.temp_dir)
        
        self.assertTrue(info["exists"])
        self.assertFalse(info["is_file"])
    
    def test_is_valid_file_path_success(self):
        """Test valid file path validation."""
        valid_paths = [
            "/path/to/file.mp4",
            "relative/path/file.mp4",
            "C:\\Windows\\file.mp4",
            "file.mp4",
            "./file.mp4",
            "../file.mp4"
        ]
        
        for path in valid_paths:
            with self.subTest(path=path):
                self.assertTrue(is_valid_file_path(path))
    
    def test_is_valid_file_path_failure(self):
        """Test invalid file path validation."""
        invalid_paths = [
            "",
            "   ",
            None  # This should be handled gracefully
        ]
        
        for path in invalid_paths:
            with self.subTest(path=path):
                if path is None:
                    # None should cause an exception that's caught
                    with self.assertRaises(TypeError):
                        is_valid_file_path(path)
                else:
                    self.assertFalse(is_valid_file_path(path))
    
    def test_is_valid_file_path_too_long(self):
        """Test file path validation with extremely long path."""
        # Create a path longer than 260 characters (Windows limit)
        long_path = "C:\\" + "very_long_directory_name_" * 20 + "file.mp4"
        
        self.assertFalse(is_valid_file_path(long_path))
    
    def test_validation_error_inheritance(self):
        """Test that ValidationError is properly inherited from Exception."""
        self.assertTrue(issubclass(ValidationError, Exception))
        
        # Test raising and catching
        with self.assertRaises(ValidationError):
            raise ValidationError("Test error")
    
    def test_case_insensitive_extension_matching(self):
        """Test that file extension matching is case insensitive."""
        upper_case_file = os.path.join(self.temp_dir, "test.MP4")
        mixed_case_file = os.path.join(self.temp_dir, "test.Mp4")
        
        # Create files with uppercase and mixed case extensions
        with open(upper_case_file, 'wb') as f:
            f.write(b"test content")
        with open(mixed_case_file, 'wb') as f:
            f.write(b"test content")
        
        # Both should be valid
        is_valid1, _ = validate_video_file(upper_case_file)
        is_valid2, _ = validate_video_file(mixed_case_file)
        
        self.assertTrue(is_valid1)
        self.assertTrue(is_valid2)


if __name__ == '__main__':
    unittest.main()