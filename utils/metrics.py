"""Prometheus metrics collection for the marketing agents system."""

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and exposes Prometheus metrics."""
    
    def __init__(self):
        self._initialized = False
        self._metrics = {}
        
        if not PROMETHEUS_AVAILABLE:
            logger.warning("prometheus_client not installed, metrics collection disabled")
            return
        
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize all metrics."""
        # Agent execution metrics
        self._metrics['agent_executions'] = Counter(
            'agent_executions_total',
            'Total number of agent executions',
            ['agent_name', 'status']
        )
        
        self._metrics['agent_latency'] = Histogram(
            'agent_latency_seconds',
            'Time spent in agent execution',
            ['agent_name']
        )
        
        # Event metrics
        self._metrics['events_discovered'] = Gauge(
            'events_discovered',
            'Number of events discovered'
        )
        
        self._metrics['events_qualified'] = Gauge(
            'events_qualified',
            'Number of events after qualification'
        )
        
        self._metrics['events_deduplicated'] = Gauge(
            'events_deduplicated',
            'Number of duplicate events removed'
        )
        
        # Search API metrics
        self._metrics['search_api_calls'] = Counter(
            'search_api_calls_total',
            'Total number of search API calls',
            ['provider', 'status']
        )
        
        self._metrics['search_latency'] = Histogram(
            'search_latency_seconds',
            'Search API call latency',
            ['provider']
        )
        
        # Web scraping metrics
        self._metrics['website_scrapes'] = Counter(
            'website_scrapes_total',
            'Total number of website scrapes',
            ['status']
        )
        
        self._metrics['scrape_latency'] = Histogram(
            'scrape_latency_seconds',
            'Website scrape latency'
        )
        
        # Cache metrics
        self._metrics['cache_hits'] = Counter(
            'cache_hits_total',
            'Total number of cache hits',
            ['cache_type']
        )
        
        self._metrics['cache_misses'] = Counter(
            'cache_misses_total',
            'Total number of cache misses',
            ['cache_type']
        )
        
        self._initialized = True
        logger.info("Metrics collector initialized")
    
    def record_agent_execution(self, agent_name: str, duration_seconds: float, success: bool = True):
        """Record an agent execution."""
        if not self._initialized:
            return
        
        status = "success" if success else "failure"
        self._metrics['agent_executions'].labels(
            agent_name=agent_name,
            status=status
        ).inc()
        
        self._metrics['agent_latency'].labels(
            agent_name=agent_name
        ).observe(duration_seconds)
    
    def record_events_discovered(self, count: int):
        """Record number of events discovered."""
        if self._initialized:
            self._metrics['events_discovered'].set(count)
    
    def record_events_qualified(self, count: int):
        """Record number of events qualified."""
        if self._initialized:
            self._metrics['events_qualified'].set(count)
    
    def record_events_deduplicated(self, count: int):
        """Record number of duplicates removed."""
        if self._initialized:
            self._metrics['events_deduplicated'].set(count)
    
    def record_search_api_call(self, provider: str, duration_seconds: float, success: bool = True):
        """Record a search API call."""
        if not self._initialized:
            return
        
        status = "success" if success else "failure"
        self._metrics['search_api_calls'].labels(
            provider=provider,
            status=status
        ).inc()
        
        self._metrics['search_latency'].labels(
            provider=provider
        ).observe(duration_seconds)
    
    def record_website_scrape(self, duration_seconds: float, success: bool = True):
        """Record a website scrape."""
        if not self._initialized:
            return
        
        status = "success" if success else "failure"
        self._metrics['website_scrapes'].labels(status=status).inc()
        self._metrics['scrape_latency'].observe(duration_seconds)
    
    def record_cache_hit(self, cache_type: str):
        """Record a cache hit."""
        if self._initialized:
            self._metrics['cache_hits'].labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Record a cache miss."""
        if self._initialized:
            self._metrics['cache_misses'].labels(cache_type=cache_type).inc()


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def start_metrics_server(port: int = 8000) -> bool:
    """Start Prometheus metrics HTTP server.
    
    Returns:
        True if server started successfully
    """
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Cannot start metrics server - prometheus_client not installed")
        return False
    
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
        return True
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        return False


class TimedAgentExecution:
    """Context manager for timing agent execution.
    
    Usage:
        with TimedAgentExecution("event_discovery"):
            result = agent.execute(input_data)
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.start_time: Optional[float] = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.success = exc_type is None
            
            collector = get_metrics_collector()
            collector.record_agent_execution(
                agent_name=self.agent_name,
                duration_seconds=duration,
                success=self.success
            )


class TimedSearch:
    """Context manager for timing search API calls.
    
    Usage:
        with TimedSearch("tavily"):
            results = client.search(query)
    """
    
    def __init__(self, provider: str):
        self.provider = provider
        self.start_time: Optional[float] = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.success = exc_type is None
            
            collector = get_metrics_collector()
            collector.record_search_api_call(
                provider=self.provider,
                duration_seconds=duration,
                success=self.success
            )


class TimedScrape:
    """Context manager for timing website scrapes.
    
    Usage:
        with TimedScrape():
            data = scraper.scrape_event_page(url)
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.success = exc_type is None
            
            collector = get_metrics_collector()
            collector.record_website_scrape(
                duration_seconds=duration,
                success=self.success
            )
