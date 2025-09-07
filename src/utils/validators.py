"""
Input validation utilities for the video transcriber pipeline.
"""

import os
import mimetypes
from pathlib import Path
from typing import List, Optional, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_file_exists(file_path: str) -> None:
    """
    Validate that a file exists at the given path.
    
    Args:
        file_path: Path to the file to validate
        
    Raises:
        ValidationError: If file does not exist or path is invalid
    """
    if not file_path:
        raise ValidationError("File path cannot be empty")
    
    if not os.path.exists(file_path):
        raise ValidationError(f"File does not exist: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValidationError(f"Path is not a file: {file_path}")


def validate_video_format(file_path: str, allowed_formats: Optional[List[str]] = None) -> None:
    """
    Validate that a file is a supported video format.
    
    Args:
        file_path: Path to the video file
        allowed_formats: List of allowed file extensions (default: ['.mp4'])
        
    Raises:
        ValidationError: If file format is not supported
    """
    if allowed_formats is None:
        allowed_formats = ['.mp4']
    
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension not in allowed_formats:
        raise ValidationError(
            f"Unsupported video format: {file_extension}. "
            f"Supported formats: {', '.join(allowed_formats)}"
        )


def validate_video_file(file_path: str, allowed_formats: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Comprehensive validation for video files.
    
    Args:
        file_path: Path to the video file
        allowed_formats: List of allowed file extensions (default: ['.mp4'])
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if file passes all validation
        - error_message: Empty string if valid, error description if invalid
    """
    try:
        # Check file existence
        validate_file_exists(file_path)
        
        # Check file format
        validate_video_format(file_path, allowed_formats)
        
        # Check file size (not empty)
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValidationError("File is empty")
        
        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                # Try to read first few bytes to ensure file is readable
                f.read(1024)
        except (IOError, PermissionError) as e:
            raise ValidationError(f"File is not readable: {str(e)}")
        
        return True, ""
        
    except ValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected validation error: {str(e)}"


def validate_output_directory(output_path: str) -> None:
    """
    Validate that the output directory exists and is writable.
    
    Args:
        output_path: Path to the output directory
        
    Raises:
        ValidationError: If directory validation fails
    """
    if not output_path:
        raise ValidationError("Output path cannot be empty")
    
    output_dir = Path(output_path)
    
    # Create directory if it doesn't exist
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        raise ValidationError(f"Cannot create output directory {output_path}: {str(e)}")
    
    # Check if directory is writable
    if not os.access(output_dir, os.W_OK):
        raise ValidationError(f"Output directory is not writable: {output_path}")


def validate_api_key(api_key: str) -> None:
    """
    Validate that the API key is provided and not empty.
    
    Args:
        api_key: The API key to validate
        
    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key:
        raise ValidationError("API key cannot be empty")
    
    if not isinstance(api_key, str):
        raise ValidationError("API key must be a string")
    
    if len(api_key.strip()) < 10:
        raise ValidationError("API key appears to be too short")


def get_file_info(file_path: str) -> dict:
    """
    Get information about a file for validation purposes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary containing file information
    """
    if not os.path.exists(file_path):
        return {"exists": False}
    
    file_stat = os.stat(file_path)
    file_path_obj = Path(file_path)
    
    # Try to determine MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    
    return {
        "exists": True,
        "is_file": os.path.isfile(file_path),
        "size": file_stat.st_size,
        "extension": file_path_obj.suffix.lower(),
        "name": file_path_obj.name,
        "mime_type": mime_type,
        "readable": os.access(file_path, os.R_OK),
        "writable": os.access(file_path, os.W_OK),
    }


def is_valid_file_path(file_path: str) -> bool:
    """
    Check if a file path is valid (not necessarily existing).
    
    Args:
        file_path: Path to validate
        
    Returns:
        True if path format is valid, False otherwise
    """
    try:
        # Try to create a Path object
        path_obj = Path(file_path)
        
        # Check for invalid characters (basic check)
        if not file_path or file_path.isspace():
            return False
        
        # Check if path is too long (Windows limitation)
        if len(str(path_obj.absolute())) > 260:
            return False
        
        return True
        
    except (ValueError, OSError):
        return False