# Writing Custom Agents

This guide shows how to create your own research agents.

## Quick Start

Create a new file in `agents/` directory:

```python
"""My custom research agent."""

from agents.base import BaseAgent, AgentInput, AgentOutput

class MyResearchAgent(BaseAgent):
    name = "my_research_agent"
    description = "What this agent researches"
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        # Your research logic here
        findings = {"key": "value"}
        
        return AgentOutput(
            agent_name=self.name,
            findings=findings,
            metadata={}
        )
```

## Agent Structure

Every agent must:
1. Inherit from `BaseAgent`
2. Define `name` and `description`
3. Implement `execute()` method

## Using the Search Tool

Agents can use the built-in search tool:

```python
from agents.base import BaseAgent, AgentInput, AgentOutput
from utils.search import WebSearchTool

class CompetitorScout(BaseAgent):
    name = "competitor_scout"
    description = "Researches competitor information"
    
    def __init__(self):
        self.search = WebSearchTool(provider="tavily")
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        query = input_data.query
        
        # Search the web
        results = self.search.search(query, max_results=10)
        
        # Process results
        findings = {
            "query": query,
            "competitors": results,
            "count": len(results)
        }
        
        return AgentOutput(
            agent_name=self.name,
            findings=findings
        )
```

## Accessing Context

Access results from previous agents:

```python
def execute(self, input_data: AgentInput) -> AgentOutput:
    # Previous agent results
    context = input_data.context
    
    # Example: get competitor data from previous agent
    competitor_data = context.get("competitor_scout", {})
    
    # Use in your research
    ...
```

## Registering Your Agent

Add to the pipeline in `main.py`:

```python
from agents.my_agent import MyResearchAgent

def create_pipeline() -> Pipeline:
    pipeline = Pipeline()
    pipeline.add_agent(MyResearchAgent())
    return pipeline
```

## Best Practices

1. **Validate input**: Use `self.validate_input(input_data)`
2. **Handle errors**: Return `status="failed"` on errors
3. **Add metadata**: Include useful info in metadata
4. **Generate summaries**: Include a summary in findings for next agent
