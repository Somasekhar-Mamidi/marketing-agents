"""Event Intelligence Agent - Strategic analysis of events for sponsorship."""

import logging
from typing import Optional
from agents.base import BaseAgent, AgentInput, AgentOutput
from utils.llm_helpers import extract_json_from_response, EVENT_INTELLIGENCE_SYSTEM

logger = logging.getLogger(__name__)


_INTELLIGENCE_PROMPT = """Analyze this event for sponsorship strategic intelligence.

Search the web for CURRENT information about this event:
- Recent sponsor lists and exhibitor data
- Attendee demographics and job roles
- Industry positioning and reputation
- Recent news or announcements

Event: {event_name}
Theme: {theme}
Location: {city}, {country}
Priority Tier: {tier}
Score: {score}
Summary: {summary}

Return JSON:
{{
  "attendee_roles": "Who typically attends (e.g., CTOs, VPs, Developers)",
  "companies_attending": "Types of companies and notable names",
  "strategic_value": "Why sponsor this event (2-3 sentences)",
  "potential_roi": "Expected return (High/Medium/Low with justification)",
  "ideal_sponsorship_format": "Best sponsorship type (booth, speaking, etc.)",
  "competitor_presence": "Likely competitors at this event",
  "key_opportunities": ["opportunity 1", "opportunity 2"],
  "risks": ["risk 1", "risk 2"]
}}
"""


