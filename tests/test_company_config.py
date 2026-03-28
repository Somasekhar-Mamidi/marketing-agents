"""Tests for company configuration."""

import pytest
import os
from unittest.mock import patch
from config.company_config import CompanyConfig, CompanyConfigLoader, get_company_config, reset_company_config


class TestCompanyConfig:
    """Test suite for CompanyConfig."""
    
    def test_company_config_creation(self):
        """Test creating a CompanyConfig instance."""
        config = CompanyConfig(
            name="Test Company",
            website="https://test.com",
            contact_name="John Doe",
            contact_title="CEO",
            contact_email="john@test.com",
            value_proposition="We test things"
        )
        
        assert config.name == "Test Company"
        assert config.website == "https://test.com"
        assert config.contact_name == "John Doe"


class TestCompanyConfigLoader:
    """Test suite for CompanyConfigLoader."""
    
    @patch.dict(os.environ, {
        "COMPANY_NAME": "Acme Corp",
        "COMPANY_WEBSITE": "https://acme.com",
        "CONTACT_NAME": "Jane Smith",
        "CONTACT_TITLE": "Marketing Director",
        "CONTACT_EMAIL": "jane@acme.com",
        "COMPANY_VALUE_PROP": "Best in class"
    }, clear=True)
    def test_load_from_env(self):
        """Test loading config from environment variables."""
        config = CompanyConfigLoader.load()
        
        assert config.name == "Acme Corp"
        assert config.website == "https://acme.com"
        assert config.contact_name == "Jane Smith"
        assert config.contact_title == "Marketing Director"
        assert config.contact_email == "jane@acme.com"
        assert config.value_proposition == "Best in class"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_defaults(self):
        """Test loading config with defaults when env vars missing."""
        config = CompanyConfigLoader.load()
        
        assert config.name == "Your Company"
        assert config.website is None
        assert config.contact_name is None
    
    @patch.dict(os.environ, {"COMPANY_NAME": "Test Company"}, clear=True)
    def test_is_configured_true(self):
        """Test is_configured returns True when company name set."""
        assert CompanyConfigLoader.is_configured() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_is_configured_false(self):
        """Test is_configured returns False when company name not set."""
        assert CompanyConfigLoader.is_configured() is False
    
    @patch.dict(os.environ, {"COMPANY_NAME": "Your Company"}, clear=True)
    def test_is_configured_false_placeholder(self):
        """Test is_configured returns False with placeholder value."""
        assert CompanyConfigLoader.is_configured() is False


class TestGetCompanyConfig:
    """Test suite for get_company_config."""
    
    def setup_method(self):
        """Reset config before each test."""
        reset_company_config()
    
    def teardown_method(self):
        """Reset config after each test."""
        reset_company_config()
    
    @patch.dict(os.environ, {"COMPANY_NAME": "Singleton Test"}, clear=True)
    def test_singleton_pattern(self):
        """Test that get_company_config returns singleton."""
        config1 = get_company_config()
        config2 = get_company_config()
        
        assert config1 is config2
        assert config1.name == "Singleton Test"