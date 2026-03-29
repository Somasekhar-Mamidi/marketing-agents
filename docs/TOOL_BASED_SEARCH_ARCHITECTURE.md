# Tool-Based Web Search Architecture

## Overview

This document describes the new architecture where LLMs use **tool calling** to perform web searches instead of separate search + LLM processing steps.

## Current Architecture (To Be Replaced)

```
┌─────────────┐     Pre-defined Queries     ┌─────────────┐
│   Agent     │ ──────────────────────────→ │ WebSearch   │
│             │ ←── Raw Search Results ───  │ (Tavily)    │
└─────────────┘                             └─────────────┘
       │
       ↓ Manual parsing
┌─────────────┐
│    LLM      │  "Parse these search results..."
│             │
└─────────────┘
```

**Problems:**
- Pre-defined search queries miss nuance
- Agent manually feeds search results to LLM
- No iterative search capability
- Two separate systems to maintain

## New Architecture (Tool-Based)

```
┌─────────────────────────────────────────────────────────┐
│                    Agent                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │  LLM with Tools                                 │   │
│  │                                                 │   │
│  │  "Find fintech events"                          │   │
│  │       ↓                                         │   │
│  │  🤔 "I should search for current events"        │   │
│  │       ↓                                         │   │
│  │  🔧 Call: web_search("fintech conferences 2025")│   │
│  │       ↓                                         │   │
│  │  📊 Results returned                            │   │
│  │       ↓                                         │   │
│  │  🤔 "Need more details on Money20/20"           │   │
│  │       ↓                                         │   │
│  │  🔧 Call: web_fetch("https://money2020.com")    │   │
│  │       ↓                                         │   │
│  │  ✅ Synthesized answer                          │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Advantages:**
- LLM decides WHAT to search (dynamic queries)
- Iterative research (search → analyze → search again)
- Context-aware search terms
- Single system (LLM with tools)
- Simpler code, better quality

## Tools Available to LLM

### 1. `web_search`
```json
{
  "name": "web_search",
  "description": "Search the web for current information about events, companies, or topics",
  "parameters": {
    "query": "Search query string",
    "max_results": "Number of results (default: 10)"
  }
}
```

### 2. `web_fetch`
```json
{
  "name": "web_fetch",
  "description": "Fetch and extract content from a specific URL",
  "parameters": {
    "url": "Website URL to fetch",
    "extract_type": "What to extract (full|text|schema)"
  }
}
```

## Model Assignments (Research-Optimized)

| Agent | Model | Tools | Rationale |
|-------|-------|-------|-----------|
| **intent_understanding** | claude-opus-4-6 | web_search | Deep reasoning + research |
| **event_discovery** | kimi-latest | web_search, web_fetch | 200K context + iterative search |
| **event_intelligence** | claude-opus-4-6 | web_search, web_fetch | Strategic analysis + deep research |
| **vendor_discovery** | kimi-latest | web_search, web_fetch | Multi-vendor research |
| **event_qualification** | claude-sonnet-4-6 | web_search | Verification + scoring |
| **event_website_scraper** | glm-latest | web_fetch | Cost-effective extraction |
| **outreach_email** | claude-sonnet-4-5 | web_search | Personalization research |
| **excel_table_generator** | glm-flash-experimental | - | Simple formatting |

## Implementation Steps

### Phase 1: Core Tool Infrastructure
1. Add `tools` parameter to `ConfigurableLLMClient.complete_for_agent()`
2. Create `ToolRegistry` for available tools
3. Implement `web_search` tool (wrapper around existing WebSearchTool)
4. Implement `web_fetch` tool (wrapper around existing scraper)

### Phase 2: Tool Execution Flow
1. LLM receives prompt + available tools
2. LLM decides to call tool(s)
3. System executes tool, returns results
4. LLM receives results, synthesizes answer
5. (Optional) LLM calls more tools for follow-up

### Phase 3: Prompt Updates
1. Update system prompts to mention available tools
2. Remove "LATEST NEWS GROUNDING" markers
3. Add examples of effective tool usage

### Phase 4: Search Provider Simplification
1. Comment out Tavily, Serper, Search1API dependencies
2. Keep DuckDuckGo as fallback
3. LLM-driven search replaces manual search

## Example Flow: Event Discovery

**User Query:** "Find payment conferences in Europe 2025"

**Traditional Approach:**
1. Agent generates 30 pre-defined queries
2. Searches each query via Tavily
3. Aggregates results
4. Feeds to LLM for parsing
5. Manual deduplication

**Tool-Based Approach:**
1. LLM receives: "Find payment conferences in Europe 2025"
2. LLM thinks: "I need to search for current payment conferences in Europe"
3. LLM calls: `web_search("payment conferences Europe 2025")`
4. Gets results, analyzes
5. LLM thinks: "Money20/20 looks big, let me get more details"
6. LLM calls: `web_fetch("https://money2020.com/europe")`
7. Synthesizes final answer with details

## Code Changes Required

### 1. `utils/configurable_llm_client.py`
```python
# Add tool support to complete_for_agent
def complete_for_agent(
    self,
    agent_name: str,
    prompt: str,
    system_message: Optional[str] = None,
    tools: Optional[List[Dict]] = None,  # NEW
    response_format: Optional[Dict] = None
) -> LLMResponse:
    # ... existing code ...
    
    # If tools provided and model supports them
    if tools and config.supports_tools:
        return self._execute_with_tools(
            prompt, config, tools, system_message, response_format
        )
    
    # ... existing completion logic ...
