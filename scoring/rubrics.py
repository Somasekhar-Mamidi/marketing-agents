"""100-point detailed scoring rubrics for events."""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ScoringCriterion:
    """Individual scoring criterion."""
    name: str
    weight: float  # Weight in final score (0-100)
    max_points: int
    description: str


class EventScoringRubrics:
    """100-point scoring system with detailed rubrics."""
    
    # Define criteria with weights (must sum to 100)
    CRITERIA = {
        'audience_quality': ScoringCriterion(
            name='Audience Quality & Relevance',
            weight=25.0,
            max_points=25,
            description='Quality and relevance of attendees to our target market'
        ),
        'event_reputation': ScoringCriterion(
            name='Event Reputation & History',
            weight=20.0,
            max_points=20,
            description='Prestige, history, and industry standing of the event'
        ),
        'sponsorship_roi': ScoringCriterion(
            name='Sponsorship ROI Potential',
            weight=20.0,
            max_points=20,
            description='Expected return on sponsorship investment'
        ),
        'strategic_alignment': ScoringCriterion(
            name='Strategic Alignment',
            weight=15.0,
            max_points=15,
            description='Alignment with company goals and messaging'
        ),
        'geographic_relevance': ScoringCriterion(
            name='Geographic Relevance',
            weight=10.0,
            max_points=10,
            description='Strategic importance of event location'
        ),
        'competitive_presence': ScoringCriterion(
            name='Competitive Presence',
            weight=10.0,
            max_points=10,
            description='Presence of competitors and industry leaders'
        )
    }
    
    @classmethod
    def score_event(cls, event: Dict) -> Dict:
        """Score an event using detailed rubrics.
        
        Returns:
            Dictionary with scores and breakdown
        """
        scores = {}
        explanations = {}
        
        # Score each criterion
        scores['audience_quality'], explanations['audience_quality'] = cls._score_audience_quality(event)
        scores['event_reputation'], explanations['event_reputation'] = cls._score_event_reputation(event)
        scores['sponsorship_roi'], explanations['sponsorship_roi'] = cls._score_sponsorship_roi(event)
        scores['strategic_alignment'], explanations['strategic_alignment'] = cls._score_strategic_alignment(event)
        scores['geographic_relevance'], explanations['geographic_relevance'] = cls._score_geographic_relevance(event)
        scores['competitive_presence'], explanations['competitive_presence'] = cls._score_competitive_presence(event)
        
        # Calculate weighted total
        total_score = sum(
            scores[criterion] * (cls.CRITERIA[criterion].weight / cls.CRITERIA[criterion].max_points)
            for criterion in scores
        )
        
        # Determine tier
        tier = cls._determine_tier(total_score)
        
        return {
            'total_score': round(total_score, 1),
            'max_score': 100,
            'tier': tier,
            'criteria_scores': scores,
            'explanations': explanations,
            'scoring_method': '100_point_rubric'
        }
    
    @classmethod
    def _score_audience_quality(cls, event: Dict) -> Tuple[int, str]:
        """Score audience quality (0-25 points)."""
        score = 0
        reasons = []
        
        theme = event.get('theme', '').lower()
        target_audience = event.get('target_audience', '').lower()
        
        # Target industry match (0-10)
        if any(kw in theme for kw in ['fintech', 'payments', 'financial']):
            score += 10
            reasons.append('Direct industry match (fintech/payments)')
        elif any(kw in theme for kw in ['technology', 'software', 'ai']):
            score += 7
            reasons.append('Related technology industry')
        else:
            score += 3
            reasons.append('Indirect industry relevance')
        
        # Decision maker presence (0-8)
        if any(kw in target_audience for kw in ['cto', 'ceo', 'vp', 'director', 'executive']):
            score += 8
            reasons.append('Senior decision makers present')
        elif any(kw in target_audience for kw in ['developer', 'engineer', 'manager']):
            score += 5
            reasons.append('Technical professionals present')
        else:
            score += 2
            reasons.append('General audience')
        
        # Audience size indication (0-7)
        summary = event.get('summary', '').lower()
        if any(kw in summary for kw in ['10,000', '10000', 'large', 'major']):
            score += 7
            reasons.append('Large audience (>10k)')
        elif any(kw in summary for kw in ['5000', '5,000', 'medium']):
            score += 5
            reasons.append('Medium audience (5-10k)')
        else:
            score += 3
            reasons.append('Audience size unknown')
        
        return score, '; '.join(reasons)
    
    @classmethod
    def _score_event_reputation(cls, event: Dict) -> Tuple[int, str]:
        """Score event reputation (0-20 points)."""
        score = 0
        reasons = []
        
        name = event.get('event_name', '').lower()
        
        # Event tier (0-10)
        if any(kw in name for kw in ['world', 'global', 'international', 'premier']):
            score += 10
            reasons.append('Global/premier event')
        elif any(kw in name for kw in ['summit', 'congress', 'conference']):
            score += 7
            reasons.append('Major conference')
        elif any(kw in name for kw in ['expo', 'forum', 'show']):
            score += 5
            reasons.append('Industry expo/forum')
        else:
            score += 3
            reasons.append('Regional/local event')
        
        # History indication (0-5)
        summary = event.get('summary', '').lower()
        if any(kw in summary for kw in ['annual', 'years', 'edition', 'established']):
            score += 5
            reasons.append('Established recurring event')
        else:
            score += 2
            reasons.append('New or unknown event')
        
        # Speaker quality (0-5)
        if 'keynote' in summary or 'speaker' in summary:
            score += 5
            reasons.append('Notable speakers mentioned')
        else:
            score += 2
            reasons.append('Speaker info unavailable')
        
        return score, '; '.join(reasons)
    
    @classmethod
    def _score_sponsorship_roi(cls, event: Dict) -> Tuple[int, str]:
        """Score sponsorship ROI potential (0-20 points)."""
        score = 0
        reasons = []
        
        # Branding opportunities (0-7)
        if event.get('sponsorship_url') and event['sponsorship_url'] != 'Not Found':
            score += 7
            reasons.append('Sponsorship info available')
        elif event.get('contact_email') and event['contact_email'] != 'Not Found':
            score += 4
            reasons.append('Contact available, sponsorship info unclear')
        else:
            score += 1
            reasons.append('Limited sponsorship info')
        
        # Lead generation potential (0-7)
        tier = event.get('priority_tier', '')
        if 'Tier 1' in tier:
            score += 7
            reasons.append('High-value audience (Tier 1)')
        elif 'Tier 2' in tier:
            score += 5
            reasons.append('Good audience value (Tier 2)')
        else:
            score += 3
            reasons.append('Moderate audience value')
        
        # Cost efficiency (0-6) - based on region
        country = event.get('country', '').lower()
        if any(kw in country for kw in ['usa', 'uk', 'germany']):
            score += 4  # Higher cost but good ROI
            reasons.append('Established market (higher cost, proven ROI)')
        elif any(kw in country for kw in ['india', 'singapore', 'dubai']):
            score += 6  # Emerging market, good value
            reasons.append('Emerging market (good value)')
        else:
            score += 3
            reasons.append('ROI uncertain')
        
        return score, '; '.join(reasons)
    
    @classmethod
    def _score_strategic_alignment(cls, event: Dict) -> Tuple[int, str]:
        """Score strategic alignment (0-15 points)."""
        score = 0
        reasons = []
        
        theme = event.get('theme', '').lower()
        
        # Product alignment (0-8)
        if any(kw in theme for kw in ['payments', 'fintech', 'financial']):
            score += 8
            reasons.append('Direct product alignment')
        elif any(kw in theme for kw in ['api', 'platform', 'infrastructure']):
            score += 6
            reasons.append('Technology alignment')
        else:
            score += 3
            reasons.append('General alignment')
        
        # Messaging fit (0-7)
        industry_focus = event.get('industry_focus', '').lower()
        if any(kw in industry_focus for kw in ['innovation', 'future', 'transformation']):
            score += 7
            reasons.append('Forward-thinking messaging fit')
        else:
            score += 4
            reasons.append('Standard industry messaging')
        
        return score, '; '.join(reasons)
    
    @classmethod
    def _score_geographic_relevance(cls, event: Dict) -> Tuple[int, str]:
        """Score geographic relevance (0-10 points)."""
        score = 0
        reasons = []
        
        country = event.get('country', '').lower()
        city = event.get('city', '').lower()
        
        # Market priority (0-6)
        priority_markets = ['usa', 'united states', 'uk', 'singapore', 'dubai']
        secondary_markets = ['germany', 'france', 'canada', 'australia', 'india']
        
        if any(m in country for m in priority_markets):
            score += 6
            reasons.append('Priority market')
        elif any(m in country for m in secondary_markets):
            score += 4
            reasons.append('Secondary market')
        else:
            score += 2
            reasons.append('Tertiary market')
        
        # Tech hub (0-4)
        tech_hubs = ['san francisco', 'new york', 'london', 'singapore', 'dubai', 'berlin']
        if any(hub in city for hub in tech_hubs):
            score += 4
            reasons.append('Major tech hub')
        else:
            score += 2
            reasons.append('Standard location')
        
        return score, '; '.join(reasons)
    
    @classmethod
    def _score_competitive_presence(cls, event: Dict) -> Tuple[int, str]:
        """Score competitive presence (0-10 points)."""
        score = 0
        reasons = []
        
        # Based on event tier and past sponsors if available
        tier = event.get('priority_tier', '')
        
        if 'Tier 1' in tier:
            score += 10
            reasons.append('Tier 1 event - competitors definitely present')
        elif 'Tier 2' in tier:
            score += 7
            reasons.append('Tier 2 event - likely competitor presence')
        else:
            score += 4
            reasons.append('Lower tier - competitor presence uncertain')
        
        return score, reasons[0] if reasons else 'Unknown'
    
    @classmethod
    def _determine_tier(cls, total_score: float) -> str:
        """Determine tier based on total score."""
        if total_score >= 80:
            return "Tier 1 - Must Sponsor (80-100)"
        elif total_score >= 60:
            return "Tier 2 - Strong Opportunity (60-79)"
        elif total_score >= 40:
            return "Tier 3 - Optional (40-59)"
        else:
            return "Tier 4 - Low Priority (0-39)"
    
    @classmethod
    def get_rubric_summary(cls) -> str:
        """Get human-readable summary of scoring rubrics."""
        summary = "# Event Scoring Rubrics (100-Point System)\n\n"
        
        for key, criterion in cls.CRITERIA.items():
            summary += f"## {criterion.name} (Max: {criterion.max_points} points)\n"
            summary += f"{criterion.description}\n\n"
        
        summary += "## Tier Thresholds\n"
        summary += "- **Tier 1**: 80-100 points (Must Sponsor)\n"
        summary += "- **Tier 2**: 60-79 points (Strong Opportunity)\n"
        summary += "- **Tier 3**: 40-59 points (Optional)\n"
        summary += "- **Tier 4**: 0-39 points (Low Priority)\n"
        
        return summary
