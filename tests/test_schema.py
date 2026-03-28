"""Tests for Schema module."""

import pytest
from schema import EVENT_SCHEMA, get_empty_schema, get_initialized_schema


class TestSchema:
    """Test cases for schema module."""
    
    def test_event_schema_exists(self):
        """Test that EVENT_SCHEMA is defined."""
        assert EVENT_SCHEMA is not None
        assert "events" in EVENT_SCHEMA
    
    def test_event_schema_has_events_list(self):
        """Test that EVENT_SCHEMA has events list."""
        assert isinstance(EVENT_SCHEMA["events"], list)
        assert len(EVENT_SCHEMA["events"]) > 0
    
    def test_event_schema_has_required_fields(self):
        """Test that EVENT_SCHEMA has all required fields."""
        event_fields = EVENT_SCHEMA["events"][0].keys()
        
        required_fields = [
            "event_name", "event_website", "city", "country",
            "expected_date", "theme", "organizer"
        ]
        
        for field in required_fields:
            assert field in event_fields
    
    def test_event_schema_has_qualification_fields(self):
        """Test that EVENT_SCHEMA has qualification fields."""
        event_fields = EVENT_SCHEMA["events"][0].keys()
        
        qualification_fields = [
            "audience_relevance_score", "industry_reputation_score",
            "attendance_score", "sponsor_value_score",
            "regional_importance_score", "overall_score", "priority_tier"
        ]
        
        for field in qualification_fields:
            assert field in event_fields
    
    def test_event_schema_has_intelligence_fields(self):
        """Test that EVENT_SCHEMA has intelligence fields."""
        event_fields = EVENT_SCHEMA["events"][0].keys()
        
        intelligence_fields = [
            "attendee_roles", "companies_attending",
            "strategic_value", "potential_roi",
            "ideal_sponsorship_format"
        ]
        
        for field in intelligence_fields:
            assert field in event_fields
    
    def test_event_schema_has_outreach_fields(self):
        """Test that EVENT_SCHEMA has outreach fields."""
        event_fields = EVENT_SCHEMA["events"][0].keys()
        
        assert "outreach_subject" in event_fields
        assert "outreach_email" in event_fields
    
    def test_event_schema_has_website_fields(self):
        """Test that EVENT_SCHEMA has website scraping fields."""
        event_fields = EVENT_SCHEMA["events"][0].keys()
        
        website_fields = [
            "start_date", "end_date", "contact_email",
            "contact_url", "sponsorship_url", "summary"
        ]
        
        for field in website_fields:
            assert field in event_fields


class TestGetEmptySchema:
    """Test cases for get_empty_schema function."""
    
    def test_returns_dict(self):
        """Test that get_empty_schema returns a dict."""
        result = get_empty_schema()
        assert isinstance(result, dict)
    
    def test_returns_events_key(self):
        """Test that result has events key."""
        result = get_empty_schema()
        assert "events" in result
    
    def test_returns_empty_list(self):
        """Test that events is empty list."""
        result = get_empty_schema()
        assert result["events"] == []
    
    def test_no_metadata(self):
        """Test that empty schema has no metadata."""
        result = get_empty_schema()
        assert len(result) == 1


class TestGetInitializedSchema:
    """Test cases for get_initialized_schema function."""
    
    def test_returns_dict(self):
        """Test that get_initialized_schema returns a dict."""
        result = get_initialized_schema()
        assert isinstance(result, dict)
    
    def test_returns_events_key(self):
        """Test that result has events key."""
        result = get_initialized_schema()
        assert "events" in result
    
    def test_returns_metadata(self):
        """Test that result has metadata."""
        result = get_initialized_schema()
        assert "metadata" in result
    
    def test_metadata_has_industry(self):
        """Test that metadata contains industry."""
        result = get_initialized_schema(industry="Payments")
        assert result["metadata"]["industry"] == "Payments"
    
    def test_metadata_has_region(self):
        """Test that metadata contains region."""
        result = get_initialized_schema(region="Middle East")
        assert result["metadata"]["region"] == "Middle East"
    
    def test_metadata_has_theme(self):
        """Test that metadata contains theme."""
        result = get_initialized_schema(theme="FinTech")
        assert result["metadata"]["theme"] == "FinTech"
    
    def test_metadata_has_time_range(self):
        """Test that metadata contains time_range."""
        result = get_initialized_schema(time_range="24")
        assert result["metadata"]["time_range_months"] == "24"
    
    def test_metadata_has_version(self):
        """Test that metadata has schema version."""
        result = get_initialized_schema()
        assert result["metadata"]["schema_version"] == "1.0"
    
    def test_metadata_has_initialized_flag(self):
        """Test that metadata has initialized flag."""
        result = get_initialized_schema()
        assert result["metadata"]["initialized"] is True
    
    def test_default_values(self):
        """Test default values for empty inputs."""
        result = get_initialized_schema()
        
        assert result["metadata"]["industry"] == ""
        assert result["metadata"]["region"] == ""
        assert result["metadata"]["theme"] == ""
        assert result["metadata"]["time_range_months"] == "12"
    
    def test_empty_events_list(self):
        """Test that events is empty list."""
        result = get_initialized_schema()
        assert result["events"] == []
