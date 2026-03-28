"""Tests for Event Discovery Agent."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.event_discovery import EventDiscoveryAgent
from agents.base import AgentInput


class TestEventDiscoveryAgent:
    """Test cases for EventDiscoveryAgent."""
    
    def test_agent_initialization(self):
        """Test agent is properly initialized."""
        agent = EventDiscoveryAgent(max_events=30, provider="tavily")
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
    
    @patch('agents.event_discovery.WebSearchTool')
    def test_execute_with_mocked_search(self, mock_search_tool):
        """Test execute with mocked search results."""
        mock_search = MagicMock()
        mock_search.search.return_value = [
            {
                "title": "Test Payments Conference 2026",
                "url": "https://testconference.com",
                "content": "A test payments conference in Dubai. March 2026."
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
    
    def test_should_include_event_excludes_google(self):
        """Test that Google-specific events are excluded."""
        agent = EventDiscoveryAgent()
        
        event = {"event_name": "Google Cloud Next", "event_website": "https://cloud.google.com"}
        assert agent._should_include_event(event, "Cloud") is False
    
    def test_should_include_event_excludes_aws(self):
        """Test that AWS-specific events are excluded."""
        agent = EventDiscoveryAgent()
        
        event = {"event_name": "AWS re:Invent 2026", "event_website": "https://aws.amazon.com"}
        assert agent._should_include_event(event, "Cloud") is False
    
    def test_should_include_event_includes_conference(self):
        """Test that industry conferences are included."""
        agent = EventDiscoveryAgent()
        
        event = {"event_name": "FinTech Summit Dubai", "event_website": "https://fintechsummit.ae"}
        assert agent._should_include_event(event, "FinTech") is True
    
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
    
    def test_extract_date_from_content(self):
        """Test date extraction from content."""
        agent = EventDiscoveryAgent()
        
        content = "Join us for the conference on March 15-17, 2026 in Dubai"
        date = agent._extract_date_from_content(content)
        
        assert date != ""
    
    def test_extract_date_from_content_no_date(self):
        """Test date extraction when no date found."""
        agent = EventDiscoveryAgent()
        
        content = "Join us for our upcoming conference"
        date = agent._extract_date_from_content(content)
        
        assert date == ""
    
    def test_parse_search_result_valid(self):
        """Test parsing valid search result."""
        agent = EventDiscoveryAgent()
        
        result = {
            "title": "Test Conference 2026",
            "url": "https://test.com",
            "content": "A test conference. March 2026."
        }
        
        event = agent._parse_search_result(result, "Technology")
        
        assert event["event_name"] == "Test Conference 2026"
        assert event["event_website"] == "https://test.com"
        assert event["theme"] == "Technology"
        assert event["status"] == "Discovered"
    
    def test_parse_search_result_skips_non_event_urls(self):
        """Test that blog/social URLs are skipped."""
        agent = EventDiscoveryAgent()
        
        result = {
            "title": "Blog Post",
            "url": "https://blog.example.com/post",
            "content": "Content"
        }
        
        event = agent._parse_search_result(result, "Technology")
        
        assert event is None
    
    def test_parse_search_result_skips_without_title(self):
        """Test that results without title are skipped."""
        agent = EventDiscoveryAgent()
        
        result = {"url": "https://test.com", "content": "Content"}
        
        event = agent._parse_search_result(result, "Technology")
        
        assert event is None
    
    def test_build_search_queries_with_region(self):
        """Test query building with region specified."""
        agent = EventDiscoveryAgent()
        
        queries = agent._build_search_queries("Payments", "Middle East", "")
        
        assert len(queries) > 0
        assert any("Middle East" in q for q in queries)
    
    def test_build_search_queries_without_region(self):
        """Test query building without region."""
        agent = EventDiscoveryAgent()
        
        queries = agent._build_search_queries("Payments", "", "")
        
        assert len(queries) > 0
        assert any(r in q for q in queries for r in ["USA", "Europe", "APAC"])
    
    def test_validate_input_requires_query(self):
        """Test that empty query raises error."""
        agent = EventDiscoveryAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        
        with pytest.raises(ValueError):
            agent.validate_input(input_data)
    
    def test_filter_uncertain_dates_filters_past_dates(self):
        """Test that past dates are marked."""
        agent = EventDiscoveryAgent()
        
        event = {"expected_date": "2024", "start_date": ""}
        result = agent._filter_uncertain_dates([event])
        
        assert len(result) == 1
        assert result[0]["date_verified"] is False
    
    def test_is_industry_wide_exception(self):
        """Test known industry-wide exceptions."""
        agent = EventDiscoveryAgent()
        
        assert agent._is_industry_wide_exception("money20/20") is True
        assert agent._is_industry_wide_exception("mrc") is True
        assert agent._is_industry_wide_exception("sibos") is True
        assert agent._is_industry_wide_exception("random-event") is False
