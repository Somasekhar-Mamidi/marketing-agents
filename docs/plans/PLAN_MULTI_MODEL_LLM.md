# Multi-Model LLM Configuration Plan

## Executive Summary
Enable per-agent model selection from your Juspay Grid AI endpoint (`https://grid.ai.juspay.net`) while maintaining backward compatibility with existing agents.

## Current State Analysis

### Existing Architecture
- **LLM Client**: `utils/llm_client.py` - OpenAI-only, single global instance
- **Base Agent**: `agents/base.py` - No LLM configuration built in
- **Config System**: `config/loader.py` + `pipeline.yaml` - YAML-based with per-agent params
- **Environment**: `.env` file stores `OPENAI_API_KEY`

### Key Files to Modify
1. `utils/llm_client.py` - Refactor to support multiple providers/models
2. `agents/base.py` - Add LLM configuration support
3. `config/models.yaml` - Add model assignment per agent (NEW FILE)
4. `.env` - Add Grid AI API key
5. `utils/__init__.py` - Export new classes

---

## Available Models at Grid AI

The following models are available at `https://grid.ai.juspay.net`:

### Claude Models (Anthropic)
| Model ID | Tier | Context | Best For |
|----------|------|---------|----------|
| `claude-opus-4-6` | Ultra | 200K | Complex reasoning, deep analysis |
| `claude-sonnet-4-6` | High | 200K | General purpose, balanced |
| `claude-opus-4-5` | High | 200K | High-quality outputs |
| `claude-sonnet-4-5` | Medium-High | 200K | Fast, good quality |
| `claude-sonnet-4-5-20250929` | Medium | 200K | Reliable, cost-effective |
| `claude-haiku-4-5-20251001` | Fast | 200K | Quick tasks, high volume |

### Gemini Models (Google)
| Model ID | Tier | Context | Best For |
|----------|------|---------|----------|
| `gemini-3-pro-preview` | High | 1M | Complex tasks, long context |
| `gemini-3.1-pro` | High | 1M | Latest Gemini capabilities |
| `gemini-3-flash-preview` | Fast | 1M | Quick responses, cost-effective |
| `gemini-embedding-001` | Embedding | - | Vector search, embeddings |

### Kimi Models (Moonshot)
| Model ID | Tier | Context | Best For |
|----------|------|---------|----------|
| `kimi-latest` | High | 200K | Long context, reasoning |

### GLM Models (Zhipu)
| Model ID | Tier | Context | Best For |
|----------|------|---------|----------|
| `glm-latest` | High | 128K | Latest GLM, reasoning |
| `glm-flash-experimental` | Fast | 128K | Speed optimized |

### OpenAI-Compatible
| Model ID | Tier | Context | Best For |
|----------|------|---------|----------|
| `open-large` | High | 128K | General purpose |
| `open-fast` | Fast | 128K | Quick completions |

---

## Detailed Implementation Plan

### Phase 1: Enhanced LLM Client (2-3 hours)

#### 1.1 Create Model Configuration Schema

