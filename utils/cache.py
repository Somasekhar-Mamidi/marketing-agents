"""Caching utilities for API responses and computed data."""

import json
import logging
import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached item."""
    key: str
    value: Any
    timestamp: datetime
    ttl_seconds: int


class SQLiteCache:
    """SQLite-based cache for persistent storage."""
    
    def __init__(self, db_path: str = ".cache/marketing_agents_cache.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize the cache database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ttl_seconds INTEGER NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)
            """)
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache if it exists and hasn't expired."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, timestamp, ttl_seconds FROM cache WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                value, timestamp_str, ttl_seconds = row
                cached_time = datetime.fromisoformat(timestamp_str)
                
                if datetime.now() - cached_time > timedelta(seconds=ttl_seconds):
                    # Cache expired
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    return None
                
                return json.loads(value)
                
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Store a value in cache with TTL."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache (key, value, timestamp, ttl_seconds)
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, json.dumps(value), datetime.now().isoformat(), ttl_seconds)
                )
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def delete(self, key: str):
        """Delete a specific cache entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        except Exception as e:
            logger.warning(f"Cache deletion failed: {e}")
    
    def clear(self):
        """Clear all cache entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache")
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")
    
    def cleanup_expired(self):
        """Remove all expired entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM cache WHERE datetime(timestamp, '+' || ttl_seconds || ' seconds') < datetime('now')"
                )
        except Exception as e:
            logger.warning(f"Cache cleanup failed: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*), AVG(ttl_seconds) FROM cache")
                total, avg_ttl = cursor.fetchone()
                
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM cache WHERE datetime(timestamp, '+' || ttl_seconds || ' seconds') < datetime('now')"
                )
                expired = cursor.fetchone()[0]
                
                return {
                    "total_entries": total,
                    "expired_entries": expired,
                    "avg_ttl_seconds": avg_ttl or 0
                }
        except Exception as e:
            logger.warning(f"Cache stats failed: {e}")
            return {"total_entries": 0, "expired_entries": 0, "avg_ttl_seconds": 0}


class SearchCache:
    """Specialized cache for search results."""
    
    DEFAULT_TTL = 86400  # 24 hours
    
    def __init__(self, cache: Optional[SQLiteCache] = None):
        self.cache = cache or SQLiteCache()
    
    def get_search_results(self, query: str, provider: str) -> Optional[list]:
        """Get cached search results."""
        key = f"search:{provider}:{query.lower().strip()}"
        return self.cache.get(key)
    
    def set_search_results(self, query: str, provider: str, results: list):
        """Cache search results."""
        key = f"search:{provider}:{query.lower().strip()}"
        self.cache.set(key, results, ttl_seconds=self.DEFAULT_TTL)


class WebsiteCache:
    """Specialized cache for website scraping results."""
    
    DEFAULT_TTL = 604800  # 7 days
    
    def __init__(self, cache: Optional[SQLiteCache] = None):
        self.cache = cache or SQLiteCache()
    
    def get_website_data(self, url: str) -> Optional[dict]:
        """Get cached website data."""
        key = f"website:{hashlib.sha256(url.encode()).hexdigest()}"
        return self.cache.get(key)
    
    def set_website_data(self, url: str, data: dict):
        """Cache website data."""
        key = f"website:{hashlib.sha256(url.encode()).hexdigest()}"
        self.cache.set(key, data, ttl_seconds=self.DEFAULT_TTL)


class QualificationCache:
    """Specialized cache for qualification scores."""
    
    DEFAULT_TTL = 2592000  # 30 days
    
    def __init__(self, cache: Optional[SQLiteCache] = None):
        self.cache = cache or SQLiteCache()
    
    def get_scores(self, event_name: str, theme: str) -> Optional[dict]:
        """Get cached qualification scores."""
        key = f"qualification:{event_name.lower()}:{theme.lower()}"
        return self.cache.get(key)
    
    def set_scores(self, event_name: str, theme: str, scores: dict):
        """Cache qualification scores."""
        key = f"qualification:{event_name.lower()}:{theme.lower()}"
        self.cache.set(key, scores, ttl_seconds=self.DEFAULT_TTL)


# Global cache instances
_search_cache: Optional[SearchCache] = None
_website_cache: Optional[WebsiteCache] = None
_qualification_cache: Optional[QualificationCache] = None


def get_search_cache() -> SearchCache:
    """Get global search cache instance."""
    global _search_cache
    if _search_cache is None:
        _search_cache = SearchCache()
    return _search_cache


def get_website_cache() -> WebsiteCache:
    """Get global website cache instance."""
    global _website_cache
    if _website_cache is None:
        _website_cache = WebsiteCache()
    return _website_cache


def get_qualification_cache() -> QualificationCache:
    """Get global qualification cache instance."""
    global _qualification_cache
    if _qualification_cache is None:
        _qualification_cache = QualificationCache()
    return _qualification_cache
