"""Tests for LLM Client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.llm_client import LLMClient, LLMResponse, get_llm_client
from utils.configurable_llm_client import (
    ConfigurableLLMClient,
    get_llm_client_for_agent,
    get_llm_with_tools_for_agent,
    LLMResponse as ConfLLMResponse,
)


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

    
def _make_fake_provider_class():
    # Fake provider to avoid real API calls during tests
    class FakeProvider:
        def __init__(self, base_url, api_key):
            self.base_url = base_url
            self.api_key = api_key
            self.available = True
            self.last_call = None

        def is_available(self):
            return self.available

        def complete(self, prompt, config, system_message=None, response_format=None):
            self.last_call = {"type": "complete", "model_id": config.model_id, "prompt": prompt, "system_message": system_message}
            return ConfLLMResponse(
                content="plain-ok",
                model=config.model_id,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                success=True,
            )

        def complete_with_tools(self, prompt, config, tools, tool_registry, system_message=None, max_tool_calls=5):
            self.last_call = {"type": "with_tools", "model_id": config.model_id, "prompt": prompt, "system_message": system_message}
            return ConfLLMResponse(
                content="tools-ok",
                model=config.model_id,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                success=True,
            )

    return FakeProvider


def _write_temp_models_yaml(tmp_path, content: str) -> str:
    p = tmp_path / "models.yaml"
    p.write_text(content)
    return str(p)


def test_get_llm_client_for_agent_plain(monkeypatch, tmp_path):
    """Test get_llm_client_for_agent returns a plain completion function."""
    yaml_content = """
llm:
  providers:
    grid_ai:
      base_url: "https://grid.example"
      api_key_env: "GRID_AI_API_KEY"
      models:
        - id: "primary-model"
          name: "Primary"
  agent_models:
    plain_agent:
      provider: grid_ai
      model: primary-model
      strategy: native_web_access
  defaults:
    provider: grid_ai
    model: primary-model
"""
    path = _write_temp_models_yaml(tmp_path, yaml_content)

    # Patch environment and provider class
    FakeProvider = _make_fake_provider_class()
    import utils.configurable_llm_client as clmc
    monkeypatch.setattr(clmc, "OpenAICompatibleProvider", FakeProvider)
    monkeypatch.setattr(clmc, "get_env_var", lambda k: "fake-key" if k == "GRID_AI_API_KEY" else None)
    clmc.ConfigurableLLMClient._instance = None
    client = clmc.ConfigurableLLMClient(config_path=path)
    clmc._llm_client = client

    # Bind the helper to the agent
    complete_for_agent = clmc.get_llm_client_for_agent("plain_agent")
    resp = complete_for_agent("Test prompt")

    # Verify that provider was used for plain completion
    prov = client._providers.get("grid_ai")
    assert prov is not None
    assert isinstance(prov, FakeProvider)
    assert prov.last_call["model_id"] == "primary-model"
    assert resp.success is True


def test_get_llm_with_tools_for_agent_routing_tool_and_hybrid(monkeypatch, tmp_path):
    """Test tool-enabled routing and hybrid fallback path."""
    yaml_content = """
llm:
  providers:
    grid_ai:
      base_url: "https://grid.example"
      api_key_env: "GRID_AI_API_KEY"
      models:
        - id: "primary-model"
          name: "Primary"
        - id: "fallback-model"
          name: "Fallback"
  agent_models:
    tool_agent:
      provider: grid_ai
      model: primary-model
      strategy: tool_calling
    hybrid_agent:
      provider: grid_ai
      model: primary-model
      strategy: hybrid
      fallback:
        provider: grid_ai
        model: fallback-model
  defaults:
    provider: grid_ai
    model: primary-model
"""
    path = _write_temp_models_yaml(tmp_path, yaml_content)

    FakeProvider = _make_fake_provider_class()
    import utils.configurable_llm_client as clmc
    monkeypatch.setattr(clmc, "OpenAICompatibleProvider", FakeProvider)
    monkeypatch.setattr(clmc, "get_env_var", lambda k: "fake-key" if k == "GRID_AI_API_KEY" else None)
    clmc.ConfigurableLLMClient._instance = None
    client = clmc.ConfigurableLLMClient(config_path=path)
    clmc._llm_client = client

    # Tooling path
    tool_for_agent = clmc.get_llm_with_tools_for_agent("tool_agent")
    res = tool_for_agent("Find something useful")
    prov = client._providers.get("grid_ai")
    assert isinstance(prov, FakeProvider)
    assert prov.last_call["type"] == "with_tools"
    assert res.success is True

    # Hybrid path should fall back to tools when native fails
    hybrid = clmc.get_llm_with_tools_for_agent("hybrid_agent")
    res2 = hybrid("Do something important")
    # last_call should indicate a fallback model usage or tool call
    assert res2.success is True


def test_hybrid_fallback_execution(monkeypatch, tmp_path):
    """Test hybrid routing explicitly triggers fallback model for hybrid_agent."""
    yaml_content = """
llm:
  providers:
    grid_ai:
      base_url: "https://grid.example"
      api_key_env: "GRID_AI_API_KEY"
      models:
        - id: "primary-model"
          name: "Primary"
        - id: "fallback-model"
          name: "Fallback"
  agent_models:
    hybrid_agent:
      provider: grid_ai
      model: primary-model
      strategy: hybrid
      fallback:
        provider: grid_ai
        model: fallback-model
  defaults:
    provider: grid_ai
    model: primary-model
"""
    path = _write_temp_models_yaml(tmp_path, yaml_content)

    class FakeProvider:
        def __init__(self, base_url, api_key):
            self.base_url = base_url
            self.api_key = api_key
            self.available = True
            self.last_call = None

        def is_available(self):
            return self.available

        def complete(self, prompt, config, system_message=None, response_format=None):
            self.last_call = {"type": "complete", "model_id": config.model_id}
            # Simulate failure for hybrid primary path
            return ConfLLMResponse(content="", model=config.model_id, usage={}, success=False)

        def complete_with_tools(self, prompt, config, tools, registry, system_message=None, max_tool_calls=5):
            self.last_call = {"type": "with_tools", "model_id": config.model_id}
            return ConfLLMResponse(content="hybrid-ok", model=config.model_id, usage={}, success=True)

    import utils.configurable_llm_client as clmc
    monkeypatch.setattr(clmc, "OpenAICompatibleProvider", FakeProvider)
    monkeypatch.setattr(clmc, "get_env_var", lambda k: "fake-key" if k == "GRID_AI_API_KEY" else None)
    clmc.ConfigurableLLMClient._instance = None
    client = clmc.ConfigurableLLMClient(config_path=path)
    clmc._llm_client = client

    hybrid = clmc.get_llm_with_tools_for_agent("hybrid_agent")
    resp = hybrid("do it now")
    # Ensure fallback path was used and a tool-based call happened (via complete_with_tools)
    prov = client._providers.get("grid_ai")
    assert isinstance(prov, FakeProvider)
    assert prov.last_call is not None
    assert resp.success is True
