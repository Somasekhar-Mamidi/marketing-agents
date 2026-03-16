# Agents Registry

This file documents all agents in the marketing swarm. Each agent is responsible for a specific research task and passes its results to the next agent in the pipeline.

## Adding New Agents

To add a new agent:
1. Create a new agent class in `agents/` directory
2. Register it in the `AGENT_REGISTRY` below
3. Update this document

## Agent Template

```python
from agents.base import BaseAgent
from pydantic import Field

class MyNewAgent(BaseAgent):
    name: str = "my_new_agent"
    description: str = "What this agent researches"
    
    def execute(self, input_data: dict, context: dict) -> dict:
        # Research logic here
        return {"result": "..."}
```

## Agent Registry

| Agent Name | Description | Status |
|------------|--------------|--------|
| *(Define your agents below)* | | |

---

## Your Custom Agents

*Define your research agents here. For each agent, specify:*
- *Name*: What you call the agent*
- *Research Scope*: What it searches for*
- *Output Format*: What data it returns*

### Agent Definition Format

```markdown
### Agent Name
- **Researches**: [what this agent finds]
- **Output**: [format of returned data]
- **Dependencies**: [other agents this needs data from, if any]
```

---

## Pipeline Configuration

The pipeline processes agents in sequence. Configure the order in `config/pipeline.yaml`:

```yaml
pipeline:
  agents:
    - agent_name: "competitor_scout"
      enabled: true
    - agent_name: "market_trends"
      enabled: true
```
