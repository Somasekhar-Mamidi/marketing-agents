"""Pytest configuration and fixtures for marketing agents tests."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import AgentInput
from schema import EVENT_SCHEMA


@pytest.fixture
def sample_event():
    """Sample event data for testing."""
    return {
        "event_name": "Test Payments Conference 2026",
        "event_website": "https://testconference.com",
        "city": "Dubai",
        "country": "UAE",
        "expected_date": "March 2026",
        "theme": "Payments",
        "organizer": "Test Organizer",
        "start_date": "March 15, 2026",
        "end_date": "March 17, 2026",
        "contact_email": "info@testconference.com",
        "contact_url": "https://testconference.com/contact",
        "sponsorship_url": "https://testconference.com/sponsor",
        "summary": "A test payments conference for testing purposes.",
        "industry_focus": "Payments",
        "target_audience": "Payment professionals",
        "technology_themes": "Digital Payments, Fintech",
        "audience_relevance_score": "8.5",
        "industry_reputation_score": "7.5",
        "attendance_score": "8.0",
        "sponsor_value_score": "7.0",
        "regional_importance_score": "6.5",
        "overall_score": "7.5",
        "priority_tier": "Tier 2 - Strong Opportunity",
        "attendee_roles": "CTOs, Product Managers",
        "companies_attending": "Banks, Fintechs",
        "strategic_value": "High brand exposure",
        "potential_roi": "Good ROI expected",
        "ideal_sponsorship_format": "Gold Sponsorship",
        "recommendation": "Research further",
        "outreach_subject": "Sponsorship Inquiry - Test Payments Conference 2026",
        "outreach_email": "Dear Team,\n\nWe are interested in sponsoring your event.",
        "date_verified": True,
        "status": "Discovered"
    }


@pytest.fixture
def sample_events(sample_event):
    """List of sample events for testing."""
    event2 = sample_event.copy()
    event2["event_name"] = "FinTech Summit Asia 2026"
    event2["overall_score"] = "8.5"
    event2["priority_tier"] = "Tier 1 - Must Sponsor"
    
    event3 = sample_event.copy()
    event3["event_name"] = "Digital Payments Expo Europe 2026"
    event3["overall_score"] = "6.0"
    event3["priority_tier"] = "Tier 3 - Optional"
    
    return [sample_event, event2, event3]


@pytest.fixture
def agent_input():
    """Sample AgentInput for testing."""
    return AgentInput(
        query="Payments events in Middle East",
        context={"events": []},
        parameters={"industry": "Payments", "region": "Middle East"}
    )


@pytest.fixture
def agent_input_with_events(agent_input, sample_events):
    """AgentInput with existing events."""
    agent_input.context["events"] = sample_events
    return agent_input


@pytest.fixture
def empty_schema():
    """Empty schema for testing."""
    return {"events": []}


@pytest.fixture
def event_schema_fields():
    """Get all fields from EVENT_SCHEMA."""
    if EVENT_SCHEMA.get("events"):
        return list(EVENT_SCHEMA["events"][0].keys())
    return []
