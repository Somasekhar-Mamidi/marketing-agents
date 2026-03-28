"""Tests for Outreach Email Agent."""

import pytest
from agents.outreach_email import OutreachEmailAgent
from agents.base import AgentInput


class TestOutreachEmailAgent:
    """Test cases for OutreachEmailAgent."""
    
    def test_agent_initialization(self):
        """Test agent is properly initialized."""
        agent = OutreachEmailAgent()
        assert agent.name == "outreach_email"
        assert agent.description == "Generates sponsorship outreach emails"
    
    def test_execute_requires_events(self):
        """Test that execute requires events in context."""
        agent = OutreachEmailAgent()
        input_data = AgentInput(
            query="Generate outreach emails",
            context={"events": []},
            parameters={}
        )
        
        result = agent.execute(input_data)
        assert result.status == "success"
        assert result.findings["events"] == []
    
    def test_execute_generates_email_for_single_event(self):
        """Test email generation for a single event."""
        agent = OutreachEmailAgent()
        events = [{
            "event_name": "Test Payments Conference",
            "organizer": "Test Org",
            "contact_email": "contact@test.com",
            "overall_score": "7.5",
            "priority_tier": "Tier 2",
            "recommendation": "Research further"  # Required for email generation
        }]
        
        input_data = AgentInput(
            query="Generate emails",
            context={"events": events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert result.agent_name == "outreach_email"
        assert result.status == "success"
        assert len(result.findings["events"]) == 1
        
        email_event = result.findings["events"][0]
        assert "outreach_subject" in email_event
        assert "outreach_email" in email_event
    
    def test_execute_generates_emails_for_multiple_events(self, sample_events):
        """Test email generation for multiple events."""
        agent = OutreachEmailAgent()
        
        input_data = AgentInput(
            query="Generate emails",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert len(result.findings["events"]) == 3
        for event in result.findings["events"]:
            assert "outreach_subject" in event
            assert "outreach_email" in event
    
    def test_email_contains_event_name(self, sample_event):
        """Test that email contains the event name."""
        agent = OutreachEmailAgent()
        
        input_data = AgentInput(
            query="Generate email",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        email_event = result.findings["events"][0]
        
        assert sample_event["event_name"] in email_event["outreach_email"]
    
    def test_email_has_professional_structure(self, sample_event):
        """Test that email has professional structure."""
        agent = OutreachEmailAgent()
        
        input_data = AgentInput(
            query="Generate email",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        email_event = result.findings["events"][0]
        email_body = email_event["outreach_email"]
        
        assert "Dear" in email_body or "Hello" in email_body
        assert "Best regards" in email_body or "Sincerely" in email_body
        assert "[Your Name]" in email_body
    
    def test_email_subject_contains_event_name(self, sample_event):
        """Test that email subject contains event name."""
        agent = OutreachEmailAgent()
        
        input_data = AgentInput(
            query="Generate email",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        email_event = result.findings["events"][0]
        
        subject = email_event["outreach_subject"]
        event_name = sample_event["event_name"]
        assert event_name[:10] in subject or "Sponsorship" in subject
    
    def test_email_subject_not_empty(self, sample_event):
        """Test that email subject is not empty."""
        agent = OutreachEmailAgent()
        
        input_data = AgentInput(
            query="Generate email",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        email_event = result.findings["events"][0]
        
        assert email_event["outreach_subject"] != ""
        assert len(email_event["outreach_subject"]) > 5
    
    def test_email_body_not_empty(self, sample_event):
        """Test that email body is not empty."""
        agent = OutreachEmailAgent()
        
        input_data = AgentInput(
            query="Generate email",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        email_event = result.findings["events"][0]
        
        assert email_event["outreach_email"] != ""
        assert len(email_event["outreach_email"]) > 50
    
    def test_email_mentions_sponsorship(self, sample_event):
        """Test that email mentions sponsorship."""
        agent = OutreachEmailAgent()
        
        input_data = AgentInput(
            query="Generate email",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        email_event = result.findings["events"][0]
        email_body = email_event["outreach_email"].lower()
        
        assert "sponsor" in email_body
    
    def test_email_preserves_original_fields(self, sample_event):
        """Test that original event fields are preserved."""
        agent = OutreachEmailAgent()
        
        input_data = AgentInput(
            query="Generate email",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        email_event = result.findings["events"][0]
        
        assert email_event["event_name"] == sample_event["event_name"]
        assert email_event["overall_score"] == sample_event["overall_score"]
    
    def test_email_includes_call_to_action(self, sample_event):
        """Test that email includes a call to action."""
        agent = OutreachEmailAgent()
        
        input_data = AgentInput(
            query="Generate email",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        email_event = result.findings["events"][0]
        email_body = email_event["outreach_email"].lower()
        
        assert any(phrase in email_body for phrase in ["call", "meeting", "discuss", "schedule", "available"])
    
    def test_validate_input_requires_query(self):
        """Test that empty query raises error."""
        agent = OutreachEmailAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        
        with pytest.raises(ValueError):
            agent.validate_input(input_data)
    
    def test_metadata_contains_event_count(self, sample_events):
        """Test that metadata contains event count."""
        agent = OutreachEmailAgent()
        
        input_data = AgentInput(
            query="Generate emails",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert "event_count" in result.metadata
        assert result.metadata["event_count"] == 3
