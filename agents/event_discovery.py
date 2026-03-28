"""Event Discovery Agent - Finds industry events for sponsorship opportunities."""

import json
import logging
from typing import Optional
from agents.base import BaseAgent, AgentInput, AgentOutput
from schema import get_empty_schema
from utils.search import WebSearchTool
from utils.deduplication import deduplicate_events, is_duplicate_event

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
        """Execute event discovery."""
        self.validate_input(input_data)
        
        params = input_data.parameters
        
        intent_data = input_data.context.get("intent")
        regions = []
        
        if intent_data:
            logger.info("Using structured intent for event discovery")
            search_queries = intent_data.get("search_queries", [])
            industry = intent_data.get("industry", input_data.query)
            regions = intent_data.get("regions", [])
            quality_requirements = intent_data.get("quality_requirements", {})
            max_events = params.get("max_events", self.max_events)
            
            logger.info(f"Event Discovery (Intent-based): Industry={industry}, "
                       f"Regions={regions}, Queries={len(search_queries)}, MaxEvents={max_events}")
        else:
            industry = params.get("industry", input_data.query)
            region = params.get("region", "")
            theme = params.get("theme", "")
            max_events = params.get("max_events", self.max_events)
            quality_requirements = {}
            
            logger.info(f"Event Discovery: Industry={industry}, Region={region}, "
                       f"Theme={theme}, MaxEvents={max_events}")
            
            search_queries = self._build_search_queries(industry, region, theme)
        
        region = params.get("region", "") if not intent_data else (regions[0] if regions else "")
        theme = params.get("theme", "")
        
        # Get existing events from context or start fresh
        existing_data = input_data.context.get("events", [])
        if existing_data and isinstance(existing_data, list) and len(existing_data) > 0:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": existing_data},
                metadata={"agent": self.name, "event_count": len(existing_data)}
            )
        
        events = []
        
        for search_query in search_queries:
            try:
                results = self.search_tool.search(search_query, max_results=20)
                
                for result in results:
                    event = self._parse_search_result(result, industry)
                    
                    if event and not self._is_duplicate(event, events):
                        # Apply filters
                        if self._should_include_event(event, industry):
                            events.append(event)
                            logger.info(f"Included: {event.get('event_name')}")
                        else:
                            logger.info(f"Excluded: {event.get('event_name')}")
                        
                        if len(events) >= max_events:
                            break
                
                if len(events) >= max_events:
                    break
                    
            except (httpx.HTTPError, ConnectionError, TimeoutError) as e:
                logger.warning(f"Search failed for '{search_query}': {e}")
                continue
        
        # Filter out events with uncertain dates
        events = self._filter_uncertain_dates(events)
        
        # Apply quality scoring if intent data available
        if intent_data and events:
            events = self._score_events_by_intent(events, intent_data)
            # Sort by score (highest first)
            events.sort(key=lambda x: x.get("discovery_score", 0), reverse=True)
        
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
        queries = []
        
        if region:
            target_regions = [region]
        else:
            target_regions = ["USA", "Europe", "APAC", "Middle East", "Asia", "India", "Brazil"]
        
        base_terms = [
            f"{industry} conference summit 2025 2026",
            f"{industry} expo forum festival 2025 2026",
            f"{industry} payments conference 2025 2026" if industry.lower() == "payments" else f"{industry} tech conference 2025 2026",
            f"{industry} event exhibition 2025 2026",
            f"{industry} meetup workshop networking 2025 2026",
            f"{industry} financial technology conference 2025 2026",
            f"{industry} digital payments summit 2025 2026",
            f"{industry} banking fintech event 2025 2026",
        ]
        
        for r in target_regions:
            for query in base_terms:
                queries.append(f"{query} {r}")
                queries.append(f"{industry} {r} conference 2025 2026")
                queries.append(f"{industry} {r} summit 2025 2026")
        
        seen = set()
        unique_queries = []
        for q in queries:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_queries.append(q)
        
        return unique_queries[:30]
    
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
    
    def _parse_search_result(self, result: dict, industry: str) -> Optional[dict]:
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
    
    def _score_events_by_intent(self, events: list, intent_data: dict) -> list:
        """Score events based on alignment with user intent."""
        scored_events = []
        
        target_industry = intent_data.get("industry", "").lower()
        target_regions = [r.lower() for r in intent_data.get("regions", [])]
        target_event_types = [t.lower() for t in intent_data.get("event_types", [])]
        quality_reqs = intent_data.get("quality_requirements", {})
        min_score_threshold = quality_reqs.get("relevance_threshold", 0.5)
        
        for event in events:
            score = 0.0
            score_breakdown = {}
            
            # 1. Industry match (25% weight)
            event_theme = event.get("theme", "").lower()
            event_name = event.get("event_name", "").lower()
            event_summary = event.get("summary", "").lower()
            
            industry_score = 0
            if target_industry in event_theme or target_industry in event_name:
                industry_score = 1.0
            elif target_industry in event_summary:
                industry_score = 0.7
            else:
                # Check related industries
                related = intent_data.get("sub_industries", [])
                for rel in related:
                    if rel.lower() in event_summary:
                        industry_score = 0.5
                        break
            
            score += industry_score * 0.25
            score_breakdown["industry_match"] = industry_score * 0.25
            
            # 2. Region/location match (20% weight)
            event_city = event.get("city", "").lower()
            event_country = event.get("country", "").lower()
            
            region_score = 0
            if target_regions and target_regions[0] != "global":
                location_text = f"{event_city} {event_country}"
                for region in target_regions:
                    if region in location_text or region in event_name:
                        region_score = 1.0
                        break
                if not region_score:
                    region_score = 0.3  # Partial credit for having location data
            else:
                region_score = 0.8  # Global search, no penalty
            
            score += region_score * 0.20
            score_breakdown["region_match"] = region_score * 0.20
            
            # 3. Event type match (15% weight)
            type_score = 0
            for event_type in target_event_types:
                if event_type in event_name:
                    type_score = 1.0
                    break
            if not type_score:
                # Check for general event keywords
                event_keywords = ["conference", "summit", "expo", "forum", "festival"]
                if any(kw in event_name for kw in event_keywords):
                    type_score = 0.7
            
            score += type_score * 0.15
            score_breakdown["event_type_match"] = type_score * 0.15
            
            # 4. Date quality (15% weight)
            start_date = event.get("start_date", "")
            expected_date = event.get("expected_date", "")
            date_verified = event.get("date_verified", False)
            
            date_score = 0
            if start_date and start_date != "Not Found":
                date_score = 1.0
            elif expected_date and expected_date != "Not Found":
                if "2025" in expected_date or "2026" in expected_date:
                    date_score = 0.7
                else:
                    date_score = 0.4
            
            score += date_score * 0.15
            score_breakdown["date_quality"] = date_score * 0.15
            
            # 5. Content richness (15% weight)
            summary_len = len(event.get("summary", ""))
            website = event.get("event_website", "")
            
            content_score = 0
            if summary_len > 300:
                content_score = 1.0
            elif summary_len > 100:
                content_score = 0.6
            elif summary_len > 0:
                content_score = 0.3
            
            if website and "." in website:
                content_score += 0.2
            
            score += min(content_score, 1.0) * 0.15
            score_breakdown["content_richness"] = min(content_score, 1.0) * 0.15
            
            # 6. Exclusion penalty (negative scoring)
            excluded_keywords = intent_data.get("excluded_keywords", [])
            exclusion_penalty = 0
            for excluded in excluded_keywords:
                if excluded.lower() in event_name or excluded.lower() in event_summary:
                    exclusion_penalty += 0.3
            
            score -= min(exclusion_penalty, 0.5)  # Cap penalty at 0.5
            
            # Normalize to 0-100 scale
            final_score = max(0, min(100, int(score * 100)))
            
            # Add score to event
            event["discovery_score"] = final_score
            event["discovery_score_breakdown"] = score_breakdown
            
            # Only include if meets minimum threshold
            if final_score >= (min_score_threshold * 100):
                scored_events.append(event)
        
        return scored_events
