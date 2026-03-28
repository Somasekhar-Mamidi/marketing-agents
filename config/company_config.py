"""Company configuration for outreach emails."""

import logging
from dataclasses import dataclass
from typing import Optional
from config.loader import get_env_var

logger = logging.getLogger(__name__)


@dataclass
class CompanyConfig:
    """Company configuration for outreach emails."""
    name: str
    website: Optional[str]
    contact_name: Optional[str]
    contact_title: Optional[str]
    contact_email: Optional[str]
    value_proposition: Optional[str]


class CompanyConfigLoader:
    """Loads company configuration from environment variables."""
    
    @staticmethod
    def load() -> CompanyConfig:
        """Load company configuration from environment.
        
        Returns:
            CompanyConfig with values from environment or defaults
        """
        config = CompanyConfig(
            name=get_env_var("COMPANY_NAME", default="Your Company") or "Your Company",
            website=get_env_var("COMPANY_WEBSITE"),
            contact_name=get_env_var("CONTACT_NAME"),
            contact_title=get_env_var("CONTACT_TITLE"),
            contact_email=get_env_var("CONTACT_EMAIL"),
            value_proposition=get_env_var("COMPANY_VALUE_PROP")
        )
        
        if config.name == "Your Company":
            logger.warning("COMPANY_NAME not set. Using default placeholder.")
        
        return config
    
    @staticmethod
    def is_configured() -> bool:
        """Check if company is properly configured."""
        company_name = get_env_var("COMPANY_NAME")
        return company_name is not None and company_name != "Your Company"


# Global instance
_config: Optional[CompanyConfig] = None


def get_company_config() -> CompanyConfig:
    """Get global company config instance."""
    global _config
    if _config is None:
        _config = CompanyConfigLoader.load()
    return _config


def reset_company_config():
    """Reset global config (useful for testing)."""
    global _config
    _config = None