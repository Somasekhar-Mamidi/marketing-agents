"""Error handling utilities for graceful degradation."""

import logging
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AgentError:
    """Represents an error that occurred in an agent."""
    agent_name: str
    error_message: str
    severity: ErrorSeverity
    partial_results: Optional[dict] = None
    recoverable: bool = True


class ErrorHandler:
    """Handles errors gracefully and preserves partial results."""
    
    def __init__(self, continue_on_error: bool = True):
        self.continue_on_error = continue_on_error
        self.errors: list[AgentError] = []
    
    def handle_error(
        self,
        agent_name: str,
        error: Exception,
        partial_results: Optional[dict] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR
    ) -> Optional[dict]:
        """Handle an error and return partial results if available.
        
        Args:
            agent_name: Name of the agent that failed
            error: The exception that was raised
            partial_results: Any partial results that were computed before the error
            severity: How severe the error is
            
        Returns:
            Partial results if available and continue_on_error is True, None otherwise
        """
        agent_error = AgentError(
            agent_name=agent_name,
            error_message=str(error),
            severity=severity,
            partial_results=partial_results,
            recoverable=severity != ErrorSeverity.CRITICAL
        )
        
        self.errors.append(agent_error)
        
        if severity == ErrorSeverity.CRITICAL:
            logger.error(f"CRITICAL: Agent {agent_name} failed: {error}")
            raise error
        
        logger.warning(f"Agent {agent_name} encountered error: {error}")
        
        if self.continue_on_error and partial_results:
            logger.info(f"Continuing with partial results from {agent_name}")
            return partial_results
        
        return None
    
    def get_errors(self, severity: Optional[ErrorSeverity] = None) -> list[AgentError]:
        """Get all errors, optionally filtered by severity."""
        if severity:
            return [e for e in self.errors if e.severity == severity]
        return self.errors
    
    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.errors) > 0
    
    def get_summary(self) -> dict:
        """Get a summary of all errors."""
        return {
            "total_errors": len(self.errors),
            "critical": len([e for e in self.errors if e.severity == ErrorSeverity.CRITICAL]),
            "errors": len([e for e in self.errors if e.severity == ErrorSeverity.ERROR]),
            "warnings": len([e for e in self.errors if e.severity == ErrorSeverity.WARNING]),
            "agent_errors": [
                {"agent": e.agent_name, "error": e.error_message, "severity": e.severity.value}
                for e in self.errors
            ]
        }
