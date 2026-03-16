# Marketing Agents Swarm

A flexible swarm of research-focused marketing agents that work in a sequential pipeline, searching the web and retrieving data based on your prompts.

## Overview

This project provides a **research agent pipeline system** where:
- Each agent is responsible for a specific research task
- Agents execute sequentially, passing results to the next agent
- You define what each agent researches via prompts and configuration

## Quick Start

```bash
# Install dependencies
cd marketing_agents
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys (OpenAI, Tavily, etc.)

# Run the pipeline
python -m marketing_agents run --prompt "Research competitor pricing for AI tools"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Prompt                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────┬───────┴───────┬─────────────┐
        ▼             ▼               ▼             ▼
   ┌─────────┐  ┌─────────┐    ┌─────────┐  ┌─────────┐
   │ Agent 1 │─▶│ Agent 2 │─▶  │ Agent 3 │─▶│ Output  │
   └─────────┘  └─────────┘    └─────────┘  └─────────┘
```

## Project Structure

```
marketing_agents/
├── agents/           # Individual agent implementations
├── pipeline/         # Sequential execution logic
├── utils/            # Shared utilities
├── config/           # Configuration files
├── docs/             # Detailed documentation
└── main.py           # Entry point
```

## Documentation

- [Agents Registry](docs/agents.md) — List of all available agents
- [Configuration Guide](docs/configuration.md) — Setting up API keys and options
- [Pipeline Design](docs/pipeline.md) — How the sequential execution works
- [Writing Custom Agents](docs/custom-agents.md) — Extending the system

## Defining Your Agents

See [agents.md](docs/agents.md) to define your research agents.
