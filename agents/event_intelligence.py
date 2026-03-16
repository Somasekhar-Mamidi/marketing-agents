"""Event Intelligence Agent - Strategic analysis of events for sponsorship."""

import logging
from agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class EventIntelligenceAgent(BaseAgent):
    """Provides strategic market intelligence for event sponsorship.
    
    Analyzes each event to determine:
    - attendee_roles: Who attends (CTOs, Developers, etc.)
    - companies_attending: Key companies
    - strategic_value: Why sponsor
    - potential_roi: Expected return on investment
    - ideal_sponsorship_format: Best sponsorship type
    """
    
    name = "event_intelligence"
    description = "Strategic analysis of events for sponsorship"
    
    # Known event patterns and their typical audiences
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
        """Analyze events for strategic intelligence."""
        self.validate_input(input_data)
        
        # Get events from context
        events = input_data.context.get("events", [])
        
        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={"events": [], "message": "No events to analyze"},
                metadata={"agent": self.name, "event_count": 0}
            )
        
        logger.info(f"Analyzing {len(events)} events for strategic intelligence")
        
        analyzed_events = []
        
        for event in events:
            analyzed_event = self._analyze_event(event)
            analyzed_events.append(analyzed_event)
        
        return AgentOutput(
            agent_name=self.name,
            findings={"events": analyzed_events},
            metadata={"agent": self.name, "event_count": len(analyzed_events)}
        )
    
    def _analyze_event(self, event: dict) -> dict:
        """Analyze a single event for strategic intelligence."""
        theme = event.get("theme", "").lower()
        event_name = event.get("event_name", "").lower()
        country = event.get("country", "").lower()
        
        # Determine audience type
        audience_info = self._get_audience_info(theme)
        
        # Set attendee roles
        event["attendee_roles"] = audience_info.get("roles", "Technology professionals")
        
        # Set companies attending
        event["companies_attending"] = audience_info.get("companies", "Various")
        
        # Calculate strategic value
        event["strategic_value"] = self._calculate_strategic_value(
            event.get("priority_tier", ""),
            event.get("overall_score", ""),
            theme
        )
        
        # Calculate potential ROI
        event["potential_roi"] = self._calculate_potential_roi(
            event.get("priority_tier", ""),
            country
        )
        
        # Determine ideal sponsorship format
        event["ideal_sponsorship_format"] = self._determine_sponsorship_format(
            event.get("priority_tier", ""),
            theme
        )
        
        event["status"] = "Intelligence Analyzed"
        
        return event
    
    def _get_audience_info(self, theme: str) -> dict:
        """Get audience information based on theme."""
        for key, info in self.EVENT_AUDIENCES.items():
            if key in theme:
                return info
        return self.EVENT_AUDIENCES.get("technology", {})
    
    def _calculate_strategic_value(self, tier: str, score: str, theme: str) -> str:
        """Calculate strategic value of sponsoring the event."""
        score_val = float(score) if score else 5.0
        
        tier_bonus = 0
        if "Tier 1" in tier:
            tier_bonus = 2
        elif "Tier 2" in tier:
            tier_bonus = 1
        
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
        else:
            return (
                f"Moderate sponsorship value. {theme.title()} event with niche audience. "
                "Consider for specific regional or audience targeting."
            )
    
    def _calculate_potential_roi(self, tier: str, country: str) -> str:
        """Calculate potential ROI estimate."""
        # Regional ROI factors
        roi_multiplier = 1.0
        
        high_roi_regions = ["usa", "united states", "uk", "singapore", "dubai"]
        if any(r in country for r in high_roi_regions):
            roi_multiplier = 1.5
        
        if "Tier 1" in tier:
            return (
                f"High ROI expected. Tier 1 events attract senior attendees with "
                f"high purchasing authority. Estimated lead generation: 50+ qualified leads."
            )
        elif "Tier 2" in tier:
            return (
                f"Good ROI expected. Tier 2 events provide solid brand exposure "
                "and lead generation opportunities. Estimated 25-50 qualified leads."
            )
        else:
            return (
                f"Moderate ROI. Tier 3/4 events good for brand awareness and "
                "niche targeting. Estimated 10-25 leads."
            )
    
    def _determine_sponsorship_format(self, tier: str, theme: str) -> str:
        """Determine the ideal sponsorship format."""
        if "Tier 1" in tier:
            return (
                "Gold/Platinum Sponsorship with booth, speaking slot, "
                "logo placement, and dedicated networking session"
            )
        elif "Tier 2" in tier:
            return (
                "Silver Sponsorship with booth, logo on website and materials, "
                "networking access"
            )
        else:
            return (
                "Bronze Sponsorship or exhibitor booth with basic branding"
            )
