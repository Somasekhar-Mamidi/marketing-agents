"""Web search utilities for research agents."""

import logging
import httpx
from typing import Optional
from config.loader import get_env_var

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Unified web search tool that supports multiple backends."""
    
    def __init__(self, provider: str = "tavily"):
        """Initialize the search tool.
        
        Args:
            provider: Search provider to use (tavily, serper, etc.)
        """
        self.provider = provider
        self._client = None
    
    def _get_client(self):
        """Lazy-load the search client based on provider."""
        if self._client is not None:
            return self._client
        
        if self.provider == "tavily":
            try:
                from tavily import TavilyClient
                api_key = get_env_var("TAVILY_API_KEY", required=True)
                self._client = TavilyClient(api_key=api_key)
            except ImportError:
                raise ImportError("tavily package not installed. Run: pip install tavily")
        
        elif self.provider == "serper":
            # Serper uses HTTP requests directly
            self._client = _SerperClient()
        
        else:
            raise ValueError(f"Unknown search provider: {self.provider}")
        
        return self._client
    
    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Search the web for a query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, and snippet
        """
        logger.info(f"Searching for: {query} (provider: {self.provider})")
        
        client = self._get_client()
        
        if self.provider == "tavily":
            # Tavily returns results directly as a list
            results = client.search(query=query)
            # Limit to max_results
            results = results[:max_results] if isinstance(results, list) else []
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0)
                }
                for r in results
            ]
        
        elif self.provider == "serper":
            return client.search(query, num_results=max_results)
        
        return []
    
    def search_with_context(self, query: str, max_results: int = 5) -> dict:
        """Search and get detailed context for each result.
        
        Args:
            query: Search query
            max_results: Number of results to get context for
            
        Returns:
            Dictionary with search results and extracted context
        """
        results = self.search(query, max_results)
        
        # For now, just return the search results
        # Future: could add content extraction from URLs
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }


class _SerperClient:
    """Serper.dev API client."""
    
    def __init__(self):
        import httpx
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
