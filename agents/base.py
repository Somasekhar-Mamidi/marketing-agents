"""Base agent class for all marketing research agents with LLM configuration support."""

from abc import ABC, abstractmethod
from typing import Any, Optional, Callable, Dict
from pydantic import BaseModel, Field

from utils.configurable_llm_client import LLMResponse, get_llm_client_for_agent


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
    model_used: str = Field(default="", description="Model ID used for this execution")


class BaseAgent(ABC):
    """Base class for all research agents with LLM configuration support."""

    name: str = "base_agent"
    description: str = "Base agent - to be extended"

    def __init__(self):
        """Initialize agent with LLM client."""
        self._llm_complete: Optional[Callable[..., LLMResponse]] = None
        self._llm_usage_stats: list = []
        self._progress_callback: Optional[Callable[[int, str], None]] = None

    def set_progress_callback(self, callback: Callable[[int, str], None]):
        """Set a callback for progress updates.

        Args:
            callback: Function that takes (progress_percent, message)
        """
        self._progress_callback = callback

    def report_progress(self, progress: int, message: str = ""):
        """Report progress via the callback if set.

        Args:
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        if self._progress_callback:
            self._progress_callback(min(100, max(0, progress)), message)
    
    @property
    def llm(self) -> Callable[..., LLMResponse]:
        """Get LLM completion function for this agent."""
        if self._llm_complete is None:
            self._llm_complete = get_llm_client_for_agent(self.name)
        return self._llm_complete
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model configuration for this agent."""
        from utils.configurable_llm_client import get_llm_client
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
    
    def get_usage_stats(self) -> Dict[str, Any]:
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
        model_info = self.get_model_info()
        return f"{self.__class__.__name__}(name={self.name!r}, model={model_info.get('model', 'unknown')!r})"
