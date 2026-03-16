"""Shared JSON schema for event research pipeline."""

# This is the master schema used by all agents in the pipeline
# Each agent receives this schema, updates relevant fields, and passes it to the next agent

EVENT_SCHEMA = {
    "events": [
        {
            # Discovery fields (Agent 1)
            "event_name": "",
            "event_website": "",
            "city": "",
            "country": "",
            "expected_date": "",
            "theme": "",
            "organizer": "",
            
            # Website scraping fields (Agent 3)
            "start_date": "",
            "end_date": "",
            "contact_email": "",
            "contact_url": "",
            "sponsorship_url": "",
            "summary": "",
            "industry_focus": "",
            "target_audience": "",
            "technology_themes": "",
            
            # Qualification fields (Agent 2)
            "audience_relevance_score": "",
            "industry_reputation_score": "",
            "attendance_score": "",
            "sponsor_value_score": "",
            "regional_importance_score": "",
            "overall_score": "",
            "priority_tier": "",
            
            # Intelligence fields (Agent 4)
            "attendee_roles": "",
            "companies_attending": "",
            "strategic_value": "",
            "potential_roi": "",
            "ideal_sponsorship_format": "",
            
            # Prioritization fields (Agent 5)
            "recommendation": "",
            
            # Outreach fields (Agent 6)
            "outreach_subject": "",
            "outreach_email": "",
            
            # Status
            "status": "Researching"
        }
    ]
}

# Empty schema for starting the pipeline
def get_empty_schema() -> dict:
    """Return an empty schema to start the pipeline."""
    return {"events": []}
