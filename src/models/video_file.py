"""VideoFile model for handling video file metadata and validation."""

import os
from typing import Optional
from pathlib import Path


class VideoFile:
    """Model representing a video file with metadata and validation."""
    
    def __init__(self, path: str):
        """Initialize VideoFile with the given path."""
        self.path = path
        self.filename = os.path.basename(path)
        
    @property
    def size(self) -> Optional[int]:
        """Get file size in bytes."""
        try:
            return os.path.getsize(self.path)
        except (OSError, FileNotFoundError):
            return None
    
    @property
    def duration(self) -> Optional[float]:
        """Get video duration in seconds. Placeholder for future implementation."""
        # TODO: Implement with ffprobe or similar tool
        return None
        
    def validate(self) -> bool:
        """Validate the video file exists and is accessible."""
        if not os.path.exists(self.path):
            return False
            
        if not os.path.isfile(self.path):
            return False
            
        # Check if file has a valid video extension
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        file_extension = Path(self.path).suffix.lower()
        
        return file_extension in valid_extensions
    
    def get_metadata(self) -> dict:
        """Get video file metadata as a dictionary."""
        return {
            'path': self.path,
            'filename': self.filename,
            'size': self.size,
            'duration': self.duration,
            'exists': os.path.exists(self.path),
            'is_valid': self.validate()
        }