"""Configuration management for the video transcriber application."""

import os
from typing import Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class Config:
    """Configuration manager for application settings."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file or self._get_default_config_path()
        self._config = {}
        self._load_dotenv()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        home_dir = Path.home()
        config_dir = home_dir / ".video_transcriber"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.txt")
    
    def _load_dotenv(self) -> None:
        """Load environment variables from .env files."""
        if not DOTENV_AVAILABLE:
            return
        
        # Load .env files in order of preference:
        # 1. .env file in current working directory
        # 2. .env file in project root (where main.py is located)
        # 3. .env file in user's home directory
        
        dotenv_paths = [
            Path.cwd() / ".env",  # Current directory
            Path(__file__).parent.parent.parent / ".env",  # Project root
            Path.home() / ".env"  # Home directory
        ]
        
        for dotenv_path in dotenv_paths:
            if dotenv_path.exists():
                load_dotenv(dotenv_path, override=False)  # Don't override existing env vars
                break
    
    def _load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Load from environment variables first
        self._config = {
            'chatgpt_api_key': os.getenv('CHATGPT_API_KEY') or os.getenv('OPENAI_API_KEY'),
            'output_directory': os.getenv('TRANSCRIBER_OUTPUT_DIR', 'output'),
            'temp_directory': os.getenv('TRANSCRIBER_TEMP_DIR', 'temp'),
        }
        
        # Load from config file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                self._config[key.strip()] = value.strip()
            except (OSError, IOError):
                pass  # Ignore file read errors
    
    def get_chatgpt_api_key(self) -> Optional[str]:
        """Get ChatGPT API key from configuration.
        
        Returns:
            API key if available, None otherwise
        """
        return self._config.get('chatgpt_api_key')
    
    def set_chatgpt_api_key(self, api_key: str) -> None:
        """Set ChatGPT API key in configuration.
        
        Args:
            api_key: The API key to set
        """
        self._config['chatgpt_api_key'] = api_key
        self._save_config()
    
    def get_output_directory(self) -> str:
        """Get output directory path.
        
        Returns:
            Output directory path
        """
        return self._config.get('output_directory', 'output')
    
    def set_output_directory(self, directory: str) -> None:
        """Set output directory path.
        
        Args:
            directory: Directory path to set
        """
        self._config['output_directory'] = directory
        self._save_config()
    
    def get_temp_directory(self) -> str:
        """Get temporary directory path.
        
        Returns:
            Temporary directory path
        """
        return self._config.get('temp_directory', 'temp')
    
    def set_temp_directory(self, directory: str) -> None:
        """Set temporary directory path.
        
        Args:
            directory: Directory path to set
        """
        self._config['temp_directory'] = directory
        self._save_config()
    
    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def set_config(self, key: str, value: str) -> None:
        """Set a configuration value by key.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
        self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Ensure config directory exists
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write("# Video Transcriber Configuration\n")
                f.write("# Format: key=value\n\n")
                
                for key, value in self._config.items():
                    if value is not None:
                        f.write(f"{key}={value}\n")
        except (OSError, IOError):
            pass  # Ignore file write errors
    
    def validate_api_key(self) -> bool:
        """Validate that ChatGPT API key is available and has correct format.
        
        Returns:
            True if API key is valid, False otherwise
        """
        api_key = self.get_chatgpt_api_key()
        if not api_key:
            return False
        
        # Basic validation - OpenAI API keys start with 'sk-'
        return api_key.startswith('sk-') and len(api_key) > 20


# Global config instance for easy access
_config_instance = None


def get_config() -> Config:
    """Get global configuration instance.
    
    Returns:
        Global Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance