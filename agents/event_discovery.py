"""Event Discovery Agent - Finds industry events for sponsorship opportunities."""

import json
import logging
import time
from typing import Optional, Callable
from agents.base import BaseAgent, AgentInput, AgentOutput
from schema import get_empty_schema
from utils.llm_helpers import extract_json_from_response, EVENT_DISCOVERY_SYSTEM

logger = logging.getLogger(__name__)


# System prompt that instructs the LLM to search and return structured events
_DISCOVERY_SEARCH_PROMPT = """You are an expert event researcher. Your task is to discover real, upcoming industry events.

INSTRUCTIONS:
1. Search the web for current events matching the criteria below.
2. For EACH event found, extract structured information.
3. EXCLUDE company-specific product launches (Google I/O, AWS re:Invent, Microsoft Build, etc.)
4. ONLY include public, industry-wide conferences, summits, expos, forums, and festivals.
5. Verify dates from official sources. Look for events in 2025 and 2026.
6. Return results as a JSON array.

For each event return this JSON structure:
{{
  "event_name": "Official event name",
  "event_website": "Official URL",
  "city": "City name",
  "country": "Country name",
  "expected_date": "Date range (e.g., March 15-17, 2025)",
  "start_date": "ISO date if known",
  "end_date": "ISO date if known",
  "theme": "Primary industry/topic",
  "organizer": "Organizer name",
  "summary": "2-3 sentence description",
  "industry_focus": "Target industry",
  "target_audience": "Who attends"
}}

Return ONLY a JSON object: {{"events": [...]}}
"""