```yaml
# config/models.yaml (NEW FILE)
llm:
  # Provider endpoint configuration
  providers:
    grid_ai:
      name: "Juspay Grid AI"
      base_url: "https://grid.ai.juspay.net"
      api_key_env: "GRID_AI_API_KEY"
      default_model: "claude-sonnet-4-5"
      
      # All available models with capabilities
      models:
        # Claude - Best for reasoning and analysis
        - id: "claude-opus-4-6"
          name: "Claude Opus 4.6"
          provider: "anthropic"
          context_window: 200000
          supports_vision: true
          supports_json: true
          tier: "ultra"
          cost_per_1k_input: 0.015
          cost_per_1k_output: 0.075
          best_for: ["complex_reasoning", "deep_analysis", "research"]
          
        - id: "claude-sonnet-4-6"
          name: "Claude Sonnet 4.6"
          provider: "anthropic"
          context_window: 200000
          supports_vision: true
          supports_json: true
          tier: "high"
          cost_per_1k_input: 0.003
          cost_per_1k_output: 0.015
          best_for: ["general_purpose", "balanced"]
          
        - id: "claude-sonnet-4-5"
          name: "Claude Sonnet 4.5"
          provider: "anthropic"
          context_window: 200000
          supports_vision: true
          supports_json: true
          tier: "medium-high"
          cost_per_1k_input: 0.003
          cost_per_1k_output: 0.015
          best_for: ["fast_quality", "reliable"]
          
        - id: "claude-haiku-4-5-20251001"
          name: "Claude Haiku 3.5"
          provider: "anthropic"
          context_window: 200000
          supports_vision: false
          supports_json: true
          tier: "fast"
          cost_per_1k_input: 0.00025
          cost_per_1k_output: 0.00125
          best_for: ["quick_tasks", "high_volume", "simple_extraction"]
        
        # Gemini - Great for long context
        - id: "gemini-3.1-pro"
          name: "Gemini 3.1 Pro"
          provider: "google"
          context_window: 1000000
          supports_vision: true
          supports_json: true
          tier: "high"
          cost_per_1k_input: 0.0035
          cost_per_1k_output: 0.0105
          best_for: ["long_context", "multimodal", "large_documents"]
          
        - id: "gemini-3-flash-preview"
          name: "Gemini 3 Flash"
          provider: "google"
          context_window: 1000000
          supports_vision: true
          supports_json: true
          tier: "fast"
          cost_per_1k_input: 0.00035
          cost_per_1k_output: 0.00105
          best_for: ["quick_responses", "cost_effective"]
          
        # Kimi - Excellent for long context
        - id: "kimi-latest"
          name: "Kimi K2.5"
          provider: "moonshot"
          context_window: 200000
          supports_vision: true
          supports_json: true
          tier: "high"
          cost_per_1k_input: 0.002
          cost_per_1k_output: 0.008
          best_for: ["long_context", "document_analysis", "coding"]
          
        # OpenAI-Compatible
        - id: "open-large"
          name: "Open Large"
          provider: "openai_compatible"
          context_window: 128000
          supports_vision: true
          supports_json: true
          tier: "high"
          cost_per_1k_input: 0.005
          cost_per_1k_output: 0.015
          best_for: ["general_purpose"]
          
        - id: "open-fast"
          name: "Open Fast"
          provider: "openai_compatible"
          context_window: 128000
          supports_vision: false
          supports_json: true
          tier: "fast"
          cost_per_1k_input: 0.0005
          cost_per_1k_output: 0.0015
          best_for: ["quick_tasks"]
          
        # GLM
        - id: "glm-latest"
          name: "GLM-5 Dev"
          provider: "zhipu"
          context_window: 128000
          supports_vision: true
          supports_json: true
          tier: "high"
          cost_per_1k_input: 0.003
          cost_per_1k_output: 0.009
          best_for: ["reasoning", "chinese_english"]
          
        - id: "glm-flash-experimental"
          name: "GLM 4.7 Flash"
          provider: "zhipu"
          context_window: 128000
          supports_vision: false
          supports_json: true
          tier: "fast"
          cost_per_1k_input: 0.0003
          cost_per_1k_output: 0.0009
          best_for: ["speed", "cost_effective"]
  
  # Agent-to-Model Mapping (Optimized Assignments)
  agent_models:
    # Schema agent - simple, needs JSON → Fast model
    schema_initialization:
      provider: grid_ai
      model: claude-haiku-4-5-20251001
      temperature: 0.1
      max_tokens: 2000
      
    # Intent understanding - CRITICAL, needs reasoning → Best model
    intent_understanding:
      provider: grid_ai
      model: claude-opus-4-6
      temperature: 0.3
      max_tokens: 4000
      
    # Event discovery - high volume, cost-sensitive → Fast + capable
    event_discovery:
      provider: grid_ai
      model: claude-sonnet-4-5
      temperature: 0.3
      max_tokens: 3000
      
    # Event qualification - quality matters → High tier
    event_qualification:
      provider: grid_ai
      model: claude-sonnet-4-6
      temperature: 0.3
      max_tokens: 4000
      
    # Website scraping - simple extraction → Cheapest
    event_website_scraper:
      provider: grid_ai
      model: glm-flash-experimental
      temperature: 0.1
      max_tokens: 2000
      
    # Intelligence - requires analysis → High tier
    event_intelligence:
      provider: grid_ai
      model: kimi-latest
      temperature: 0.4
      max_tokens: 4000
      
    # Prioritization - scoring logic → Fast + accurate
    event_prioritization:
      provider: grid_ai
      model: claude-haiku-4-5-20251001
      temperature: 0.2
      max_tokens: 2000
      
    # Email generation - creative + professional → Balanced
    outreach_email:
      provider: grid_ai
      model: claude-sonnet-4-5
      temperature: 0.7
      max_tokens: 4000
      
    # Vendor discovery - search + analysis → Cost-effective
    vendor_discovery:
      provider: grid_ai
      model: gemini-3-flash-preview
      temperature: 0.3
      max_tokens: 3000
      
    # Excel export - structured data → Fast
    excel_table_generator:
      provider: grid_ai
      model: open-fast
      temperature: 0.1
      max_tokens: 2000
  
  # Global defaults
  defaults:
    provider: grid_ai
    model: claude-sonnet-4-5
    temperature: 0.3
    max_tokens: 2000
    timeout_seconds: 60
```

