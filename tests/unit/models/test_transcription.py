"""
Unit tests for the Transcription model.
"""

import unittest
import tempfile
import os
from datetime import datetime
from src.models.transcription import Transcription


class TestTranscription(unittest.TestCase):
    """Test cases for the Transcription model."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sample_text = "This is a sample transcription text for testing purposes."
        self.sample_confidence = 0.95
        self.sample_language = "en"
        self.transcription = Transcription(
            text=self.sample_text,
            confidence=self.sample_confidence,
            language=self.sample_language
        )
    
    def test_initialization(self):
        """Test Transcription object initialization."""
        self.assertEqual(self.transcription.text, self.sample_text)
        self.assertEqual(self.transcription.confidence, self.sample_confidence)
        self.assertEqual(self.transcription.language, self.sample_language)
        self.assertIsInstance(self.transcription.timestamp, datetime)
        
        # Test with default language
        transcription_default = Transcription("Test text", 0.8)
        self.assertEqual(transcription_default.language, "en")
    
    def test_get_word_count(self):
        """Test word count calculation."""
        self.assertEqual(self.transcription.get_word_count(), 9)
        
        # Test with empty text
        empty_transcription = Transcription("", 0.5)
        self.assertEqual(empty_transcription.get_word_count(), 0)
        
        # Test with single word
        single_word = Transcription("Hello", 0.9)
        self.assertEqual(single_word.get_word_count(), 1)
        
        # Test with multiple spaces
        spaced_text = Transcription("Hello    world   test", 0.8)
        self.assertEqual(spaced_text.get_word_count(), 3)
    
    def test_save_to_file(self):
        """Test saving transcription to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test_transcription.txt")
            
            # Save transcription to file
            self.transcription.save_to_file(file_path)
            
            # Verify file exists
            self.assertTrue(os.path.exists(file_path))
            
            # Read and verify file contents
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Check that all expected elements are in the file
                self.assertIn("Transcription Generated:", content)
                self.assertIn(f"Language: {self.sample_language}", content)
                self.assertIn(f"Confidence: {self.sample_confidence:.2f}", content)
                self.assertIn("Word Count: 9", content)
                self.assertIn(self.sample_text, content)
                self.assertIn("-" * 50, content)
    
    def test_save_to_file_creates_directory(self):
        """Test that save_to_file creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "nested", "folder", "transcription.txt")
            
            # Save transcription to nested path
            self.transcription.save_to_file(nested_path)
            
            # Verify file and directories were created
            self.assertTrue(os.path.exists(nested_path))
            self.assertTrue(os.path.isfile(nested_path))
    
    def test_str_representation(self):
        """Test string representation of Transcription."""
        str_repr = str(self.transcription)
        expected = "Transcription(words=9, confidence=0.95, language=en)"
        self.assertEqual(str_repr, expected)
    
    def test_repr_representation(self):
        """Test detailed string representation of Transcription."""
        repr_str = repr(self.transcription)
        
        # Check that all expected elements are in the repr
        self.assertIn("Transcription(", repr_str)
        self.assertIn("text='This is a sample transcription text for testing pu...", repr_str)
        self.assertIn("confidence=0.95", repr_str)
        self.assertIn("language='en'", repr_str)
        self.assertIn("timestamp=", repr_str)
    
    def test_confidence_edge_cases(self):
        """Test transcription with edge case confidence values."""
        # Test minimum confidence
        min_confidence = Transcription("Test", 0.0)
        self.assertEqual(min_confidence.confidence, 0.0)
        
        # Test maximum confidence
        max_confidence = Transcription("Test", 1.0)
        self.assertEqual(max_confidence.confidence, 1.0)
        
        # Test decimal confidence
        decimal_confidence = Transcription("Test", 0.754)
        self.assertEqual(decimal_confidence.confidence, 0.754)
    
    def test_different_languages(self):
        """Test transcription with different language codes."""
        languages = ["en", "es", "fr", "de", "zh"]
        
        for lang in languages:
            transcription = Transcription("Test text", 0.9, lang)
            self.assertEqual(transcription.language, lang)
    
    def test_timestamp_uniqueness(self):
        """Test that timestamps are unique for different transcription instances."""
        import time
        
        transcription1 = Transcription("Text 1", 0.8)
        time.sleep(0.01)  # Small delay to ensure different timestamps
        transcription2 = Transcription("Text 2", 0.8)
        
        self.assertNotEqual(transcription1.timestamp, transcription2.timestamp)
        self.assertLess(transcription1.timestamp, transcription2.timestamp)
    
    def test_special_characters_in_text(self):
        """Test transcription with special characters and unicode."""
        special_text = "Hello! This includes symbols: @#$%^&*() and unicode: ñáéíóú 中文"
        transcription = Transcription(special_text, 0.9)
        
        self.assertEqual(transcription.text, special_text)
        self.assertEqual(transcription.get_word_count(), 9)
        
        # Test saving file with special characters
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "special_chars.txt")
            transcription.save_to_file(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.assertIn(special_text, content)


if __name__ == '__main__':
    unittest.main()