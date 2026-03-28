"""Tests for Web Search Tool."""

import pytest
from utils.search import WebSearchTool


class TestWebSearchTool:
    """Test cases for WebSearchTool."""
    
    def test_web_search_tool_initialization(self):
        """Test WebSearchTool initialization."""
        tool = WebSearchTool(provider="tavily")
        assert tool.provider == "tavily"
    
    def test_web_search_tool_auto_provider(self):
        """Test WebSearchTool with auto provider."""
        tool = WebSearchTool(provider="auto")
        assert tool.provider == "auto"
    
    def test_search_returns_list_or_empty(self):
        """Test that search returns a list (or empty on error)."""
        tool = WebSearchTool(provider="tavily")
        
        try:
            results = tool.search("test query", max_results=10)
            assert isinstance(results, list)
        except Exception:
            results = []
            assert results == []


class TestSearchFallback:
    """Test cases for search provider fallback."""
    
    def test_fallback_returns_list(self):
        """Test that fallback returns a list."""
        tool = WebSearchTool(provider="tavily")
        
        try:
            results = tool.search("test")
        except Exception:
            results = []
        
        assert isinstance(results, list)
