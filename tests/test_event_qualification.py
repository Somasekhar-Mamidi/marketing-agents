"""Tests for Event Qualification Agent."""

import pytest
from unittest.mock import patch, MagicMock
from agents.event_qualification import EventQualificationAgent
from agents.base import AgentInput


class TestEventQualificationAgent:
    """Test cases for EventQualificationAgent."""
    
    def test_agent_initialization(self):
        """Test agent is properly initialized."""
        agent = EventQualificationAgent()
        assert agent.name == "event_qualification"
        assert agent.description == "Scores events for sponsorship potential"
    
    def test_execute_requires_events_in_context(self):
        """Test that execute requires events in context."""
        agent = EventQualificationAgent()
        input_data = AgentInput(
            query="Qualify events",
            context={"events": []},
            parameters={}
        )
        
        result = agent.execute(input_data)
        assert result.status == "success"
        assert result.findings["events"] == []
    
    def test_execute_qualifies_single_event(self):
        """Test qualification of a single event."""
        agent = EventQualificationAgent()
        events = [{
            "event_name": "Test Conference",
            "event_website": "https://test.com",
            "theme": "Payments"
        }]
        
        input_data = AgentInput(
            query="Qualify events",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert result.agent_name == "event_qualification"
        assert result.status == "success"
        assert len(result.findings["events"]) == 1
        
        qualified_event = result.findings["events"][0]
        assert "audience_relevance_score" in qualified_event
        assert "industry_reputation_score" in qualified_event
        assert "attendance_score" in qualified_event
        assert "sponsor_value_score" in qualified_event
        assert "regional_importance_score" in qualified_event
        assert "overall_score" in qualified_event
        assert "priority_tier" in qualified_event
    
    def test_execute_qualifies_multiple_events(self, sample_events):
        """Test qualification of multiple events."""
        agent = EventQualificationAgent()
        
        input_data = AgentInput(
            query="Qualify events",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        qualified_events = result.findings["events"]
        
        assert len(qualified_events) == 3
        for event in qualified_events:
            assert "overall_score" in event
            assert "priority_tier" in event
    
    def test_scores_are_within_valid_range(self, sample_events):
        """Test that all scores are between 1 and 10."""
        agent = EventQualificationAgent()
        
        input_data = AgentInput(
            query="Qualify events",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        for event in result.findings["events"]:
            for score_field in [
                "audience_relevance_score",
                "industry_reputation_score",
                "attendance_score",
                "sponsor_value_score",
                "regional_importance_score"
            ]:
                score = float(event[score_field])
                assert 1 <= score <= 10
    
    def test_priority_tiers_are_valid(self, sample_events):
        """Test that priority tiers are valid values."""
        agent = EventQualificationAgent()
        
        input_data = AgentInput(
            query="Qualify events",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        valid_tiers = [
            "Tier 1 - Must Sponsor",
            "Tier 2 - Strong Opportunity",
            "Tier 3 - Optional",
            "Tier 4 - Low Priority"
        ]
        
        for event in result.findings["events"]:
            assert event["priority_tier"] in valid_tiers
    
    def test_higher_scores_get_higher_tiers(self):
        """Test that events with higher scores get better tiers."""
        agent = EventQualificationAgent()
        
        events = [
            {"event_name": "Major Conference", "theme": "FinTech"},
            {"event_name": "Small Meetup", "theme": "FinTech"}
        ]
        
        input_data = AgentInput(
            query="Qualify events",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        qualified = result.findings["events"]
        scores = [float(e["overall_score"]) for e in qualified]
        
        max_score_idx = scores.index(max(scores))
        min_score_idx = scores.index(min(scores))
        
        tier_order = {
            "Tier 1 - Must Sponsor": 1,
            "Tier 2 - Strong Opportunity": 2,
            "Tier 3 - Optional": 3,
            "Tier 4 - Low Priority": 4
        }
        
        assert tier_order[qualified[max_score_idx]["priority_tier"]] <= tier_order[qualified[min_score_idx]["priority_tier"]]
    
    def test_execute_preserves_original_event_data(self, sample_event):
        """Test that original event data is preserved."""
        agent = EventQualificationAgent()
        
        input_data = AgentInput(
            query="Qualify events",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        qualified = result.findings["events"][0]
        
        assert qualified["event_name"] == sample_event["event_name"]
        assert qualified["event_website"] == sample_event["event_website"]
        assert qualified["theme"] == sample_event["theme"]
    
    def test_execute_with_theme_in_parameters(self):
        """Test that theme from parameters is used."""
        agent = EventQualificationAgent()
        events = [{"event_name": "Test", "theme": ""}]
        
        input_data = AgentInput(
            query="Qualify",
            context={"events": events},
            parameters={"theme": "Payments"}
        )
        
        result = agent.execute(input_data)
        
        assert result.status == "success"
        assert len(result.findings["events"]) == 1
    
    @patch.object(EventQualificationAgent, 'llm_with_tools')
    def test_execute_with_llm_happy_path(self, mock_llm_method):
        """Test that LLM qualification is used when available."""
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = '{"audience_relevance_score": 8.5, "industry_reputation_score": 8.0, "attendance_score": 7.5, "sponsor_value_score": 8.0, "regional_importance_score": 7.0, "reasoning": "Top tier event"}'
        mock_response.model = "gemini-2.0-flash"
        mock_response.usage = {"total_tokens": 200}
        mock_llm_method.return_value = mock_response
        
        agent = EventQualificationAgent()
        events = [
            {"event_name": "Event 1", "event_website": "https://e1.com", "theme": "FinTech", "city": "London", "country": "UK"}
        ]
        
        input_data = AgentInput(
            query="Qualify",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        qualified = result.findings["events"][0]
        
        assert float(qualified["audience_relevance_score"]) == 8.5
        assert float(qualified["overall_score"]) > 7.0
    
    @patch.object(EventQualificationAgent, 'llm_with_tools')
    def test_execute_fallback_when_llm_fails(self, mock_llm_method):
        """Test rule-based fallback when LLM fails."""
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.error = "API Error"
        mock_llm_method.return_value = mock_response
        
        agent = EventQualificationAgent()
        events = [
            {"event_name": "Event 1", "event_website": "https://e1.com", "theme": "FinTech", "city": "London", "country": "UK"}
        ]
        
        input_data = AgentInput(
            query="Qualify",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        qualified = result.findings["events"][0]
        
        assert "audience_relevance_score" in qualified
        assert "overall_score" in qualified
        assert qualified["status"] == "Qualified"
    
    def test_validate_input_requires_query(self):
        """Test that empty query raises error."""
        agent = EventQualificationAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        
        with pytest.raises(ValueError):
            agent.validate_input(input_data)
    
    def test_metadata_contains_event_count(self, sample_events):
        """Test that metadata contains event count."""
        agent = EventQualificationAgent()
        
        input_data = AgentInput(
            query="Qualify",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert "event_count" in result.metadata
        assert result.metadata["event_count"] == 3
