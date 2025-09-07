"""
Transcriber service for converting audio files to text using speech recognition.
"""

import os
from typing import Optional
import speech_recognition as sr
from src.models.transcription import Transcription
from src.utils.validators import validate_file_exists, ValidationError


class TranscriberError(Exception):
    """Custom exception for transcription errors."""
    pass


class Transcriber:
    """
    Service for converting audio files to text transcriptions using speech recognition.
    
    This service uses the SpeechRecognition library with Google Speech Recognition
    as the default engine for converting audio to text.
    """
    
    def __init__(self, language: str = "en-US"):
        """
        Initialize the Transcriber service.
        
        Args:
            language: Language code for speech recognition (default: "en-US")
        """
        self.language = language
        self.recognizer = sr.Recognizer()
        
        # Configure recognizer settings for better accuracy
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.8
    
    def set_language(self, language: str) -> None:
        """
        Set the language for speech recognition.
        
        Args:
            language: Language code (e.g., "en-US", "es-ES", "fr-FR")
        """
        if not language or not isinstance(language, str):
            raise TranscriberError("Language must be a non-empty string")
        
        self.language = language
    
    def transcribe(self, audio_path: str) -> str:
        """
        Convert audio file to text transcription.
        
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
        
        # Check file extension
        supported_formats = ['.wav', '.flac', '.aiff', '.aif']
        file_extension = os.path.splitext(audio_path)[1].lower()
        
        if file_extension not in supported_formats:
            raise TranscriberError(
                f"Unsupported audio format: {file_extension}. "
                f"Supported formats: {', '.join(supported_formats)}"
            )
        
        try:
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Record the audio data
                audio_data = self.recognizer.record(source)
            
            # Perform speech recognition
            try:
                text = self.recognizer.recognize_google(audio_data, language=self.language)
                
                if not text or text.strip() == "":
                    raise TranscriberError("No speech detected in audio file")
                
                return text
                
            except sr.UnknownValueError:
                raise TranscriberError("Could not understand audio - speech may be unclear or inaudible")
            except sr.RequestError as e:
                raise TranscriberError(f"Speech recognition service error: {str(e)}")
                
        except Exception as e:
            if isinstance(e, TranscriberError):
                raise
            else:
                raise TranscriberError(f"Failed to process audio file: {str(e)}")
    
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
            # Get transcribed text
            text = self.transcribe(audio_path)
            
            # For now, we'll use a default confidence score
            # In a real implementation, this might come from the recognition engine
            confidence = 0.85
            
            # Create and return Transcription object
            return Transcription(
                text=text,
                confidence=confidence,
                language=self.language
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
            List of supported file extensions
        """
        return ['.wav', '.flac', '.aiff', '.aif']
    
    def get_current_language(self) -> str:
        """
        Get the current language setting.
        
        Returns:
            Current language code
        """
        return self.language
    
    def configure_recognizer(self, **kwargs) -> None:
        """
        Configure speech recognizer settings.
        
        Args:
            **kwargs: Recognizer configuration parameters
                - energy_threshold: Minimum energy level for speech detection
                - pause_threshold: Seconds of pause to consider end of phrase
                - phrase_threshold: Minimum length of phrase to consider
                - dynamic_energy_threshold: Enable automatic threshold adjustment
        """
        if 'energy_threshold' in kwargs:
            self.recognizer.energy_threshold = kwargs['energy_threshold']
        
        if 'pause_threshold' in kwargs:
            self.recognizer.pause_threshold = kwargs['pause_threshold']
        
        if 'phrase_threshold' in kwargs:
            self.recognizer.phrase_threshold = kwargs['phrase_threshold']
        
        if 'dynamic_energy_threshold' in kwargs:
            self.recognizer.dynamic_energy_threshold = kwargs['dynamic_energy_threshold']
        
        if 'non_speaking_duration' in kwargs:
            self.recognizer.non_speaking_duration = kwargs['non_speaking_duration']