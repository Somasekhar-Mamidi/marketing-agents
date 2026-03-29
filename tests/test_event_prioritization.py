"""Tests for Event Prioritization Agent."""

import pytest
from unittest.mock import patch
from agents.event_prioritization import EventPrioritizationAgent
from agents.base import AgentInput


class TestEventPrioritizationAgent:
    """Test cases for EventPrioritizationAgent."""
    
    def test_agent_initialization(self):
        """Test agent is properly initialized."""
        agent = EventPrioritizationAgent()
        assert agent.name == "event_prioritization"
        assert agent.description == "Prioritizes events and provides sponsorship recommendations"
    
    def test_execute_requires_events(self):
        """Test that execute requires events in context."""
        agent = EventPrioritizationAgent()
        input_data = AgentInput(
            query="Prioritize events",
            context={"events": []},
            parameters={}
        )
        
        result = agent.execute(input_data)
        assert result.status == "success"
        assert result.findings["events"] == []
    
    def test_execute_prioritizes_single_event(self):
        """Test prioritization of a single event."""
        agent = EventPrioritizationAgent()
        events = [{
            "event_name": "Test Conference",
            "overall_score": "8.5",
            "priority_tier": "Tier 1"
        }]
        
        input_data = AgentInput(
            query="Prioritize",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert result.agent_name == "event_prioritization"
        assert result.status == "success"
        assert len(result.findings["events"]) == 1
        
        prioritized = result.findings["events"][0]
        assert "recommendation" in prioritized
    
    def test_execute_prioritizes_multiple_events(self, sample_events):
        """Test prioritization of multiple events."""
        agent = EventPrioritizationAgent()
        
        input_data = AgentInput(
            query="Prioritize",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert len(result.findings["events"]) == 3
        for event in result.findings["events"]:
            assert "recommendation" in event
    
    @patch.object(EventPrioritizationAgent, '_generate_recommendation_with_llm', return_value=None)
    def test_high_score_gets_must_sponsor_recommendation(self, mock_llm):
        """Test that high-scoring events get 'reach out' recommendation."""
        agent = EventPrioritizationAgent()
        events = [{
            "event_name": "Major Conference",
            "overall_score": "9.5",
            "priority_tier": "Tier 1"
        }]

        input_data = AgentInput(
            query="Prioritize",
            context={"events": events},
            parameters={}
        )

        result = agent.execute(input_data)
        prioritized = result.findings["events"][0]

        assert "reach" in prioritized["recommendation"].lower() or "must" in prioritized["recommendation"].lower()

    @patch.object(EventPrioritizationAgent, '_generate_recommendation_with_llm', return_value=None)
    def test_low_score_gets_monitor_recommendation(self, mock_llm):
        """Test that low-scoring events get 'monitor' recommendation."""
        agent = EventPrioritizationAgent()
        events = [{
            "event_name": "Small Event",
            "overall_score": "4.0",
            "priority_tier": "Tier 4"
        }]

        input_data = AgentInput(
            query="Prioritize",
            context={"events": events},
            parameters={}
        )

        result = agent.execute(input_data)
        prioritized = result.findings["events"][0]

        assert "monitor" in prioritized["recommendation"].lower() or "optional" in prioritized["recommendation"].lower()
    
    def test_events_are_sorted_by_score(self, sample_events):
        """Test that events are sorted by overall score (descending)."""
        agent = EventPrioritizationAgent()
        
        input_data = AgentInput(
            query="Prioritize",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        events = result.findings["events"]
        scores = [float(e.get("overall_score", 0)) for e in events]
        
        assert scores == sorted(scores, reverse=True)
    
    def test_recommendations_are_valid(self, sample_events):
        """Test that all recommendations are valid."""
        agent = EventPrioritizationAgent()
        
        input_data = AgentInput(
            query="Prioritize",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        valid_recommendations = [
            "Reach out immediately",
            "Research further",
            "Monitor for now",
            "Consider if budget allows"
        ]
        
        for event in result.findings["events"]:
            rec = event["recommendation"].lower()
            assert any(vr.lower() in rec for vr in valid_recommendations)
    
    def test_execute_preserves_fields(self, sample_event):
        """Test that key event fields are preserved."""
        agent = EventPrioritizationAgent()
        
        input_data = AgentInput(
            query="Prioritize",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        prioritized = result.findings["events"][0]
        
        assert prioritized["event_name"] == sample_event["event_name"]
        assert "recommendation" in prioritized
    
    def test_validate_input_requires_query(self):
        """Test that empty query raises error."""
        agent = EventPrioritizationAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        
        with pytest.raises(ValueError):
            agent.validate_input(input_data)
    
    def test_metadata_contains_priority_count(self, sample_events):
        """Test that metadata contains priority count."""
        agent = EventPrioritizationAgent()
        
        input_data = AgentInput(
            query="Prioritize",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert "event_count" in result.metadata
        assert result.metadata["event_count"] == 3
    
    def test_tier1_events_come_first(self):
        """Test that Tier 1 events appear first after sorting."""
        agent = EventPrioritizationAgent()
        events = [
            {"event_name": "Tier 3 Event", "overall_score": "5.0", "priority_tier": "Tier 3"},
            {"event_name": "Tier 1 Event", "overall_score": "9.0", "priority_tier": "Tier 1"},
            {"event_name": "Tier 2 Event", "overall_score": "7.0", "priority_tier": "Tier 2"}
        ]
        
        input_data = AgentInput(
            query="Prioritize",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        prioritized = result.findings["events"]
        
        assert "Tier 1" in prioritized[0]["priority_tier"]
