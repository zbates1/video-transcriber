"""Unit tests for Summary model."""

import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

from src.models.summary import Summary


class TestSummary(unittest.TestCase):
    """Test cases for Summary model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for file operations
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, "test_summary.txt")
        
        # Test data
        self.sample_text = "This is a sample summary text."
        self.original_length = 1000
        self.empty_text = ""
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files and directory
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_init_with_valid_data(self):
        """Test Summary initialization with valid data."""
        summary = Summary(self.sample_text, self.original_length)
        
        self.assertEqual(summary.text, self.sample_text)
        self.assertEqual(summary.original_length, self.original_length)
        self.assertIsInstance(summary.timestamp, datetime)
    
    def test_init_with_empty_text(self):
        """Test Summary initialization with empty text."""
        summary = Summary(self.empty_text, self.original_length)
        
        self.assertEqual(summary.text, self.empty_text)
        self.assertEqual(summary.original_length, self.original_length)
        self.assertIsInstance(summary.timestamp, datetime)
    
    def test_init_with_zero_original_length(self):
        """Test Summary initialization with zero original length."""
        summary = Summary(self.sample_text, 0)
        
        self.assertEqual(summary.text, self.sample_text)
        self.assertEqual(summary.original_length, 0)
        self.assertIsInstance(summary.timestamp, datetime)
    
    def test_summary_length_property(self):
        """Test summary_length property returns correct length."""
        summary = Summary(self.sample_text, self.original_length)
        expected_length = len(self.sample_text)
        
        self.assertEqual(summary.summary_length, expected_length)
    
    def test_summary_length_property_empty_text(self):
        """Test summary_length property returns 0 for empty text."""
        summary = Summary(self.empty_text, self.original_length)
        
        self.assertEqual(summary.summary_length, 0)
    
    def test_get_compression_ratio_normal_case(self):
        """Test get_compression_ratio returns correct ratio."""
        summary = Summary(self.sample_text, self.original_length)
        expected_ratio = len(self.sample_text) / self.original_length
        
        self.assertEqual(summary.get_compression_ratio(), expected_ratio)
    
    def test_get_compression_ratio_zero_original_length(self):
        """Test get_compression_ratio returns 0.0 when original length is zero."""
        summary = Summary(self.sample_text, 0)
        
        self.assertEqual(summary.get_compression_ratio(), 0.0)
    
    def test_get_compression_ratio_empty_text(self):
        """Test get_compression_ratio returns 0.0 when text is empty."""
        summary = Summary(self.empty_text, self.original_length)
        expected_ratio = 0 / self.original_length
        
        self.assertEqual(summary.get_compression_ratio(), expected_ratio)
    
    def test_save_to_file_success(self):
        """Test save_to_file creates file with correct content."""
        summary = Summary(self.sample_text, self.original_length)
        
        result = summary.save_to_file(self.temp_file)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.temp_file))
        
        # Verify file content
        with open(self.temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn("# Summary", content)
        self.assertIn("Generated:", content)
        self.assertIn(f"Original length: {self.original_length} characters", content)
        self.assertIn(f"Summary length: {len(self.sample_text)} characters", content)
        self.assertIn("Compression ratio:", content)
        self.assertIn(self.sample_text, content)
    
    def test_save_to_file_creates_directory(self):
        """Test save_to_file creates output directory if it doesn't exist."""
        nested_dir = os.path.join(self.temp_dir, "nested", "output")
        nested_file = os.path.join(nested_dir, "summary.txt")
        summary = Summary(self.sample_text, self.original_length)
        
        result = summary.save_to_file(nested_file)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(nested_file))
        self.assertTrue(os.path.exists(nested_dir))
        
        # Clean up
        os.remove(nested_file)
        os.rmdir(nested_dir)
        os.rmdir(os.path.dirname(nested_dir))
    
    def test_save_to_file_handles_io_error(self):
        """Test save_to_file handles IO errors gracefully."""
        summary = Summary(self.sample_text, self.original_length)
        invalid_path = "/invalid/path/that/does/not/exist/summary.txt"
        
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            result = summary.save_to_file(invalid_path)
            
        self.assertFalse(result)
    
    def test_save_to_file_with_unicode_content(self):
        """Test save_to_file handles Unicode content correctly."""
        unicode_text = "Summary with unicode: 你好世界 🌍 café"
        summary = Summary(unicode_text, self.original_length)
        
        result = summary.save_to_file(self.temp_file)
        
        self.assertTrue(result)
        
        # Verify Unicode content is preserved
        with open(self.temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn(unicode_text, content)
    
    def test_get_metadata_complete(self):
        """Test get_metadata returns complete metadata dictionary."""
        summary = Summary(self.sample_text, self.original_length)
        metadata = summary.get_metadata()
        
        expected_keys = {'text', 'original_length', 'summary_length', 'compression_ratio', 'timestamp'}
        self.assertEqual(set(metadata.keys()), expected_keys)
        
        self.assertEqual(metadata['text'], self.sample_text)
        self.assertEqual(metadata['original_length'], self.original_length)
        self.assertEqual(metadata['summary_length'], len(self.sample_text))
        self.assertEqual(metadata['compression_ratio'], len(self.sample_text) / self.original_length)
        self.assertIsInstance(metadata['timestamp'], str)
    
    def test_get_metadata_timestamp_format(self):
        """Test get_metadata timestamp is in ISO format."""
        summary = Summary(self.sample_text, self.original_length)
        metadata = summary.get_metadata()
        
        # Verify timestamp is a valid ISO format string
        timestamp_str = metadata['timestamp']
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        self.assertIsInstance(parsed_timestamp, datetime)
    
    def test_timestamp_set_during_initialization(self):
        """Test timestamp is set during object initialization."""
        before_creation = datetime.now()
        summary = Summary(self.sample_text, self.original_length)
        after_creation = datetime.now()
        
        self.assertGreaterEqual(summary.timestamp, before_creation)
        self.assertLessEqual(summary.timestamp, after_creation)
    
    def test_properties_immutable_after_init(self):
        """Test that properties work correctly after initialization."""
        summary = Summary(self.sample_text, self.original_length)
        
        # Test that properties return consistent values
        first_length = summary.summary_length
        second_length = summary.summary_length
        self.assertEqual(first_length, second_length)
        
        first_ratio = summary.get_compression_ratio()
        second_ratio = summary.get_compression_ratio()
        self.assertEqual(first_ratio, second_ratio)


if __name__ == '__main__':
    unittest.main()