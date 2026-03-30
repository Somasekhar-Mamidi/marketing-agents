"""Event Qualification Agent - Scores events for sponsorship potential."""

import logging
from typing import Optional
from agents.base import BaseAgent, AgentInput, AgentOutput
from utils.llm_helpers import extract_json_from_response, EVENT_QUALIFICATION_SYSTEM

logger = logging.getLogger(__name__)


_QUALIFICATION_PROMPT = """You are an event qualification expert. Evaluate this event for sponsorship potential.

Event: {event_name}
Theme: {theme}
Location: {city}, {country}
Summary: {summary}

Search the web for:
- How many attendees this event typically has
- Who the past sponsors were
- The event's industry reputation

Then score on these criteria (1-10 scale):
- audience_relevance_score: Quality/relevance of attendees for a FinTech/Payments company
- industry_reputation_score: Event prestige and recognition in the industry
- attendance_score: Expected attendance size and seniority
- sponsor_value_score: Value proposition for sponsors
- regional_importance_score: Geographic significance for tech market

Return JSON:
{{
  "audience_relevance_score": <float>,
  "industry_reputation_score": <float>,
  "attendance_score": <float>,
  "sponsor_value_score": <float>,
  "regional_importance_score": <float>,
  "reasoning": "Brief justification"
}}
"""


class EventQualificationAgent(BaseAgent):
    """Evaluates and scores events based on sponsorship potential.

    Uses LLM-driven web research to gather attendee/sponsor data, then
    scores each event on 5 criteria and assigns a priority tier.
    Falls back to rule-based heuristics if LLM search fails.
    """

    name = "event_qualification"
    description = "Scores events for sponsorship potential"

    TIER_THRESHOLDS = {
        "Tier 1 - Must Sponsor": 8.0,
        "Tier 2 - Strong Opportunity": 6.0,
        "Tier 3 - Optional": 4.0,
        "Tier 4 - Low Priority": 0.0
    }

    def execute(self, input_data: AgentInput) -> AgentOutput:
        self.validate_input(input_data)

        events = input_data.context.get("events", [])
        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": [], "message": "No events to qualify"},
                metadata={"agent": self.name, "event_count": 0}
            )

        self.emit_thinking("scoring", f"Qualifying {len(events)} events for sponsorship potential")
        logger.info(f"Qualifying {len(events)} events")

        qualified_events = []
        for event in events:
            qualified_events.append(self._qualify_event(event))

        if qualified_events:
            self.emit_thinking("result", f"Qualification complete. Top event: {qualified_events[0].get('event_name', 'N/A')} (Score: {qualified_events[0].get('overall_score', 'N/A')})")

        qualified_events.sort(
            key=lambda x: float(x.get("overall_score") or 0),
            reverse=True
        )

        logger.info(f"Qualified {len(qualified_events)} events")
        return AgentOutput(
            agent_name=self.name,
            findings={"events": qualified_events},
            metadata={"agent": self.name, "event_count": len(qualified_events)}
        )

    def _qualify_event(self, event: dict) -> dict:
        """Qualify a single event — try LLM first, fall back to rules."""
        event_name = event.get("event_name", "Unknown")
        self.emit_thinking("scoring", f"Scoring '{event_name}'...")

        scores = self._qualify_with_llm(event)
        if scores:
            self.emit_thinking("result", f"LLM scored '{event_name}': audience={scores['audience_relevance_score']:.1f}, reputation={scores['industry_reputation_score']:.1f}")
        else:
            self.emit_thinking("fallback", f"LLM scoring failed for '{event_name}', using rule-based heuristics")
            scores = self._qualify_with_rules(event)

        event["audience_relevance_score"] = str(scores["audience_relevance_score"])
        event["industry_reputation_score"] = str(scores["industry_reputation_score"])
        event["attendance_score"] = str(scores["attendance_score"])
        event["sponsor_value_score"] = str(scores["sponsor_value_score"])
        event["regional_importance_score"] = str(scores["regional_importance_score"])

        overall = (
            scores["audience_relevance_score"] * 0.25 +
            scores["industry_reputation_score"] * 0.25 +
            scores["attendance_score"] * 0.20 +
            scores["sponsor_value_score"] * 0.15 +
            scores["regional_importance_score"] * 0.15
        )

        event["overall_score"] = str(round(overall, 1))
        event["priority_tier"] = self._determine_tier(overall)
        event["status"] = "Qualified"
        self.emit_thinking("result", f"'{event_name}' → Score: {round(overall, 1)}, {event['priority_tier']}")
        return event

    def _qualify_with_llm(self, event: dict) -> Optional[dict]:
        """Use LLM with web research to score the event."""
        try:
            prompt = _QUALIFICATION_PROMPT.format(
                event_name=event.get("event_name", "Unknown"),
                theme=event.get("theme", "Unknown"),
                city=event.get("city", "Unknown"),
                country=event.get("country", "Unknown"),
                summary=event.get("summary", "N/A")[:300],
            )

            response = self.llm_with_tools(
                prompt=prompt,
                system_message=EVENT_QUALIFICATION_SYSTEM,
            )

            if not response.success or not response.content:
                return None

            self._track_llm_usage(response)
            data = extract_json_from_response(response.content)
            if not data:
                return None

            return {
                "audience_relevance_score": float(data.get("audience_relevance_score", 6.0)),
                "industry_reputation_score": float(data.get("industry_reputation_score", 6.0)),
                "attendance_score": float(data.get("attendance_score", 5.0)),
                "sponsor_value_score": float(data.get("sponsor_value_score", 6.0)),
                "regional_importance_score": float(data.get("regional_importance_score", 5.0)),
            }
        except Exception as e:
            logger.debug(f"LLM qualification failed: {e}")
            return None

    def _qualify_with_rules(self, event: dict) -> dict:
        """Rule-based fallback scoring."""
        theme = event.get("theme", "").lower()
        country = event.get("country", "").lower()
        name = event.get("event_name", "").lower()

        # Audience relevance
        target = ["fintech", "payments", "artificial intelligence", "ai"]
        audience = 8.5 if any(t in theme for t in target) else 6.5

        # Reputation
        reputation = 7.5 if any(kw in name for kw in ["world", "global", "summit", "conference", "expo"]) else 6.0

        # Attendance (heuristic)
        attendance = 5.0

        # Sponsor value
        sponsor = 6.0

        # Regional importance
        major = ["usa", "united states", "uk", "singapore", "dubai", "india"]
        regional = ["brazil", "saudi arabia", "riyadh", "australia", "japan"]
        if any(h in country for h in major):
            region_score = 8.5
        elif any(h in country for h in regional):
            region_score = 6.5
        else:
            region_score = 5.0

        return {
            "audience_relevance_score": audience,
            "industry_reputation_score": reputation,
            "attendance_score": attendance,
            "sponsor_value_score": sponsor,
            "regional_importance_score": region_score,
        }

    def _determine_tier(self, overall_score: float) -> str:
        if overall_score >= 8.0:
            return "Tier 1 - Must Sponsor"
        elif overall_score >= 6.0:
            return "Tier 2 - Strong Opportunity"
        elif overall_score >= 4.0:
            return "Tier 3 - Optional"
        else:
            return "Tier 4 - Low Priority"