```

### 2. `utils/tools.py` (NEW FILE)
```python
class ToolRegistry:
    """Registry of available tools for LLM agents."""
    
    def __init__(self):
        self._tools = {}
    
    def register(self, name: str, handler: Callable, schema: Dict):
        """Register a tool."""
        self._tools[name] = {"handler": handler, "schema": schema}
    
    def execute(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool."""
        if tool_name not in self._tools:
            return f"Error: Tool '{tool_name}' not found"
        return self._tools[tool_name]["handler"](**arguments)
    
    def get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions for LLM."""
        return [
            {"type": "function", "function": tool["schema"]}
            for tool in self._tools.values()
        ]

# Initialize with web tools
tool_registry = ToolRegistry()
tool_registry.register("web_search", web_search_handler, WEB_SEARCH_SCHEMA)
tool_registry.register("web_fetch", web_fetch_handler, WEB_FETCH_SCHEMA)
```

### 3. `agents/event_discovery.py` (Example Update)
```python
# OLD: Separate search + LLM
search_results = self.search_tool.search(query, max_results=20)
events = self.llm.parse(search_results)

# NEW: LLM with tools
result = llm_client.complete_for_agent(
    agent_name="event_discovery",
    prompt=f"Find events for: {query}",
    tools=tool_registry.get_tool_definitions(),  # LLM decides when to search
    system_message=UPDATED_PROMPT_WITH_TOOLS
)
```

## Migration Strategy

### Step 1: Add Tool Support (Backward Compatible)
- Add tool parameters without breaking existing code
- Test with one agent (event_discovery)

### Step 2: Gradual Agent Migration
- Migrate agents one by one
- Compare quality between old and new approach
- Keep old code as fallback

### Step 3: Simplify Search Infrastructure
- Once all agents migrated, comment out manual search
- Keep DuckDuckGo for LLM tool backend

## Expected Benefits

1. **Quality**: LLM-driven research vs template queries
2. **Flexibility**: Dynamic, context-aware searches
3. **Simplicity**: Single system instead of two
4. **Maintainability**: Less code, clearer flow
5. **Cost**: No more 30+ pre-defined queries per discovery

## Risk Mitigation

1. **Tool Support Not Universal**: Only use tools on supported models
2. **Rate Limits**: Implement caching for tool results
3. **Latency**: Tools add round-trips, but improve accuracy
4. **Fallback**: Keep manual search as fallback option
