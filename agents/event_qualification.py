"""Event Qualification Agent - Scores events for sponsorship potential."""

import logging
from typing import Optional
from agents.base import BaseAgent, AgentInput, AgentOutput
from utils.search import WebSearchTool

logger = logging.getLogger(__name__)


class EventQualificationAgent(BaseAgent):
    """Evaluates and scores events based on sponsorship potential.
    
    Scores each event on:
    - Audience relevance (1-10)
    - Industry reputation (1-10)
    - Estimated attendance (1-10)
    - Sponsor visibility (1-10)
    - Regional importance (1-10)
    
    Then calculates overall_score and assigns priority_tier.
    """
    
    name = "event_qualification"
    description = "Scores events for sponsorship potential"
    
    # Scoring thresholds for tier classification
    TIER_THRESHOLDS = {
        "Tier 1 - Must Sponsor": 8.0,  # overall_score >= 8.0
        "Tier 2 - Strong Opportunity": 6.0,  # >= 6.0
        "Tier 3 - Optional": 4.0,  # >= 4.0
        "Tier 4 - Low Priority": 0.0  # < 4.0
    }
    
    def __init__(self, provider: str = "tavily"):
        self.search_tool = WebSearchTool(provider=provider)
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """ify andQual score discovered events."""
        self.validate_input(input_data)
        
        # Get events from context
        events = input_data.context.get("events", [])
        
        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": [], "message": "No events to qualify"},
                metadata={"agent": self.name, "event_count": 0}
            )
        
        logger.info(f"Qualifying {len(events)} events")
        
        qualified_events = []
        
        for event in events:
            qualified_event = self._qualify_event(event)
            qualified_events.append(qualified_event)
        
        # Sort by overall_score descending
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
        """Qualify a single event by scoring it."""
        event_name = event.get("event_name", "")
        theme = event.get("theme", "")
        country = event.get("country", "")
        
        # Search for event info to help score
        scores = self._search_for_scores(event_name, theme, country)
        
        # Calculate individual scores (1-10 scale)
        audience_score = self._calculate_audience_score(scores, theme)
        reputation_score = self._calculate_reputation_score(scores, event_name)
        attendance_score = self._calculate_attendance_score(scores)
        sponsor_score = self._calculate_sponsor_score(scores)
        regional_score = self._calculate_regional_score(country)
        
        # Calculate overall score (weighted average)
        overall = (
            audience_score * 0.25 +
            reputation_score * 0.25 +
            attendance_score * 0.20 +
            sponsor_score * 0.15 +
            regional_score * 0.15
        )
        
        # Determine tier
        tier = self._determine_tier(overall)
        
        # Update event with scores
        event["audience_relevance_score"] = str(audience_score)
        event["industry_reputation_score"] = str(reputation_score)
        event["attendance_score"] = str(attendance_score)
        event["sponsor_value_score"] = str(sponsor_score)
        event["regional_importance_score"] = str(regional_score)
        event["overall_score"] = str(round(overall, 1))
        event["priority_tier"] = tier
        event["status"] = "Qualified"
        
        return event
    
    def _search_for_scores(self, event_name: str, theme: str, country: str) -> dict:
        """Search for event information to help with scoring."""
        scores = {
            "attendee_count": "Not Found",
            "sponsors": "Not Found",
            "reputation": "Not Found"
        }
        
        if not event_name:
            return scores
        
        try:
            # Search for attendee count
            query = f"{event_name} attendees participants 2024 2025"
            results = self.search_tool.search(query, max_results=3)
            if results and results[0].get("content"):
                scores["attendee_count"] = results[0]["content"][:200]
        except Exception:
            pass
        
        return scores
    
    def _calculate_audience_score(self, scores: dict, theme: str) -> float:
        """Calculate audience relevance score."""
        # Higher score for FinTech, AI, Payments (our target industries)
        target_industries = ["fintech", "payments", "artificial intelligence", "ai"]
        theme_lower = theme.lower() if theme else ""
        
        for industry in target_industries:
            if industry in theme_lower:
                return 8.5
        
        return 6.5
    
    def _calculate_reputation_score(self, scores: dict, event_name: str) -> float:
        """Calculate industry reputation score."""
        name_lower = event_name.lower() if event_name else ""
        
        # Known high-reputation events get higher scores
        high_reputation = ["world", "global", "summit", "conference", "expo"]
        
        for term in high_reputation:
            if term in name_lower:
                return 7.5
        
        return 6.0
    
    def _calculate_attendance_score(self, scores: dict) -> float:
        """Calculate estimated attendance score."""
        content = scores.get("attendee_count", "").lower()
        
        # Try to estimate from search results
        if "thousand" in content or "5000" in content or "10000" in content:
            return 9.0
        elif "thousands" in content or "3000" in content:
            return 7.5
        elif "hundred" in content or "500" in content:
            return 5.5
        
        # Default for unknown
        return 5.0
    
    def _calculate_sponsor_score(self, scores: dict) -> float:
        """Calculate sponsor visibility score."""
        # Default score based on search presence
        return 6.0
    
    def _calculate_regional_score(self, country: str) -> float:
        """Calculate regional importance score."""
        # Major tech hubs get higher scores
        major_hubs = ["usa", "united states", "uk", "singapore", "dubai", "india"]
        country_lower = country.lower() if country else ""
        
        for hub in major_hubs:
            if hub in country_lower:
                return 8.5
        
        # Regional hubs
        regional_hubs = ["brazil", "saudi arabia", "riyadh", "australia", "japan"]
        for hub in regional_hubs:
            if hub in country_lower:
                return 6.5
        
        return 5.0
    
    def _determine_tier(self, overall_score: float) -> str:
        """Determine priority tier based on overall score."""
        if overall_score >= 8.0:
            return "Tier 1 - Must Sponsor"
        elif overall_score >= 6.0:
            return "Tier 2 - Strong Opportunity"
        elif overall_score >= 4.0:
            return "Tier 3 - Optional"
        else:
            return "Tier 4 - Low Priority"
