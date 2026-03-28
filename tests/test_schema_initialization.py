"""Tests for Schema Initialization Agent."""

import pytest
from agents.schema_initialization import SchemaInitializationAgent
from agents.base import AgentInput


class TestSchemaInitializationAgent:
    """Test cases for SchemaInitializationAgent."""
    
    def test_agent_initialization(self):
        """Test agent is properly initialized."""
        agent = SchemaInitializationAgent()
        assert agent.name == "schema_initialization"
        assert agent.description == "Initializes the workflow with a standard JSON schema"
        assert agent.schema == {"events": []}
    
    def test_execute_returns_empty_events(self, agent_input):
        """Test execute returns empty events array."""
        agent = SchemaInitializationAgent()
        result = agent.execute(agent_input)
        
        assert result.agent_name == "schema_initialization"
        assert result.status == "success"
        assert "events" in result.findings
        assert result.findings["events"] == []
    
    def test_execute_preserves_parameters(self):
        """Test that parameters are preserved in metadata."""
        agent = SchemaInitializationAgent()
        input_data = AgentInput(
            query="test query",
            context={},
            parameters={
                "industry": "Payments",
                "region": "Middle East",
                "theme": "Fintech",
                "time_range": "24"
            }
        )
        
        result = agent.execute(input_data)
        metadata = result.findings.get("metadata", {})
        
        assert metadata["industry"] == "Payments"
        assert metadata["region"] == "Middle East"
        assert metadata["theme"] == "Fintech"
        assert metadata["time_range_months"] == "24"
    
    def test_execute_returns_schema_version(self, agent_input):
        """Test that schema version is included."""
        agent = SchemaInitializationAgent()
        result = agent.execute(agent_input)
        
        metadata = result.findings.get("metadata", {})
        assert metadata.get("schema_version") == "1.0"
        assert metadata.get("initialized") is True
    
    def test_validate_input_always_true(self):
        """Test that validation always passes."""
        agent = SchemaInitializationAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        
        assert agent.validate_input(input_data) is True
    
    def test_execute_with_minimal_parameters(self):
        """Test execute with no parameters."""
        agent = SchemaInitializationAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        
        result = agent.execute(input_data)
        
        assert result.status == "success"
        assert result.findings["events"] == []
        assert result.findings["metadata"]["industry"] == ""
        assert result.findings["metadata"]["region"] == ""
    
    def test_execute_with_partial_parameters(self):
        """Test execute with only industry set."""
        agent = SchemaInitializationAgent()
        input_data = AgentInput(
            query="",
            context={},
            parameters={"industry": "AI"}
        )
        
        result = agent.execute(input_data)
        
        assert result.findings["metadata"]["industry"] == "AI"
        assert result.findings["metadata"]["region"] == ""
    
    def test_result_metadata_fields(self, agent_input):
        """Test that result metadata contains expected fields."""
        agent = SchemaInitializationAgent()
        result = agent.execute(agent_input)
        
        metadata = result.metadata
        assert "agent" in metadata
        assert "schema_fields" in metadata
        assert metadata["initialized"] is True
    
    def test_repr_method(self):
        """Test string representation of agent."""
        agent = SchemaInitializationAgent()
        repr_str = repr(agent)
        
        assert "SchemaInitializationAgent" in repr_str
        assert "schema_initialization" in repr_str
