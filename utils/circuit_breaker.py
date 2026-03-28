"""Circuit breaker pattern for resilient external service calls."""

import time
import logging
import functools
from enum import Enum
from threading import Lock
from typing import Callable, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker for external service calls.
    
    Automatically opens when failure threshold is reached,
    and attempts recovery after timeout.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self._lock = Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call a function with circuit breaker protection."""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit {self.name} entering HALF_OPEN state")
                else:
                    logger.warning(f"Circuit {self.name} is OPEN, rejecting request")
                    raise CircuitBreakerOpen(f"Circuit {self.name} is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery."""
        if not self.last_failure_time:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self._reset()
                logger.info(f"Circuit {self.name} recovered, closing circuit")
            else:
                self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit {self.name} re-opened after failed recovery attempt")
            elif self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    f"Circuit {self.name} opened after {self.failure_count} failures"
                )
    
    def _reset(self):
        """Reset circuit to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self.state


# Global circuit breakers registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60
) -> CircuitBreaker:
    """Get or create a circuit breaker."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
    return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60
):
    """Decorator to add circuit breaker to a function.
    
    Usage:
        @circuit_breaker("tavily_api", failure_threshold=3)
        def search_with_tavily(query):
            ...
    """
    def decorator(func: Callable) -> Callable:
        cb = get_circuit_breaker(name, failure_threshold, recovery_timeout)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        
        return wrapper
    return decorator


def get_circuit_breaker_status(name: str) -> Optional[dict]:
    """Get status of a circuit breaker."""
    if name not in _circuit_breakers:
        return None
    
    cb = _circuit_breakers[name]
    return {
        "name": cb.name,
        "state": cb.get_state().value,
        "failure_count": cb.failure_count,
        "failure_threshold": cb.failure_threshold,
        "recovery_timeout": cb.recovery_timeout
    }


def get_all_circuit_breaker_status() -> dict:
    """Get status of all circuit breakers."""
    return {
        name: get_circuit_breaker_status(name)
        for name in _circuit_breakers.keys()
    }
