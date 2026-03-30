"""Outreach Email Agent - Generates professional sponsorship outreach emails."""

import logging
from typing import Optional
from agents.base import BaseAgent, AgentInput, AgentOutput
from config.company_config import get_company_config

logger = logging.getLogger(__name__)


class OutreachEmailAgent(BaseAgent):
    """Generates professional B2B outreach emails for event sponsorship."""
    
    name = "outreach_email"
    description = "Generates sponsorship outreach emails"
    
    def __init__(self):
        super().__init__()
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
        
        vendors = input_data.context.get("vendors", [])
        self.emit_thinking("searching", f"Generating outreach emails for {len(events)} events and {len(vendors)} vendors")
        logger.info(f"Generating outreach emails for {len(events)} events")

        outreach_events = []
        for event in events:
            recommendation = event.get("recommendation", "")

            if "Reach out" in recommendation or "Research further" in recommendation:
                email_event = self._generate_outreach(event)
                outreach_events.append(email_event)

        self.emit_thinking("result", f"Generated {len(outreach_events)} outreach emails")
        logger.info(f"Generated {len(outreach_events)} outreach emails")
        
        return AgentOutput(
            agent_name=self.name,
            findings={"events": outreach_events},
            metadata={"agent": self.name, "event_count": len(outreach_events)}
        )
    
    def _generate_outreach(self, event: dict) -> dict:
        """Generate outreach email for a single event."""
        event_name = event.get("event_name", "Unknown")
        self.emit_thinking("scoring", f"Drafting sponsorship email for '{event_name}'")
        llm_email = self._generate_with_llm(event)
        if llm_email:
            subject = llm_email["subject"][:60]
            self.emit_thinking("result", f"Email drafted for '{event_name}': Subject: {subject}...")
            event["outreach_subject"] = llm_email["subject"]
            event["outreach_email"] = llm_email["body"]
        else:
            event["outreach_subject"] = self._generate_subject_fallback(event)
            event["outreach_email"] = self._generate_body_fallback(event)

        event["status"] = "Outreach Ready"
        return event
    
    def _generate_with_llm(self, event: dict) -> Optional[dict]:
        try:
            from utils.llm_helpers import llm_call_with_json_output, OUTREACH_EMAIL_SYSTEM
            
            contact_name = self.config.contact_name or "[Your Name]"
            company_name = self.config.name
            
            prompt = f"""
            Generate a personalized sponsorship outreach email for this event:
            
            Event: {event.get('event_name', 'Unknown')}
            Organizer: {event.get('organizer', 'Event Team')}
            Theme: {event.get('theme', 'Technology')}
            Priority: {event.get('priority_tier', 'Standard')}
            Strategic Value: {event.get('strategic_value', 'Industry event')[:200]}
            
            Sender: {contact_name} from {company_name}
            
            Return JSON with:
            - subject: Compelling subject line (under 60 characters)
            - body: Professional email body (100-150 words)
            
            The email should:
            1. Show genuine interest in the event
            2. Mention why we're a good fit
            3. Request sponsorship information
            4. Include a clear call-to-action
            """
            
            result = llm_call_with_json_output(
                llm_func=self.llm,
                prompt=prompt,
                system_message=OUTREACH_EMAIL_SYSTEM,
                max_retries=1
            )
            
            if not result:
                return None
            
            return {
                "subject": result.get("subject", f"Sponsorship Opportunity: {event.get('event_name', 'Event')}"),
                "body": result.get("body", "")
            }
            
        except Exception as e:
            logger.debug(f"LLM email generation failed: {e}")
            return None
    
    def _generate_subject_fallback(self, event: dict) -> str:
        tier = event.get("priority_tier", "")
        tier_indicator = "Partnership" if "Tier 1" in tier else "Sponsorship"
        return f"{self.config.name} - {tier_indicator}: {event.get('event_name', 'Event')}"
    
    def _generate_body_fallback(self, event: dict) -> str:
        contact_name = self.config.contact_name or "[Your Name]"
        event_name = event.get("event_name", "the event")
        organizer = event.get("organizer", "Team")
        theme = event.get("theme", "technology")
        
        return f"""Dear {organizer},

I'm {contact_name} from {self.config.name}, a {theme.title()} solutions provider.

We're interested in sponsoring {event_name} and would like to learn about sponsorship opportunities.

Could you share details on sponsorship tiers, benefits, and attendee demographics?

I'd welcome a quick call to discuss. Please let me know your availability.

Best regards,
{contact_name}
{self.config.name}"""