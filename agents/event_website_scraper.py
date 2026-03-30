"""Event Website Scraper Agent - Extracts detailed event information from websites."""

import logging
from typing import Optional
from agents.base import BaseAgent, AgentInput, AgentOutput
from utils.llm_helpers import extract_json_from_response

logger = logging.getLogger(__name__)


_SCRAPER_SYSTEM = """You are a data extraction specialist. You visit event websites and extract structured information.

When given an event URL, use the web_fetch tool to retrieve the page content, then extract:
- start_date, end_date (ISO format preferred)
- city, country
- organizer name
- contact_email, contact_url
- sponsorship_url (link to sponsorship/partnership page)
- summary (2-3 sentence event description)
- industry_focus
- target_audience
- technology_themes

Return ONLY valid JSON. Use null for fields not found."""


class EventWebsiteScraperAgent(BaseAgent):
    """Extracts detailed information from event websites using LLM + web_fetch.

    Uses the LLM's tool-calling capability to fetch and parse event pages.
    Falls back to direct BeautifulSoup scraping if LLM fails.
    """

    name = "event_website_scraper"
    description = "Extracts detailed event info from official websites"

    def __init__(self, timeout: float = 30.0):
        super().__init__()
        self.timeout = timeout

    def execute(self, input_data: AgentInput) -> AgentOutput:
        self.validate_input(input_data)

        events = input_data.context.get("events", [])
        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": [], "message": "No events to scrape"},
                metadata={"agent": self.name, "event_count": 0}
            )

        self.emit_thinking("searching", f"Scraping websites for {len(events)} events")
        logger.info(f"Scraping websites for {len(events)} events")
        scraped_events = []

        for event in events:
            scraped_events.append(self._scrape_event(event))

        successful = sum(1 for e in scraped_events if e.get("scraped_successfully", False))
        self.emit_thinking("result", f"Scraped {successful}/{len(scraped_events)} event websites successfully")

        successful = sum(1 for e in scraped_events if e.get("scraped_successfully", False))
        logger.info(f"Scraped {len(scraped_events)} events, {successful} successful")

        return AgentOutput(
            agent_name=self.name,
            findings={"events": scraped_events},
            metadata={"agent": self.name, "event_count": len(scraped_events), "successful_scrapes": successful}
        )

    def _scrape_event(self, event: dict) -> dict:
        """Scrape a single event website — LLM first, then direct fallback."""
        website = event.get("event_website", "")
        if not website:
            event["status"] = "Website Missing"
            event["scraped_successfully"] = False
            return event

        # Try LLM-driven extraction
        llm_data = self._scrape_with_llm(website, event)
        if llm_data:
            for key, value in llm_data.items():
                if value is not None:
                    event[key] = value
            event["scraped_successfully"] = True
            event["status"] = "Website Scraped"
        else:
            # Fallback to direct scraping
            direct_data = self._scrape_direct(website)
            if direct_data:
                for key, value in direct_data.items():
                    if key != "error" and value is not None:
                        event[key] = value
                event["scraped_successfully"] = direct_data.get("scraped_successfully", False)
                event["status"] = "Website Scraped" if event["scraped_successfully"] else "Scrape Failed"
            else:
                event["scraped_successfully"] = False
                event["status"] = "Scrape Failed"

        # Fill defaults for missing fields
        for field, default in [
            ("start_date", "Not Found"), ("end_date", "Not Found"),
            ("contact_email", "Not Found"), ("contact_url", "Not Found"),
            ("sponsorship_url", "Not Found"),
            ("summary", event.get("theme", "") + " - Details to be confirmed"),
            ("industry_focus", event.get("theme", "Technology")),
            ("target_audience", "Technology professionals"),
            ("technology_themes", event.get("theme", "")),
        ]:
            if not event.get(field):
                event[field] = default

        return event

    def _scrape_with_llm(self, url: str, event: dict) -> Optional[dict]:
        """Use LLM with web_fetch tool to extract event data."""
        try:
            prompt = (
                f"Fetch and extract structured information from this event website:\n"
                f"URL: {url}\n"
                f"Event Name: {event.get('event_name', 'Unknown')}\n\n"
                f"Use the web_fetch tool to retrieve the page, then extract:\n"
                f"- start_date, end_date (ISO format)\n"
                f"- city, country\n"
                f"- organizer\n"
                f"- contact_email, contact_url, sponsorship_url\n"
                f"- summary (2-3 sentences)\n"
                f"- industry_focus, target_audience, technology_themes\n\n"
                f"Return JSON with these fields. Use null for fields not found."
            )

            response = self.llm_with_tools(
                prompt=prompt,
                system_message=_SCRAPER_SYSTEM,
            )

            if not response.success or not response.content:
                return None

            self._track_llm_usage(response)
            data = extract_json_from_response(response.content)
            return data

        except Exception as e:
            logger.debug(f"LLM scraping failed for {url}: {e}")
            return None

    def _scrape_direct(self, url: str) -> Optional[dict]:
        """Fallback: direct BeautifulSoup scraping."""
        try:
            from utils.web_scraper import EventWebsiteScraper
            with EventWebsiteScraper(timeout=self.timeout) as scraper:
                return scraper.scrape_event_page(url)
        except Exception as e:
            logger.warning(f"Direct scraping failed for {url}: {e}")
            return None
