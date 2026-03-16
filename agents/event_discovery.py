"""Event Discovery Agent - Finds industry events for sponsorship opportunities."""

import json
import logging
from agents.base import BaseAgent, AgentInput, AgentOutput
from schema import get_empty_schema
from utils.search import WebSearchTool

logger = logging.getLogger(__name__)


class EventDiscoveryAgent(BaseAgent):
    """Discovers industry events relevant for sponsorship across global regions.
    
    Searches for FinTech, Payments, AI, Technology, Software Development, and 
    Open Source events in US, North America, South America, APAC, India, 
    Singapore, Dubai, Riyadh, Middle East, and Brazil.
    """
    
    name = "event_discovery"
    description = "Discovers industry events globally for sponsorship opportunities"
    
    # Industry focus areas
    INDUSTRIES = [
        "FinTech",
        "Payments", 
        "Artificial Intelligence",
        "Technology",
        "Software Development",
        "Open Source"
    ]
    
    # Regions to search
    REGIONS = [
        "United States",
        "North America",
        "South America",
        "APAC",
        "India",
        "Singapore",
        "Dubai",
        "Riyadh",
        "Middle East",
        "Brazil"
    ]
    
    def __init__(self, max_events: int = 50, provider: str = "tavily"):
        self.search_tool = WebSearchTool(provider=provider)
        self.max_events = max_events
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Discover events based on the query and context."""
        self.validate_input(input_data)
        
        query = input_data.query
        logger.info(f"Event Discovery Agent running with query: {query}")
        
        # Get existing events from context or start fresh
        existing_data = input_data.context.get("events", [])
        if existing_data and isinstance(existing_data, list) and len(existing_data) > 0:
            # Already have events, pass through
            return AgentOutput(
                agent_name=self.name,
                findings={"events": existing_data},
                metadata={"agent": self.name, "event_count": len(existing_data)}
            )
        
        events = []
        
        # Build search queries for each industry
        for industry in self.INDUSTRIES:
            for region in self.REGIONS[:3]:  # Limit searches to avoid rate limits
                search_query = f"{industry} conference summit 2025 2026 {region} sponsorship"
                
                try:
                    results = self.search_tool.search(search_query, max_results=5)
                    
                    for result in results:
                        event = self._parse_search_result(result, industry)
                        if event and not self._is_duplicate(event, events):
                            events.append(event)
                            
                            if len(events) >= self.max_events:
                                break
                    
                    if len(events) >= self.max_events:
                        break
                        
                except Exception as e:
                    logger.warning(f"Search failed for {industry} {region}: {e}")
                    continue
            
            if len(events) >= self.max_events:
                break
        
        logger.info(f"Discovered {len(events)} events")
        
        return AgentOutput(
            agent_name=self.name,
            findings={"events": events},
            metadata={"agent": self.name, "event_count": len(events)}
        )
    
    def _parse_search_result(self, result: dict, industry: str) -> dict | None:
        """Parse a search result into event schema."""
        title = result.get("title", "")
        url = result.get("url", "")
        
        # Skip if no useful data
        if not title or not url:
            return None
        
        # Skip non-event URLs
        skip_patterns = ["blog", "news", "article", "youtube", "linkedin", "twitter"]
        if any(p in url.lower() for p in skip_patterns):
            return None
        
        return {
            "event_name": title,
            "event_website": url,
            "city": "",
            "country": "",
            "expected_date": "",
            "theme": industry,
            "organizer": "",
            "start_date": "",
            "end_date": "",
            "contact_email": "",
            "contact_url": "",
            "sponsorship_url": "",
            "summary": result.get("content", "")[:500],
            "industry_focus": industry,
            "target_audience": "",
            "attendee_roles": "",
            "companies_attending": "",
            "technology_themes": "",
            "strategic_value": "",
            "potential_roi": "",
            "ideal_sponsorship_format": "",
            "audience_relevance_score": "",
            "industry_reputation_score": "",
            "attendance_score": "",
            "sponsor_value_score": "",
            "regional_importance_score": "",
            "overall_score": "",
            "priority_tier": "",
            "recommendation": "",
            "outreach_subject": "",
            "outreach_email": "",
            "status": "Discovered"
        }
    
    def _is_duplicate(self, event: dict, events: list) -> bool:
        """Check if event is a duplicate."""
        event_name = event.get("event_name", "").lower()
        event_url = event.get("event_website", "").lower()
        
        for existing in events:
            existing_name = existing.get("event_name", "").lower()
            existing_url = existing.get("event_website", "").lower()
            
            if event_name == existing_name or event_url == existing_url:
                return True
        
        return False
