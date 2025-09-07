"""Audio extraction service for extracting audio from video files."""

import os
import subprocess
import tempfile
from typing import Optional, List
from pathlib import Path

from ..utils.config import get_config
from ..utils.file_handler import FileHandler


class AudioExtractor:
    """Service for extracting audio from video files using ffmpeg."""
    
    def __init__(self):
        """Initialize AudioExtractor service."""
        self.config = get_config()
        self._temp_files: List[str] = []
        self._temp_directory = self.config.get_temp_directory()
        
        # Ensure temp directory exists
        FileHandler.ensure_directory_exists(self._temp_directory)
    
    def extract_audio(self, video_path: str) -> Optional[str]:
        """Extract audio from video file and return path to audio file.
        
        Args:
            video_path: Path to the input video file
            
        Returns:
            Path to extracted audio file, or None if extraction failed
        """
        if not os.path.exists(video_path):
            return None
        
        if not os.path.isfile(video_path):
            return None
            
        try:
            # Generate output audio file path
            video_filename = FileHandler.get_filename_without_extension(video_path)
            audio_filename = f"{video_filename}_audio.wav"
            audio_path = os.path.join(self._temp_directory, audio_filename)
            
            # Ensure unique filename
            audio_path = FileHandler.create_unique_filename(audio_path)
            
            # Construct ffmpeg command
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', video_path,           # Input video file
                '-vn',                      # Disable video recording
                '-acodec', 'pcm_s16le',     # Audio codec: 16-bit PCM
                '-ar', '16000',             # Sample rate: 16kHz (good for speech recognition)
                '-ac', '1',                 # Mono audio
                '-y',                       # Overwrite output file if exists
                audio_path                  # Output audio file
            ]
            
            # Execute ffmpeg command
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5-minute timeout for large files
            )
            
            if result.returncode == 0 and os.path.exists(audio_path):
                # Track temporary file for cleanup
                self._temp_files.append(audio_path)
                return audio_path
            else:
                # Log error for debugging (in a real application, use proper logging)
                return None
                
        except subprocess.TimeoutExpired:
            return None
        except subprocess.SubprocessError:
            return None
        except (OSError, ValueError):
            return None
    
    def cleanup_temp_files(self) -> None:
        """Clean up all temporary audio files created by this instance."""
        for temp_file in self._temp_files:
            try:
                FileHandler.delete_file(temp_file)
            except Exception:
                # Continue cleanup even if one file fails
                pass
        
        # Clear the list after cleanup
        self._temp_files.clear()
    
    def get_temp_files(self) -> List[str]:
        """Get list of temporary files created by this instance.
        
        Returns:
            List of temporary file paths
        """
        return self._temp_files.copy()
    
    def is_ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available on the system.
        
        Returns:
            True if ffmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def get_audio_info(self, audio_path: str) -> Optional[dict]:
        """Get information about an audio file using ffprobe.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary with audio information, or None if failed
        """
        if not os.path.exists(audio_path):
            return None
            
        try:
            ffprobe_cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                audio_path
            ]
            
            result = subprocess.run(
                ffprobe_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                probe_data = json.loads(result.stdout)
                
                # Extract relevant audio information
                audio_info = {
                    'duration': None,
                    'sample_rate': None,
                    'channels': None,
                    'codec': None,
                    'size': FileHandler.get_file_size(audio_path)
                }
                
                if 'format' in probe_data:
                    format_info = probe_data['format']
                    audio_info['duration'] = float(format_info.get('duration', 0))
                
                if 'streams' in probe_data and probe_data['streams']:
                    stream = probe_data['streams'][0]  # First audio stream
                    audio_info['sample_rate'] = int(stream.get('sample_rate', 0))
                    audio_info['channels'] = int(stream.get('channels', 0))
                    audio_info['codec'] = stream.get('codec_name')
                
                return audio_info
            else:
                return None
                
        except (subprocess.SubprocessError, json.JSONDecodeError, ValueError):
            return None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically cleanup temp files."""
        self.cleanup_temp_files()