"""Example research agent - use this as a template for your agents."""

import logging
from agents.base import BaseAgent, AgentInput, AgentOutput
from utils.search import WebSearchTool

logger = logging.getLogger(__name__)


class WebResearchAgent(BaseAgent):
    """Example agent that performs web research for a given query.
    
    This agent searches the web and returns structured findings.
    Use this as a template for creating your own research agents.
    """
    
    name = "web_researcher"
    description = "Searches the web for information based on the query"
    
    def __init__(self, provider: str = "tavily", max_results: int = 10):
        """Initialize the research agent.
        
        Args:
            provider: Search provider (tavily, serper)
            max_results: Maximum number of search results
        """
        self.search_tool = WebSearchTool(provider=provider)
        self.max_results = max_results
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute web research for the given query.
        
        Args:
            input_data: Input containing query and context
            
        Returns:
            AgentOutput with search findings
        """
        self.validate_input(input_data)
        
        query = input_data.query
        
        # Use context from previous agents if available
        if input_data.context:
            # You can incorporate previous agent results into your search
            logger.info(f"Context from previous agents: {list(input_data.context.keys())}")
        
        # Perform the search
        try:
            search_results = self.search_tool.search(query, max_results=self.max_results)
            
            # Structure the findings
            findings = {
                "query": query,
                "results": search_results,
                "count": len(search_results),
                "summary": self._generate_summary(search_results)
            }
            
            return AgentOutput(
                agent_name=self.name,
                findings=findings,
                metadata={"provider": self.search_tool.provider}
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return AgentOutput(
                agent_name=self.name,
                findings={"error": str(e)},
                status="failed"
            )
    
    def _generate_summary(self, results: list[dict]) -> str:
        """Generate a summary of search results."""
        if not results:
            return "No results found"
        
        summary_parts = []
        for r in results[:3]:  # Top 3 results
            title = r.get("title", "Untitled")
            summary_parts.append(title)
        
        return "; ".join(summary_parts)
