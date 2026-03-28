# Pipeline Design

The Marketing Agents Swarm uses a **sequential pipeline architecture** where 8 agents execute one after another, passing results to the next agent.

## How It Works

```
User Inputs: Industry + Region + Theme + Time Range
    │
    ▼
┌─────────────────────────────────────────┐
│         Pipeline Orchestrator           │
│  (manages execution order & context)    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────┐──┌─────────┐──┌─────────┐──┌─────────┐──┌─────────┐──┌─────────┐──┌─────────┐──┌─────────┐
│Agent 0  │─▶│Agent 1  │─▶│Agent 2  │─▶│Agent 3  │─▶│Agent 4  │─▶│Agent 5  │─▶│Agent 6  │─▶│Agent 7  │
│Schema   │  │Discovery│  │Qualify  │  │Scraper  │  │Intelligence│ │Prioritize│  │Email    │  │Excel    │
│Init     │  │         │  │         │  │         │  │         │  │         │  │         │  │Export   │
└─────────┘──└─────────┘──└─────────┘──└─────────┘──└─────────┘──└─────────┘──└─────────┘──┴─────────┘
```

## 8-Agent Pipeline Details

| # | Agent | Purpose | Input | Output |
|---|-------|---------|-------|--------|
| 0 | Schema Initialization | Create empty event structure | None | Empty events array |
| 1 | Event Discovery | Find events with filters | Industry, Region, Theme | Raw event list |
| 2 | Event Qualification | Score & tier events | Events | Scored events |
| 3 | Event Website Scraper | Extract website details | Events with URLs | Enriched events |
| 4 | Event Intelligence | Strategic analysis | Qualified events | Intelligence insights |
| 5 | Event Prioritization | Sort & recommend | Analyzed events | Prioritized list |
| 6 | Outreach Email | Generate sponsorship emails | Prioritized events | Email templates |
| 7 | Excel Table Generator | Export to CSV/Excel | Complete events | CSV, JSON, Markdown |

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
