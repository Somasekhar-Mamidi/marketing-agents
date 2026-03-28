"""Tests for LLM Client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.llm_client import LLMClient, LLMResponse, get_llm_client


class TestLLMClient:
    """Test suite for LLMClient."""
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        client = LLMClient(api_key=None)
        assert client.api_key is None
        assert not client.is_configured
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = LLMClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.is_configured
    
    def test_complete_without_config(self):
        """Test completion without configuration."""
        client = LLMClient(api_key=None)
        response = client.complete("test prompt")
        
        assert not response.success
        assert "not configured" in response.error.lower()
    
    @patch('utils.llm_client.OpenAI')
    def test_complete_success(self, mock_openai_class):
        """Test successful completion."""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Test
        client = LLMClient(api_key="test-key")
        response = client.complete("test prompt")
        
        assert response.success
        assert response.content == "Test response"
        assert response.model == "gpt-4o-mini"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["total_tokens"] == 15
    
    @patch('utils.llm_client.OpenAI')
    def test_complete_with_system_message(self, mock_openai_class):
        """Test completion with system message."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        client = LLMClient(api_key="test-key")
        response = client.complete(
            "test prompt",
            system_message="You are a helpful assistant"
        )
        
        assert response.success
        # Verify system message was included
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant"
    
    @patch('utils.llm_client.OpenAI')
    def test_complete_api_error(self, mock_openai_class):
        """Test completion with API error."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        client = LLMClient(api_key="test-key")
        response = client.complete("test prompt")
        
        assert not response.success
        assert "API Error" in response.error
    
    def test_parse_json_response_success(self):
        """Test parsing valid JSON response."""
        client = LLMClient(api_key="test-key")
        response = LLMResponse(
            content='{"score": 8.5, "reason": "good"}',
            model="gpt-4o-mini",
            usage={},
            success=True
        )
        
        result = client.parse_json_response(response)
        assert result["score"] == 8.5
        assert result["reason"] == "good"
    
    def test_parse_json_response_with_code_block(self):
        """Test parsing JSON from markdown code block."""
        client = LLMClient(api_key="test-key")
        response = LLMResponse(
            content='```json\n{"score": 8.5}\n```',
            model="gpt-4o-mini",
            usage={},
            success=True
        )
        
        result = client.parse_json_response(response)
        assert result["score"] == 8.5
    
    def test_parse_json_response_invalid(self):
        """Test parsing invalid JSON response."""
        client = LLMClient(api_key="test-key")
        response = LLMResponse(
            content="not valid json",
            model="gpt-4o-mini",
            usage={},
            success=True
        )
        
        result = client.parse_json_response(response)
        assert "error" in result
        assert result["raw_content"] == "not valid json"
    
    def test_parse_json_response_failed(self):
        """Test parsing response that failed."""
        client = LLMClient(api_key="test-key")
        response = LLMResponse(
            content="",
            model="gpt-4o-mini",
            usage={},
            success=False,
            error="API Error"
        )
        
        result = client.parse_json_response(response)
        assert result["error"] == "API Error"


class TestGetLLMClient:
    """Test suite for get_llm_client function."""
    
    def test_singleton_pattern(self):
        """Test that get_llm_client returns singleton."""
        with patch('utils.llm_client._llm_client', None):
            client1 = get_llm_client()
            client2 = get_llm_client()
            assert client1 is client2