#### 1.2 Refactored LLM Client Architecture

```python
# utils/llm_client.py

from enum import Enum
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import logging
import time

from config.loader import get_env_var
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    model_id: str
    provider: str
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout_seconds: int = 60
    
    # Provider-specific settings
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    
    # Capabilities
    supports_json: bool = True
    supports_vision: bool = False


@dataclass  
class LLMResponse:
    """Structured LLM response."""
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
    """OpenAI-compatible API provider (works with Grid AI)."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self._client = None
    
    def _get_client(self):
        """Lazy initialize OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        return self._client
    
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
                "max_tokens": config.max_tokens
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
                error=str(e)
            )
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key and self.api_key != "your_api_key_here")


class ConfigurableLLMClient:
    """Multi-provider LLM client with per-agent model selection."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with model configuration.
        
        Args:
            config_path: Path to models.yaml (default: config/models.yaml)
        """
        import yaml
        from pathlib import Path
        
        self.config_path = config_path or str(
            Path(__file__).parent.parent / "config" / "models.yaml"
        )
        self.config = self._load_config()
        self._providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()
    
    def _load_config(self) -> Dict:
        """Load model configuration from YAML."""
        import yaml
        from pathlib import Path
        
        config_file = Path(self.config_path)
        if not config_file.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return self._default_config()
        
        with open(config_file) as f:
            return yaml.safe_load(f) or {}
    
    def _default_config(self) -> Dict:
        """Return default configuration."""
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
    
    def get_model_config(self, agent_name: str) -> ModelConfig:
        """Get model configuration for specific agent."""
        agent_models = self.config.get("llm", {}).get("agent_models", {})
        defaults = self.config.get("llm", {}).get("defaults", {})
        
        # Get agent-specific config or use defaults
        agent_config = agent_models.get(agent_name, defaults)
        
        provider_name = agent_config.get("provider", defaults.get("provider", "grid_ai"))
        model_id = agent_config.get("model", defaults.get("model", "claude-sonnet-4-5"))
        
        # Get provider config for base_url and api_key
        provider_config = self.config.get("llm", {}).get("providers", {}).get(provider_name, {})
        api_key_env = provider_config.get("api_key_env", f"{provider_name.upper()}_API_KEY")
        
        return ModelConfig(
            model_id=model_id,
            provider=provider_name,
            temperature=agent_config.get("temperature", defaults.get("temperature", 0.3)),
            max_tokens=agent_config.get("max_tokens", defaults.get("max_tokens", 2000)),
            base_url=provider_config.get("base_url"),
            api_key=get_env_var(api_key_env)
        )
    
    def complete_for_agent(
        self,
        agent_name: str,
        prompt: str,
        system_message: Optional[str] = None,
        response_format: Optional[Dict] = None
    ) -> LLMResponse:
        """Execute completion using agent's configured model."""
        config = self.get_model_config(agent_name)
        provider = self._providers.get(config.provider)
        
        if not provider:
            return LLMResponse(
                content="",
                model=config.model_id,
                usage={},
                success=False,
                error=f"Provider '{config.provider}' not available"
            )
        
        return provider.complete(
            prompt=prompt,
            config=config,
            system_message=system_message,
            response_format=response_format
        )
    
    def get_agent_model_info(self, agent_name: str) -> Dict[str, Any]:
        """Get model info for an agent (for UI display)."""
        config = self.get_model_config(agent_name)
        
        return {
            "agent": agent_name,
            "model": config.model_id,
            "provider": config.provider,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens
        }
    
    def list_available_models(self) -> Dict[str, list]:
        """List all available models by provider."""
        result = {}
        
        providers_config = self.config.get("llm", {}).get("providers", {})
        for provider_name in self._providers.keys():
            provider_config = providers_config.get(provider_name, {})
            models = provider_config.get("models", [])
            result[provider_name] = models
        
        return result


# Global instance
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
```

