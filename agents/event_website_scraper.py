"""Event Website Scraper Agent - Extracts detailed event information from websites."""

import json
import logging
import re
from typing import Dict, Any, Optional
from agents.base import BaseAgent, AgentInput, AgentOutput
from utils.web_scraper import EventWebsiteScraper

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
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.scraper = None
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
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
        
        with EventWebsiteScraper(timeout=self.timeout) as scraper:
            for event in events:
                scraped_event = self._scrape_event(event, scraper)
                scraped_events.append(scraped_event)
        
        successful = sum(1 for e in scraped_events if e.get("scraped_successfully", False))
        logger.info(f"Scraped {len(scraped_events)} events, {successful} successful")
        
        return AgentOutput(
            agent_name=self.name,
            findings={"events": scraped_events},
            metadata={
                "agent": self.name, 
                "event_count": len(scraped_events),
                "successful_scrapes": successful
            }
        )
    
    def _scrape_event(self, event: dict, scraper: EventWebsiteScraper) -> dict:
        """Scrape a single event website."""
        website = event.get("event_website", "")
        
        if not website:
            event["status"] = "Website Missing"
            event["scraped_successfully"] = False
            return event
        
        try:
            scraped_data = scraper.scrape_event_page(website)
            
            for key, value in scraped_data.items():
                if key != "error" and value is not None:
                    event[key] = value
            
            if scraped_data.get("scraped_successfully", False):
                event["status"] = "Website Scraped"
            else:
                event["status"] = "Scrape Failed"
                if scraped_data.get("error"):
                    event["scrape_error"] = scraped_data["error"]
            
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
            
        except Exception as e:
            logger.error(f"Failed to scrape {website}: {e}")
            event["status"] = "Scrape Error"
            event["scrape_error"] = str(e)
            event["scraped_successfully"] = False
        
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
