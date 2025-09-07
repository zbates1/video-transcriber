"""Summarizer service for generating AI summaries using ChatGPT API."""

import json
import os
import sys
import requests
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.summary import Summary
from utils.config import get_config


class Summarizer:
    """Service for generating AI summaries using ChatGPT API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Summarizer with API key.
        
        Args:
            api_key: OpenAI API key. If None, will try to get from config.
        """
        self.api_key = api_key or get_config().get_chatgpt_api_key()
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.summary_length = "medium"  # short, medium, long
        
    def generate_summary(self, text: str, api_key: Optional[str] = None) -> Optional[str]:
        """Generate AI summary using ChatGPT API.
        
        Args:
            text: Text to summarize
            api_key: Optional API key to use for this request
            
        Returns:
            Generated summary text, or None if generation failed
        """
        if not text or not text.strip():
            return None
            
        # Use provided API key or instance API key
        key_to_use = api_key or self.api_key
        if not key_to_use:
            return None
            
        try:
            # Prepare the prompt based on summary length
            prompt = self._create_summary_prompt(text)
            
            # Make request to OpenAI API
            headers = {
                "Authorization": f"Bearer {key_to_use}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates concise and accurate summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self._get_max_tokens_for_length(),
                "temperature": 0.3
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    return response_data["choices"][0]["message"]["content"].strip()
            
            return None
            
        except (requests.RequestException, json.JSONDecodeError, KeyError, Exception):
            return None
    
    def set_summary_length(self, length: str) -> None:
        """Set summary length preference.
        
        Args:
            length: Summary length ("short", "medium", "long")
        """
        if length.lower() in ["short", "medium", "long"]:
            self.summary_length = length.lower()
    
    def set_model(self, model: str) -> None:
        """Set the OpenAI model to use.
        
        Args:
            model: Model name (e.g., "gpt-3.5-turbo", "gpt-4")
        """
        self.model = model
    
    def create_summary_object(self, original_text: str, summary_text: str) -> Summary:
        """Create a Summary object from the original text and summary.
        
        Args:
            original_text: The original text that was summarized
            summary_text: The generated summary text
            
        Returns:
            Summary object
        """
        return Summary(
            text=summary_text,
            original_length=len(original_text)
        )
    
    def _create_summary_prompt(self, text: str) -> str:
        """Create a summary prompt based on the configured length.
        
        Args:
            text: Text to summarize
            
        Returns:
            Formatted prompt for the API
        """
        length_instructions = {
            "short": "in 1-2 concise sentences",
            "medium": "in 3-5 sentences",
            "long": "in 1-2 paragraphs"
        }
        
        instruction = length_instructions.get(self.summary_length, "in 3-5 sentences")
        
        return (
            f"Please summarize the following text {instruction}. "
            f"Focus on the key points and main ideas:\n\n{text}"
        )
    
    def _get_max_tokens_for_length(self) -> int:
        """Get maximum tokens based on summary length setting.
        
        Returns:
            Maximum tokens for the response
        """
        token_limits = {
            "short": 100,
            "medium": 200,
            "long": 400
        }
        
        return token_limits.get(self.summary_length, 200)
    
    def validate_api_key(self, api_key: Optional[str] = None) -> bool:
        """Validate that the API key works with a simple API call.
        
        Args:
            api_key: API key to validate. If None, uses instance API key.
            
        Returns:
            True if API key is valid, False otherwise
        """
        key_to_use = api_key or self.api_key
        if not key_to_use:
            return False
        
        try:
            # Make a simple API call to test the key
            headers = {
                "Authorization": f"Bearer {key_to_use}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Test"
                    }
                ],
                "max_tokens": 5
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except (requests.RequestException, Exception):
            return False