### Phase 2: Update Base Agent (1 hour)

```python
# agents/base.py

from abc import ABC, abstractmethod
from typing import Any, Optional, Callable, Dict
from pydantic import BaseModel, Field

# Import LLM types
from utils.llm_client import LLMResponse, get_llm_client_for_agent


class AgentInput(BaseModel):
    """Input data passed to an agent."""
    query: str = Field(description="The research query for this agent")
    context: dict[str, Any] = Field(default_factory=dict, description="Context from previous agents")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Agent-specific parameters")


class AgentOutput(BaseModel):
    """Output data returned by an agent."""
    agent_name: str = Field(description="Name of the agent that produced this output")
    findings: dict[str, Any] = Field(description="Research findings")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    status: str = Field(default="success", description="Execution status")
    llm_usage: dict[str, Any] = Field(default_factory=dict, description="LLM usage statistics")


class BaseAgent(ABC):
    """Base class for all research agents with LLM configuration."""
    
    name: str = "base_agent"
    description: str = "Base agent - to be extended"
    
    def __init__(self):
        """Initialize agent with LLM client."""
        self._llm_complete: Optional[Callable[..., LLMResponse]] = None
        self._llm_usage_stats: list = []
    
    @property
    def llm(self) -> Callable[..., LLMResponse]:
        """Get LLM completion function for this agent.
        
        Returns:
            Pre-configured completion function for this agent's model
        """
        if self._llm_complete is None:
            self._llm_complete = get_llm_client_for_agent(self.name)
        return self._llm_complete
    
    def get_model_info(self) -> dict[str, Any]:
        """Get model configuration for this agent."""
        from utils.llm_client import get_llm_client
        client = get_llm_client()
        return client.get_agent_model_info(self.name)
    
    @abstractmethod
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute the agent's research task."""
        pass
    
    def validate_input(self, input_data: AgentInput) -> bool:
        """Validate input before execution."""
        if not input_data.query:
            raise ValueError("Query cannot be empty")
        return True
    
    def _track_llm_usage(self, response: LLMResponse):
        """Track LLM usage for this agent."""
        self._llm_usage_stats.append({
            "model": response.model,
            "success": response.success,
            "usage": response.usage,
            "latency_ms": response.latency_ms
        })
    
    def get_usage_stats(self) -> dict[str, Any]:
        """Get accumulated usage statistics."""
        total_calls = len(self._llm_usage_stats)
        successful_calls = sum(1 for s in self._llm_usage_stats if s.get("success"))
        total_tokens = sum(
            s.get("usage", {}).get("total_tokens", 0) 
            for s in self._llm_usage_stats
        )
        
        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": total_calls - successful_calls,
            "total_tokens": total_tokens,
            "model_info": self.get_model_info()
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, model={self.get_model_info()['model']!r})"
```

### Phase 3: Migration Example (1 agent) (1 hour)

