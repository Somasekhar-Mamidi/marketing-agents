"""Tests for Event Intelligence Agent."""

import pytest
from agents.event_intelligence import EventIntelligenceAgent
from agents.base import AgentInput


class TestEventIntelligenceAgent:
    """Test cases for EventIntelligenceAgent."""
    
    def test_agent_initialization(self):
        """Test agent is properly initialized."""
        agent = EventIntelligenceAgent()
        assert agent.name == "event_intelligence"
        assert agent.description == "Strategic analysis of events for sponsorship"
    
    def test_execute_requires_events(self):
        """Test that execute requires events in context."""
        agent = EventIntelligenceAgent()
        input_data = AgentInput(
            query="Analyze events",
            context={"events": []},
            parameters={}
        )
        
        result = agent.execute(input_data)
        assert result.status == "success"
        assert result.findings["events"] == []
    
    def test_execute_analyzes_single_event(self):
        """Test analysis of a single event."""
        agent = EventIntelligenceAgent()
        events = [{
            "event_name": "Test Conference",
            "theme": "Payments"
        }]
        
        input_data = AgentInput(
            query="Analyze",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert result.agent_name == "event_intelligence"
        assert result.status == "success"
        assert len(result.findings["events"]) == 1
        
        analyzed = result.findings["events"][0]
        assert "attendee_roles" in analyzed
        assert "companies_attending" in analyzed
        assert "strategic_value" in analyzed
        assert "potential_roi" in analyzed
        assert "ideal_sponsorship_format" in analyzed
    
    def test_execute_analyzes_multiple_events(self, sample_events):
        """Test analysis of multiple events."""
        agent = EventIntelligenceAgent()
        
        input_data = AgentInput(
            query="Analyze",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert len(result.findings["events"]) == 3
        for event in result.findings["events"]:
            assert "attendee_roles" in event
            assert "strategic_value" in event
    
    def test_strategic_value_is_generated(self, sample_event):
        """Test that strategic value is generated."""
        agent = EventIntelligenceAgent()
        
        input_data = AgentInput(
            query="Analyze",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        analyzed = result.findings["events"][0]
        
        assert analyzed["strategic_value"] != ""
        assert len(analyzed["strategic_value"]) > 10
    
    def test_potential_roi_is_generated(self, sample_event):
        """Test that potential ROI is generated."""
        agent = EventIntelligenceAgent()
        
        input_data = AgentInput(
            query="Analyze",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        analyzed = result.findings["events"][0]
        
        assert analyzed["potential_roi"] != ""
    
    def test_attendee_roles_are_generated(self, sample_event):
        """Test that attendee roles are generated."""
        agent = EventIntelligenceAgent()
        
        input_data = AgentInput(
            query="Analyze",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        analyzed = result.findings["events"][0]
        
        assert analyzed["attendee_roles"] != ""
    
    def test_companies_attending_are_generated(self, sample_event):
        """Test that companies attending are mentioned."""
        agent = EventIntelligenceAgent()
        
        input_data = AgentInput(
            query="Analyze",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        analyzed = result.findings["events"][0]
        
        assert analyzed["companies_attending"] != ""
    
    def test_ideal_sponsorship_format_is_generated(self, sample_event):
        """Test that ideal sponsorship format is suggested."""
        agent = EventIntelligenceAgent()
        
        input_data = AgentInput(
            query="Analyze",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        analyzed = result.findings["events"][0]
        
        assert analyzed["ideal_sponsorship_format"] != ""
        sponsorship_keywords = ["sponsor", "booth", "gold", "silver", "bronze", "exhibit"]
        assert any(kw in analyzed["ideal_sponsorship_format"].lower() for kw in sponsorship_keywords)
    
    def test_execute_preserves_original_fields(self, sample_event):
        """Test that original event data is preserved."""
        agent = EventIntelligenceAgent()
        
        input_data = AgentInput(
            query="Analyze",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        analyzed = result.findings["events"][0]
        
        assert analyzed["event_name"] == sample_event["event_name"]
        assert analyzed["overall_score"] == sample_event["overall_score"]
    
    def test_execute_uses_theme_context(self):
        """Test that theme is considered in analysis."""
        agent = EventIntelligenceAgent()
        events = [{"event_name": "Test", "theme": "FinTech"}]
        
        input_data = AgentInput(
            query="Analyze",
            context={"events": events},
            parameters={"theme": "Payments"}
        )
        
        result = agent.execute(input_data)
        
        assert result.status == "success"
    
    def test_validate_input_requires_query(self):
        """Test that empty query raises error."""
        agent = EventIntelligenceAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        
        with pytest.raises(ValueError):
            agent.validate_input(input_data)
    
    def test_metadata_contains_event_count(self, sample_events):
        """Test that metadata contains analysis count."""
        agent = EventIntelligenceAgent()
        
        input_data = AgentInput(
            query="Analyze",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert "event_count" in result.metadata
        assert result.metadata["event_count"] == 3
