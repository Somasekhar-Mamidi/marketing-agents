# Configuration Guide

This guide explains how to configure the Marketing Agents Swarm.

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM-based agents |
| `TAVILY_API_KEY` | No | Tavily search API key |
| `SERPER_API_KEY` | No | Serper search API key |

## Getting API Keys

### OpenAI
1. Go to [platform.openai.com](https://platform.openai.com)
2. Navigate to API Keys
3. Create a new secret key

### Tavily
1. Go to [tavily.com](https://tavily.com)
2. Sign up for an account
3. Get your API key from the dashboard

### Serper
1. Go to [serper.dev](https://serper.dev)
2. Sign up for an account
3. Get your API key

## Pipeline Configuration

Edit `config/pipeline.yaml` to configure which agents run and their order:

```yaml
pipeline:
  name: "marketing-research-pipeline"
  
  agents:
    - agent_name: "web_researcher"
      enabled: true
      parameters:
        max_results: 10
        provider: "tavily"
```

## Agent Parameters

Each agent can accept custom parameters in the pipeline config:

```yaml
parameters:
  max_results: 10
  provider: "tavily"
  search_depth: "advanced"
```