```python
# agents/intent_understanding.py (example migration)

import json
import logging
from typing import Dict, Any

from agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class IntentUnderstandingAgent(BaseAgent):
    """Parses user queries to extract structured intent."""
    
    name = "intent_understanding"
    description = "Extracts intent from natural language queries"
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Parse query to extract intent."""
        self.validate_input(input_data)
        
        # Use pre-configured LLM for this agent (automatically uses claude-opus-4-6)
        response = self.llm(
            prompt=self._build_prompt(input_data.query),
            system_message=self._get_system_message(),
            response_format={"type": "json_object"}
        )
        
        # Track usage
        self._track_llm_usage(response)
        
        if not response.success:
            logger.error(f"Intent understanding failed: {response.error}")
            return AgentOutput(
                agent_name=self.name,
                findings={"error": response.error},
                status="error"
            )
        
        # Parse JSON response
        try:
            intent_data = json.loads(response.content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent JSON: {e}")
            return AgentOutput(
                agent_name=self.name,
                findings={"error": "Invalid JSON response"},
                status="error"
            )
        
        return AgentOutput(
            agent_name=self.name,
            findings={"intent": intent_data},
            metadata={
                "model_used": response.model,
                "tokens_used": response.usage.get("total_tokens", 0)
            },
            llm_usage={
                "calls": 1,
                "tokens": response.usage
            }
        )
    
    def _build_prompt(self, query: str) -> str:
        """Build prompt for intent extraction."""
        return f"""Extract structured intent from this query:

Query: "{query}"

Return JSON with:
- industry: detected industry (fintech, payments, ai, etc.)
- region: geographic region
- themes: list of themes/topics
- event_types: types of events interested in
- intent_confidence: 0-1 score
"""
    
    def _get_system_message(self) -> str:
        """Get system message for this agent."""
        return """You are an intent extraction specialist. 
Parse user queries about event discovery and extract structured information.
Always return valid JSON."""
```

### Phase 4: Environment Configuration (30 min)

```bash
# .env additions

# Grid AI Configuration (Primary)
GRID_AI_API_KEY=your_grid_ai_key_here
GRID_AI_BASE_URL=https://grid.ai.juspay.net

# Feature Flags
ENABLE_LLM_COST_TRACKING=true
```

### Phase 5: API Endpoints for UI (2 hours)

```python
# api/main.py additions

from typing import List, Dict, Any
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Model information for UI."""
    id: str
    name: str
    provider: str
    context_window: int
    supports_vision: bool
    cost_per_1k_input: float
    cost_per_1k_output: float


class AgentModelConfig(BaseModel):
    """Agent model configuration."""
    agent_name: str
    current_model: str
    provider: str
    temperature: float
    max_tokens: int
    available_models: List[str]


@app.get("/llm/models", response_model=List[ModelInfo])
async def list_available_models():
    """List all available LLM models."""
    from utils.llm_client import get_llm_client
    
    client = get_llm_client()
    all_models = []
    
    models_by_provider = client.list_available_models()
    for provider, models in models_by_provider.items():
        for model in models:
            all_models.append(ModelInfo(
                id=model["id"],
                name=model["name"],
                provider=provider,
                context_window=model.get("context_window", 128000),
                supports_vision=model.get("supports_vision", False),
                cost_per_1k_input=model.get("cost_per_1k_input", 0),
                cost_per_1k_output=model.get("cost_per_1k_output", 0)
            ))
    
    return all_models


@app.get("/llm/agents/{agent_name}/config", response_model=AgentModelConfig)
async def get_agent_model_config(agent_name: str):
    """Get current model configuration for an agent."""
    from utils.llm_client import get_llm_client
    
    client = get_llm_client()
    info = client.get_agent_model_info(agent_name)
    all_models = client.list_available_models()
    
    available = [m["id"] for m in all_models.get(info["provider"], [])]
    
    return AgentModelConfig(
        agent_name=agent_name,
        current_model=info["model"],
        provider=info["provider"],
        temperature=info["temperature"],
        max_tokens=info["max_tokens"],
        available_models=available
    )
```

---

## Information Still Needed From You

| Item | Status | Question |
|------|--------|----------|
| API Key | ❓ | What's the API key (or env var name)? |
| Auth Method | ❓ | Bearer token? Custom header? |
| API Format | ❓ | OpenAI-compatible endpoint? |

---

## Timeline

| Phase | Task | Duration | Priority |
|-------|------|----------|----------|
| 1 | Create `config/models.yaml` | 30 min | High |
| 1 | Refactor `utils/llm_client.py` | 2 hours | High |
| 2 | Update `agents/base.py` | 1 hour | High |
| 3 | Migrate 1-2 agents | 1 hour | Medium |
| 4 | Update `.env` | 15 min | High |
| 5 | Add API endpoints | 2 hours | Medium |
| - | Testing | 2 hours | High |

**Total: ~8-9 hours**

**Ready to start implementation once you provide the API key and confirm the endpoint is OpenAI-compatible.**
