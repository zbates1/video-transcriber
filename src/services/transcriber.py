"""
Transcriber service for converting audio files to text using OpenAI Whisper.
"""

import os
import sys
from typing import Optional
import whisper
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.transcription import Transcription
from utils.validators import validate_file_exists, ValidationError


class TranscriberError(Exception):
    """Custom exception for transcription errors."""
    pass


class Transcriber:
    """
    Service for converting audio files to text transcriptions using OpenAI Whisper.
    
    This service uses OpenAI's Whisper model for high-quality speech recognition
    supporting multiple languages and audio formats.
    """
    
    def __init__(self, model_name: str = "turbo", language: str = None):
        """
        Initialize the Transcriber service.
        
        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large, turbo)
            language: Language code for speech recognition (None for auto-detection)
        """
        self.model_name = model_name
        self.language = language
        self.model = None
        
    def _load_model(self):
        """Load the Whisper model if not already loaded."""
        if self.model is None:
            print(f"[WHISPER] Loading {self.model_name} model...")
            self.model = whisper.load_model(self.model_name)
    
    def set_language(self, language: str) -> None:
        """
        Set the language for speech recognition.
        
        Args:
            language: Language code (e.g., "en", "es", "fr") or None for auto-detection
        """
        self.language = language
    
    def transcribe(self, audio_path: str) -> str:
        """
        Convert audio file to text transcription using Whisper.
        
        Args:
            audio_path: Path to the audio file to transcribe
            
        Returns:
            The transcribed text as a string
            
        Raises:
            TranscriberError: If transcription fails
            ValidationError: If audio file is invalid
        """
        # Validate audio file exists
        try:
            validate_file_exists(audio_path)
        except ValidationError as e:
            raise TranscriberError(f"Audio file validation failed: {str(e)}")
        
        try:
            # Load Whisper model
            self._load_model()
            
            # Transcribe audio using Whisper
            print(f"[WHISPER] Transcribing audio: {os.path.basename(audio_path)}")
            
            # Prepare transcription options
            options = {
                'verbose': False,
                'fp16': False,  # Use fp32 for better compatibility
            }
            
            if self.language:
                options['language'] = self.language
            
            # Perform transcription
            result = self.model.transcribe(audio_path, **options)
            
            # Extract text from result
            text = result['text'].strip()
            
            if not text:
                raise TranscriberError("No speech detected in audio file")
            
            print(f"[WHISPER] Transcription completed: {len(text.split())} words")
            return text
                
        except Exception as e:
            if isinstance(e, TranscriberError):
                raise
            else:
                raise TranscriberError(f"Failed to transcribe audio: {str(e)}")
    
    def transcribe_to_model(self, audio_path: str) -> Transcription:
        """
        Transcribe audio file and return a Transcription model object.
        
        Args:
            audio_path: Path to the audio file to transcribe
            
        Returns:
            Transcription object containing the transcribed text and metadata
            
        Raises:
            TranscriberError: If transcription fails
        """
        try:
            # Load Whisper model
            self._load_model()
            
            # Transcribe with full results
            print(f"[WHISPER] Transcribing audio with metadata: {os.path.basename(audio_path)}")
            
            # Prepare transcription options
            options = {
                'verbose': False,
                'fp16': False,
            }
            
            if self.language:
                options['language'] = self.language
            
            # Perform transcription
            result = self.model.transcribe(audio_path, **options)
            
            # Extract information from result
            text = result['text'].strip()
            detected_language = result.get('language', self.language or 'unknown')
            
            if not text:
                raise TranscriberError("No speech detected in audio file")
            
            # Whisper doesn't provide a direct confidence score, but we can estimate
            # based on the average log probability of segments if available
            confidence = 0.90  # Whisper is generally very accurate
            
            if 'segments' in result and result['segments']:
                # Calculate average confidence from segments if available
                segment_probs = []
                for segment in result['segments']:
                    if 'avg_logprob' in segment:
                        # Convert log probability to confidence (rough approximation)
                        prob = min(1.0, max(0.0, (segment['avg_logprob'] + 3) / 3))
                        segment_probs.append(prob)
                
                if segment_probs:
                    confidence = sum(segment_probs) / len(segment_probs)
            
            print(f"[WHISPER] Transcription completed: {len(text.split())} words, language: {detected_language}")
            
            # Create and return Transcription object
            return Transcription(
                text=text,
                confidence=confidence,
                language=detected_language
            )
            
        except Exception as e:
            if isinstance(e, TranscriberError):
                raise
            else:
                raise TranscriberError(f"Failed to create transcription model: {str(e)}")
    
    def get_supported_formats(self) -> list:
        """
        Get list of supported audio formats.
        
        Returns:
            List of supported file extensions (Whisper supports many formats)
        """
        return ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.opus', '.aac', '.aiff', '.wma']
    
    def get_current_language(self) -> str:
        """
        Get the current language setting.
        
        Returns:
            Current language code or None for auto-detection
        """
        return self.language
    
    def get_model_name(self) -> str:
        """
        Get the current Whisper model name.
        
        Returns:
            Current model name
        """
        return self.model_name
    
    def set_model(self, model_name: str) -> None:
        """
        Set the Whisper model to use.
        
        Args:
            model_name: Name of the Whisper model (tiny, base, small, medium, large, turbo)
        """
        if model_name not in whisper.available_models():
            raise TranscriberError(f"Invalid model name: {model_name}. Available: {whisper.available_models()}")
        
        self.model_name = model_name
        self.model = None  # Force reload on next transcription