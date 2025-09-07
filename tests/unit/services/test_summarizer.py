"""Unit tests for Summarizer service."""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock

from src.services.summarizer import Summarizer
from src.models.summary import Summary


class TestSummarizer(unittest.TestCase):
    """Test cases for Summarizer service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "sk-test-api-key-123"
        self.summarizer = Summarizer(api_key=self.api_key)
        self.test_text = "This is a long text that needs to be summarized for testing purposes."
        self.test_summary = "This is a summary of the text."
    
    def test_init_with_api_key(self):
        """Test Summarizer initialization with API key."""
        summarizer = Summarizer(api_key=self.api_key)
        self.assertEqual(summarizer.api_key, self.api_key)
        self.assertEqual(summarizer.model, "gpt-3.5-turbo")
        self.assertEqual(summarizer.summary_length, "medium")
    
    @patch('src.services.summarizer.get_config')
    def test_init_without_api_key_uses_config(self, mock_get_config):
        """Test Summarizer initialization without API key uses config."""
        mock_config = Mock()
        mock_config.get_chatgpt_api_key.return_value = "sk-config-key"
        mock_get_config.return_value = mock_config
        
        summarizer = Summarizer()
        self.assertEqual(summarizer.api_key, "sk-config-key")
    
    @patch('src.services.summarizer.requests.post')
    def test_generate_summary_success(self, mock_post):
        """Test successful summary generation."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": self.test_summary
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        result = self.summarizer.generate_summary(self.test_text)
        
        self.assertEqual(result, self.test_summary)
        mock_post.assert_called_once()
        
        # Verify the API call was made with correct parameters
        call_args = mock_post.call_args
        self.assertIn("headers", call_args.kwargs)
        self.assertIn("json", call_args.kwargs)
        self.assertEqual(call_args.kwargs["headers"]["Authorization"], f"Bearer {self.api_key}")
    
    @patch('src.services.summarizer.requests.post')
    def test_generate_summary_api_error(self, mock_post):
        """Test summary generation with API error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        result = self.summarizer.generate_summary(self.test_text)
        
        self.assertIsNone(result)
    
    @patch('src.services.summarizer.requests.post')
    def test_generate_summary_network_error(self, mock_post):
        """Test summary generation with network error."""
        mock_post.side_effect = Exception("Network error")
        
        result = self.summarizer.generate_summary(self.test_text)
        
        self.assertIsNone(result)
    
    def test_generate_summary_empty_text(self):
        """Test summary generation with empty text."""
        result = self.summarizer.generate_summary("")
        self.assertIsNone(result)
        
        result = self.summarizer.generate_summary("   ")
        self.assertIsNone(result)
    
    def test_generate_summary_no_api_key(self):
        """Test summary generation without API key."""
        summarizer = Summarizer(api_key=None)
        result = summarizer.generate_summary(self.test_text)
        
        self.assertIsNone(result)
    
    @patch('src.services.summarizer.requests.post')
    def test_generate_summary_with_custom_api_key(self, mock_post):
        """Test summary generation with custom API key parameter."""
        custom_key = "sk-custom-key"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": self.test_summary}}]
        }
        mock_post.return_value = mock_response
        
        result = self.summarizer.generate_summary(self.test_text, api_key=custom_key)
        
        self.assertEqual(result, self.test_summary)
        
        # Verify custom API key was used
        call_args = mock_post.call_args
        self.assertEqual(call_args.kwargs["headers"]["Authorization"], f"Bearer {custom_key}")
    
    @patch('src.services.summarizer.requests.post')
    def test_generate_summary_malformed_response(self, mock_post):
        """Test summary generation with malformed API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "malformed response"}
        mock_post.return_value = mock_response
        
        result = self.summarizer.generate_summary(self.test_text)
        
        self.assertIsNone(result)
    
    def test_set_summary_length_valid(self):
        """Test setting valid summary lengths."""
        self.summarizer.set_summary_length("short")
        self.assertEqual(self.summarizer.summary_length, "short")
        
        self.summarizer.set_summary_length("LONG")
        self.assertEqual(self.summarizer.summary_length, "long")
        
        self.summarizer.set_summary_length("Medium")
        self.assertEqual(self.summarizer.summary_length, "medium")
    
    def test_set_summary_length_invalid(self):
        """Test setting invalid summary length doesn't change value."""
        original_length = self.summarizer.summary_length
        self.summarizer.set_summary_length("invalid")
        self.assertEqual(self.summarizer.summary_length, original_length)
    
    def test_set_model(self):
        """Test setting the model."""
        new_model = "gpt-4"
        self.summarizer.set_model(new_model)
        self.assertEqual(self.summarizer.model, new_model)
    
    def test_create_summary_object(self):
        """Test creating Summary object."""
        original_text = "This is the original text that was summarized."
        summary_text = "This is the summary."
        
        summary = self.summarizer.create_summary_object(original_text, summary_text)
        
        self.assertIsInstance(summary, Summary)
        self.assertEqual(summary.text, summary_text)
        self.assertEqual(summary.original_length, len(original_text))
    
    def test_create_summary_prompt_short(self):
        """Test creating summary prompt for short length."""
        self.summarizer.set_summary_length("short")
        prompt = self.summarizer._create_summary_prompt(self.test_text)
        
        self.assertIn("1-2 concise sentences", prompt)
        self.assertIn(self.test_text, prompt)
    
    def test_create_summary_prompt_medium(self):
        """Test creating summary prompt for medium length."""
        self.summarizer.set_summary_length("medium")
        prompt = self.summarizer._create_summary_prompt(self.test_text)
        
        self.assertIn("3-5 sentences", prompt)
        self.assertIn(self.test_text, prompt)
    
    def test_create_summary_prompt_long(self):
        """Test creating summary prompt for long length."""
        self.summarizer.set_summary_length("long")
        prompt = self.summarizer._create_summary_prompt(self.test_text)
        
        self.assertIn("1-2 paragraphs", prompt)
        self.assertIn(self.test_text, prompt)
    
    def test_get_max_tokens_for_length(self):
        """Test getting max tokens for different lengths."""
        self.summarizer.set_summary_length("short")
        self.assertEqual(self.summarizer._get_max_tokens_for_length(), 100)
        
        self.summarizer.set_summary_length("medium")
        self.assertEqual(self.summarizer._get_max_tokens_for_length(), 200)
        
        self.summarizer.set_summary_length("long")
        self.assertEqual(self.summarizer._get_max_tokens_for_length(), 400)
    
    @patch('src.services.summarizer.requests.post')
    def test_validate_api_key_valid(self, mock_post):
        """Test API key validation with valid key."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = self.summarizer.validate_api_key()
        
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    @patch('src.services.summarizer.requests.post')
    def test_validate_api_key_invalid(self, mock_post):
        """Test API key validation with invalid key."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        result = self.summarizer.validate_api_key()
        
        self.assertFalse(result)
    
    @patch('src.services.summarizer.requests.post')
    def test_validate_api_key_network_error(self, mock_post):
        """Test API key validation with network error."""
        mock_post.side_effect = Exception("Network error")
        
        result = self.summarizer.validate_api_key()
        
        self.assertFalse(result)
    
    def test_validate_api_key_no_key(self):
        """Test API key validation without key."""
        summarizer = Summarizer(api_key=None)
        result = summarizer.validate_api_key()
        
        self.assertFalse(result)
    
    @patch('src.services.summarizer.requests.post')
    def test_validate_api_key_custom_key(self, mock_post):
        """Test API key validation with custom key parameter."""
        custom_key = "sk-custom-key"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = self.summarizer.validate_api_key(api_key=custom_key)
        
        self.assertTrue(result)
        
        # Verify custom API key was used
        call_args = mock_post.call_args
        self.assertEqual(call_args.kwargs["headers"]["Authorization"], f"Bearer {custom_key}")
    
    @patch('src.services.summarizer.requests.post')
    def test_api_request_timeout(self, mock_post):
        """Test API request with timeout settings."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": self.test_summary}}]
        }
        mock_post.return_value = mock_response
        
        result = self.summarizer.generate_summary(self.test_text)
        
        self.assertEqual(result, self.test_summary)
        
        # Verify timeout was set
        call_args = mock_post.call_args
        self.assertEqual(call_args.kwargs["timeout"], 30)
    
    @patch('src.services.summarizer.requests.post')
    def test_api_request_payload_structure(self, mock_post):
        """Test that API request payload has correct structure."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": self.test_summary}}]
        }
        mock_post.return_value = mock_response
        
        self.summarizer.set_summary_length("short")
        result = self.summarizer.generate_summary(self.test_text)
        
        self.assertEqual(result, self.test_summary)
        
        # Verify payload structure
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        
        self.assertEqual(payload["model"], "gpt-3.5-turbo")
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["role"], "user")
        self.assertEqual(payload["max_tokens"], 100)  # short length
        self.assertEqual(payload["temperature"], 0.3)


if __name__ == '__main__':
    unittest.main()