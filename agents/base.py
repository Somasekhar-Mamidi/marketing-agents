"""Base agent class for all marketing research agents."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field


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


class BaseAgent(ABC):
    """Base class for all research agents."""
    
    name: str = "base_agent"
    description: str = "Base agent - to be extended"
    
    @abstractmethod
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute the agent's research task.
        
        Args:
            input_data: Input containing query, context from previous agents, and parameters
            
        Returns:
            AgentOutput with research findings
        """
        pass
    
    def validate_input(self, input_data: AgentInput) -> bool:
        """Validate input before execution.
        
        Args:
            input_data: The input to validate
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        if not input_data.query:
            raise ValueError("Query cannot be empty")
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
