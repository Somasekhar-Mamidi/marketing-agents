"""Structured logging configuration with correlation IDs."""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')


class CorrelationIdFilter(logging.Filter):
    """Filter that adds correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get() or 'N/A'
        return True


def setup_structured_logging(log_level: str = 'INFO') -> None:
    """Configure structured logging with correlation IDs.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    log_format = (
        '%(asctime)s | %(correlation_id)s | %(levelname)s | '
        '%(name)s | %(message)s'
    )
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Add correlation ID filter to root handler
    root_logger = logging.getLogger()
    correlation_filter = CorrelationIdFilter()
    
    for handler in root_logger.handlers:
        handler.addFilter(correlation_filter)


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for current context.
    
    Args:
        correlation_id: Optional correlation ID, generates UUID if not provided
        
    Returns:
        The correlation ID
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())[:8]
    
    correlation_id_var.set(correlation_id)
    return correlation_id


class CorrelationContext:
    """Context manager for correlation IDs.
    
    Usage:
        with CorrelationContext() as cid:
            # All logs in this block have the same correlation ID
            logger.info("Starting operation")
    """
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())[:8]
        self.token = None
    
    def __enter__(self):
        self.token = correlation_id_var.set(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            correlation_id_var.reset(self.token)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with correlation ID support.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Add filter if not already present
    has_filter = any(
        isinstance(f, CorrelationIdFilter) for f in logger.filters
    )
    if not has_filter:
        logger.addFilter(CorrelationIdFilter())
    
    return logger


def log_agent_start(agent_name: str, query: str) -> None:
    """Log agent start with correlation."""
    logger = get_logger('pipeline')
    logger.info(f"AGENT_START | agent={agent_name} | query={query[:50]}...")


def log_agent_complete(agent_name: str, duration_ms: float, success: bool = True) -> None:
    """Log agent completion with correlation."""
    logger = get_logger('pipeline')
    status = "SUCCESS" if success else "FAILED"
    logger.info(
        f"AGENT_COMPLETE | agent={agent_name} | duration_ms={duration_ms:.0f} | status={status}"
    )


def log_pipeline_start(query: str, num_agents: int) -> None:
    """Log pipeline start."""
    logger = get_logger('pipeline')
    cid = get_correlation_id()
    logger.info(f"PIPELINE_START | correlation_id={cid} | query={query[:50]}... | agents={num_agents}")


def log_pipeline_complete(duration_ms: float, events_count: int) -> None:
    """Log pipeline completion."""
    logger = get_logger('pipeline')
    logger.info(
        f"PIPELINE_COMPLETE | duration_ms={duration_ms:.0f} | events={events_count}"
    )


def log_search_attempt(provider: str, query: str) -> None:
    """Log search attempt."""
    logger = get_logger('search')
    logger.info(f"SEARCH_ATTEMPT | provider={provider} | query={query[:50]}...")


def log_search_success(provider: str, results_count: int, duration_ms: float) -> None:
    """Log search success."""
    logger = get_logger('search')
    logger.info(
        f"SEARCH_SUCCESS | provider={provider} | results={results_count} | duration_ms={duration_ms:.0f}"
    )


def log_search_failure(provider: str, error: str) -> None:
    """Log search failure."""
    logger = get_logger('search')
    logger.error(f"SEARCH_FAILURE | provider={provider} | error={error}")


def log_scrape_attempt(url: str) -> None:
    """Log website scrape attempt."""
    logger = get_logger('scraper')
    logger.info(f"SCRAPE_ATTEMPT | url={url[:80]}...")


def log_scrape_success(url: str, duration_ms: float, fields_found: int) -> None:
    """Log website scrape success."""
    logger = get_logger('scraper')
    logger.info(
        f"SCRAPE_SUCCESS | url={url[:80]}... | duration_ms={duration_ms:.0f} | fields={fields_found}"
    )


def log_scrape_failure(url: str, error: str) -> None:
    """Log website scrape failure."""
    logger = get_logger('scraper')
    logger.error(f"SCRAPE_FAILURE | url={url[:80]}... | error={error}")


def log_deduplication(original_count: int, deduplicated_count: int) -> None:
    """Log deduplication results."""
    logger = get_logger('deduplication')
    removed = original_count - deduplicated_count
    logger.info(
        f"DEDUPLICATION | original={original_count} | final={deduplicated_count} | removed={removed}"
    )


def log_cache_hit(cache_type: str, key: str) -> None:
    """Log cache hit."""
    logger = get_logger('cache')
    logger.debug(f"CACHE_HIT | type={cache_type} | key={key[:40]}...")


def log_cache_miss(cache_type: str, key: str) -> None:
    """Log cache miss."""
    logger = get_logger('cache')
    logger.debug(f"CACHE_MISS | type={cache_type} | key={key[:40]}...")
