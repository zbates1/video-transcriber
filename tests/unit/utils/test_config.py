"""Unit tests for Config utility."""

import os
import tempfile
import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from src.utils.config import Config, get_config


class TestConfig(unittest.TestCase):
    """Test cases for Config utility."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for config files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_file = os.path.join(self.temp_dir, "test_config.txt")
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        if os.path.exists(self.temp_config_file):
            os.remove(self.temp_config_file)
        os.rmdir(self.temp_dir)
        
        # Reset global config instance
        import src.utils.config
        src.utils.config._config_instance = None
    
    def test_init_with_custom_config_file(self):
        """Test Config initialization with custom config file."""
        config = Config(self.temp_config_file)
        self.assertEqual(config.config_file, self.temp_config_file)
    
    def test_init_with_default_config_file(self):
        """Test Config initialization with default config file."""
        config = Config()
        # Handle both Unix and Windows path separators
        expected_ending = os.path.join('.video_transcriber', 'config.txt')
        self.assertTrue(config.config_file.endswith(expected_ending))
    
    @patch.dict(os.environ, {'CHATGPT_API_KEY': 'sk-test-key-123'})
    def test_load_config_from_environment(self):
        """Test loading configuration from environment variables."""
        config = Config(self.temp_config_file)
        self.assertEqual(config.get_chatgpt_api_key(), 'sk-test-key-123')
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-openai-key-456'})
    def test_load_config_openai_env_var(self):
        """Test loading configuration from OPENAI_API_KEY environment variable."""
        config = Config(self.temp_config_file)
        self.assertEqual(config.get_chatgpt_api_key(), 'sk-openai-key-456')
    
    @patch.dict(os.environ, {'TRANSCRIBER_OUTPUT_DIR': '/custom/output'})
    def test_load_output_dir_from_environment(self):
        """Test loading output directory from environment variable."""
        config = Config(self.temp_config_file)
        self.assertEqual(config.get_output_directory(), '/custom/output')
    
    def test_load_config_from_file(self):
        """Test loading configuration from file."""
        # Create test config file
        with open(self.temp_config_file, 'w') as f:
            f.write("# Test config\n")
            f.write("chatgpt_api_key=sk-file-key-789\n")
            f.write("output_directory=/file/output\n")
        
        config = Config(self.temp_config_file)
        self.assertEqual(config.get_chatgpt_api_key(), 'sk-file-key-789')
        self.assertEqual(config.get_output_directory(), '/file/output')
    
    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables
    @patch('src.utils.config.DOTENV_AVAILABLE', False)  # Disable .env loading
    def test_get_chatgpt_api_key_none(self):
        """Test get_chatgpt_api_key returns None when not set."""
        config = Config(self.temp_config_file)
        self.assertIsNone(config.get_chatgpt_api_key())
    
    def test_set_chatgpt_api_key(self):
        """Test setting ChatGPT API key."""
        config = Config(self.temp_config_file)
        config.set_chatgpt_api_key('sk-new-key-abc')
        self.assertEqual(config.get_chatgpt_api_key(), 'sk-new-key-abc')
    
    def test_get_output_directory_default(self):
        """Test get_output_directory returns default value."""
        config = Config(self.temp_config_file)
        self.assertEqual(config.get_output_directory(), 'output')
    
    def test_set_output_directory(self):
        """Test setting output directory."""
        config = Config(self.temp_config_file)
        config.set_output_directory('/new/output')
        self.assertEqual(config.get_output_directory(), '/new/output')
    
    def test_get_temp_directory_default(self):
        """Test get_temp_directory returns default value."""
        config = Config(self.temp_config_file)
        self.assertEqual(config.get_temp_directory(), 'temp')
    
    def test_set_temp_directory(self):
        """Test setting temporary directory."""
        config = Config(self.temp_config_file)
        config.set_temp_directory('/new/temp')
        self.assertEqual(config.get_temp_directory(), '/new/temp')
    
    def test_get_config_with_default(self):
        """Test get_config returns default value for non-existent key."""
        config = Config(self.temp_config_file)
        self.assertEqual(config.get_config('nonexistent', 'default_value'), 'default_value')
        self.assertIsNone(config.get_config('nonexistent'))
    
    def test_set_config(self):
        """Test setting custom configuration value."""
        config = Config(self.temp_config_file)
        config.set_config('custom_key', 'custom_value')
        self.assertEqual(config.get_config('custom_key'), 'custom_value')
    
    def test_save_config_creates_file(self):
        """Test that save_config creates configuration file."""
        config = Config(self.temp_config_file)
        config.set_chatgpt_api_key('sk-test-save-key')
        
        # Check that file was created and contains the key
        self.assertTrue(os.path.exists(self.temp_config_file))
        with open(self.temp_config_file, 'r') as f:
            content = f.read()
            self.assertIn('chatgpt_api_key=sk-test-save-key', content)
    
    def test_validate_api_key_valid(self):
        """Test validate_api_key returns True for valid API key."""
        config = Config(self.temp_config_file)
        config.set_chatgpt_api_key('sk-valid-key-with-sufficient-length')
        self.assertTrue(config.validate_api_key())
    
    def test_validate_api_key_invalid_format(self):
        """Test validate_api_key returns False for invalid format."""
        config = Config(self.temp_config_file)
        config.set_chatgpt_api_key('invalid-key-format')
        self.assertFalse(config.validate_api_key())
    
    def test_validate_api_key_too_short(self):
        """Test validate_api_key returns False for too short key."""
        config = Config(self.temp_config_file)
        config.set_chatgpt_api_key('sk-short')
        self.assertFalse(config.validate_api_key())
    
    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables
    @patch('src.utils.config.DOTENV_AVAILABLE', False)  # Disable .env loading
    def test_validate_api_key_none(self):
        """Test validate_api_key returns False when no key is set."""
        config = Config(self.temp_config_file)
        self.assertFalse(config.validate_api_key())
    
    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables
    @patch('src.utils.config.DOTENV_AVAILABLE', False)  # Disable .env loading
    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist doesn't raise error."""
        non_existent_file = os.path.join(self.temp_dir, "nonexistent.txt")
        config = Config(non_existent_file)
        # Should not raise an exception
        self.assertIsNone(config.get_chatgpt_api_key())
    
    def test_load_config_malformed_line(self):
        """Test loading config with malformed lines doesn't break."""
        # Create test config file with malformed line
        with open(self.temp_config_file, 'w') as f:
            f.write("# Test config\n")
            f.write("chatgpt_api_key=sk-valid-key\n")
            f.write("malformed_line_without_equals\n")
            f.write("output_directory=/test/output\n")
        
        config = Config(self.temp_config_file)
        self.assertEqual(config.get_chatgpt_api_key(), 'sk-valid-key')
        self.assertEqual(config.get_output_directory(), '/test/output')
    
    @patch('src.utils.config.DOTENV_AVAILABLE', True)
    @patch('src.utils.config.load_dotenv')
    @patch('src.utils.config.Path')
    def test_load_dotenv_file_found(self, mock_path_class, mock_load_dotenv):
        """Test loading .env file when it exists."""
        # Mock Path.cwd() and Path.exists()
        mock_cwd = MagicMock()
        mock_cwd.__truediv__ = MagicMock(return_value=mock_cwd)
        mock_cwd.exists.return_value = True
        mock_path_class.cwd.return_value = mock_cwd
        
        # Mock other paths to return False
        mock_other_path = MagicMock()
        mock_other_path.exists.return_value = False
        mock_path_class.return_value = mock_other_path
        
        # Create config which should trigger .env loading
        config = Config(self.temp_config_file)
        
        # Verify load_dotenv was called
        mock_load_dotenv.assert_called_once()
        call_args = mock_load_dotenv.call_args
        self.assertEqual(call_args.kwargs['override'], False)
    
    @patch('src.utils.config.DOTENV_AVAILABLE', True)
    @patch('src.utils.config.load_dotenv')
    @patch('src.utils.config.Path.exists')
    def test_load_dotenv_no_file_found(self, mock_exists, mock_load_dotenv):
        """Test behavior when no .env file is found."""
        # Mock that no .env file exists
        mock_exists.return_value = False
        
        # Create config
        config = Config(self.temp_config_file)
        
        # Verify load_dotenv was not called since no file exists
        mock_load_dotenv.assert_not_called()
    
    @patch('src.utils.config.DOTENV_AVAILABLE', False)
    def test_load_dotenv_not_available(self):
        """Test behavior when python-dotenv is not installed."""
        # This should not raise an error
        config = Config(self.temp_config_file)
        
        # Config should still work without dotenv
        self.assertIsNotNone(config)
    
    @patch('src.utils.config.DOTENV_AVAILABLE', True)
    @patch('src.utils.config.load_dotenv')
    @patch('src.utils.config.Path.exists')
    def test_dotenv_priority_order(self, mock_exists, mock_load_dotenv):
        """Test that .env files are loaded in correct priority order."""
        # Mock that only project root .env exists (second priority)
        def exists_side_effect(path):
            return 'parent.parent.parent' in str(path) and str(path).endswith('.env')
        
        mock_exists.side_effect = exists_side_effect
        
        # Create config
        config = Config(self.temp_config_file)
        
        # Verify load_dotenv was called with project root path
        mock_load_dotenv.assert_called_once()
        call_args = mock_load_dotenv.call_args
        self.assertIn('parent', str(call_args[0][0]))
    
    @patch.dict(os.environ, {}, clear=True)  # Clear environment
    @patch('src.utils.config.DOTENV_AVAILABLE', True)
    @patch('src.utils.config.load_dotenv')
    @patch('src.utils.config.Path.exists')
    def test_dotenv_loads_api_key(self, mock_exists, mock_load_dotenv):
        """Test that API key from .env file is accessible."""
        # Mock .env file exists
        mock_exists.return_value = True
        
        # Mock load_dotenv to set environment variable
        def mock_load_dotenv_func(*args, **kwargs):
            os.environ['OPENAI_API_KEY'] = 'sk-dotenv-test-key'
        
        mock_load_dotenv.side_effect = mock_load_dotenv_func
        
        # Create config
        config = Config(self.temp_config_file)
        
        # Verify API key was loaded from .env
        self.assertEqual(config.get_chatgpt_api_key(), 'sk-dotenv-test-key')
        
        # Clean up
        os.environ.pop('OPENAI_API_KEY', None)


class TestGetConfig(unittest.TestCase):
    """Test cases for get_config global function."""
    
    def tearDown(self):
        """Clean up global config instance."""
        import src.utils.config
        src.utils.config._config_instance = None
    
    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        self.assertIs(config1, config2)
    
    def test_get_config_returns_config_instance(self):
        """Test that get_config returns a Config instance."""
        config = get_config()
        self.assertIsInstance(config, Config)


if __name__ == '__main__':
    unittest.main()