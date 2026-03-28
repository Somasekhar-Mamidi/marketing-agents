"""Rate limiting utilities for API endpoints."""

import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int
    requests_per_hour: int
    burst_size: int


class TokenBucket:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: float, capacity: int):
        """Initialize token bucket.
        
        Args:
            rate: Token refill rate per second
            capacity: Maximum bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        now = time.time()
        elapsed = now - self.last_update
        
        # Refill tokens
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now
        
        # Check if we can consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait before tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Seconds to wait
        """
        if self.tokens >= tokens:
            return 0.0
        
        needed = tokens - self.tokens
        return needed / self.rate


class RateLimiter:
    """Rate limiter for API endpoints."""
    
    DEFAULT_LIMITS = RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        burst_size=10
    )
    
    def __init__(self):
        """Initialize rate limiter."""
        self._buckets: Dict[str, TokenBucket] = {}
        self._hourly_counts: Dict[str, Tuple[int, float]] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request.
        
        Args:
            request: FastAPI request
            
        Returns:
            Client identifier (IP or API key)
        """
        # Try to get API key from header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _get_bucket(self, client_id: str) -> TokenBucket:
        """Get or create token bucket for client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            TokenBucket for client
        """
        if client_id not in self._buckets:
            # Create bucket: 1 request per second, burst of 10
            self._buckets[client_id] = TokenBucket(
                rate=self.DEFAULT_LIMITS.requests_per_minute / 60.0,
                capacity=self.DEFAULT_LIMITS.burst_size
            )
        
        return self._buckets[client_id]
    
    def _check_hourly_limit(self, client_id: str) -> bool:
        """Check if client is within hourly limit.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if within limit, False otherwise
        """
        now = time.time()
        count, reset_time = self._hourly_counts.get(client_id, (0, 0))
        
        # Reset if hour has passed
        if now > reset_time:
            self._hourly_counts[client_id] = (1, now + 3600)
            return True
        
        # Check limit
        if count >= self.DEFAULT_LIMITS.requests_per_hour:
            return False
        
        # Increment count
        self._hourly_counts[client_id] = (count + 1, reset_time)
        return True
    
    def is_allowed(self, request: Request) -> Tuple[bool, Dict[str, str]]:
        """Check if request is allowed.
        
        Args:
            request: FastAPI request
            
        Returns:
            Tuple of (allowed, headers)
        """
        client_id = self._get_client_id(request)
        bucket = self._get_bucket(client_id)
        
        headers = {
            "X-RateLimit-Limit": str(self.DEFAULT_LIMITS.requests_per_minute),
            "X-RateLimit-Remaining": str(int(bucket.tokens)),
            "X-RateLimit-Reset": str(int(time.time() + bucket.get_wait_time(1)))
        }
        
        # Check hourly limit first
        if not self._check_hourly_limit(client_id):
            headers["Retry-After"] = str(int(3600 - (time.time() - self._hourly_counts[client_id][1])))
            return False, headers
        
        # Check burst limit
        if not bucket.consume(1):
            wait_time = bucket.get_wait_time(1)
            headers["Retry-After"] = str(int(wait_time) + 1)
            return False, headers
        
        return True, headers


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        """Initialize middleware.
        
        Args:
            app: FastAPI application
            rate_limiter: RateLimiter instance
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)
        
        allowed, headers = self.rate_limiter.is_allowed(request)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {request.client}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers=headers
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        for key, value in headers.items():
            response.headers[key] = value
        
        return response


# Global instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter