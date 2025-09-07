"""
Transcription model for storing and managing transcribed text data.
"""

from datetime import datetime
from typing import Optional
import os


class Transcription:
    """
    Model for storing transcription data with confidence metrics and metadata.
    
    Properties:
        text (str): The transcribed text content
        confidence (float): Confidence score for the transcription (0.0 to 1.0)
        language (str): Language of the transcription
        timestamp (datetime): When the transcription was created
    """
    
    def __init__(self, text: str, confidence: float, language: str = "en"):
        """
        Initialize a Transcription object.
        
        Args:
            text: The transcribed text content
            confidence: Confidence score (0.0 to 1.0)
            language: Language code (default: "en")
        """
        self.text = text
        self.confidence = confidence
        self.language = language
        self.timestamp = datetime.now()
    
    def save_to_file(self, path: str) -> None:
        """
        Save the transcription to a text file.
        
        Args:
            path: File path where to save the transcription
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as file:
            file.write(f"Transcription Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"Language: {self.language}\n")
            file.write(f"Confidence: {self.confidence:.2f}\n")
            file.write(f"Word Count: {self.get_word_count()}\n")
            file.write("-" * 50 + "\n\n")
            file.write(self.text)
    
    def get_word_count(self) -> int:
        """
        Get the word count of the transcription text.
        
        Returns:
            Number of words in the transcription
        """
        if not self.text:
            return 0
        return len(self.text.split())
    
    def __str__(self) -> str:
        """String representation of the transcription."""
        return f"Transcription(words={self.get_word_count()}, confidence={self.confidence:.2f}, language={self.language})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the transcription."""
        return f"Transcription(text='{self.text[:50]}...', confidence={self.confidence}, language='{self.language}', timestamp={self.timestamp})"