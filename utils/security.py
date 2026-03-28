"""Security utilities for input validation and data protection."""

import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


# Sensitive field patterns to redact
SENSITIVE_PATTERNS = [
    r'api[_-]?key',
    r'api[_-]?secret',
    r'auth[_-]?token',
    r'password',
    r'secret',
    r'private[_-]?key',
    r'access[_-]?token',
    r'client[_-]?secret',
    r'email',  # In some contexts
    r'phone',
]

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r'(\%27)|(\')|(\-\-)|(\%23)|(#)',
    r'((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))',
    r'\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))',
    r'((\%27)|(\'))union',
    r'exec(\s|\+)+(s|x)p\w+',
    r'UNION\s+SELECT',
    r'INSERT\s+INTO',
    r'DELETE\s+FROM',
    r'DROP\s+TABLE',
]

# XSS patterns
XSS_PATTERNS = [
    r'<script[^>]*>[\s\S]*?</script>',
    r'javascript:',
    r'on\w+\s*=',
    r'<iframe',
    r'<object',
    r'<embed',
]


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Trim to max length
    if len(value) > max_length:
        value = value[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Check for SQL injection
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            logger.warning(f"Potential SQL injection detected: {value[:50]}...")
            # Remove dangerous characters
            value = re.sub(r'[;\-\']', '', value)
    
    # Check for XSS
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            logger.warning(f"Potential XSS detected: {value[:50]}...")
            # HTML encode dangerous characters
            value = value.replace('<', '&lt;').replace('>', '&gt;')
    
    return value


def sanitize_search_query(query: str) -> str:
    """Sanitize search query input.
    
    Args:
        query: Search query string
        
    Returns:
        Sanitized query
    """
    if not query:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
    for char in dangerous_chars:
        query = query.replace(char, ' ')
    
    # Normalize whitespace
    query = re.sub(r'\s+', ' ', query).strip()
    
    return query


def redact_sensitive_data(data: Dict[str, Any], patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Redact sensitive information from data.
    
    Args:
        data: Dictionary potentially containing sensitive data
        patterns: List of regex patterns for sensitive field names
        
    Returns:
        Dictionary with sensitive data redacted
    """
    if patterns is None:
        patterns = SENSITIVE_PATTERNS
    
    redacted = {}
    
    for key, value in data.items():
        # Check if key matches sensitive pattern
        is_sensitive = any(re.search(pattern, key, re.IGNORECASE) for pattern in patterns)
        
        if is_sensitive:
            redacted[key] = '***REDACTED***'
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_data(value, patterns)
        elif isinstance(value, list):
            redacted[key] = [
                redact_sensitive_data(item, patterns) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted[key] = value
    
    return redacted


def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def validate_industry(industry: str) -> bool:
    """Validate industry input.
    
    Args:
        industry: Industry string
        
    Returns:
        True if valid, False otherwise
    """
    valid_industries = [
        'payments', 'fintech', 'ai', 'artificial intelligence',
        'technology', 'software', 'blockchain', 'e-commerce',
        'healthcare', 'cybersecurity', 'cloud', 'devops'
    ]
    
    return industry.lower() in valid_industries or len(industry) >= 3


def rate_limit_check(
    key: str,
    max_requests: int = 100,
    window_seconds: int = 3600,
    storage: Optional[Dict] = None
) -> tuple[bool, int]:
    """Simple in-memory rate limiting check.
    
    Args:
        key: Identifier for the rate limit (e.g., IP address, API key)
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        storage: Optional external storage dict (for persistence)
        
    Returns:
        Tuple of (allowed: bool, remaining: int)
    """
    import time
    
    if storage is None:
        storage = _rate_limit_storage
    
    now = time.time()
    
    if key not in storage:
        storage[key] = {'count': 1, 'window_start': now}
        return True, max_requests - 1
    
    entry = storage[key]
    
    # Check if window has expired
    if now - entry['window_start'] > window_seconds:
        entry['count'] = 1
        entry['window_start'] = now
        return True, max_requests - 1
    
    # Check if under limit
    if entry['count'] < max_requests:
        entry['count'] += 1
        return True, max_requests - entry['count']
    
    return False, 0


# Global rate limit storage (use Redis in production)
_rate_limit_storage: Dict[str, Dict] = {}


def check_rate_limit(key: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
    """Check if request is within rate limit.
    
    Args:
        key: Rate limit key
        max_requests: Max requests allowed
        window_seconds: Time window
        
    Returns:
        True if allowed, False if rate limited
    """
    allowed, _ = rate_limit_check(key, max_requests, window_seconds)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for key: {key}")
    
    return allowed


class SecurityContext:
    """Context manager for security operations."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(
                f"Security error in context {self.correlation_id}: {exc_val}"
            )
