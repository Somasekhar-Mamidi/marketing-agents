"""Pydantic schema validation for events and agent data."""

from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, HttpUrl


class EventStatus(str, Enum):
    """Event processing status."""
    DISCOVERED = "Discovered"
    QUALIFIED = "Qualified"
    WEBSITE_SCRAPED = "Website Scraped"
    INTELLIGENCE_ANALYZED = "Intelligence Analyzed"
    PRIORITIZED = "Prioritized"
    OUTREACH_READY = "Outreach Ready"


class PriorityTier(str, Enum):
    """Priority tier classification."""
    TIER_1 = "Tier 1 - Must Sponsor"
    TIER_2 = "Tier 2 - Strong Opportunity"
    TIER_3 = "Tier 3 - Optional"
    TIER_4 = "Tier 4 - Low Priority"


class EventSchema(BaseModel):
    """Complete event schema with validation."""
    
    # Discovery fields
    event_name: str = Field(..., min_length=1, description="Name of the event")
    event_website: str = Field(..., description="Event website URL")
    city: Optional[str] = Field(None, description="City where event takes place")
    country: Optional[str] = Field(None, description="Country where event takes place")
    expected_date: Optional[str] = Field(None, description="Expected event date (string)")
    theme: str = Field(..., description="Event theme/industry")
    organizer: Optional[str] = Field(None, description="Event organizer")
    
    # Website scraping fields
    start_date: Optional[str] = Field(None, description="Event start date")
    end_date: Optional[str] = Field(None, description="Event end date")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_url: Optional[str] = Field(None, description="Contact page URL")
    sponsorship_url: Optional[str] = Field(None, description="Sponsorship page URL")
    summary: Optional[str] = Field(None, description="Event summary")
    industry_focus: Optional[str] = Field(None, description="Industry focus")
    target_audience: Optional[str] = Field(None, description="Target audience")
    technology_themes: Optional[str] = Field(None, description="Technology themes")
    
    # Qualification fields
    audience_relevance_score: Optional[str] = Field(None, description="Audience relevance score")
    industry_reputation_score: Optional[str] = Field(None, description="Industry reputation score")
    attendance_score: Optional[str] = Field(None, description="Attendance score")
    sponsor_value_score: Optional[str] = Field(None, description="Sponsor value score")
    regional_importance_score: Optional[str] = Field(None, description="Regional importance score")
    overall_score: Optional[str] = Field(None, description="Overall score")
    priority_tier: Optional[PriorityTier] = Field(None, description="Priority tier")
    
    # Intelligence fields
    attendee_roles: Optional[str] = Field(None, description="Typical attendee roles")
    companies_attending: Optional[str] = Field(None, description="Companies that attend")
    strategic_value: Optional[str] = Field(None, description="Strategic value of sponsorship")
    potential_roi: Optional[str] = Field(None, description="Potential ROI estimate")
    ideal_sponsorship_format: Optional[str] = Field(None, description="Ideal sponsorship format")
    
    # Prioritization fields
    recommendation: Optional[str] = Field(None, description="Sponsorship recommendation")
    
    # Outreach fields
    outreach_subject: Optional[str] = Field(None, description="Outreach email subject")
    outreach_email: Optional[str] = Field(None, description="Outreach email body")
    
    # Status
    status: EventStatus = Field(default=EventStatus.DISCOVERED, description="Event status")
    
    @validator('overall_score')
    def validate_score(cls, v):
        """Validate that score is between 0 and 10."""
        if v is None or v == "":
            return v
        try:
            score = float(v)
            if not 0 <= score <= 10:
                raise ValueError('Score must be between 0 and 10')
        except ValueError:
            pass  # Allow non-numeric strings for compatibility
        return v
    
    @validator('event_website')
    def validate_url(cls, v):
        """Validate URL format."""
        if v and not v.startswith(('http://', 'https://')):
            return f"https://{v}"
        return v
    
    class Config:
        use_enum_values = True


class AgentInputSchema(BaseModel):
    """Schema for agent input validation."""
    
    query: str = Field(..., min_length=1, description="The research query")
    context: dict = Field(default_factory=dict, description="Context from previous agents")
    parameters: dict = Field(default_factory=dict, description="Agent-specific parameters")
    
    @validator('query')
    def validate_query(cls, v):
        """Ensure query is not empty after stripping."""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class AgentOutputSchema(BaseModel):
    """Schema for agent output validation."""
    
    agent_name: str = Field(..., min_length=1, description="Name of the agent")
    findings: dict = Field(default_factory=dict, description="Research findings")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    status: str = Field(default="success", description="Execution status")
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        allowed = ['success', 'partial', 'error', 'failed']
        if v.lower() not in allowed:
            raise ValueError(f'Status must be one of {allowed}')
        return v.lower()


class EventsListSchema(BaseModel):
    """Schema for a list of events."""
    
    events: List[EventSchema] = Field(default_factory=list, description="List of events")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


def validate_event(event_data: dict) -> EventSchema:
    """Validate event data against schema.
    
    Args:
        event_data: Dictionary containing event data
        
    Returns:
        Validated EventSchema
        
    Raises:
        ValidationError: If data is invalid
    """
    return EventSchema(**event_data)


def validate_events(events_data: List[dict]) -> List[EventSchema]:
    """Validate a list of events.
    
    Args:
        events_data: List of event dictionaries
        
    Returns:
        List of validated EventSchema objects
    """
    return [validate_event(e) for e in events_data]


def validate_agent_input(input_data: dict) -> AgentInputSchema:
    """Validate agent input data.
    
    Args:
        input_data: Dictionary containing agent input
        
    Returns:
        Validated AgentInputSchema
    """
    return AgentInputSchema(**input_data)


def validate_agent_output(output_data: dict) -> AgentOutputSchema:
    """Validate agent output data.
    
    Args:
        output_data: Dictionary containing agent output
        
    Returns:
        Validated AgentOutputSchema
    """
    return AgentOutputSchema(**output_data)


def sanitize_event_for_storage(event: dict) -> dict:
    """Sanitize event data before storage.
    
    Removes or truncates fields that are too large.
    
    Args:
        event: Event dictionary
        
    Returns:
        Sanitized event dictionary
    """
    sanitized = event.copy()
    
    # Truncate long fields
    max_lengths = {
        'summary': 2000,
        'outreach_email': 5000,
        'strategic_value': 1000,
        'potential_roi': 1000
    }
    
    for field, max_len in max_lengths.items():
        if field in sanitized and sanitized[field]:
            if len(str(sanitized[field])) > max_len:
                sanitized[field] = str(sanitized[field])[:max_len] + "..."
    
    return sanitized
