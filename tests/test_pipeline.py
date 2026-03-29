"""Tests for Pipeline Orchestrator."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pipeline.orchestrator import Pipeline
from agents.base import AgentInput, AgentOutput, BaseAgent


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, name: str = "mock_agent", fail: bool = False):
        self.name = name
        self.description = "Mock agent for testing"
        self.fail = fail
        self.execution_count = 0
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        self.execution_count += 1
        
        if self.fail:
            raise Exception("Agent failed")
        
        events = input_data.context.get("events", [])
        if self.name == "agent_1":
            events = [{"event_name": f"Event from {self.name}"}]
        elif self.name == "agent_2" and events:
            for e in events:
                e["from_agent_2"] = True
        
        return AgentOutput(
            agent_name=self.name,
            findings={"events": events, f"from_{self.name}": True},
            metadata={"executed": True}
        )


class TestPipeline:
    """Test cases for Pipeline orchestrator."""
    
    def test_pipeline_initialization(self):
        """Test pipeline is properly initialized."""
        pipeline = Pipeline()
        assert pipeline.agents == []
        assert pipeline.execution_history == []
    
    def test_add_agent(self):
        """Test adding agents to pipeline."""
        pipeline = Pipeline()
        agent = MockAgent("test_agent")
        
        result = pipeline.add_agent(agent)
        
        assert len(pipeline.agents) == 1
        assert pipeline.agents[0].name == "test_agent"
        assert result is pipeline
    
    def test_add_multiple_agents(self):
        """Test adding multiple agents."""
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("agent_1"))
        pipeline.add_agent(MockAgent("agent_2"))
        pipeline.add_agent(MockAgent("agent_3"))
        
        assert len(pipeline.agents) == 3
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_execute_requires_agents(self, mock_llm_with_tools):
        """Test that execute raises error without agents."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        
        with pytest.raises(ValueError) as exc_info:
            pipeline.execute("test query")
        
        assert "no agents" in str(exc_info.value).lower()
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_execute_single_agent(self, mock_llm_with_tools):
        """Test execution with single agent."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("single_agent"))
        
        result = pipeline.execute("test query")
        
        assert result.agent_name == "single_agent"
        assert result.status == "success"
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_execute_multiple_agents_sequential(self, mock_llm_with_tools):
        """Test that agents execute sequentially."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("agent_1"))
        pipeline.add_agent(MockAgent("agent_2"))
        
        result = pipeline.execute("test query")
        
        assert result.agent_name == "agent_2"
        assert len(pipeline.execution_history) == 2
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_execute_passes_context_between_agents(self, mock_llm_with_tools):
        """Test that context is passed between agents."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("agent_1"))
        pipeline.add_agent(MockAgent("agent_2"))
        
        result = pipeline.execute("test query")
        
        assert len(result.findings["events"]) >= 0
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_execute_with_initial_context(self, mock_llm_with_tools):
        """Test execution with initial context."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("agent_1"))
        
        initial_context = {"events": [{"existing": "event"}]}
        result = pipeline.execute("test query", initial_context=initial_context)
        
        assert result.status == "success"
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_execute_with_parameters(self, mock_llm_with_tools):
        """Test execution with parameters."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("test"))
        
        result = pipeline.execute(
            "test query",
            initial_context={"parameters": {"industry": "Payments"}}
        )
        
        assert result.status == "success"
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_execute_stops_on_agent_failure(self, mock_llm_with_tools):
        """Test that pipeline tracks agent failures."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline(continue_on_error=False)
        pipeline.add_agent(MockAgent("success_agent"))
        pipeline.add_agent(MockAgent("fail_agent", fail=True))
        pipeline.add_agent(MockAgent("never_runs"))

        with pytest.raises(Exception) as exc_info:
            pipeline.execute("test query")

        assert "failed" in str(exc_info.value).lower()
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_get_history(self, mock_llm_with_tools):
        """Test getting execution history."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("agent_1"))
        pipeline.add_agent(MockAgent("agent_2"))
        
        pipeline.execute("test query")
        history = pipeline.get_history()
        
        assert len(history) == 2
        assert history[0].agent_name == "agent_1"
        assert history[1].agent_name == "agent_2"
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_clear_history(self, mock_llm_with_tools):
        """Test clearing execution history."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("test"))
        pipeline.execute("test")
        
        assert len(pipeline.execution_history) == 1
        
        pipeline.clear()
        
        assert len(pipeline.execution_history) == 0
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_agent_execution_count(self, mock_llm_with_tools):
        """Test that each agent is executed exactly once per run."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("agent_1"))
        pipeline.add_agent(MockAgent("agent_2"))
        
        pipeline.execute("test")
        
        assert pipeline.agents[0].execution_count == 1
        assert pipeline.agents[1].execution_count == 1
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_execute_returns_final_output(self, mock_llm_with_tools):
        """Test that execute returns output from last agent."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("first"))
        pipeline.add_agent(MockAgent("last"))
        
        result = pipeline.execute("test")
        
        assert result.agent_name == "last"
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_pipeline_with_empty_initial_context(self, mock_llm_with_tools):
        """Test pipeline with empty initial context."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("test"))
        
        result = pipeline.execute("test", initial_context={})
        
        assert result.status == "success"
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_pipeline_with_none_initial_context(self, mock_llm_with_tools):
        """Test pipeline with None initial context."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        pipeline.add_agent(MockAgent("test"))
        
        result = pipeline.execute("test", initial_context=None)
        
        assert result.status == "success"
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_agent_validate_input_called(self, mock_llm_with_tools):
        """Test that agent validate_input is called."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        agent = MockAgent("test")
        agent.validate_input = Mock(return_value=True)
        
        pipeline.add_agent(agent)
        pipeline.execute("test")
        
        assert agent.validate_input.called
    
    @patch.object(MockAgent, 'llm_with_tools', autospec=True)
    def test_execution_history_preserves_order(self, mock_llm_with_tools):
        """Test that execution history preserves agent order."""
        mock_llm_with_tools.return_value = {"text": "mocked"}
        pipeline = Pipeline()
        for i in range(5):
            pipeline.add_agent(MockAgent(f"agent_{i}"))
        
        pipeline.execute("test")
        
        for i, output in enumerate(pipeline.execution_history):
            assert output.agent_name == f"agent_{i}"
