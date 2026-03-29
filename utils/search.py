"""Web search utilities for research agents with fallback support and caching."""

import logging
import httpx
from typing import Optional
from config.loader import get_env_var
from utils.retry import retry_with_backoff
from utils.cache import get_search_cache

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Unified web search tool with automatic fallback and caching."""

    def __init__(self, provider: str = "auto", enable_cache: bool = False):
        """Initialize the search tool.

        Args:
            provider: Search provider or "auto" for fallback
            enable_cache: Whether to enable result caching
        """
        self.provider = provider
        self.enable_cache = enable_cache
        self._client = None
        self._provider_tried = []
        self._cache = get_search_cache() if enable_cache else None

    def _get_client(self):
        """Lazy-load the search client with fallback support."""
        if self._client is not None:
            return self._client

        # Use DuckDuckGo as primary search provider (free, no API key needed)
        # Paid services (Tavily, Serper, Search1API) removed - using Gemini native web instead
        self._client = _DuckDuckGoClient()
        self.provider = "duckduckgo"
        logger.info(f"Using DuckDuckGo search provider (free, no API key)")
        return self._client

    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exceptions=(Exception,)
    )
    def _search_with_provider(self, query: str, max_results: int) -> list[dict]:
        """Execute search with current provider (with retry)."""
        client = self._get_client()

        if self.provider == "tavily":
            raw_results = client.search(query=query)
            results_list = raw_results.get("results", []) if isinstance(raw_results, dict) else raw_results
            results_list = results_list[:max_results] if isinstance(results_list, list) else []
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0)
                }
                for r in results_list
            ]
        else:
            return client.search(query, num_results=max_results)

    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Search the web for a query with caching, retry and fallback."""
        logger.info(f"Searching for: {query}")

        # Check cache first
        if self._cache and self.enable_cache:
            cached_results = self._cache.get_search_results(query, self.provider)
            if cached_results is not None:
                logger.info(f"Cache hit for query: {query}")
                return cached_results

        try:
            results = self._search_with_provider(query, max_results)

            # Cache the results
            if self._cache and self.enable_cache:
                self._cache.set_search_results(query, self.provider, results)
                logger.info(f"Cached results for query: {query}")

            return results
        except (httpx.HTTPError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Search failed with {self.provider} after retries: {e}")
            # Try fallback
            if self.provider != "duckduckgo":
                self._client = None
                self.provider = "auto"
                return self.search(query, max_results)
            return []

    def search_with_context(self, query: str, max_results: int = 5) -> dict:
        """Search and get detailed context."""
        results = self.search(query, max_results)

        return {
            "query": query,
            "results": results,
            "count": len(results)
        }


class _SerperClient:
    """Serper.dev API client."""

    def __init__(self):
        api_key = get_env_var("SERPER_API_KEY", required=True)
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"
        self.client = httpx.Client(timeout=30.0)

    def search(self, query: str, num_results: int = 10) -> list[dict]:
        """Execute search via Serper API."""
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query, "num": num_results}

        response = self.client.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        return [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "content": item.get("snippet", ""),
            }
            for item in data.get("organic", [])
        ]


class _Search1APIClient:
    """Search1API client."""

    def __init__(self):
        api_key = get_env_var("SEARCH1API_KEY", required=True)
        self.api_key = api_key
        self.base_url = "https://api.search1api.com/search"
        self.client = httpx.Client(timeout=30.0)

    def search(self, query: str, num_results: int = 10) -> list[dict]:
        """Execute search via Search1API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "search_service": "google",
            "max_results": num_results
        }

        response = self.client.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("snippet", ""),
            }
            for item in data.get("data", []) if isinstance(data.get("data"), list)
        ]


class _DuckDuckGoClient:
    def search(self, query: str, num_results: int = 10) -> list[dict]:
        import urllib.request
        import urllib.parse
        import json
        import ssl
        
        # Create SSL context that allows legacy TLS (for macOS LibreSSL compatibility)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Use DuckDuckGo HTML interface
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        request = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(request, context=ssl_context, timeout=30) as response:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.read(), "html.parser")
            
            results = []
            for result in soup.select(".result")[:num_results]:
                title_elem = result.select_one(".result__a")
                snippet_elem = result.select_one(".result__snippet")
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")
                    content = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # Clean up the URL (DuckDuckGo uses redirects)
                    if href.startswith("//"):
                        href = "https:" + href
                    
                    results.append({
                        "title": title,
                        "url": href,
                        "content": content,
                    })
            
            return results