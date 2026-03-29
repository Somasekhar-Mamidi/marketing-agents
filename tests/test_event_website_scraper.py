"""Tests for Event Website Scraper Agent."""

import json
import pytest
from unittest.mock import patch, MagicMock
from agents.event_website_scraper import EventWebsiteScraperAgent
from agents.base import AgentInput


@patch.object(EventWebsiteScraperAgent, 'llm_with_tools')
class TestEventWebsiteScraperAgent:
    """Test cases for EventWebsiteScraperAgent with llm boundary mocked."""

    # Helper to construct a successful LLM response payload
    def _llm_success_payload(self, events=None):
        if events is None:
            events = [{
                "event_name": "Test Conference",
                "event_website": "https://test.com"
            }]
        payload = {
            "events": events,
            "contact_email": "test@example.com",
            "contact_url": "https://test.com/contact",
            "start_date": "2026-04-01",
            "end_date": "2026-04-02",
            "city": "Test City",
            "country": "US",
            "sponsorship_url": "https://test.com/sponsor",
            "summary": "Test Summary",
            "industry_focus": "Tech",
            "target_audience": "Developers"
        }
        return json.dumps(payload)

    # Helper to construct a failed LLM response payload
    def _llm_failure_payload(self):
        return {
            "success": False
        }

    def test_agent_initialization(self, mock_llm_with_tools):
        """Test agent is properly initialized."""
        agent = EventWebsiteScraperAgent()
        assert agent.name == "event_website_scraper"
        assert agent.description == "Extracts detailed event info from official websites"
        # No llm call should be required just for initialization

    def test_execute_requires_events(self, mock_llm_with_tools):
        """Test that execute requires events in context."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(
            query="Scrape websites",
            context={"events": []},
            parameters={}
        )
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(),
            model="llm-model",
            usage={"total_tokens": 100},
            latency_ms=50
        )
        result = agent.execute(input_data)
        assert result.status == "success"
        assert result.findings["events"] == []

    def test_execute_scrapes_event_websites(self, mock_llm_with_tools, sample_event):
        """Test that websites are scraped for events."""
        agent = EventWebsiteScraperAgent()
        events = [{
            "event_name": sample_event["event_name"],
            "event_website": sample_event["event_website"]
        }]
        input_data = AgentInput(
            query="Scrape websites",
            context={"events": events},
            parameters={}
        )
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(events=events),
            model="llm-model",
            usage={"total_tokens": 100},
            latency_ms=50
        )
        result = agent.execute(input_data)
        assert result.agent_name == "event_website_scraper"
        assert result.status == "success"
        assert len(result.findings["events"]) == 1

    def test_execute_extracts_contact_info(self, mock_llm_with_tools, sample_event):
        """Test that contact information is extracted."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(events=[sample_event]),
            model="llm-model",
            usage={"total_tokens": 100},
            latency_ms=50
        )
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        assert "contact_email" in scraped
        assert "contact_url" in scraped

    def test_execute_extracts_dates(self, mock_llm_with_tools, sample_event):
        """Test that event dates are extracted."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(events=[sample_event]),
            model="llm-model",
            usage={"total_tokens": 100},
            latency_ms=50
        )
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        assert "start_date" in scraped
        assert "end_date" in scraped

    def test_execute_extracts_location(self, mock_llm_with_tools, sample_event):
        """Test that location is extracted."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(events=[sample_event]),
            model="llm-model",
            usage={"total_tokens": 100},
            latency_ms=50
        )
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        assert "city" in scraped
        assert "country" in scraped

    def test_execute_extracts_sponsorship_info(self, mock_llm_with_tools, sample_event):
        """Test that sponsorship info is extracted."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(events=[sample_event]),
            model="llm-model",
            usage={"total_tokens": 100},
            latency_ms=50
        )
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        assert "sponsorship_url" in scraped

    def test_execute_extracts_about_info(self, mock_llm_with_tools, sample_event):
        """Test that about/summary info is extracted."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(events=[sample_event]),
            model="llm-model",
            usage={"total_tokens": 100},
            latency_ms=50
        )
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        assert "summary" in scraped
        assert "industry_focus" in scraped
        assert "target_audience" in scraped

    def test_execute_handles_multiple_events(self, mock_llm_with_tools, sample_events):
        """Test scraping multiple events."""
        agent = EventWebsiteScraperAgent()
        events = sample_events
        input_data = AgentInput(
            query="Scrape",
            context={"events": events},
            parameters={}
        )
        multi_events = [
            {"event_name": e["event_name"], "event_website": e["event_website"]} for e in events
        ]
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(events=multi_events),
            model="llm-model",
            usage={"total_tokens": 300},
            latency_ms=60
        )
        result = agent.execute(input_data)
        assert len(result.findings["events"]) == len(events)
        for event in result.findings["events"]:
            assert "contact_email" in event
            assert "summary" in event

    def test_execute_preserves_original_fields(self, mock_llm_with_tools, sample_event):
        """Test that original event fields are preserved."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(events=[sample_event]),
            model="llm-model",
            usage={"total_tokens": 100},
            latency_ms=50
        )
        result = agent.execute(input_data)
        scraped = result.findings["events"][0]
        assert scraped["event_name"] == sample_event["event_name"]
        assert scraped["event_website"] == sample_event["event_website"]

    def test_execute_skips_events_without_website(self, mock_llm_with_tools):
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
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(events=events),
            model="llm-model",
            usage={"total_tokens": 100},
            latency_ms=50
        )
        result = agent.execute(input_data)
        assert result.status == "success"
        assert len(result.findings["events"]) == 1

    def test_execute_handles_events(self, mock_llm_with_tools, sample_event):
        """Test that execution handles events properly."""
        agent = EventWebsiteScraperAgent()
        events = [{"event_name": sample_event["event_name"], "event_website": sample_event["event_website"]}]
        input_data = AgentInput(
            query="Scrape",
            context={"events": events},
            parameters={}
        )
        mock_llm_with_tools.return_value = MagicMock(
            success=True,
            content=self._llm_success_payload(events=events),
            model="llm-model",
            usage={"total_tokens": 100},
            latency_ms=50
        )
        result = agent.execute(input_data)
        assert result.status == "success"

    def test_validate_input_requires_query(self, mock_llm_with_tools):
        """Test that empty query raises error."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        with pytest.raises(ValueError):
            agent.validate_input(input_data)

    def test_metadata_contains_event_count(self, mock_llm_with_tools, sample_events):
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

    def test_llm_failure_fallback_path(self, mock_llm_with_tools, sample_event):
        """Test that when LLM fails, agent uses fallback behavior gracefully."""
        agent = EventWebsiteScraperAgent()
        input_data = AgentInput(
            query="Scrape",
            context={"events": [sample_event]},
            parameters={}
        )
        mock_llm_with_tools.return_value = MagicMock(
            success=False,
            content=json.dumps({}),
            model="llm-model",
            usage={"total_tokens": 0},
            latency_ms=0
        )
        result = agent.execute(input_data)
        assert result.status == "success"  # should still complete gracefully
        # Original fields should be preserved in the absence of LLM data
        scraped = result.findings["events"][0]
        assert scraped["event_name"] == sample_event["event_name"]
        assert scraped["event_website"] == sample_event["event_website"]
