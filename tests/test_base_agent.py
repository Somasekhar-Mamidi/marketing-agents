"""Tests for Base Agent classes."""

import pytest
from agents.base import AgentInput, AgentOutput, BaseAgent


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    def __init__(self):
        self.name = "concrete_agent"
        self.description = "Concrete agent for testing"
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            findings={"result": "executed"},
            metadata={"test": True}
        )


class TestAgentInput:
    """Test cases for AgentInput."""
    
    def test_agent_input_requires_query(self):
        """Test that AgentInput requires query."""
        input_data = AgentInput(query="test query")
        assert input_data.query == "test query"
    
    def test_agent_input_has_context(self):
        """Test that AgentInput has context with default."""
        input_data = AgentInput(query="test")
        assert input_data.context == {}
    
    def test_agent_input_has_parameters(self):
        """Test that AgentInput has parameters with default."""
        input_data = AgentInput(query="test")
        assert input_data.parameters == {}
    
    def test_agent_input_with_context(self):
        """Test AgentInput with custom context."""
        input_data = AgentInput(
            query="test",
            context={"key": "value"}
        )
        assert input_data.context["key"] == "value"
    
    def test_agent_input_with_parameters(self):
        """Test AgentInput with custom parameters."""
        input_data = AgentInput(
            query="test",
            parameters={"industry": "Payments"}
        )
        assert input_data.parameters["industry"] == "Payments"


class TestAgentOutput:
    """Test cases for AgentOutput."""
    
    def test_agent_output_requires_name(self):
        """Test that AgentOutput requires agent_name."""
        output = AgentOutput(
            agent_name="test_agent",
            findings={}
        )
        assert output.agent_name == "test_agent"
    
    def test_agent_output_has_findings(self):
        """Test that AgentOutput has findings."""
        output = AgentOutput(
            agent_name="test",
            findings={"key": "value"}
        )
        assert output.findings["key"] == "value"
    
    def test_agent_output_has_default_status(self):
        """Test that AgentOutput has default status."""
        output = AgentOutput(
            agent_name="test",
            findings={}
        )
        assert output.status == "success"
    
    def test_agent_output_has_metadata(self):
        """Test that AgentOutput has metadata with default."""
        output = AgentOutput(
            agent_name="test",
            findings={}
        )
        assert output.metadata == {}
    
    def test_agent_output_with_metadata(self):
        """Test AgentOutput with custom metadata."""
        output = AgentOutput(
            agent_name="test",
            findings={},
            metadata={"count": 5}
        )
        assert output.metadata["count"] == 5
    
    def test_agent_output_with_error_status(self):
        """Test AgentOutput with error status."""
        output = AgentOutput(
            agent_name="test",
            findings={},
            status="error"
        )
        assert output.status == "error"


class TestBaseAgent:
    """Test cases for BaseAgent."""
    
    def test_concrete_agent_has_name(self):
        """Test that concrete agent has name."""
        agent = ConcreteAgent()
        assert agent.name == "concrete_agent"
    
    def test_concrete_agent_has_description(self):
        """Test that concrete agent has description."""
        agent = ConcreteAgent()
        assert agent.description == "Concrete agent for testing"
    
    def test_concrete_agent_execute(self):
        """Test that concrete agent can execute."""
        agent = ConcreteAgent()
        input_data = AgentInput(query="test")
        
        output = agent.execute(input_data)
        
        assert output.agent_name == "concrete_agent"
        assert output.status == "success"
    
    def test_validate_input_requires_query(self):
        """Test that validate_input raises for empty query."""
        agent = ConcreteAgent()
        input_data = AgentInput(query="")
        
        with pytest.raises(ValueError):
            agent.validate_input(input_data)
    
    def test_validate_input_accepts_valid_query(self):
        """Test that validate_input accepts non-empty query."""
        agent = ConcreteAgent()
        input_data = AgentInput(query="valid query")
        
        result = agent.validate_input(input_data)
        
        assert result is True
    
    def test_repr(self):
        """Test string representation of agent."""
        agent = ConcreteAgent()
        repr_str = repr(agent)
        
        assert "ConcreteAgent" in repr_str
        assert "concrete_agent" in repr_str
    
    def test_abstract_class_cannot_be_instantiated(self):
        """Test that BaseAgent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAgent()


class TestAgentValidation:
    """Test cases for agent input validation."""
    
    def test_validate_empty_query_raises(self):
        """Test that empty query raises ValueError."""
        agent = ConcreteAgent()
        
        with pytest.raises(ValueError) as exc_info:
            agent.validate_input(AgentInput(query=""))
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_validate_valid_query_succeeds(self):
        """Test that valid query passes validation."""
        agent = ConcreteAgent()
        
        result = agent.validate_input(AgentInput(query="valid"))
        
        assert result is True