class EventDiscoveryAgent(BaseAgent):
    """Discovers industry events relevant for sponsorship across global regions.

    Uses LLM-driven search (Gemini native web / GLM+tools / Kimi+tools)
    instead of hardcoded search queries. The LLM autonomously decides what
    to search for and synthesizes results.

    FILTERS APPLIED:
    - Excludes company-specific product launch events
    - Only includes public, industry-wide events
    - Verifies event dates from official sources
    """

    name = "event_discovery"
    description = "Discovers industry events globally for sponsorship opportunities"

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

    INDUSTRY_WIDE_KEYWORDS = [
        "conference", "summit", "expo", "forum", "festival",
        "meeting", "convention", "symposium", "workshop",
        "bootcamp", "unconference", "meetup"
    ]

    def __init__(self, max_events: int = 50, provider: str = "auto",
                 max_execution_time: int = 120):
        super().__init__()
        self.max_events = max_events
        self.max_execution_time = max_execution_time
        self.progress_callback: Optional[Callable[[str, int], None]] = None

    def set_progress_callback(self, callback: Callable[[str, int], None]):
        self.progress_callback = callback

    def _report_progress(self, message: str, percent: int):
        logger.info(f"Progress [{percent}%]: {message}")
        if self.progress_callback:
            try:
                self.progress_callback(message, percent)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute event discovery using LLM-driven web search."""
        self.validate_input(input_data)
        start_time = time.time()
        params = input_data.parameters

        # --- extract intent ---
        intent_data = input_data.context.get("intent")
        if intent_data:
            industry = intent_data.get("industry", input_data.query)
            regions = intent_data.get("regions", [])
            region = regions[0] if regions else ""
            theme = intent_data.get("themes", [""])[0] if intent_data.get("themes") else ""
        else:
            industry = params.get("industry", input_data.query)
            region = params.get("region", "")
            theme = params.get("theme", "")

        max_events = params.get("max_events", self.max_events)

        # Skip if events already provided
        existing_data = input_data.context.get("events", [])
        if existing_data and isinstance(existing_data, list) and len(existing_data) > 0:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": existing_data},
                metadata={"agent": self.name, "event_count": len(existing_data)}
            )

        self._report_progress("Starting LLM-driven event discovery", 10)

        # --- build the research prompt ---
        region_clause = f" in {region}" if region else " globally"
        theme_clause = f" focused on {theme}" if theme else ""
        prompt = (
            f"Find up to {max_events} upcoming {industry} industry conferences, "
            f"summits, expos, and forums{region_clause}{theme_clause}.\n\n"
            f"Search for events happening in 2025 and 2026. "
            f"Include event name, official website URL, dates, location (city + country), "
            f"organizer, and a brief summary.\n\n"
            f"IMPORTANT: Exclude company-specific product launches like Google I/O, "
            f"AWS re:Invent, Microsoft Build, Apple WWDC, etc. "
            f"Only include public, industry-wide events.\n\n"
            f"Return ONLY a JSON object: {{\"events\": [...]}}"
        )

        self._report_progress("LLM researching events via web search...", 25)

        # --- call LLM with tools (strategy-aware) ---
        response = self.llm_with_tools(
            prompt=prompt,
            system_message=_DISCOVERY_SEARCH_PROMPT,
        )

        events = []
        if response.success and response.content:
            self._report_progress("Parsing LLM response...", 60)
            events = self._parse_llm_response(response.content, industry)
            self._track_llm_usage(response)
        else:
            logger.warning(f"LLM search failed: {response.error}. Falling back to DuckDuckGo.")
            self._report_progress("Falling back to DuckDuckGo search...", 30)
            events = self._fallback_search(industry, region, theme, max_events, start_time)

        # --- post-processing: filter, dedup, score ---
        events = self._filter_excluded_events(events, industry)
        events = self._deduplicate(events)
        events = events[:max_events]

        if intent_data and events:
            self._report_progress("Scoring events by relevance...", 75)
            events = self._score_events_by_intent(events, intent_data)
            events.sort(key=lambda x: x.get("discovery_score", 0), reverse=True)

        elapsed = time.time() - start_time
        logger.info(f"Discovered {len(events)} events in {elapsed:.1f}s")
        self._report_progress(f"Discovery complete: {len(events)} events", 100)

        return self._create_output(events, industry, region, theme)
    
    def _create_output(self, events: list, industry: str, region: str, theme: str) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            findings={
                "events": events,
                "inputs": {"industry": industry, "region": region, "theme": theme}
            },
            metadata={"agent": self.name, "event_count": len(events)}
        )

    # --- LLM response parsing ---

    def _parse_llm_response(self, content: str, industry: str) -> list:
        """Parse structured events from LLM response."""
        data = extract_json_from_response(content)
        if not data:
            logger.warning("Could not parse JSON from LLM response")
            return []

        raw_events = data.get("events", []) if isinstance(data, dict) else data
        if not isinstance(raw_events, list):
            return []

        events = []
        for raw in raw_events:
            if not isinstance(raw, dict):
                continue
            event = self._normalize_event(raw, industry)
            if event:
                events.append(event)

        logger.info(f"Parsed {len(events)} events from LLM response")
        return events

    def _normalize_event(self, raw: dict, industry: str) -> Optional[dict]:
        """Normalize an LLM-returned event dict into the full schema."""
        name = raw.get("event_name", "").strip()
        if not name:
            return None

        return {
            "event_name": name,
            "event_website": raw.get("event_website", raw.get("url", "")),
            "city": raw.get("city", ""),
            "country": raw.get("country", ""),
            "expected_date": raw.get("expected_date", ""),
            "start_date": raw.get("start_date", ""),
            "end_date": raw.get("end_date", ""),
            "theme": raw.get("theme", industry),
            "organizer": raw.get("organizer", ""),
            "summary": raw.get("summary", ""),
            "industry_focus": raw.get("industry_focus", industry),
            "target_audience": raw.get("target_audience", ""),
            "contact_email": "",
            "contact_url": "",
            "sponsorship_url": "",
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
            "date_verified": bool(raw.get("start_date")),
            "status": "Discovered",
        }

    # --- Fallback: DuckDuckGo direct search ---

    def _fallback_search(self, industry: str, region: str, theme: str,
                         max_events: int, start_time: float) -> list:
        """Fallback to direct DuckDuckGo search if LLM-driven search fails."""
        from utils.search import WebSearchTool

        search_tool = WebSearchTool(provider="duckduckgo")
        queries = self._build_fallback_queries(industry, region, theme)
        events = []

        for query in queries[:8]:
            if time.time() - start_time > self.max_execution_time:
                break
            try:
                results = search_tool.search(query, max_results=10)
                for result in results:
                    event = self._parse_fallback_result(result, industry)
                    if event and not self._is_duplicate(event, events):
                        events.append(event)
                        if len(events) >= max_events:
                            return events
            except Exception as e:
                logger.warning(f"Fallback search failed for '{query}': {e}")
        return events

    def _build_fallback_queries(self, industry: str, region: str, theme: str) -> list:
        regions = [region] if region else ["USA", "Europe", "APAC", "Middle East"]
        queries = []
        for r in regions:
            queries.append(f"{industry} conference summit 2025 2026 {r}")
            queries.append(f"{industry} expo forum 2025 2026 {r}")
        return queries

    def _parse_fallback_result(self, result: dict, industry: str) -> Optional[dict]:
        title = result.get("title", "")
        url = result.get("url", "")
        content = result.get("content", "")
        if not title or not url:
            return None
        skip = ["blog", "news", "article", "youtube", "linkedin", "twitter", "facebook"]
        if any(p in url.lower() for p in skip):
            return None
        return self._normalize_event({
            "event_name": title,
            "event_website": url,
            "summary": content[:500] if content else "",
        }, industry)

    # --- Post-processing ---

    def _filter_excluded_events(self, events: list, industry: str) -> list:
        """Remove company-specific events."""
        filtered = []
        vendor_urls = ["google.com", "aws.amazon", "microsoft.com", "salesforce.com",
                       "shopify.com", "stripe.com", "paypal.com", "github.com"]

        for event in events:
            name_lower = event.get("event_name", "").lower()
            url_lower = event.get("event_website", "").lower()

            if any(c in name_lower or c in url_lower for c in self.EXCLUDED_COMPANIES):
                logger.info(f"Excluded (company-specific): {event.get('event_name')}")
                continue
            if any(p in url_lower for p in vendor_urls):
                logger.info(f"Excluded (vendor URL): {event.get('event_name')}")
                continue
            filtered.append(event)
        return filtered

    def _deduplicate(self, events: list) -> list:
        seen_names = set()
        seen_urls = set()
        unique = []
        for event in events:
            name = event.get("event_name", "").lower().strip()
            url = event.get("event_website", "").lower().strip()
            if name in seen_names or (url and url in seen_urls):
                continue
            seen_names.add(name)
            if url:
                seen_urls.add(url)
            unique.append(event)
        return unique

    def _is_duplicate(self, event: dict, events: list) -> bool:
        name = event.get("event_name", "").lower()
        url = event.get("event_website", "").lower()
        for existing in events[-50:]:
            if name == existing.get("event_name", "").lower():
                return True
            if url and url == existing.get("event_website", "").lower():
                return True
        return False

    def _score_events_by_intent(self, events: list, intent_data: dict) -> list:
        """Score events against intent criteria."""
        target_industry = intent_data.get("industry", "").lower()
        target_regions = [r.lower() for r in intent_data.get("regions", [])]
        min_threshold = intent_data.get("quality_requirements", {}).get("relevance_threshold", 0.3)

        scored = []
        for event in events:
            name = event.get("event_name", "").lower()
            theme = event.get("theme", "").lower()
            summary = event.get("summary", "").lower()
            country = event.get("country", "").lower()
            city = event.get("city", "").lower()

            score = 0.0
            # Industry match (30%)
            if target_industry in theme or target_industry in name:
                score += 0.30
            elif target_industry in summary:
                score += 0.20
            # Region match (25%)
            if target_regions:
                loc = f"{city} {country}"
                if any(r in loc or r in name for r in target_regions):
                    score += 0.25
                else:
                    score += 0.08
            else:
                score += 0.20
            # Has dates (20%)
            if event.get("start_date") or event.get("expected_date"):
                score += 0.20
            # Has website (15%)
            if event.get("event_website") and "." in event.get("event_website", ""):
                score += 0.15
            # Has summary (10%)
            if len(event.get("summary", "")) > 50:
                score += 0.10

            final = max(0, min(100, int(score * 100)))
            event["discovery_score"] = final
            if final >= int(min_threshold * 100):
                scored.append(event)
        return scored
