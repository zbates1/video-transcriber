"""File handler utility for consistent file I/O operations."""

import os
import shutil
from typing import Optional, List
from pathlib import Path


class FileHandler:
    """Utility class for consistent file I/O operations."""
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            True if directory exists or was created, False if creation failed
        """
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, PermissionError):
            return False
    
    @staticmethod
    def read_text_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """Read text content from a file.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content as string, or None if reading failed
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except (OSError, IOError, UnicodeDecodeError):
            return None
    
    @staticmethod
    def write_text_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """Write text content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            encoding: File encoding (default: utf-8)
            
        Returns:
            True if write was successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not FileHandler.ensure_directory_exists(parent_dir):
                return False
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except (OSError, IOError, UnicodeEncodeError):
            return False
    
    @staticmethod
    def append_text_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """Append text content to a file.
        
        Args:
            file_path: Path to the file to append to
            content: Content to append
            encoding: File encoding (default: utf-8)
            
        Returns:
            True if append was successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not FileHandler.ensure_directory_exists(parent_dir):
                return False
            
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(content)
            return True
        except (OSError, IOError, UnicodeEncodeError):
            return False
    
    @staticmethod
    def copy_file(source_path: str, destination_path: str) -> bool:
        """Copy a file from source to destination.
        
        Args:
            source_path: Path to source file
            destination_path: Path to destination file
            
        Returns:
            True if copy was successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not FileHandler.ensure_directory_exists(dest_dir):
                return False
            
            shutil.copy2(source_path, destination_path)
            return True
        except (OSError, IOError, shutil.Error):
            return False
    
    @staticmethod
    def move_file(source_path: str, destination_path: str) -> bool:
        """Move a file from source to destination.
        
        Args:
            source_path: Path to source file
            destination_path: Path to destination file
            
        Returns:
            True if move was successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not FileHandler.ensure_directory_exists(dest_dir):
                return False
            
            shutil.move(source_path, destination_path)
            return True
        except (OSError, IOError, shutil.Error):
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except (OSError, PermissionError):
            return False
    
    @staticmethod
    def delete_directory(directory_path: str, recursive: bool = False) -> bool:
        """Delete a directory.
        
        Args:
            directory_path: Path to the directory to delete
            recursive: Whether to delete recursively (default: False)
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if not os.path.exists(directory_path):
                return True
            
            if recursive:
                shutil.rmtree(directory_path)
            else:
                os.rmdir(directory_path)
            return True
        except (OSError, PermissionError, shutil.Error):
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """Get the size of a file in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes, or None if file doesn't exist or error occurred
        """
        try:
            return os.path.getsize(file_path)
        except (OSError, FileNotFoundError):
            return None
    
    @staticmethod
    def list_files(directory_path: str, pattern: str = "*") -> List[str]:
        """List files in a directory matching a pattern.
        
        Args:
            directory_path: Path to the directory
            pattern: Glob pattern to match files (default: "*")
            
        Returns:
            List of file paths matching the pattern
        """
        try:
            directory = Path(directory_path)
            if not directory.exists() or not directory.is_dir():
                return []
            
            return [str(path) for path in directory.glob(pattern) if path.is_file()]
        except (OSError, ValueError):
            return []
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get the file extension from a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File extension (including the dot), empty string if no extension
        """
        return Path(file_path).suffix
    
    @staticmethod
    def get_filename_without_extension(file_path: str) -> str:
        """Get the filename without extension from a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Filename without extension
        """
        return Path(file_path).stem
    
    @staticmethod
    def create_unique_filename(base_path: str) -> str:
        """Create a unique filename by appending a number if the file exists.
        
        Args:
            base_path: Base file path
            
        Returns:
            Unique file path
        """
        if not os.path.exists(base_path):
            return base_path
        
        path = Path(base_path)
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return str(new_path)
            counter += 1
    
    @staticmethod
    def is_file_writable(file_path: str) -> bool:
        """Check if a file is writable.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is writable, False otherwise
        """
        try:
            # If file exists, check write permission
            if os.path.exists(file_path):
                return os.access(file_path, os.W_OK)
            
            # If file doesn't exist, check if parent directory is writable
            parent_dir = os.path.dirname(file_path)
            if not parent_dir:
                parent_dir = '.'
            
            return os.access(parent_dir, os.W_OK)
        except (OSError, ValueError):
            return False