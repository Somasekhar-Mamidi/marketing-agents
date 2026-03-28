"""DuckDuckGo-only search implementation (no API keys required)."""

import logging
import httpx
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DuckDuckGoSearch:
    """Free web search using DuckDuckGo (no API keys required)."""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        self.base_url = "https://html.duckduckgo.com/html/"
    
    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Search DuckDuckGo and return results.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, and snippet
        """
        logger.info(f"[DuckDuckGo] Searching: {query}")
        
        try:
            params = {
                "q": query,
                "kl": "us-en"  # US English results
            }
            
            response = self.client.get(self.base_url, params=params)
            response.raise_for_status()
            
            results = self._parse_results(response.text, max_results)
            
            logger.info(f"[DuckDuckGo] Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"[DuckDuckGo] Search failed: {e}")
            return []
    
    def _parse_results(self, html: str, max_results: int) -> list[dict]:
        """Parse HTML response and extract search results."""
        soup = BeautifulSoup(html, "html.parser")
        results = []
        
        # DuckDuckGo HTML structure
        for result in soup.select(".result")[:max_results]:
            try:
                # Extract title and URL
                title_elem = result.select_one(".result__a")
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url = title_elem.get("href", "")
                
                # Extract snippet
                snippet_elem = result.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                if title and url:
                    results.append({
                        "title": title,
                        "url": self._clean_url(url),
                        "content": snippet,
                        "source": "duckduckgo"
                    })
                    
            except Exception as e:
                logger.debug(f"Error parsing result: {e}")
                continue
        
        return results
    
    def _clean_url(self, url: str) -> str:
        """Clean and validate URL."""
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = "https://duckduckgo.com" + url
        
        # Remove DuckDuckGo redirects
        if "duckduckgo.com/l/?" in url:
            # Extract actual URL from redirect
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if "uddg" in params:
                url = urllib.parse.unquote(params["uddg"][0])
        
        return url
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()


class SimpleDuckDuckGoSearch:
    """Simplified DuckDuckGo search for event discovery."""
    
    def __init__(self):
        self.searcher = DuckDuckGoSearch()
    
    def search_events(self, industry: str, region: str = "", year: str = "2025", max_results: int = 20) -> list[dict]:
        """Search for industry events.
        
        Args:
            industry: Industry type (fintech, payments, ai, etc.)
            region: Geographic region
            year: Event year
            max_results: Max results to return
            
        Returns:
            List of event results
        """
        queries = [
            f"{industry} conferences {year}",
            f"{industry} summit {region} {year}" if region else f"{industry} summit {year}",
            f"{industry} expo {year}",
            f"{industry} forum {region} {year}" if region else f"{industry} forum {year}",
        ]
        
        all_results = []
        seen_urls = set()
        
        for query in queries:
            try:
                results = self.searcher.search(query, max_results=10)
                for result in results:
                    url = result.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(result)
            except Exception as e:
                logger.warning(f"Search failed for '{query}': {e}")
                continue
        
        return all_results[:max_results]
    
    def search_vendors(self, event_name: str, max_results: int = 10) -> list[dict]:
        """Search for vendors/sponsors of an event.
        
        Args:
            event_name: Name of the event
            max_results: Max results to return
            
        Returns:
            List of vendor results
        """
        queries = [
            f"{event_name} sponsors",
            f"{event_name} exhibitors",
            f"{event_name} partners 2025",
        ]
        
        all_results = []
        seen_urls = set()
        
        for query in queries:
            try:
                results = self.searcher.search(query, max_results=5)
                for result in results:
                    url = result.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(result)
            except Exception as e:
                logger.warning(f"Vendor search failed: {e}")
                continue
        
        return all_results[:max_results]


# Global instance
_ddg_search: Optional[DuckDuckGoSearch] = None


def get_duckduckgo_search() -> DuckDuckGoSearch:
    """Get global DuckDuckGo search instance."""
    global _ddg_search
    if _ddg_search is None:
        _ddg_search = DuckDuckGoSearch()
    return _ddg_search
