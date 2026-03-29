"""Tests for Event Discovery Agent."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.event_discovery import EventDiscoveryAgent
from agents.base import AgentInput


class TestEventDiscoveryAgent:
    """Test cases for EventDiscoveryAgent."""
    
    def test_agent_initialization(self):
        """Test agent is properly initialized."""
        agent = EventDiscoveryAgent(max_events=30)
        assert agent.name == "event_discovery"
        assert agent.max_events == 30
    
    def test_excluded_companies_list(self):
        """Test that excluded companies list is defined."""
        agent = EventDiscoveryAgent()
        assert len(agent.EXCLUDED_COMPANIES) > 0
        assert "google" in agent.EXCLUDED_COMPANIES
        assert "aws" in agent.EXCLUDED_COMPANIES
        assert "stripe" in agent.EXCLUDED_COMPANIES
    
    def test_industry_wide_keywords(self):
        """Test that industry-wide keywords are defined."""
        agent = EventDiscoveryAgent()
        assert len(agent.INDUSTRY_WIDE_KEYWORDS) > 0
        assert "conference" in agent.INDUSTRY_WIDE_KEYWORDS
        assert "summit" in agent.INDUSTRY_WIDE_KEYWORDS
        assert "expo" in agent.INDUSTRY_WIDE_KEYWORDS
    
    @patch.object(EventDiscoveryAgent, 'llm_with_tools')
    def test_execute_with_mocked_llm(self, mock_llm_method):
        """Test execute with mocked LLM - happy path where LLM returns good data."""
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = '{"events": [{"event_name": "Test Payments Conference 2026", "event_website": "https://testconference.com", "city": "Dubai", "country": "UAE", "expected_date": "March 15-17, 2026", "theme": "Payments", "organizer": "Test Org", "summary": "A test payments conference in Dubai"}]}'
        mock_response.model = "gemini-2.0-flash"
        mock_response.usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        mock_response.latency_ms = 1234
        mock_response.error = None
        mock_llm_method.return_value = mock_response
        
        agent = EventDiscoveryAgent(max_events=10)
        input_data = AgentInput(
            query="Payments events",
            context={},
            parameters={"industry": "Payments", "region": "Dubai"}
        )
        
        result = agent.execute(input_data)
        
        assert result.agent_name == "event_discovery"
        assert result.status == "success"
        assert "events" in result.findings
        assert len(result.findings["events"]) > 0
    
    @patch('utils.search.WebSearchTool')
    @patch.object(EventDiscoveryAgent, 'llm_with_tools')
    def test_execute_fallback_to_duckduckgo(self, mock_llm_method, mock_search_tool):
        """Test fallback path when LLM fails - DuckDuckGo kicks in."""
        mock_llm_response = MagicMock()
        mock_llm_response.success = False
        mock_llm_response.error = "Rate limit exceeded"
        mock_llm_method.return_value = mock_llm_response
        
        mock_search = MagicMock()
        mock_search.search.return_value = [
            {
                "title": "Fallback Conference 2026",
                "url": "https://fallback.com",
                "content": "A fallback conference. March 2026."
            }
        ]
        mock_search_tool.return_value = mock_search
        
        agent = EventDiscoveryAgent(max_events=10)
        input_data = AgentInput(
            query="Payments events",
            context={},
            parameters={"industry": "Payments", "region": "Dubai"}
        )
        
        result = agent.execute(input_data)
        
        assert result.agent_name == "event_discovery"
        assert result.status == "success"
        assert "events" in result.findings
    
    def test_execute_with_existing_events_skips(self):
        """Test that existing events are returned without searching."""
        existing_events = [{"event_name": "Existing Event"}]
        input_data = AgentInput(
            query="test",
            context={"events": existing_events},
            parameters={}
        )
        
        agent = EventDiscoveryAgent()
        result = agent.execute(input_data)
        
        assert result.findings["events"] == existing_events
    
    def test_is_duplicate_detects_same_name(self):
        """Test duplicate detection by name."""
        agent = EventDiscoveryAgent()
        
        event = {"event_name": "Test Conference", "event_website": "https://different.com"}
        existing = [{"event_name": "Test Conference", "event_website": "https://original.com"}]
        
        assert agent._is_duplicate(event, existing) is True
    
    def test_is_duplicate_detects_same_url(self):
        """Test duplicate detection by URL."""
        agent = EventDiscoveryAgent()
        
        event = {"event_name": "Different Name", "event_website": "https://same.com"}
        existing = [{"event_name": "Original Name", "event_website": "https://same.com"}]
        
        assert agent._is_duplicate(event, existing) is True
    
    def test_is_duplicate_returns_false_for_new(self):
        """Test that new events are not duplicates."""
        agent = EventDiscoveryAgent()
        
        event = {"event_name": "New Conference", "event_website": "https://new.com"}
        existing = [
            {"event_name": "Conference A", "event_website": "https://a.com"},
            {"event_name": "Conference B", "event_website": "https://b.com"}
        ]
        
        assert agent._is_duplicate(event, existing) is False
    
    def test_validate_input_requires_query(self):
        """Test that empty query raises error."""
        agent = EventDiscoveryAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        
        with pytest.raises(ValueError):
            agent.validate_input(input_data)
    
    @patch.object(EventDiscoveryAgent, 'llm_with_tools')
    def test_execute_with_intent_data(self, mock_llm_method):
        """Test execute uses intent data when available."""
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = '{"events": [{"event_name": "AI Conference", "event_website": "https://ai-conf.com", "city": "London", "country": "UK"}]}'
        mock_llm_method.return_value = mock_response
        
        agent = EventDiscoveryAgent(max_events=10)
        input_data = AgentInput(
            query="Find events",
            context={
                "intent": {
                    "industry": "AI",
                    "regions": ["Europe"],
                    "themes": ["Machine Learning"]
                }
            },
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert result.agent_name == "event_discovery"
        assert result.status == "success"
        assert "events" in result.findings
    
    @patch.object(EventDiscoveryAgent, 'llm_with_tools')
    def test_execute_filters_excluded_companies(self, mock_llm_method):
        """Test that company-specific events are filtered out."""
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = '{"events": [{"event_name": "Google Cloud Next", "event_website": "https://cloud.google.com"}, {"event_name": "FinTech Summit", "event_website": "https://fintech.com"}]}'
        mock_llm_method.return_value = mock_response
        
        agent = EventDiscoveryAgent(max_events=10)
        input_data = AgentInput(
            query="Cloud events",
            context={},
            parameters={"industry": "Cloud"}
        )
        
        result = agent.execute(input_data)
        
        assert result.agent_name == "event_discovery"
        assert result.status == "success"
        events = result.findings["events"]
        assert all("google" not in e.get("event_name", "").lower() for e in events)
    
    @patch.object(EventDiscoveryAgent, 'llm_with_tools')
    def test_execute_deduplicates_events(self, mock_llm_method):
        """Test that duplicate events are removed."""
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = '{"events": [{"event_name": "Same Event", "event_website": "https://same.com"}, {"event_name": "Same Event", "event_website": "https://same.com"}]}'
        mock_llm_method.return_value = mock_response
        
        agent = EventDiscoveryAgent(max_events=10)
        input_data = AgentInput(
            query="Events",
            context={},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert len(result.findings["events"]) == 1
    
    @patch.object(EventDiscoveryAgent, 'llm_with_tools')
    def test_execute_respects_max_events(self, mock_llm_method):
        """Test that max_events parameter is respected."""
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = '{"events": [{"event_name": "Event 1"}, {"event_name": "Event 2"}, {"event_name": "Event 3"}, {"event_name": "Event 4"}]}'
        mock_llm_method.return_value = mock_response
        
        agent = EventDiscoveryAgent(max_events=2)
        input_data = AgentInput(
            query="Events",
            context={},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert len(result.findings["events"]) <= 2
