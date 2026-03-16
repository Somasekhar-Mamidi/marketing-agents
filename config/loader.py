"""Configuration loader for pipeline and agents."""

import os
import yaml
from pathlib import Path
from typing import Any, Optional

DEFAULT_CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_yaml(file_path: Path) -> dict[str, Any]:
    """Load a YAML configuration file."""
    if not file_path.exists():
        return {}
    
    with open(file_path) as f:
        return yaml.safe_load(f) or {}


def load_pipeline_config(config_path: Optional[str] = None) -> dict[str, Any]:
    """Load pipeline configuration.
    
    Args:
        config_path: Optional path to custom config file
        
    Returns:
        Configuration dictionary
    """
    if config_path:
        return load_yaml(Path(config_path))
    
    # Default: load pipeline.yaml from config directory
    return load_yaml(DEFAULT_CONFIG_DIR / "pipeline.yaml")


def load_agent_config(agent_name: str) -> dict[str, Any]:
    """Load configuration for a specific agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Agent configuration dictionary
    """
    agent_config_file = DEFAULT_CONFIG_DIR / "agents" / f"{agent_name}.yaml"
    return load_yaml(agent_config_file)


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Get environment variable with optional default and required check.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether to raise error if not found
        
    Returns:
        Environment variable value or default
    """
    value = os.environ.get(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    
    return value
