"""Configurable LLM Client with multi-provider and per-agent model selection."""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import yaml
from pathlib import Path

from config.loader import get_env_var
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a specific model instance."""
    model_id: str
    provider: str
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout_seconds: int = 60
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    supports_json: bool = True
    supports_vision: bool = False
    supports_search: bool = False


@dataclass
class LLMResponse:
    """Structured LLM response with metadata."""
    content: str
    model: str
    usage: Dict[str, int]
    success: bool
    error: Optional[str] = None
    latency_ms: Optional[int] = None


class LLMProvider(ABC):
    """Abstract base for LLM providers."""
    
    @abstractmethod
    def complete(
        self,
        prompt: str,
        config: ModelConfig,
        system_message: Optional[str] = None,
        response_format: Optional[Dict] = None
    ) -> LLMResponse:
        """Execute completion request."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible API provider for Grid AI and similar endpoints."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self._client = None
    
    def _get_client(self):
        """Lazy initialize OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
                logger.info(f"Initialized OpenAI client for {self.base_url}")
            except ImportError:
                logger.error("OpenAI package not installed. Run: pip install openai")
                raise
        return self._client
    
    def complete_with_tools(
        self,
        prompt: str,
        config: ModelConfig,
        tools: list,
        tool_registry: Any,
        system_message: Optional[str] = None,
        max_tool_calls: int = 5
    ) -> LLMResponse:
        """Execute completion with tool calling support.
        
        This method allows the LLM to call tools (like web_search) during generation.
        It handles the tool calling loop: LLM decides to call tool -> tool executes -> 
        results returned to LLM -> LLM synthesizes final answer.
        
        Args:
            prompt: User prompt
            config: Model configuration
            tools: List of tool definitions for OpenAI format
            tool_registry: Registry to execute tools
            system_message: Optional system message
            max_tool_calls: Maximum number of tool call rounds (prevents infinite loops)
            
        Returns:
            LLMResponse with final content
        """
        import json
        start_time = time.time()
        
        try:
            client = self._get_client()
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            tool_calls_made = 0
            
            while tool_calls_made < max_tool_calls:
                kwargs = {
                    "model": config.model_id,
                    "messages": messages,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                    "timeout": config.timeout_seconds,
                    "tools": tools,
                    "tool_choice": "auto"
                }
                
                response = client.chat.completions.create(**kwargs)
                message = response.choices[0].message
                
                # Check if model wants to call tools
                if not message.tool_calls:
                    # No tool calls, we have final answer
                    latency_ms = int((time.time() - start_time) * 1000)
                    return LLMResponse(
                        content=message.content or "",
                        model=response.model,
                        usage={
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        },
                        success=True,
                        latency_ms=latency_ms
                    )
                
                # Model wants to call tools - add assistant message to conversation
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                
                # Execute each tool call
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    logger.info(f"Tool call: {tool_name}({arguments})")
                    
                    # Execute tool
                    tool_result = tool_registry.execute(tool_name, arguments)
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                tool_calls_made += 1
            
            # Max tool calls reached, get final response without tools
            kwargs = {
                "model": config.model_id,
                "messages": messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "timeout": config.timeout_seconds
            }
            
            response = client.chat.completions.create(**kwargs)
            latency_ms = int((time.time() - start_time) * 1000)
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                success=True,
                latency_ms=latency_ms,
                error=f"Max tool calls ({max_tool_calls}) reached"
            )
            
        except Exception as e:
            logger.error(f"LLM completion with tools failed: {e}")
            latency_ms = int((time.time() - start_time) * 1000)
            return LLMResponse(
                content="",
                model=config.model_id,
                usage={},
                success=False,
                error=str(e),
                latency_ms=latency_ms
            )
    
    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exceptions=(Exception,)
    )
    def complete(
        self,
        prompt: str,
        config: ModelConfig,
        system_message: Optional[str] = None,
        response_format: Optional[Dict] = None
    ) -> LLMResponse:
        """Execute OpenAI-compatible completion."""
        start_time = time.time()
        
        try:
            client = self._get_client()
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            kwargs = {
                "model": config.model_id,
                "messages": messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "timeout": config.timeout_seconds
            }
            
            if response_format and config.supports_json:
                kwargs["response_format"] = response_format
            
            response = client.chat.completions.create(**kwargs)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                success=True,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            return LLMResponse(
                content="",
                model=config.model_id,
                usage={},
                success=False,
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000)
            )
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key and self.api_key not in ["", "your_api_key_here", "${GRID_AI_API_KEY}"])


class ConfigurableLLMClient:
    """Multi-provider LLM client with per-agent model selection."""
    
    _instance: Optional['ConfigurableLLMClient'] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure one client instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with model configuration.
        
        Args:
            config_path: Path to models.yaml (default: config/models.yaml)
        """
        if self._initialized:
            return
        
        self.config_path = config_path or str(
            Path(__file__).parent.parent / "config" / "models.yaml"
        )
        self.config = self._load_config()
        self._providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()
        self._initialized = True
        
        logger.info(f"ConfigurableLLMClient initialized with {len(self._providers)} providers")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration from YAML."""
        config_file = Path(self.config_path)
        if not config_file.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return self._default_config()
        
        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded model config from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration if file not found."""
        return {
            "llm": {
                "providers": {
                    "grid_ai": {
                        "base_url": "https://grid.ai.juspay.net",
                        "api_key_env": "GRID_AI_API_KEY"
                    }
                },
                "agent_models": {},
                "defaults": {
                    "provider": "grid_ai",
                    "model": "claude-sonnet-4-5"
                }
            }
        }
    
    def _initialize_providers(self):
        """Initialize all configured providers."""
        providers_config = self.config.get("llm", {}).get("providers", {})
        
        for provider_name, provider_config in providers_config.items():
            api_key_env = provider_config.get("api_key_env", f"{provider_name.upper()}_API_KEY")
            api_key = get_env_var(api_key_env)
            base_url = provider_config.get("base_url")
            
            if api_key and base_url:
                self._providers[provider_name] = OpenAICompatibleProvider(
                    base_url=base_url,
                    api_key=api_key
                )
                logger.info(f"Initialized provider: {provider_name}")
            else:
                logger.warning(f"Provider {provider_name} not configured (missing API key or base URL)")
    
    def get_model_config(self, agent_name: str) -> ModelConfig:
        """Get model configuration for specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., "intent_understanding")
            
        Returns:
            ModelConfig with provider, model, and parameters
        """
        agent_models = self.config.get("llm", {}).get("agent_models", {})
        defaults = self.config.get("llm", {}).get("defaults", {})
        
        agent_config = agent_models.get(agent_name, defaults)
        
        provider_name = agent_config.get("provider", defaults.get("provider", "grid_ai"))
        model_id = agent_config.get("model", defaults.get("model", "claude-sonnet-4-5"))
        
        provider_config = self.config.get("llm", {}).get("providers", {}).get(provider_name, {})
        api_key_env = provider_config.get("api_key_env", f"{provider_name.upper()}_API_KEY")
        
        # Get model capabilities from config
        model_capabilities = self._get_model_capabilities(provider_name, model_id)
        
        return ModelConfig(
            model_id=model_id,
            provider=provider_name,
            temperature=agent_config.get("temperature", defaults.get("temperature", 0.3)),
            max_tokens=agent_config.get("max_tokens", defaults.get("max_tokens", 2000)),
            timeout_seconds=agent_config.get("timeout_seconds", defaults.get("timeout_seconds", 60)),
            base_url=provider_config.get("base_url"),
            api_key=get_env_var(api_key_env),
            supports_json=model_capabilities.get("supports_json", True),
            supports_vision=model_capabilities.get("supports_vision", False),
            supports_search=model_capabilities.get("supports_search", False)
        )
    
    def _get_model_capabilities(self, provider: str, model_id: str) -> Dict[str, bool]:
        """Get model capabilities from configuration."""
        providers_config = self.config.get("llm", {}).get("providers", {})
        provider_models = providers_config.get(provider, {}).get("models", [])
        
        for model in provider_models:
            if model.get("id") == model_id:
                return {
                    "supports_json": model.get("supports_json", True),
                    "supports_vision": model.get("supports_vision", False),
                    "supports_search": model.get("supports_search", False)
                }
        
        return {"supports_json": True, "supports_vision": False, "supports_search": False}
    
    def complete_for_agent(
        self,
        agent_name: str,
        prompt: str,
        system_message: Optional[str] = None,
        response_format: Optional[Dict] = None
    ) -> LLMResponse:
        """Execute completion using agent's configured model.
        
        Args:
            agent_name: Name of the agent requesting completion
            prompt: User prompt
            system_message: Optional system message
            response_format: Optional response format (e.g., {"type": "json_object"})
            
        Returns:
            LLMResponse with result
        """
        config = self.get_model_config(agent_name)
        provider = self._providers.get(config.provider)
        
        if not provider:
            return LLMResponse(
                content="",
                model=config.model_id,
                usage={},
                success=False,
                error=f"Provider '{config.provider}' not available. Check API key configuration."
            )
        
        if not provider.is_available():
            return LLMResponse(
                content="",
                model=config.model_id,
                usage={},
                success=False,
                error=f"Provider '{config.provider}' not configured. Check API key."
            )
        
        return provider.complete(
            prompt=prompt,
            config=config,
            system_message=system_message,
            response_format=response_format
        )
    
    def get_agent_model_info(self, agent_name: str) -> Dict[str, Any]:
        """Get model info for an agent (for UI display).
        
        Returns:
            Dict with model name, provider, capabilities
        """
        config = self.get_model_config(agent_name)
        
        return {
            "agent": agent_name,
            "model": config.model_id,
            "provider": config.provider,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "supports_json": config.supports_json,
            "supports_vision": config.supports_vision,
            "supports_search": config.supports_search
        }
    
    def list_available_models(self) -> Dict[str, list]:
        """List all available models by provider.
        
        Returns:
            Dict mapping provider names to model lists
        """
        result = {}
        
        providers_config = self.config.get("llm", {}).get("providers", {})
        for provider_name in self._providers.keys():
            provider_config = providers_config.get(provider_name, {})
            models = provider_config.get("models", [])
            result[provider_name] = [
                {
                    "id": m["id"],
                    "name": m.get("name", m["id"]),
                    "tier": m.get("tier", "unknown"),
                    "cost_per_1k_input": m.get("cost_per_1k_input", 0),
                    "cost_per_1k_output": m.get("cost_per_1k_output", 0),
                    "supports_vision": m.get("supports_vision", False),
                    "supports_search": m.get("supports_search", False)
                }
                for m in models
            ]
        
        return result
    
    def _get_agent_strategy(self, agent_name: str) -> str:
        """Get the execution strategy for an agent from config.

        Returns one of: native_web_access, tool_calling, tool_based,
        hybrid, reasoning_only, writing_only, formatting_only, json_only.
        """
        agent_models = self.config.get("llm", {}).get("agent_models", {})
        agent_config = agent_models.get(agent_name, {})
        return agent_config.get("strategy", "reasoning_only")

    def _get_fallback_model_config(self, agent_name: str) -> Optional[ModelConfig]:
        """Get fallback model config for hybrid-strategy agents."""
        agent_models = self.config.get("llm", {}).get("agent_models", {})
        agent_config = agent_models.get(agent_name, {})
        fallback = agent_config.get("fallback")
        if not fallback:
            return None

        defaults = self.config.get("llm", {}).get("defaults", {})
        provider_name = fallback.get("provider", agent_config.get("provider", defaults.get("provider", "grid_ai")))
        model_id = fallback.get("model")
        if not model_id:
            return None

        provider_config = self.config.get("llm", {}).get("providers", {}).get(provider_name, {})
        api_key_env = provider_config.get("api_key_env", f"{provider_name.upper()}_API_KEY")
        model_capabilities = self._get_model_capabilities(provider_name, model_id)

        return ModelConfig(
            model_id=model_id,
            provider=provider_name,
            temperature=agent_config.get("temperature", defaults.get("temperature", 0.3)),
            max_tokens=agent_config.get("max_tokens", defaults.get("max_tokens", 2000)),
            timeout_seconds=agent_config.get("timeout_seconds", defaults.get("timeout_seconds", 60)),
            base_url=provider_config.get("base_url"),
            api_key=get_env_var(api_key_env),
            supports_json=model_capabilities.get("supports_json", True),
            supports_vision=model_capabilities.get("supports_vision", False),
            supports_search=model_capabilities.get("supports_search", False),
        )

    def complete_for_agent_with_tools(
        self,
        agent_name: str,
        prompt: str,
        system_message: Optional[str] = None,
        response_format: Optional[Dict] = None,
    ) -> LLMResponse:
        """Execute completion using the agent's configured strategy.

        Routes automatically based on ``models.yaml`` strategy:
        - **native_web_access** (Gemini): plain completion (model searches natively).
        - **tool_calling / tool_based** (GLM/Kimi): ``complete_with_tools``.
        - **hybrid**: tries native first, falls back to tool-calling model.
        - **reasoning_only / writing_only / etc.**: plain completion, no tools.
        """
        strategy = self._get_agent_strategy(agent_name)

        # --- strategies that never need tools ---
        if strategy in ("reasoning_only", "writing_only", "formatting_only", "json_only"):
            return self.complete_for_agent(agent_name, prompt, system_message, response_format)

        # Lazy-import to avoid circular deps
        from utils.tools import get_tool_registry, get_research_tools

        registry = get_tool_registry()
        tools = get_research_tools()

        primary_config = self.get_model_config(agent_name)
        provider = self._providers.get(primary_config.provider)

        # --- native_web_access (Gemini): just call complete, model searches on its own ---
        if strategy == "native_web_access":
            if provider and provider.is_available():
                return provider.complete(prompt, primary_config, system_message, response_format)
            return LLMResponse(content="", model=primary_config.model_id, usage={}, success=False,
                               error=f"Provider '{primary_config.provider}' not available")

        # --- tool_calling / tool_based: use tool loop ---
        if strategy in ("tool_calling", "tool_based"):
            if provider and provider.is_available():
                return provider.complete_with_tools(
                    prompt, primary_config, tools, registry, system_message
                )
            return LLMResponse(content="", model=primary_config.model_id, usage={}, success=False,
                               error=f"Provider '{primary_config.provider}' not available")

        # --- hybrid: try native (Gemini) first, fall back to tool-calling model ---
        if strategy == "hybrid":
            # 1. Try primary model (native web)
            if provider and provider.is_available():
                response = provider.complete(prompt, primary_config, system_message, response_format)
                if response.success and response.content:
                    return response
                logger.warning(f"Primary model ({primary_config.model_id}) failed for {agent_name}, trying fallback")

            # 2. Fallback to tool-calling model
            fallback_config = self._get_fallback_model_config(agent_name)
            if fallback_config:
                fb_provider = self._providers.get(fallback_config.provider)
                if fb_provider and fb_provider.is_available():
                    return fb_provider.complete_with_tools(
                        prompt, fallback_config, tools, registry, system_message
                    )

            return LLMResponse(content="", model=primary_config.model_id, usage={}, success=False,
                               error="Both primary and fallback models failed")

        # Catch-all: plain completion
        return self.complete_for_agent(agent_name, prompt, system_message, response_format)

    def get_model_cost(self, model_id: str) -> Dict[str, float]:
        """Get cost per 1K tokens for a model.
        
        Returns:
            Dict with input and output costs
        """
        providers_config = self.config.get("llm", {}).get("providers", {})
        
        for provider_config in providers_config.values():
            for model in provider_config.get("models", []):
                if model.get("id") == model_id:
                    return {
                        "input": model.get("cost_per_1k_input", 0),
                        "output": model.get("cost_per_1k_output", 0)
                    }
        
        return {"input": 0.01, "output": 0.03}  # Default fallback


