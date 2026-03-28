# Marketing Agents Swarm

A flexible swarm of research-focused marketing agents with sequential pipeline execution.

## Overview

This project provides an **event research pipeline system** for discovering, qualifying, and generating outreach for industry events. Perfect for event sponsorship research.

## Key Features

- **Input-based discovery**: Start with industry, region, and theme
- **Smart filtering**: Excludes vendor-specific events (Google I/O, AWS re:Invent, etc.)
- **Industry-wide only**: Focuses on public, ecosystem-level events
- **Date verification**: Ensures event dates are accurate and current

## Quick Start

```bash
# Install dependencies
cd marketing_agents
pip install -e .

# Set up environment variables
cp .env.example .env

# Run with industry and region
python -m marketing_agents run --industry Payments --region "Middle East"
```

## Usage

```bash
# Find Payments events in Middle East
python -m marketing_agents run --industry Payments --region "Middle East"

# Find AI conferences in APAC
python -m marketing_agents run --industry "Artificial Intelligence" --region APAC

# Find FinTech events globally
python -m marketing_agents run --industry FinTech --region global

# With custom theme
python -m marketing_agents run --industry Payments --theme "digital payments" --region USA

# Custom output file
python -m marketing_agents run --industry FinTech --output my_events.json

# List available agents
python -m marketing_agents list-agents
```

## Filtering Rules Applied

The pipeline automatically applies these filters:

| Rule | Description |
|------|-------------|
| **Exclude Vendor Events** | Filters out company-specific product launches (Google I/O, AWS re:Invent, etc.) |
| **Industry-wide Only** | Only includes public events with multiple companies/participants |
| **Date Verification** | Marks events with verified dates; excludes uncertain dates |
| **Consistent Filtering** | Same rules applied across all industries |

## Agent Pipeline

| # | Agent | Purpose |
|---|-------|---------|
| 0 | Schema Initialization | Initialize empty event structure |
| 1 | Event Discovery | Find events (with vendor/industry filters) |
| 2 | Event Qualification | Score & tier events (1-10 scale) |
| 3 | Event Website Scraper | Extract details from event websites |
| 4 | Event Intelligence | Strategic analysis & ROI potential |
| 5 | Event Prioritization | Sort & recommend (Reach out/Research/Monitor) |
| 6 | Outreach Email | Generate professional sponsorship emails |
| 7 | Excel Table Generator | Output CSV/Excel-ready format |

## Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--industry` | Yes | Industry (FinTech, Payments, AI, Technology, etc.) |
| `--region` | No | Region (USA, Europe, APAC, Middle East, Asia, global) |
| `--theme` | No | Specific theme (digital payments, blockchain, etc.) |
| `--time-range` | No | Months ahead (12 or 24, default: 12) |
| `--output` | No | Output file (default: event_pipeline_results.json) |

## Project Structure

```
marketing_agents/
├── agents/
│   ├── base.py                    # Base agent class
│   ├── event_discovery.py        # Agent 1: Find events (with filters)
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
    ├── configuration.md           # API keys setup
    ├── pipeline.md               # How it works
    └── custom-agents.md          # Creating new agents
```

## Output

The pipeline generates:
- **JSON file**: Full results with all event data
- **CSV output**: For Excel/Google Sheets import
- **Markdown output**: For documentation
- **Console summary**: Top events with scores and tiers

## Web UI

A Streamlit web interface is available at `app.py`. Features:

```bash
# Run the web UI
streamlit run app.py
```

### UI Features:
- **Sidebar Configuration**: Industry, Region, Theme, Time Range selectors
- **Metrics Dashboard**: Events discovered, Tier 1/2 counts, average score
- **Interactive Table**: Filter by tier, sort by score/date/name
- **Event Details Panel**: Tabbed view (Overview, Website, Intelligence, Outreach)
- **Email Panel**: Copy email, open email client
- **Export Options**: Download CSV, JSON, or Markdown
