"""Summary model for handling AI-generated text summaries."""

import os
from datetime import datetime
from typing import Optional
from pathlib import Path


class Summary:
    """Model representing an AI-generated summary with metadata."""
    
    def __init__(self, text: str, original_length: int):
        """Initialize Summary with text and original text length."""
        self.text = text
        self.original_length = original_length
        self.timestamp = datetime.now()
    
    @property
    def summary_length(self) -> int:
        """Get the length of the summary text."""
        return len(self.text)
    
    def get_compression_ratio(self) -> float:
        """Calculate compression ratio as summary_length / original_length."""
        if self.original_length == 0:
            return 0.0
        return self.summary_length / self.original_length
    
    def save_to_file(self, path: str) -> bool:
        """Save summary text to a file."""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"# Summary\n")
                f.write(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Original length: {self.original_length} characters\n")
                f.write(f"Summary length: {self.summary_length} characters\n")
                f.write(f"Compression ratio: {self.get_compression_ratio():.2%}\n")
                f.write(f"\n---\n\n")
                f.write(self.text)
            
            return True
        except (OSError, IOError) as e:
            return False
    
    def get_metadata(self) -> dict:
        """Get summary metadata as a dictionary."""
        return {
            'text': self.text,
            'original_length': self.original_length,
            'summary_length': self.summary_length,
            'compression_ratio': self.get_compression_ratio(),
            'timestamp': self.timestamp.isoformat()
        }