class EventIntelligenceAgent(BaseAgent):
    """Provides strategic market intelligence for event sponsorship.

    Uses LLM-driven web search to gather current attendee data, sponsor
    history, and competitive landscape. Falls back to heuristics.
    """

    name = "event_intelligence"
    description = "Strategic analysis of events for sponsorship"

    EVENT_AUDIENCES = {
        "fintech": {
            "roles": "CFO, CTO, VP Engineering, Product Managers, Financial Technology Leaders",
            "companies": "Banks, Payment Processors, Crypto Companies, Financial Institutions, Fintech Startups"
        },
        "ai": {
            "roles": "Data Scientists, ML Engineers, AI Researchers, CTOs, Product Leaders",
            "companies": "Tech Giants, AI Startups, Research Labs, Enterprise Companies"
        },
        "payments": {
            "roles": "Payment Engineers, Product Managers, CTOs, Finance Leaders",
            "companies": "Payment Gateways, Banks, E-commerce, Retail Tech"
        },
        "developer": {
            "roles": "Software Engineers, Developers, DevOps, Architects, Technical Leads",
            "companies": "Tech Companies, Startups, Agencies, Enterprise"
        },
        "open source": {
            "roles": "Open Source Contributors, Developers, DevRel, Technical Architects",
            "companies": "Tech Companies, Cloud Providers, Enterprise"
        },
        "technology": {
            "roles": "CTOs, Tech Leaders, Engineers, Product Managers, Innovators",
            "companies": "Various Tech Companies, Enterprises, Startups"
        }
    }

    def execute(self, input_data: AgentInput) -> AgentOutput:
        self.validate_input(input_data)

        events = input_data.context.get("events", [])
        self.emit_thinking("searching", f"Analyzing {len(events)} events for strategic intelligence")
        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": [], "message": "No events to analyze"},
                metadata={"agent": self.name, "event_count": 0}
            )

        logger.info(f"Analyzing {len(events)} events for strategic intelligence")

        analyzed_events = []
        for event in events:
            analyzed_events.append(self._analyze_event(event))

        return AgentOutput(
            agent_name=self.name,
            findings={"events": analyzed_events},
            metadata={"agent": self.name, "event_count": len(analyzed_events)}
        )

    def _analyze_event(self, event: dict) -> dict:
        """Analyze event — try LLM with web search, fall back to heuristics."""
        event_name = event.get("event_name", "Unknown")
        self.emit_thinking("searching", f"Researching attendee data, sponsors, and competition for '{event_name}'")
        llm_analysis = self._analyze_with_llm(event)
        if llm_analysis:
            roi = llm_analysis.get("potential_roi", "Unknown")
            format_type = llm_analysis.get("ideal_sponsorship_format", "N/A")
            self.emit_thinking("result", f"'{event_name}': ROI={roi}, format={format_type}")
            event.update(llm_analysis)
        else:
            self.emit_thinking("fallback", f"LLM analysis failed for '{event_name}', using heuristic assessment")
            theme = event.get("theme", "").lower()
            audience_info = self._get_audience_info(theme)
            event["attendee_roles"] = audience_info.get("roles", "Technology professionals")
            event["companies_attending"] = audience_info.get("companies", "Various")
            event["strategic_value"] = self._calculate_strategic_value(
                event.get("priority_tier", ""), event.get("overall_score", ""), theme
            )
            event["potential_roi"] = self._calculate_potential_roi(
                event.get("priority_tier", ""), event.get("country", "").lower()
            )
            event["ideal_sponsorship_format"] = self._determine_sponsorship_format(
                event.get("priority_tier", ""), theme
            )

        event["status"] = "Intelligence Analyzed"
        return event

    def _analyze_with_llm(self, event: dict) -> Optional[dict]:
        """Use LLM with web research for strategic analysis."""
        try:
            prompt = _INTELLIGENCE_PROMPT.format(
                event_name=event.get("event_name", "Unknown"),
                theme=event.get("theme", "Unknown"),
                city=event.get("city", ""),
                country=event.get("country", ""),
                tier=event.get("priority_tier", "Unknown"),
                score=event.get("overall_score", "N/A"),
                summary=event.get("summary", "N/A")[:300],
            )

            response = self.llm_with_tools(
                prompt=prompt,
                system_message=EVENT_INTELLIGENCE_SYSTEM,
            )

            if not response.success or not response.content:
                return None

            self._track_llm_usage(response)
            data = extract_json_from_response(response.content)
            if not data:
                return None

            return {
                "attendee_roles": data.get("attendee_roles", "Technology professionals"),
                "companies_attending": data.get("companies_attending", "Various tech companies"),
                "strategic_value": data.get("strategic_value", ""),
                "potential_roi": data.get("potential_roi", "Medium"),
                "ideal_sponsorship_format": data.get("ideal_sponsorship_format", "Standard booth"),
                "competitor_presence": data.get("competitor_presence", ""),
                "key_opportunities": data.get("key_opportunities", []),
                "risks": data.get("risks", []),
            }

        except Exception as e:
            logger.debug(f"LLM analysis failed: {e}")
            return None

    # --- Fallback heuristics ---

    def _get_audience_info(self, theme: str) -> dict:
        for key, info in self.EVENT_AUDIENCES.items():
            if key in theme:
                return info
        return self.EVENT_AUDIENCES.get("technology", {})

    def _calculate_strategic_value(self, tier: str, score: str, theme: str) -> str:
        score_val = float(score) if score else 5.0
        if score_val >= 7:
            return (
                f"High-impact sponsorship opportunity. {theme.title()} event with strong "
                f"industry presence. Direct access to target decision-makers and developers. "
                f"Brand visibility among key stakeholders."
            )
        elif score_val >= 5:
            return (
                f"Valuable sponsorship opportunity. {theme.title()} focused event with "
                "good audience reach. Opportunity to generate leads and build partnerships."
            )
        return (
            f"Moderate sponsorship value. {theme.title()} event with niche audience. "
            "Consider for specific regional or audience targeting."
        )

    def _calculate_potential_roi(self, tier: str, country: str) -> str:
        if "Tier 1" in tier:
            return (
                "High ROI expected. Tier 1 events attract senior attendees with "
                "high purchasing authority. Estimated lead generation: 50+ qualified leads."
            )
        elif "Tier 2" in tier:
            return (
                "Good ROI expected. Tier 2 events provide solid brand exposure "
                "and lead generation opportunities. Estimated 25-50 qualified leads."
            )
        return (
            "Moderate ROI. Tier 3/4 events good for brand awareness and "
            "niche targeting. Estimated 10-25 leads."
        )

    def _determine_sponsorship_format(self, tier: str, theme: str) -> str:
        if "Tier 1" in tier:
            return ("Gold/Platinum Sponsorship with booth, speaking slot, "
                    "logo placement, and dedicated networking session")
        elif "Tier 2" in tier:
            return ("Silver Sponsorship with booth, logo on website and materials, "
                    "networking access")
        return "Bronze Sponsorship or exhibitor booth with basic branding"
