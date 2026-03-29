 

import json
from unittest.mock import patch

import pytest

from agents.event_intelligence import EventIntelligenceAgent
from agents.base import AgentInput
from utils.configurable_llm_client import LLMResponse


def _fake_llm_response(content_json: dict, model: str = "gemini-2.0", success: bool = True) -> LLMResponse:
    return LLMResponse(
        content=json.dumps(content_json),
        model=model,
        usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        success=success,
        latency_ms=42,
    )


def test_llm_with_tools_success_parses_json():
    """When the strategy-aware LLM returns JSON, the agent should parse and expose fields."""
    agent = EventIntelligenceAgent()
    events = [{
        "event_name": "Test Conf",
        "theme": "Payments",
        "city": "NYC",
        "country": "USA",
        "priority_tier": "Tier 1",
        "overall_score": "8.5",
        "summary": "Test summary"
    }]

    input_data = AgentInput(query="Analyze", context={"events": events}, parameters={})

    # Mock the strategy-aware LLM to return a valid JSON payload
    payload = {
        "attendee_roles": "CTOs and VPs",
        "companies_attending": "Major banks and fintechs",
        "strategic_value": "High value event",
        "potential_roi": "High ROI",
        "ideal_sponsorship_format": "Gold sponsorship",
    }

    with patch.object(EventIntelligenceAgent, 'llm_with_tools') as mock_llm_with_tools:
        mock_llm_with_tools.return_value = _fake_llm_response(payload, model="gemini-2.0")

        result = agent.execute(input_data)
        analyzed = result.findings["events"][0]

        assert analyzed.get("attendee_roles") == payload["attendee_roles"]
        assert analyzed.get("strategic_value") == payload["strategic_value"]
        assert result.status == "success"


def test_fallback_to_heuristics_when_llm_fails():
    """If the LLM path fails, heuristics should populate key fields."""
    agent = EventIntelligenceAgent()
    events = [{
        "event_name": "Test Conf",
        "theme": "Payments",
        "city": "London",
        "country": "UK",
        "priority_tier": "Tier 2",
        "overall_score": "6.8",
        "summary": "Test summary"
    }]

    input_data = AgentInput(query="Analyze", context={"events": events}, parameters={})

    # Simulate the LLM path failing and ensure heuristics fill in data
    with patch.object(EventIntelligenceAgent, 'llm_with_tools') as mock_llm_with_tools:
        mock_llm_with_tools.return_value = LLMResponse(
            content="", model="glm-latest", usage={}, success=False, latency_ms=0
        )

        result = agent.execute(input_data)
        analyzed = result.findings["events"][0]

        # Heuristic fallbacks should populate these keys
        assert analyzed.get("attendee_roles", "").strip() != ""
        assert analyzed.get("companies_attending", "").strip() != ""
        assert analyzed.get("strategic_value", "").strip() != ""
