"""Event Prioritization Agent - Prioritizes and recommends events."""

import logging
from agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class EventPrioritizationAgent(BaseAgent):
    """Prioritizes events and provides recommendations.
    
    Sorts events by overall_score and priority_tier.
    Populates recommendation field with:
    - Reach out immediately
    - Research further
    - Monitor for next year
    """
    
    name = "event_prioritization"
    description = "Prioritizes events and provides sponsorship recommendations"
    
    # Target industries for recommendation logic
    TARGET_INDUSTRIES = ["fintech", "payments", "ai", "artificial intelligence"]
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Prioritize events and generate recommendations."""
        self.validate_input(input_data)
        
        # Get events from context
        events = input_data.context.get("events", [])
        
        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": [], "message": "No events to prioritize"},
                metadata={"agent": self.name, "event_count": 0}
            )
        
        logger.info(f"Prioritizing {len(events)} events")
        
        # Sort events by score and tier
        prioritized_events = self._prioritize_events(events)
        
        # Add recommendations
        recommended_events = []
        for event in prioritized_events:
            recommended = self._add_recommendation(event)
            recommended_events.append(recommended)
        
        return AgentOutput(
            agent_name=self.name,
            findings={"events": recommended_events},
            metadata={"agent": self.name, "event_count": len(recommended_events)}
        )
    
    def _prioritize_events(self, events: list) -> list:
        """Sort events by priority."""
        
        # Define tier order
        tier_order = {
            "Tier 1 - Must Sponsor": 1,
            "Tier 2 - Strong Opportunity": 2,
            "Tier 3 - Optional": 3,
            "Tier 4 - Low Priority": 4
        }
        
        def sort_key(event):
            tier = event.get("priority_tier", "Tier 4 - Low Priority")
            score = float(event.get("overall_score") or 0)
            
            return (
                tier_order.get(tier, 5),  # Sort by tier first
                -score  # Then by score descending
            )
        
        return sorted(events, key=sort_key)
    
    def _add_recommendation(self, event: dict) -> dict:
        """Add recommendation based on event attributes."""
        tier = event.get("priority_tier", "")
        score = float(event.get("overall_score") or 0)
        theme = event.get("theme", "").lower()
        country = event.get("country", "").lower()
        
        # High priority industries
        is_target_industry = any(ind in theme for ind in self.TARGET_INDUSTRIES)
        
        # High priority regions
        is_target_region = any(r in country for r in ["usa", "uk", "singapore", "dubai", "india"])
        
        # Determine recommendation
        if "Tier 1" in tier and score >= 8:
            recommendation = "Reach out immediately"
        elif "Tier 1" in tier or (score >= 7 and is_target_industry):
            recommendation = "Reach out immediately"
        elif "Tier 2" in tier or (score >= 6 and is_target_industry and is_target_region):
            recommendation = "Research further"
        elif "Tier 2" in tier and is_target_industry:
            recommendation = "Research further"
        elif "Tier 3" in tier:
            recommendation = "Research further"
        else:
            recommendation = "Monitor for next year"
        
        event["recommendation"] = recommendation
        event["status"] = "Prioritized"
        
        return event
