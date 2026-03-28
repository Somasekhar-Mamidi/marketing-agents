"""Outreach Email Agent - Generates professional sponsorship outreach emails."""

import logging
from agents.base import BaseAgent, AgentInput, AgentOutput
from config.company_config import get_company_config

logger = logging.getLogger(__name__)


class OutreachEmailAgent(BaseAgent):
    """Generates professional B2B outreach emails for event sponsorship."""
    
    name = "outreach_email"
    description = "Generates sponsorship outreach emails"
    
    def __init__(self):
        self.config = get_company_config()
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Generate outreach emails for all events."""
        self.validate_input(input_data)
        
        events = input_data.context.get("events", [])
        
        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": [], "message": "No events for outreach"},
                metadata={"agent": self.name, "event_count": 0}
            )
        
        logger.info(f"Generating outreach emails for {len(events)} events")
        
        outreach_events = []
        for event in events:
            recommendation = event.get("recommendation", "")
            
            if "Reach out" in recommendation or "Research further" in recommendation:
                email_event = self._generate_outreach(event)
                outreach_events.append(email_event)
        
        logger.info(f"Generated {len(outreach_events)} outreach emails")
        
        return AgentOutput(
            agent_name=self.name,
            findings={"events": outreach_events},
            metadata={"agent": self.name, "event_count": len(outreach_events)}
        )
    
    def _generate_outreach(self, event: dict) -> dict:
        """Generate outreach email for a single event."""
        event_name = event.get("event_name", "the event")
        organizer = event.get("organizer", "the organizer")
        theme = event.get("theme", "technology")
        tier = event.get("priority_tier", "")
        
        subject = self._generate_subject(event_name, theme, tier)
        body = self._generate_email_body(event_name, theme, organizer, tier)
        
        event["outreach_subject"] = subject
        event["outreach_email"] = body
        event["status"] = "Outreach Ready"
        
        return event
    
    def _generate_subject(self, event_name: str, theme: str, tier: str) -> str:
        """Generate professional subject line."""
        tier_indicator = "Partnership Inquiry" if "Tier 1" in tier else "Sponsorship Opportunity"
        return f"{self.config.name} - {tier_indicator}: {event_name}"
    
    def _generate_email_body(self, event_name: str, theme: str, organizer: str, tier: str) -> str:
        """Generate concise email body (under 120 words)."""
        contact_name = self.config.contact_name or "[Your Name]"
        contact_title = self.config.contact_title or "[Your Title]"
        
        body = f"""Dear {organizer if organizer else 'Team'},

I hope this email finds you well. My name is {contact_name} from {self.config.name}, a leader in {theme.title()} solutions.

We are interested in sponsoring {event_name} and would love to learn more about available sponsorship opportunities.

Specifically, we'd like to understand:
- Sponsorship tiers and benefits
- Available branding opportunities
- Expected attendee demographics

Would you be available for a brief 15-minute call this week to discuss? We're excited about the possibility of partnering with you.

Best regards,
{contact_name}
{contact_title}
{self.config.name}"""
        
        word_count = len(body.split())
        if word_count > 120:
            body = f"""Dear {organizer if organizer else 'Team'},

I'm {contact_name} from {self.config.name}, a {theme.title()} solutions provider.

We're interested in sponsoring {event_name} and would like to learn about sponsorship opportunities.

Could you share details on sponsorship tiers, benefits, and attendee demographics?

I'd welcome a quick call to discuss. Please let me know your availability.

Best regards,
{contact_name}
{self.config.name}"""
        
        return body