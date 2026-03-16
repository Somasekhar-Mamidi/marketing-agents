# Marketing Agents Swarm

A flexible swarm of research-focused marketing agents with sequential pipeline execution.

## Overview

This project provides an **event research pipeline system** for discovering, qualifying, and generating outreach for industry events. Perfect for event sponsorship research.

## Quick Start

```bash
# Install dependencies
cd marketing_agents
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys (OpenAI, Tavily, etc.)

# Run the event research pipeline
python -m marketing_agents run --prompt "Find FinTech conferences 2025"
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
        ┌─────────┬─────────┬─────────┬─────────┬─────────┐
        ▼         ▼         ▼         ▼         ▼         ▼
   ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
   │Discover││Qualify ││ Scrape ││Intelli-││Priorit-││Outreach│
   │ Events ││ Events ││Website ││  gence ││  ize   ││ Email  │
   └────────┘└────────┘└────────┘└────────┘└────────┘└────────┘
                                                                  │
                                                                  ▼
                                                           ┌────────┐
                                                           │ Excel  │
                                                           │Output  │
                                                           └────────┘
```

## Agent Pipeline

| # | Agent | Purpose |
|---|-------|---------|
| 1 | Event Discovery | Find events globally (FinTech, AI, Payments, etc.) |
| 2 | Event Qualification | Score & tier events (1-10 scale) |
| 3 | Event Website Scraper | Extract details from event websites |
| 4 | Event Intelligence | Strategic analysis & ROI potential |
| 5 | Event Prioritization | Sort & recommend (Reach out/Research/Monitor) |
| 6 | Outreach Email | Generate professional sponsorship emails |
| 7 | Excel Table Generator | Output CSV/Excel-ready format |

## JSON Schema

All agents share a common JSON schema for reliable data passing:

```json
{
  "events": [
    {
      "event_name": "...",
      "event_website": "...",
      "city": "...",
      "country": "...",
      "overall_score": "...",
      "priority_tier": "...",
      "outreach_email": "...",
      ...
    }
  ]
}
```

## Project Structure

```
marketing_agents/
├── agents/
│   ├── base.py                    # Base agent class
│   ├── event_discovery.py        # Agent 1: Find events
│   ├── event_qualification.py     # Agent 2: Score events
│   ├── event_website_scraper.py   # Agent 3: Extract details
│   ├── event_intelligence.py      # Agent 4: Strategic analysis
│   ├── event_prioritization.py    # Agent 5: Sort & recommend
│   ├── outreach_email.py          # Agent 6: Generate emails
│   └── excel_table_generator.py   # Agent 7: Excel output
├── pipeline/
│   └── orchestrator.py            # Sequential execution
├── utils/
│   └── search.py                  # Web search (Tavily, Serper)
├── config/
│   └── pipeline.yaml              # Config files
├── schema.py                      # Shared JSON schema
├── main.py                        # CLI entry point
└── docs/
    ├── agents.md                  # Agent registry
    ├── configuration.md          # API keys setup
    ├── pipeline.md               # How it works
    └── custom-agents.md          # Creating new agents
```

## Documentation

- [Agents Registry](docs/agents.md) — List of all available agents
- [Configuration Guide](docs/configuration.md) — Setting up API keys
- [Pipeline Design](docs/pipeline.md) — Sequential execution explained
- [Writing Custom Agents](docs/custom-agents.md) — Extending the system

## Configuration

Set up your `.env` file:

```bash
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
SERPER_API_KEY=your_serper_key
```

## Running the Pipeline

```bash
# Basic usage
python -m marketing_agents run --prompt "Find AI conferences 2025"

# List available agents
python -m marketing_agents list-agents
```

## Output

The pipeline generates:
- **JSON file**: `event_pipeline_results.json` - Full results
- **CSV output**: For Excel/Google Sheets import
- **Console summary**: Top events with scores
