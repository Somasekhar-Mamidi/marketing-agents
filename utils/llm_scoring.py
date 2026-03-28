"""LLM-based dynamic scoring for events."""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown."""
    audience_relevance: float
    industry_reputation: float
    attendance: float
    sponsor_value: float
    regional_importance: float
    explanation: str


class LLMEventScorer:
    """Uses LLM to dynamically score events based on detailed criteria."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.use_llm = api_key is not None
    
    def score_event(self, event: Dict) -> Dict:
        """Score an event using LLM or fallback to rules.
        
        Args:
            event: Event dictionary with available information
            
        Returns:
            Dictionary with scores and explanation
        """
        if self.use_llm:
            try:
                return self._score_with_llm(event)
            except Exception as e:
                logger.warning(f"LLM scoring failed, using fallback: {e}")
        
        return self._score_with_rules(event)
    
    def _score_with_llm(self, event: Dict) -> Dict:
        """Score event using LLM API."""
        # Placeholder for LLM integration
        # In production, this would call OpenAI, Anthropic, etc.
        
        prompt = self._build_scoring_prompt(event)
        
        # Mock LLM response for now
        # Replace with actual API call:
        # response = openai.ChatCompletion.create(...)
        
        logger.info(f"Would call LLM with prompt length: {len(prompt)}")
        
        # Fallback to rules for now
        return self._score_with_rules(event)
    
    def _build_scoring_prompt(self, event: Dict) -> str:
        """Build prompt for LLM scoring."""
        return f"""
        Score this event for sponsorship potential (1-10 scale):
        
        Event: {event.get('event_name', 'Unknown')}
        Theme: {event.get('theme', 'Unknown')}
        Location: {event.get('city', '')}, {event.get('country', '')}
        Summary: {event.get('summary', 'N/A')}
        Target Audience: {event.get('target_audience', 'N/A')}
        Industry Focus: {event.get('industry_focus', 'N/A')}
        
        Score on:
        1. Audience Relevance - How well does audience match our target?
        2. Industry Reputation - How prestigious is this event?
        3. Attendance - Expected attendance quality/quantity
        4. Sponsor Value - Visibility and ROI potential
        5. Regional Importance - Strategic value of the region
        
        Return JSON with scores and brief explanation.
        """
    
    def _score_with_rules(self, event: Dict) -> Dict:
        """Score event using rule-based system (fallback)."""
        theme = event.get('theme', '').lower()
        event_name = event.get('event_name', '').lower()
        country = event.get('country', '').lower()
        
        # Audience relevance
        audience_score = self._calculate_audience_relevance(theme)
        
        # Industry reputation
        reputation_score = self._calculate_reputation(event_name, theme)
        
        # Attendance estimate
        attendance_score = self._estimate_attendance(event)
        
        # Sponsor value
        sponsor_score = self._calculate_sponsor_value(event)
        
        # Regional importance
        regional_score = self._calculate_regional_importance(country)
        
        # Calculate weighted overall score
        overall = (
            audience_score * 0.25 +
            reputation_score * 0.25 +
            attendance_score * 0.20 +
            sponsor_score * 0.15 +
            regional_score * 0.15
        )
        
        explanation = self._generate_explanation(
            audience_score, reputation_score, attendance_score,
            sponsor_score, regional_score, theme
        )
        
        return {
            'audience_relevance_score': str(audience_score),
            'industry_reputation_score': str(reputation_score),
            'attendance_score': str(attendance_score),
            'sponsor_value_score': str(sponsor_score),
            'regional_importance_score': str(regional_score),
            'overall_score': str(round(overall, 1)),
            'scoring_method': 'rules',
            'explanation': explanation
        }
    
    def _calculate_audience_relevance(self, theme: str) -> float:
        """Calculate audience relevance score."""
        target_keywords = ['fintech', 'payments', 'ai', 'artificial intelligence', 'technology']
        
        for keyword in target_keywords:
            if keyword in theme:
                return 9.0
        
        related_keywords = ['software', 'developer', 'engineering', 'cloud', 'data']
        for keyword in related_keywords:
            if keyword in theme:
                return 7.5
        
        return 5.0
    
    def _calculate_reputation(self, event_name: str, theme: str) -> float:
        """Calculate industry reputation score."""
        # High prestige indicators
        prestige_terms = ['world', 'global', 'international', 'summit', 'premier']
        for term in prestige_terms:
            if term in event_name:
                return 9.0
        
        # Medium prestige
        medium_terms = ['conference', 'expo', 'forum', 'congress']
        for term in medium_terms:
            if term in event_name:
                return 7.0
        
        return 5.5
    
    def _estimate_attendance(self, event: Dict) -> float:
        """Estimate attendance score based on available data."""
        summary = event.get('summary', '').lower()
        
        # Look for attendance indicators
        if any(term in summary for term in ['10000', '10,000', 'thousands', 'major']):
            return 9.0
        elif any(term in summary for term in ['5000', '5,000', 'large']):
            return 7.5
        elif any(term in summary for term in ['1000', '1,000', 'medium']):
            return 6.0
        
        # Default based on event type
        return 5.5
    
    def _calculate_sponsor_value(self, event: Dict) -> float:
        """Calculate sponsor value score."""
        # Check for sponsorship info
        if event.get('sponsorship_url') and event['sponsorship_url'] != 'Not Found':
            return 7.5
        
        if event.get('contact_email') and event['contact_email'] != 'Not Found':
            return 6.5
        
        return 5.0
    
    def _calculate_regional_importance(self, country: str) -> float:
        """Calculate regional importance score."""
        tier1 = ['usa', 'united states', 'uk', 'singapore', 'dubai']
        tier2 = ['germany', 'france', 'canada', 'australia', 'japan', 'india']
        
        if any(t in country for t in tier1):
            return 8.5
        elif any(t in country for t in tier2):
            return 7.0
        
        return 5.0
    
    def _generate_explanation(
        self,
        audience: float,
        reputation: float,
        attendance: float,
        sponsor: float,
        regional: float,
        theme: str
    ) -> str:
        """Generate human-readable explanation of scores."""
        overall = (audience * 0.25 + reputation * 0.25 + attendance * 0.20 + 
                   sponsor * 0.15 + regional * 0.15)
        
        if overall >= 8.0:
            tier = "Tier 1 - Must Sponsor"
        elif overall >= 6.0:
            tier = "Tier 2 - Strong Opportunity"
        elif overall >= 4.0:
            tier = "Tier 3 - Optional"
        else:
            tier = "Tier 4 - Low Priority"
        
        return (
            f"Event scored {overall:.1f}/10 ({tier}). "
            f"Strong audience match ({audience}/10) for {theme}. "
            f"Reputation: {reputation}/10, "
            f"Attendance: {attendance}/10, "
            f"Sponsor Value: {sponsor}/10, "
            f"Regional Importance: {regional}/10."
        )


def score_event_with_llm(event: Dict, api_key: Optional[str] = None) -> Dict:
    """Convenience function to score an event."""
    scorer = LLMEventScorer(api_key=api_key)
    return scorer.score_event(event)