# Global accessor functions

_llm_client: Optional[ConfigurableLLMClient] = None


def get_llm_client() -> ConfigurableLLMClient:
    """Get or create global LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = ConfigurableLLMClient()
    return _llm_client


def get_llm_client_for_agent(agent_name: str) -> Callable[..., LLMResponse]:
    """Get a pre-configured completion function for an agent.
    
    Usage:
        complete = get_llm_client_for_agent("intent_understanding")
        response = complete("What is the query intent?", system_message="...")
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Partial function pre-bound to agent
    """
    client = get_llm_client()
    
    def complete(
        prompt: str,
        system_message: Optional[str] = None,
        response_format: Optional[Dict] = None
    ) -> LLMResponse:
        return client.complete_for_agent(
            agent_name=agent_name,
            prompt=prompt,
            system_message=system_message,
            response_format=response_format
        )
    
    return complete


def get_llm_with_tools_for_agent(agent_name: str) -> Callable[..., LLMResponse]:
    """Get a strategy-aware completion function for an agent.

    Unlike ``get_llm_client_for_agent`` (plain completion only), this routes
    through ``complete_for_agent_with_tools`` which picks the right approach
    (native web, tool calling, hybrid, or plain) based on ``models.yaml``.

    Usage::

        research = get_llm_with_tools_for_agent("event_discovery")
        response = research("Find fintech conferences in 2025", system_message="...")
    """
    client = get_llm_client()

    def complete(
        prompt: str,
        system_message: Optional[str] = None,
        response_format: Optional[Dict] = None,
    ) -> LLMResponse:
        return client.complete_for_agent_with_tools(
            agent_name=agent_name,
            prompt=prompt,
            system_message=system_message,
            response_format=response_format,
        )

    return complete


def calculate_execution_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for an execution.
    
    Args:
        model_id: Model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Cost in USD
    """
    client = get_llm_client()
    costs = client.get_model_cost(model_id)
    
    input_cost = (input_tokens / 1000) * costs["input"]
    output_cost = (output_tokens / 1000) * costs["output"]
    
    return input_cost + output_cost
