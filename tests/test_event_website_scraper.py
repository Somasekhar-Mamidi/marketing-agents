"""Tests for Event Website Scraper Agent."""

import pytest
from unittest.mock import patch, MagicMock
from agents.event_website_scraper import EventWebsiteScraperAgent
from agents.base import AgentInput


class TestEventWebsiteScraperAgent:
    """Test cases for EventWebsiteScraperAgent."""
    
    def test_agent_initialization(self):
        """Test agent is properly initialized."""
        agent = EventWebsiteScraperAgent()
        assert agent.name == "event_website_scraper"
        assert agent.description == "Extracts detailed event info from official websites"
    
    def test_execute_requires_events(self):
        """Test that execute requires events in context."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(
            query="Scrape websites",
            context={"events": []},
            parameters={}
        )
        
        result = agent.execute(input_data)
        assert result.status == "success"
        assert result.findings["events"] == []
    
    def test_execute_scrapes_event_websites(self):
        """Test that websites are scraped for events."""
        agent = EventWebsiteScraperAgent()
        events = [{
            "event_name": "Test Conference",
            "event_website": "https://test.com"
        }]
        
        input_data = AgentInput(
            query="Scrape websites",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert result.agent_name == "event_website_scraper"
        assert result.status == "success"
        assert len(result.findings["events"]) == 1
    
    def test_execute_extracts_contact_info(self, sample_event):
        """Test that contact information is extracted."""
        agent = EventWebsiteScraperAgent()
        
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        
        assert "contact_email" in scraped
        assert "contact_url" in scraped
    
    def test_execute_extracts_dates(self, sample_event):
        """Test that event dates are extracted."""
        agent = EventWebsiteScraperAgent()
        
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        
        assert "start_date" in scraped
        assert "end_date" in scraped
    
    def test_execute_extracts_location(self, sample_event):
        """Test that location is extracted."""
        agent = EventWebsiteScraperAgent()
        
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        
        assert "city" in scraped
        assert "country" in scraped
    
    def test_execute_extracts_sponsorship_info(self, sample_event):
        """Test that sponsorship info is extracted."""
        agent = EventWebsiteScraperAgent()
        
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        
        assert "sponsorship_url" in scraped
    
    def test_execute_extracts_about_info(self, sample_event):
        """Test that about/summary info is extracted."""
        agent = EventWebsiteScraperAgent()
        
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        
        assert "summary" in scraped
        assert "industry_focus" in scraped
        assert "target_audience" in scraped
    
    def test_execute_handles_multiple_events(self, sample_events):
        """Test scraping multiple events."""
        agent = EventWebsiteScraperAgent()
        
        input_data = AgentInput(
            query="Scrape",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert len(result.findings["events"]) == 3
        for event in result.findings["events"]:
            assert "contact_email" in event
            assert "summary" in event
    
    def test_execute_preserves_original_fields(self, sample_event):
        """Test that original event fields are preserved."""
        agent = EventWebsiteScraperAgent()
        
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        
        assert scraped["event_name"] == sample_event["event_name"]
        assert scraped["event_website"] == sample_event["event_website"]
    
    def test_execute_skips_events_without_website(self):
        """Test that events without websites are handled."""
        agent = EventWebsiteScraperAgent()
        events = [{
            "event_name": "Test Event",
            "event_website": ""
        }]
        
        input_data = AgentInput(
            query="Scrape",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert result.status == "success"
        assert len(result.findings["events"]) == 1
    
    def test_execute_handles_events(self):
        """Test that execution handles events properly."""
        agent = EventWebsiteScraperAgent()
        events = [{"event_name": "Test", "event_website": "https://test.com"}]
        
        input_data = AgentInput(
            query="Scrape",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert result.status == "success"
    
    def test_validate_input_requires_query(self):
        """Test that empty query raises error."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        
        with pytest.raises(ValueError):
            agent.validate_input(input_data)
    
    def test_metadata_contains_event_count(self, sample_events):
        """Test that metadata contains event count."""
        agent = EventWebsiteScraperAgent()
        
        input_data = AgentInput(
            query="Scrape",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert "event_count" in result.metadata
        assert result.metadata["event_count"] == 3
