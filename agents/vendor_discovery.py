"""Vendor Discovery Agent - Discovers sponsors and exhibitors for events."""

import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse
from agents.base import BaseAgent, AgentInput, AgentOutput
from utils.llm_helpers import extract_json_from_response, VENDOR_DISCOVERY_SYSTEM

logger = logging.getLogger(__name__)


_VENDOR_SEARCH_PROMPT = """You are a vendor research specialist. Find real service providers, sponsors, and exhibitors.

Search the web for current information. For each vendor found, return:
{{
  "vendor_name": "Company name",
  "vendor_website": "Official URL",
  "vendor_type": "sponsor|exhibitor|service_provider",
  "service_category": "Category of service",
  "relevance_score": 0.0-1.0,
  "description": "Brief description of services"
}}

Return ONLY a JSON object: {{"vendors": [...]}}

IMPORTANT:
- Only include REAL companies with working websites
- Prioritize vendors with recent activity (2024-2025)
- Include contact information if found
"""


class VendorDiscoveryAgent(BaseAgent):
    """Discovers vendors using LLM-driven web search.

    Uses Gemini native search or GLM/Kimi tool calling to find sponsors,
    exhibitors, and service providers. Falls back to DuckDuckGo if LLM fails.
    """

    name = "vendor_discovery"
    description = "Discovers vendors, sponsors, and service providers for events"

    VENDOR_TYPES = ['sponsor', 'exhibitor', 'partner', 'speaker', 'service_provider']

    SERVICE_CATEGORIES = {
        'booth_builder': ['booth builder', 'exhibition stand', 'stand contractor'],
        'av_equipment': ['av equipment', 'audio visual', 'stage design'],
        'catering': ['catering', 'food service', 'event catering'],
        'printing': ['event printing', 'banner printing', 'signage'],
        'logistics': ['event logistics', 'freight', 'shipping'],
        'marketing': ['event marketing', 'promotion', 'pr agency'],
        'technology': ['event technology', 'registration system', 'event app'],
        'security': ['event security', 'crowd management'],
        'staffing': ['event staffing', 'hostess', 'promotional staff'],
        'transportation': ['transportation', 'shuttle service'],
        'venue': ['venue', 'conference center'],
        'photography': ['event photography', 'videography'],
        'furniture': ['event furniture', 'rental furniture'],
        'floral': ['event floral', 'decoration', 'staging']
    }

    def __init__(self, max_vendors_per_event: int = 10, search_service_providers: bool = True):
        super().__init__()
        self.max_vendors_per_event = max_vendors_per_event
        self.search_service_providers = search_service_providers

    def execute(self, input_data: AgentInput) -> AgentOutput:
        self.validate_input(input_data)

        events = input_data.context.get("events", [])
        service_category = input_data.parameters.get('service_category')
        location = input_data.parameters.get('location')

        # Direct service provider search (no events needed)
        if not events and service_category and location:
            self.emit_thinking("searching", f"Searching for {service_category} providers in {location}")
            vendors = self._search_service_providers_llm(service_category, location)
            self.emit_thinking("result", f"Found {len(vendors)} service providers")
            return AgentOutput(
                agent_name=self.name,
                findings={"vendors": vendors, "service_category": service_category, "location": location},
                metadata={"agent": self.name, "vendor_count": len(vendors), "search_type": "direct_service_provider"}
            )

        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={"vendors": [], "message": "No events to process"},
                metadata={"agent": self.name, "vendor_count": 0}
            )

        self.emit_thinking("searching", f"Discovering vendors for {len(events)} events")
        logger.info(f"Discovering vendors for {len(events)} events")
        all_vendors = []

        for event in events:
            event_name = event.get("event_name", "Unknown")
            self.emit_thinking("searching", f"Finding sponsors and exhibitors for '{event_name}'")
            event_vendors = self._discover_for_event_llm(event)
            self.emit_thinking("result", f"Found {len(event_vendors)} vendors for '{event_name}'")
            for v in event_vendors:
                v['event_id'] = event.get('id')
                v['event_name'] = event.get('event_name')
            all_vendors.extend(event_vendors)

        all_vendors = self._deduplicate_vendors(all_vendors)
        self.emit_thinking("result", f"Vendor discovery complete: {len(all_vendors)} unique vendors")
        logger.info(f"Discovered {len(all_vendors)} total vendors")

        return AgentOutput(
            agent_name=self.name,
            findings={"vendors": all_vendors, "events": events},
            metadata={"agent": self.name, "vendor_count": len(all_vendors), "events_processed": len(events)}
        )

    # --- LLM-driven search methods ---

    def _discover_for_event_llm(self, event: dict) -> List[Dict]:
        """Use LLM to find sponsors and exhibitors for an event."""
        event_name = event.get('event_name', '')
        if not event_name:
            return []

        location = f"{event.get('city', '')} {event.get('country', '')}".strip()

        prompt = (
            f"Find sponsors, exhibitors, and service providers for the event: {event_name}\n"
            f"Location: {location or 'Unknown'}\n\n"
            f"Search the web for:\n"
            f"1. Current and past sponsors of {event_name} (2024-2025)\n"
            f"2. Exhibitors at {event_name}\n"
        )
        if self.search_service_providers and location:
            prompt += (
                f"3. Booth builders and exhibition stand contractors in {location}\n"
                f"4. AV equipment and event service providers in {location}\n"
            )
        prompt += f"\nReturn up to {self.max_vendors_per_event} vendors as JSON: {{\"vendors\": [...]}}"

        vendors = self._call_llm_for_vendors(prompt)
        if not vendors:
            return self._fallback_vendor_search(event_name)
        return vendors[:self.max_vendors_per_event]

    def _search_service_providers_llm(self, category: str, location: str) -> List[Dict]:
        """Use LLM to find service providers by category and location."""
        keywords = self.SERVICE_CATEGORIES.get(category, [category])
        keyword_str = ", ".join(keywords[:3])

        prompt = (
            f"Find {keyword_str} companies and service providers in {location}.\n\n"
            f"Search for real companies that provide {category.replace('_', ' ')} services "
            f"for events and exhibitions in {location}.\n\n"
            f"Return up to {self.max_vendors_per_event * 2} vendors as JSON: {{\"vendors\": [...]}}"
        )

        vendors = self._call_llm_for_vendors(prompt)
        if not vendors:
            return self._fallback_service_search(category, location)

        for v in vendors:
            v['service_category'] = category
        return vendors[:self.max_vendors_per_event * 2]

    def _call_llm_for_vendors(self, prompt: str) -> List[Dict]:
        """Call LLM with tools and parse vendor results."""
        try:
            response = self.llm_with_tools(
                prompt=prompt,
                system_message=_VENDOR_SEARCH_PROMPT,
            )

            if not response.success or not response.content:
                self.emit_thinking("fallback", f"LLM vendor search failed: {response.error}")
                logger.warning(f"LLM vendor search failed: {response.error}")
                return []

            self._track_llm_usage(response)
            data = extract_json_from_response(response.content)
            if not data:
                return []

            raw_vendors = data.get("vendors", []) if isinstance(data, dict) else data
            if not isinstance(raw_vendors, list):
                return []

            vendors = []
            for raw in raw_vendors:
                if not isinstance(raw, dict):
                    continue
                v = self._normalize_vendor(raw)
                if v:
                    vendors.append(v)
            return vendors

        except Exception as e:
            logger.warning(f"LLM vendor search error: {e}")
            return []

    def _normalize_vendor(self, raw: dict) -> Optional[Dict]:
        """Normalize a vendor dict from LLM response."""
        name = raw.get("vendor_name", "").strip()
        if not name:
            return None
        return {
            'vendor_name': name,
            'vendor_website': raw.get("vendor_website", raw.get("url", "")),
            'vendor_type': raw.get("vendor_type", "service_provider"),
            'service_category': raw.get("service_category", ""),
            'source': 'llm_search',
            'relevance_score': float(raw.get("relevance_score", 0.5)),
            'description': raw.get("description", ""),
            'contact_email': raw.get("contact_email"),
            'contact_phone': raw.get("contact_phone"),
        }

    # --- Fallback: DuckDuckGo ---

    def _fallback_vendor_search(self, event_name: str) -> List[Dict]:
        """Fallback to DuckDuckGo if LLM search fails."""
        from utils.search import WebSearchTool
        search_tool = WebSearchTool(provider="duckduckgo")
        vendors = []

        for query in [f"{event_name} 2025 sponsors partners", f"{event_name} exhibitors 2025"]:
            try:
                results = search_tool.search(query, max_results=5)
                for r in results:
                    name = r.get("title", "").split("|")[0].split("-")[0].strip()
                    if name:
                        vendors.append({
                            'vendor_name': name,
                            'vendor_website': r.get("url", ""),
                            'vendor_type': 'sponsor',
                            'source': 'duckduckgo_fallback',
                            'relevance_score': 0.5,
                            'description': r.get("content", "")[:200],
                        })
            except Exception as e:
                logger.warning(f"Fallback vendor search failed: {e}")

        return self._deduplicate_vendors(vendors)[:self.max_vendors_per_event]

    def _fallback_service_search(self, category: str, location: str) -> List[Dict]:
        from utils.search import WebSearchTool
        search_tool = WebSearchTool(provider="duckduckgo")
        keywords = self.SERVICE_CATEGORIES.get(category, [category])
        vendors = []

        for kw in keywords[:2]:
            try:
                results = search_tool.search(f"{kw} {location}", max_results=5)
                for r in results:
                    name = r.get("title", "").split("|")[0].split("-")[0].strip()
                    if name:
                        vendors.append({
                            'vendor_name': name,
                            'vendor_website': r.get("url", ""),
                            'vendor_type': 'service_provider',
                            'service_category': category,
                            'source': 'duckduckgo_fallback',
                            'relevance_score': 0.5,
                            'description': r.get("content", "")[:200],
                        })
            except Exception as e:
                logger.warning(f"Fallback service search failed: {e}")

        return self._deduplicate_vendors(vendors)

    # --- Deduplication ---

    def _deduplicate_vendors(self, vendors: List[Dict]) -> List[Dict]:
        seen_names = set()
        seen_domains = set()
        unique = []
        for v in vendors:
            name = v.get('vendor_name', '').lower().strip()
            url = v.get('vendor_website', '')
            domain = urlparse(url).netloc.replace('www.', '') if url else ""

            if name in seen_names:
                continue
            if domain and domain in seen_domains:
                continue

            seen_names.add(name)
            if domain:
                seen_domains.add(domain)
            unique.append(v)
        return unique
