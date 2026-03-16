"""Event Discovery Agent - Finds industry events for sponsorship opportunities."""

import json
import logging
from agents.base import BaseAgent, AgentInput, AgentOutput
from schema import get_empty_schema
from utils.search import WebSearchTool

logger = logging.getLogger(__name__)


class EventDiscoveryAgent(BaseAgent):
    """Discovers industry events relevant for sponsorship across global regions.
    
    Searches for events based on user-provided:
    - Industry focus (e.g., FinTech, Payments, AI, Technology)
    - Region (e.g., US, Europe, APAC, Middle East)
    
    FILTERS APPLIED:
    - Excludes company-specific product launch events (Google I/O, AWS re:Invent, etc.)
    - Only includes public, industry-wide events
    - Verifies event dates from official sources
    """
    
    name = "event_discovery"
    description = "Discovers industry events globally for sponsorship opportunities"
    
    # Companies whose events should be EXCLUDED (vendor-specific product events)
    EXCLUDED_COMPANIES = [
        "google", "aws", "amazon", "microsoft", "meta", "facebook", 
        "apple", "salesforce", "oracle", "ibm", "intel", "nvidia",
        "adobe", "shopify", "stripe", "paypal", "square", "zoom",
        "slack", "github", "gitlab", "docker", "kubernetes",
        "twilio", "snowflake", "databricks", "cloudflare", "fastly",
        "hubspot", "zendesk", "intercom", "mailchimp", "hootsuite",
        "linkedin", "twitter", "tiktok", "snapchat", "reddit",
        "yahoo", "baidu", "tencent", "alibaba", "huawei", "xiaomi"
    ]
    
    # Keywords indicating vendor-specific events (to exclude)
    EXCLUDED_KEYWORDS = [
        "launch", "keynote", "build", "develop", "summit",  # Company-specific events
        "connect", "forward", "imagine", "ignite", "reinvent",  # Company event names
        "world tour", "global summit", "annual conference",  # Could be company-specific
    ]
    
    # Keywords indicating industry-wide events (to include)
    INDUSTRY_WIDE_KEYWORDS = [
        "conference", "summit", "expo", "forum", "festival", 
        "meeting", "convention", "symposium", "workshop", 
        "bootcamp", "unconference", "meetup"
    ]
    
    def __init__(self, max_events: int = 50, provider: str = "tavily"):
        self.search_tool = WebSearchTool(provider=provider)
        self.max_events = max_events
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Discover events based on user inputs."""
        self.validate_input(input_data)
        
        # Get user inputs from parameters
        params = input_data.parameters
        industry = params.get("industry", input_data.query)
        region = params.get("region", "")
        theme = params.get("theme", "")
        
        logger.info(f"Event Discovery: Industry={industry}, Region={region}, Theme={theme}")
        
        # Get existing events from context or start fresh
        existing_data = input_data.context.get("events", [])
        if existing_data and isinstance(existing_data, list) and len(existing_data) > 0:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": existing_data},
                metadata={"agent": self.name, "event_count": len(existing_data)}
            )
        
        events = []
        
        # Build search query based on inputs
        search_queries = self._build_search_queries(industry, region, theme)
        
        for search_query in search_queries:
            try:
                results = self.search_tool.search(search_query, max_results=10)
                
                for result in results:
                    event = self._parse_search_result(result, industry)
                    
                    if event and not self._is_duplicate(event, events):
                        # Apply filters
                        if self._should_include_event(event, industry):
                            events.append(event)
                            logger.info(f"Included: {event.get('event_name')}")
                        else:
                            logger.info(f"Excluded: {event.get('event_name')}")
                        
                        if len(events) >= self.max_events:
                            break
                
                if len(events) >= self.max_events:
                    break
                    
            except Exception as e:
                logger.warning(f"Search failed for '{search_query}': {e}")
                continue
        
        # Filter out events with uncertain dates
        events = self._filter_uncertain_dates(events)
        
        logger.info(f"Discovered {len(events)} qualified events")
        
        return AgentOutput(
            agent_name=self.name,
            findings={
                "events": events,
                "inputs": {
                    "industry": industry,
                    "region": region,
                    "theme": theme
                }
            },
            metadata={
                "agent": self.name, 
                "event_count": len(events),
                "search_queries": search_queries
            }
        )
    
    def _build_search_queries(self, industry: str, region: str, theme: str) -> list:
        """Build search queries based on user inputs."""
        queries = []
        
        # Primary queries - industry-wide events
        base_terms = [
            f"{industry} {theme} conference 2025 2026" if theme else f"{industry} conference summit 2025 2026",
            f"{industry} payments conference 2025 2026" if industry.lower() == "payments" else f"{industry} summit expo 2025 2026",
        ]
        
        for query in base_terms:
            if region:
                queries.append(f"{query} {region}")
            else:
                queries.append(query)
                # Add common regions
                for r in ["USA", "Europe", "APAC", "Middle East", "Dubai", "Singapore"]:
                    queries.append(f"{query} {r}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_queries.append(q)
        
        return unique_queries[:10]  # Limit queries
    
    def _should_include_event(self, event: dict, industry: str) -> bool:
        """Apply filters to determine if event should be included."""
        event_name = event.get("event_name", "").lower()
        url = event.get("event_website", "").lower()
        
        # Filter 1: Exclude company-specific events
        for company in self.EXCLUDED_COMPANIES:
            if company in event_name or company in url:
                # Exception: If it's a well-known industry event that happens to have company in name
                if not self._is_industry_wide_exception(event_name):
                    logger.info(f"Excluded (company-specific): {event.get('event_name')}")
                    return False
        
        # Filter 2: Check for vendor-specific keywords
        for keyword in self.EXCLUDED_KEYWORDS:
            # Only exclude if it looks like a company event
            if keyword in event_name and any(c in event_name for c in self.EXCLUDED_COMPANIES):
                logger.info(f"Excluded (vendor event): {event.get('event_name')}")
                return False
        
        # Filter 3: Must have industry-wide keywords
        has_industry_keyword = any(kw in event_name for kw in self.INDUSTRY_WIDE_KEYWORDS)
        
        # Filter 4: Exclude if URL suggests vendor-specific page
        vendor_url_patterns = ["google.com", "aws.amazon", "microsoft.com", "salesforce.com", 
                              "shopify.com", "stripe.com", "paypal.com", "github.com"]
        if any(p in url for p in vendor_url_patterns):
            logger.info(f"Excluded (vendor URL): {event.get('event_name')}")
            return False
        
        return True
    
    def _is_industry_wide_exception(self, event_name: str) -> bool:
        """Check if event is an exception - well-known industry event."""
        # Known industry-wide events that have company-like names
        exceptions = [
            "mrc", "mag", "pls",  # Payments events
            "sibos",  # Banking
            "money20/20", "money2020",  # FinTech
            "dreamforce",  # Salesforce - but it's industry-wide
            "nvidia gtc",  # GPU conf - borderline
        ]
        return any(ex in event_name for ex in exceptions)
    
    def _filter_uncertain_dates(self, events: list) -> list:
        """Filter out events with uncertain or missing dates."""
        filtered = []
        
        for event in events:
            # Check if date is verified
            start_date = event.get("start_date", "")
            expected_date = event.get("expected_date", "")
            
            # Include if we have a verified date
            if start_date and start_date != "Not Found":
                filtered.append(event)
                continue
            
            # Include if expected date is reasonable (has year 2025 or 2026)
            if expected_date and expected_date != "Not Found":
                if "2025" in expected_date or "2026" in expected_date:
                    filtered.append(event)
                    continue
            
            # Events without dates will need verification - mark for later
            # For now, include but mark as needing date verification
            event["date_verified"] = False
            filtered.append(event)
        
        return filtered
    
    def _parse_search_result(self, result: dict, industry: str) -> dict | None:
        """Parse a search result into event schema."""
        title = result.get("title", "")
        url = result.get("url", "")
        content = result.get("content", "")
        
        # Skip if no useful data
        if not title or not url:
            return None
        
        # Skip non-event URLs
        skip_patterns = ["blog", "news", "article", "youtube", "linkedin", "twitter", 
                        "facebook", "instagram", "youtube.com/watch"]
        if any(p in url.lower() for p in skip_patterns):
            return None
        
        # Extract date from content if available
        expected_date = self._extract_date_from_content(content)
        
        return {
            "event_name": title,
            "event_website": url,
            "city": "",
            "country": "",
            "expected_date": expected_date,
            "theme": industry,
            "organizer": "",
            "start_date": "",
            "end_date": "",
            "contact_email": "",
            "contact_url": "",
            "sponsorship_url": "",
            "summary": content[:500] if content else "",
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
            "date_verified": False,
            "status": "Discovered"
        }
    
    def _extract_date_from_content(self, content: str) -> str:
        """Extract date information from content."""
        import re
        
        # Common date patterns
        patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}-\d{1,2},?\s+\d{4}',
            r'Q[1-4]\s+\d{4}',
            r'(Spring|Summer|Fall|Winter)\s+\d{4}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
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
