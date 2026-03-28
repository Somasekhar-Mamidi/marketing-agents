"""Health check utilities for monitoring system status."""

import time
import logging
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    response_time_ms: float
    message: str
    details: Optional[Dict] = None


class HealthChecker:
    """Performs health checks on system components."""
    
    VERSION = "1.0.0"
    
    def __init__(self):
        self.checks: Dict[str, callable] = {}
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check function."""
        self.checks[name] = check_func
    
    def check_search_apis(self) -> HealthCheckResult:
        """Check search API connectivity."""
        start = time.time()
        
        try:
            from config.loader import get_env_var
            
            apis = {
                "tavily": get_env_var("TAVILY_API_KEY", required=False),
                "serper": get_env_var("SERPER_API_KEY", required=False),
                "search1api": get_env_var("SEARCH1API_KEY", required=False)
            }
            
            available = sum(1 for v in apis.values() if v and not v.startswith("your_"))
            
            if available == 0:
                return HealthCheckResult(
                    name="search_apis",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=(time.time() - start) * 1000,
                    message=f"No search APIs configured (will use DuckDuckGo fallback)",
                    details={"available": available, "total": len(apis)}
                )
            
            return HealthCheckResult(
                name="search_apis",
                status=HealthStatus.HEALTHY,
                response_time_ms=(time.time() - start) * 1000,
                message=f"{available} search APIs configured",
                details={"available": available, "total": len(apis)}
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="search_apis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start) * 1000,
                message=f"Error checking search APIs: {str(e)}"
            )
    
    def check_web_scraper(self) -> HealthCheckResult:
        """Check web scraper functionality."""
        start = time.time()
        
        try:
            import httpx
            # Try to fetch a simple, reliable page
            response = httpx.get("https://example.com", timeout=10.0)
            response.raise_for_status()
            
            return HealthCheckResult(
                name="web_scraper",
                status=HealthStatus.HEALTHY,
                response_time_ms=(time.time() - start) * 1000,
                message="Web scraper can fetch external pages"
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="web_scraper",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start) * 1000,
                message=f"Web scraper cannot fetch pages: {str(e)}"
            )
    
    def check_cache(self) -> HealthCheckResult:
        """Check cache availability."""
        start = time.time()
        
        try:
            from utils.cache import SQLiteCache
            
            cache = SQLiteCache()
            # Test write and read
            cache.set("health_check", {"status": "ok"}, ttl_seconds=60)
            result = cache.get("health_check")
            
            if result and result.get("status") == "ok":
                return HealthCheckResult(
                    name="cache",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=(time.time() - start) * 1000,
                    message="Cache is operational"
                )
            else:
                return HealthCheckResult(
                    name="cache",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=(time.time() - start) * 1000,
                    message="Cache read/write test failed"
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="cache",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start) * 1000,
                message=f"Cache error: {str(e)}"
            )
    
    def check_pipeline(self) -> HealthCheckResult:
        """Check if pipeline can initialize."""
        start = time.time()
        
        try:
            from pipeline.orchestrator import Pipeline
            
            pipeline = Pipeline()
            
            # Check that all required agents can be imported
            from agents.schema_initialization import SchemaInitializationAgent
            from agents.event_discovery import EventDiscoveryAgent
            from agents.event_qualification import EventQualificationAgent
            
            pipeline.add_agent(SchemaInitializationAgent())
            
            return HealthCheckResult(
                name="pipeline",
                status=HealthStatus.HEALTHY,
                response_time_ms=(time.time() - start) * 1000,
                message="Pipeline can initialize successfully"
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="pipeline",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start) * 1000,
                message=f"Pipeline initialization failed: {str(e)}"
            )
    
    def check_all(self) -> Dict:
        """Run all health checks and return comprehensive status."""
        checks = [
            self.check_search_apis(),
            self.check_web_scraper(),
            self.check_cache(),
            self.check_pipeline()
        ]
        
        # Determine overall status
        statuses = [c.status for c in checks]
        if HealthStatus.UNHEALTHY in statuses:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        
        return {
            "status": overall.value,
            "timestamp": datetime.utcnow().isoformat(),
            "version": self.VERSION,
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "response_time_ms": round(check.response_time_ms, 2),
                    "message": check.message,
                    "details": check.details
                }
                for check in checks
            }
        }


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def get_health_status() -> Dict:
    """Get comprehensive health status."""
    return get_health_checker().check_all()


def is_healthy() -> bool:
    """Quick check if system is healthy."""
    status = get_health_status()
    return status["status"] == HealthStatus.HEALTHY.value


def format_health_for_display(status: Dict) -> str:
    """Format health status for display."""
    lines = [
        f"Status: {status['status'].upper()}",
        f"Version: {status['version']}",
        f"Timestamp: {status['timestamp']}",
        "",
        "Component Checks:"
    ]
    
    for name, check in status["checks"].items():
        icon = "✅" if check["status"] == "healthy" else "⚠️" if check["status"] == "degraded" else "❌"
        lines.append(f"  {icon} {name}: {check['message']} ({check['response_time_ms']}ms)")
    
    return "\n".join(lines)
