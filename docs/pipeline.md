# Pipeline Design

The Marketing Agents Swarm uses a **sequential pipeline architecture** where agents execute one after another, passing results to the next agent.

## How It Works

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────┐
│         Pipeline Orchestrator           │
│  (manages execution order & context)    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Agent 1 │───▶│ Agent 2 │───▶│ Agent 3 │
└─────────┘    └─────────┘    └─────────┘
    │              │              │
    ▼              ▼              ▼
 Findings     Findings      Final Output
 (context)    (context)
```

## Execution Flow

1. **Initialize**: Pipeline loads configuration and registers agents
2. **Execute**: Each agent receives:
   - `query`: The original prompt or modified query
   - `context`: Results from all previous agents
   - `parameters`: Agent-specific configuration
3. **Pass Results**: Each agent's output becomes context for the next
4. **Return**: Final output from the last agent is returned

## Context Passing

Each agent receives context from previous agents:

```python
def execute(self, input_data: AgentInput) -> AgentOutput:
    # Access previous agent results
    previous_results = input_data.context
    
    # Your research logic
    
    # Return findings that become context for next agent
    return AgentOutput(
        agent_name=self.name,
        findings={"key": "value"},
        metadata={}
    )
```

## Adding Agents to Pipeline

In `main.py`:

```python
from agents.example import WebResearchAgent

def create_pipeline() -> Pipeline:
    pipeline = Pipeline()
    pipeline.add_agent(WebResearchAgent(max_results=10))
    return pipeline
```

## Error Handling

If any agent fails, the pipeline stops and raises an exception. Configure error handling as needed.
