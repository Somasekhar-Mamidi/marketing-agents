"""Tool registry and handlers for LLM tool calling.

This module provides tools that LLMs can call to perform actions like
web search and web fetching. Tools are registered with a central registry
and can be executed by the LLM client.
"""

import logging
import json
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass
from utils.search import WebSearchTool
from utils.web_scraper import EventWebsiteScraper

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a tool available to LLMs."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable


class ToolRegistry:
    """Registry of available tools for LLM agents."""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._search_tool: Optional[WebSearchTool] = None
        self._scraper: Optional[EventWebsiteScraper] = None
    
    def register(self, tool: ToolDefinition):
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def execute(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool and return result as string."""
        if tool_name not in self._tools:
            error_msg = f"Error: Tool '{tool_name}' not found"
            logger.error(error_msg)
            return error_msg
        
        tool = self._tools[tool_name]
        try:
            logger.info(f"Executing tool: {tool_name} with args: {arguments}")
            result = tool.handler(**arguments)
            # Convert result to string for LLM consumption
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2)
            return str(result)
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions in OpenAI format for LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self._tools.values()
        ]
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)


# Global tool registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = _create_default_registry()
    return _tool_registry


def _create_default_registry() -> ToolRegistry:
    """Create registry with default tools."""
    registry = ToolRegistry()
    
    # Register web_search tool
    registry.register(ToolDefinition(
        name="web_search",
        description="Search the web for current information about events, companies, or topics. "
                    "Use this when you need up-to-date information not in your training data. "
                    "Returns search results with titles, URLs, and content snippets.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific and include relevant keywords like year, location, industry."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-20). Default: 10",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        },
        handler=_web_search_handler
    ))
    
    # Register web_fetch tool
    registry.register(ToolDefinition(
        name="web_fetch",
        description="Fetch and extract content from a specific URL. "
                    "Use this when you need detailed information from a specific webpage. "
                    "Returns the page content, metadata, and extracted information.",
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The complete URL to fetch (must start with http:// or https://)"
                },
                "extract_type": {
                    "type": "string",
                    "description": "What to extract from the page",
                    "enum": ["full", "text", "structured"],
                    "default": "structured"
                }
            },
            "required": ["url"]
        },
        handler=_web_fetch_handler
    ))
    
    return registry


def _web_search_handler(query: str, max_results: int = 10) -> List[Dict]:
    """Handle web_search tool calls."""
    logger.info(f"web_search: query='{query}', max_results={max_results}")
    
    # Use existing WebSearchTool with DuckDuckGo (no API key needed)
    search_tool = WebSearchTool(provider="duckduckgo", enable_cache=True)
    results = search_tool.search(query, max_results=max_results)
    
    # Format results for LLM
    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append({
            "rank": i,
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "content": result.get("content", "")[:500]  # Limit content length
        })
    
    return {
        "query": query,
        "total_results": len(formatted),
        "results": formatted
    }


def _web_fetch_handler(url: str, extract_type: str = "structured") -> Dict:
    """Handle web_fetch tool calls."""
    logger.info(f"web_fetch: url='{url}', extract_type='{extract_type}'")
    
    # Use existing EventWebsiteScraper
    scraper = EventWebsiteScraper(timeout=30)
    
    try:
        if extract_type == "structured":
            # Extract structured event data
            data = scraper.scrape_event_page(url)
            return {
                "url": url,
                "success": True,
                "extracted_data": data
            }
        else:
            # Fetch raw content
            import requests
            response = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (compatible; MarketingAgents/1.0)"
            })
            content = response.text[:5000]  # Limit content
            
            return {
                "url": url,
                "success": True,
                "status_code": response.status_code,
                "content_length": len(content),
                "content_preview": content[:1000]
            }
    except Exception as e:
        return {
            "url": url,
            "success": False,
            "error": str(e)
        }


# Convenience function for agents
def get_research_tools() -> List[Dict]:
    """Get tools suitable for research-heavy agents."""
    return get_tool_registry().get_tool_definitions()
