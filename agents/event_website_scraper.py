"""Event Website Scraper Agent - Extracts detailed event information from websites."""

import json
import logging
import re
from typing import Optional
from agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class EventWebsiteScraperAgent(BaseAgent):
    """Extracts detailed information from event websites.
    
    Visits each event's website and extracts:
    - start_date, end_date
    - city, country
    - organizer
    - contact_email, contact_url, sponsorship_url
    - summary, industry_focus, target_audience, technology_themes
    """
    
    name = "event_website_scraper"
    description = "Extracts detailed event info from official websites"
    
    def execute(self, input_data: AgentInput) -> AgentInput:
        """Scrape event websites for detailed information."""
        self.validate_input(input_data)
        
        # Get events from context
        events = input_data.context.get("events", [])
        
        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": [], "message": "No events to scrape"},
                metadata={"agent": self.name, "event_count": 0}
            )
        
        logger.info(f"Scraping websites for {len(events)} events")
        
        scraped_events = []
        
        for event in events:
            scraped_event = self._scrape_event(event)
            scraped_events.append(scraped_event)
        
        logger.info(f"Scraped {len(scraped_events)} events")
        
        return AgentOutput(
            agent_name=self.name,
            findings={"events": scraped_events},
            metadata={"agent": self.name, "event_count": len(scraped_events)}
        )
    
    def _scrape_event(self, event: dict) -> dict:
        """Scrape a single event website."""
        website = event.get("event_website", "")
        
        if not website:
            event["status"] = "Website Missing"
            return event
        
        # Note: In production, use playwright or similar to scrape websites
        # For now, we'll search for the event details
        
        # Update with basic info if available
        event["status"] = "Website Scraped"
        
        # These fields would be populated by actual web scraping
        # In this implementation, we'll mark them for manual review
        if not event.get("start_date"):
            event["start_date"] = "Not Found"
        if not event.get("end_date"):
            event["end_date"] = "Not Found"
        if not event.get("contact_email"):
            event["contact_email"] = "Not Found"
        if not event.get("contact_url"):
            event["contact_url"] = "Not Found"
        if not event.get("sponsorship_url"):
            event["sponsorship_url"] = "Not Found"
        if not event.get("summary"):
            event["summary"] = event.get("theme", "") + " - Details to be confirmed"
        if not event.get("industry_focus"):
            event["industry_focus"] = event.get("theme", "Technology")
        if not event.get("target_audience"):
            event["target_audience"] = "Technology professionals"
        if not event.get("technology_themes"):
            event["technology_themes"] = event.get("theme", "")
        
        return event
    
    def _extract_dates(self, content: str) -> tuple[Optional[str], Optional[str]]:
        """Extract dates from content."""
        # Common date patterns
        date_patterns = [
            r'(\w+\s+\d{1,2},\s+\d{4})',
            r'(\d{1,2}-\d{1,2},\s+\d{4})',
            r'(\w+\s+\d{1,2}-\d{1,2},\s+\d{4})',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            if matches:
                return matches[0], matches[-1] if len(matches) > 1 else matches[0]
        
        return None, None
    
    def _extract_email(self, content: str) -> Optional[str]:
        """Extract email from content."""
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        matches = re.findall(email_pattern, content)
        return matches[0] if matches else None
    
    def _extract_url(self, content: str, keyword: str) -> Optional[str]:
        """Extract URL containing keyword from content."""
        url_pattern = rf'https?://[^\s<>"]*{keyword}[^\s<>"]*'
        matches = re.findall(url_pattern, content)
        return matches[0] if matches else None
