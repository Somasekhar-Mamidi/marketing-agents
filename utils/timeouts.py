"""Timeout utilities for agent execution."""

import signal
import logging
from typing import Optional, Callable, Any
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Raised when operation times out."""
    pass


class AgentTimeout:
    """Timeout handler for agent operations."""
    
    DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes
    
    def __init__(self, timeout_seconds: Optional[int] = None):
        self.timeout_seconds = timeout_seconds or self.DEFAULT_TIMEOUT_SECONDS
        self._original_handler = None
    
    def _timeout_handler(self, signum, frame):
        """Signal handler for timeout."""
        raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")
    
    def __enter__(self):
        """Start timeout context."""
        # Set up signal handler (Unix only)
        try:
            self._original_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.timeout_seconds)
        except AttributeError:
            # Windows doesn't support SIGALRM, use alternative approach
            logger.debug("SIGALRM not available, timeout via threading")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up timeout context."""
        try:
            signal.alarm(0)  # Disable alarm
            if self._original_handler:
                signal.signal(signal.SIGALRM, self._original_handler)
        except AttributeError:
            pass  # Windows
        
        # Don't suppress TimeoutError
        return False


@contextmanager
def timeout_context(seconds: int):
    """Context manager for operation timeout.
    
    Usage:
        with timeout_context(30):
            result = long_running_operation()
    """
    try:
        with AgentTimeout(seconds):
            yield
    except TimeoutError:
        raise


def with_timeout(seconds: Optional[int] = None):
    """Decorator to add timeout to a function.
    
    Usage:
        @with_timeout(60)
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            timeout_seconds = seconds or AgentTimeout.DEFAULT_TIMEOUT_SECONDS
            with timeout_context(timeout_seconds):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class AgentTimeoutConfig:
    """Timeout configuration for different agent types."""
    
    # Timeouts in seconds
    DISCOVERY_TIMEOUT = 180       # 3 minutes
    QUALIFICATION_TIMEOUT = 120   # 2 minutes
    SCRAPING_TIMEOUT = 60         # 1 minute per website
    INTELLIGENCE_TIMEOUT = 90     # 1.5 minutes
    PRIORITIZATION_TIMEOUT = 60   # 1 minute
    OUTREACH_TIMEOUT = 60         # 1 minute
    
    @classmethod
    def get_timeout(cls, agent_name: str) -> int:
        """Get timeout for specific agent."""
        timeouts = {
            'event_discovery': cls.DISCOVERY_TIMEOUT,
            'event_qualification': cls.QUALIFICATION_TIMEOUT,
            'event_website_scraper': cls.SCRAPING_TIMEOUT,
            'event_intelligence': cls.INTELLIGENCE_TIMEOUT,
            'event_prioritization': cls.PRIORITIZATION_TIMEOUT,
            'outreach_email': cls.OUTREACH_TIMEOUT,
        }
        return timeouts.get(agent_name, cls.DEFAULT_TIMEOUT_SECONDS)


class TimeoutManager:
    """Manages timeouts across the pipeline."""
    
    def __init__(self):
        self.timeouts: dict[str, int] = {}
    
    def set_timeout(self, agent_name: str, seconds: int):
        """Set custom timeout for an agent."""
        self.timeouts[agent_name] = seconds
        logger.info(f"Set timeout for {agent_name}: {seconds}s")
    
    def get_timeout(self, agent_name: str) -> int:
        """Get timeout for an agent."""
        if agent_name in self.timeouts:
            return self.timeouts[agent_name]
        return AgentTimeoutConfig.get_timeout(agent_name)
    
    def execute_with_timeout(
        self,
        agent_name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with agent-specific timeout."""
        timeout = self.get_timeout(agent_name)
        
        logger.debug(f"Executing {agent_name} with {timeout}s timeout")
        
        with timeout_context(timeout):
            return func(*args, **kwargs)


# Global timeout manager
_timeout_manager: Optional[TimeoutManager] = None


def get_timeout_manager() -> TimeoutManager:
    """Get global timeout manager."""
    global _timeout_manager
    if _timeout_manager is None:
        _timeout_manager = TimeoutManager()
    return _timeout_manager


def configure_timeout(agent_name: str, seconds: int):
    """Configure timeout for a specific agent."""
    get_timeout_manager().set_timeout(agent_name, seconds)
