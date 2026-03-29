# Agent Capabilities Analysis with Search Grounding & Web Fetch

## Executive Summary

This analysis covers:
1. **Search Grounding Requirements** - Which agents need real-time search + LLM integration
2. **Web Fetch/Scrape Requirements** - Which agents need web content extraction
3. **Model Capabilities** - Which Grid AI models support search grounding natively
4. **Optimized Assignments** - Updated model recommendations considering search capabilities

---

## Current Search & Web Infrastructure

### Existing Search Tool (`utils/search.py`)
```python
WebSearchTool(provider="auto")  # Tavily → Serper → Search1API → DuckDuckGo
```
- **Providers**: Tavily, Serper, Search1API, DuckDuckGo
- **Features**: Caching, retry, fallback, context extraction
- **Output**: Title, URL, Content snippet

### Existing Web Scraper (`utils/web_scraper.py`)
```python
EventWebsiteScraper(timeout=30)  # Extracts dates, venue, organizer, etc.
```
- **Capabilities**: HTML parsing, structured data extraction
- **Extracts**: Dates, location, organizer, contact info, sponsorship URLs

### Key Gap
Current architecture separates search/scrape from LLM - agents manually feed search results into LLM prompts. **Search Grounding** would allow LLM to do this natively.

---

## Agent-by-Agent Search & Web Requirements

### 1. Schema Initialization
**Search Grounding**: ❌ Not needed
**Web Fetch**: ❌ Not needed
**Current Pattern**: Template-based JSON generation
**Notes**: Static schema, no external data needed

**Model Requirements**: JSON mode only
**Recommended**: `claude-haiku-4-5` or `glm-flash`

---

### 2. Intent Understanding ⭐ CRITICAL
**Search Grounding**: ⚠️ **BENEFICIAL** but not required
**Web Fetch**: ❌ Not needed
**Current Pattern**: 
```python
# Current: Pure LLM inference
response = llm.complete(prompt, system_message)
```
**Enhanced Pattern (with search grounding)**:
```python
# With search grounding: LLM can verify industry terms, trending topics
response = llm.complete_with_search(
    prompt, 
    search_queries=["fintech conferences 2025 trends"],
    system_message="..."
)
```

**Why Search Grounding Helps**:
- Verify industry terminology is current
- Check trending themes in the industry
- Validate region-specific terminology
- Ground intent in real-world context

**Model Requirements**: 
- ✅ JSON mode (required)
- 🔍 Search grounding (beneficial)
- 🧠 High reasoning (critical)

**Recommended**: 
- **Primary**: `claude-opus-4-6` (best reasoning)
- **With Search**: `gemini-3.1-pro` (native search grounding)

---

### 3. Event Discovery ⭐⭐⭐ HIGH VOLUME
**Search Grounding**: ✅ **HIGHLY BENEFICIAL**
**Web Fetch**: ✅ **REQUIRED** (event details)
**Current Pattern**:
```python
# Current: Separate search + LLM processing
search_results = search_tool.search(query)
parsed_events = llm.parse(search_results)  # Agent parses manually
```

**Enhanced Pattern (with search grounding)**:
```python
# With search grounding: LLM does search + parsing in one call
response = llm.complete_with_search(
    "Find fintech conferences in Europe 2025",
    search_queries_auto_generated=True,  # LLM generates optimal queries
    max_search_results=20
)
```

**Why Search Grounding Transforms This Agent**:
- **Current bottleneck**: Agent manually iterates search queries
- **With grounding**: LLM can dynamically refine searches based on partial results
- **Better results**: LLM can synthesize across multiple sources in one context
- **Cost efficiency**: Fewer separate API calls (search + LLM merged)

**Model Requirements**:
- ✅ JSON mode (required)
- 🔍 Search grounding (highly beneficial)
- 📏 Long context (for 20+ search results)
- 💰 Cost-effective (runs many times)

**Recommended**:
- **Primary**: `gemini-3-flash-preview` (1M context, cheap, has search)
- **Alternative**: `claude-sonnet-4-5` (no native search, but better reasoning)

---

### 4. Event Qualification
**Search Grounding**: ✅ **BENEFICIAL**
**Web Fetch**: ⚠️ Sometimes (if checking event reputation)
**Current Pattern**: Rule-based + LLM scoring

**Why Search Grounding Helps**:
- Look up event reputation online
- Find past attendee reviews
- Verify sponsor lists from external sources
- Ground qualification in real data

**Model Requirements**:
- ✅ JSON mode (required)
- 🔍 Search grounding (beneficial)
- 🧠 High reasoning (for judgment)

**Recommended**: 
- **Primary**: `claude-sonnet-4-6`
- **With Search**: `gemini-3.1-pro`

---

### 5. Event Website Scraper
**Search Grounding**: ❌ Not needed
**Web Fetch**: ✅ **REQUIRED** (core functionality)
**Current Pattern**:
```python
# Current: BeautifulSoup + heuristics
scraper = EventWebsiteScraper()
data = scraper.scrape_event_page(url)
```

**Enhanced Pattern (Vision + LLM)**:
```python
# With vision LLM: Can parse screenshots when HTML fails
html_content = fetch_url(url)
screenshot = capture_screenshot(url)  # For complex layouts
response = vision_llm.parse(
    html=html_content,
    screenshot=screenshot,  # Fallback for SPAs, complex UIs
    instruction="Extract event dates, venue, pricing"
)
```

**Why Vision Model Helps**:
- Handles JavaScript-heavy sites (SPAs)
- Parses visual layouts (tables, grids)
- Extracts from images (event posters, infographics)
- More resilient than HTML-only parsing

**Model Requirements**:
- ✅ JSON mode (required)
- 👁️ Vision (highly beneficial for complex sites)
- 💰 Low cost (runs per event, high volume)

**Recommended**:
- **HTML-only**: `glm-flash` (cheapest)
- **With Vision**: `gemini-3-flash-preview` (vision + cheap)
- **Fallback**: `claude-haiku-4-5` (if no vision needed)

---

### 6. Event Intelligence ⭐⭐⭐ STRATEGIC
**Search Grounding**: ✅✅ **CRITICAL**
**Web Fetch**: ✅ **REQUIRED** (competitor analysis)
**Current Pattern**: Rule-based templates (see `EVENT_AUDIENCES` dict)

**Current Limitation**:
```python
# Current: Static mapping
EVENT_AUDIENCES = {
    "fintech": {"roles": "CFO, CTO, ..."},
    "ai": {"roles": "Data Scientists, ..."}
}
```

**Enhanced Pattern (with search grounding)**:
```python
# With search: Real-time competitive intelligence
response = llm.complete_with_search(
    f"Analyze {event_name} sponsorship strategy",
    search_queries=[
        f"{event_name} 2024 sponsors",
        f"{event_name} attendee demographics",
        f"{event_name} vs competitor events"
    ],
    system_message="Analyze event for sponsorship ROI"
)
```

**Why Search Grounding is GAME-CHANGING for This Agent**:
- **Current**: Static audience assumptions
- **With search**: Real past sponsor lists, attendee feedback, competitor events
- **Strategic value**: 10x better insights with live data
- **ROI calculation**: Based on real ticket prices, past sponsor visibility

**Model Requirements**:
- ✅ JSON mode (required)
- 🔍 Search grounding (critical)
- 📏 Very long context (200K+ for multiple searches)
- 🧠 Very high reasoning (strategic analysis)

**Recommended**:
- **Primary**: `gemini-3.1-pro` (1M context + search grounding)
- **Alternative**: `kimi-latest` (200K context, manual search feed)
- **Premium**: `claude-opus-4-6` (best reasoning, manual search)

---

### 7. Event Prioritization
**Search Grounding**: ❌ Not needed
**Web Fetch**: ❌ Not needed
**Current Pattern**: Sorting algorithm on scores
**Notes**: Pure data processing, no external data needed

**Model Requirements**: JSON mode, basic reasoning
**Recommended**: `claude-haiku-4-5` or `glm-flash`

---

### 8. Outreach Email
**Search Grounding**: ⚠️ **BENEFICIAL** (research recipient)
**Web Fetch**: ⚠️ Sometimes (personalization)
**Current Pattern**: Template + LLM generation

**Enhanced Pattern**:
```python
# With search: Personalize based on recipient's recent activity
response = llm.complete_with_search(
    "Draft sponsorship email to event organizer",
    search_queries=[
        f"{organizer_name} recent news",
        f"{event_name} sponsorship opportunities 2025"
    ]
)
```

**Why Search Grounding Helps**:
- Reference recent organizer achievements
- Mention specific event details from latest announcements
- Show you've done your homework
- Higher response rates

**Model Requirements**:
- ❌ JSON mode (not needed - natural language)
- 🔍 Search grounding (beneficial)
- 🧠 High reasoning (creative + professional)

**Recommended**: 
- **Primary**: `claude-sonnet-4-5`
- **With Search**: `gemini-3.1-pro` or `gemini-3-flash`

---

### 9. Vendor Discovery ⭐⭐⭐ RESEARCH INTENSIVE
**Search Grounding**: ✅✅ **CRITICAL**
**Web Fetch**: ✅ **REQUIRED** (vendor details)
**Current Pattern**: Search tool + LLM extraction

**Enhanced Pattern**:
```python
# With search grounding: Discover vendors across multiple categories
response = llm.complete_with_search(
    "Find booth builders for ATPS Dublin",
    search_queries_auto=True,  # LLM generates: "booth builders Dublin", "exhibition stands Ireland", etc.
    max_search_results=30
)
```

**Why Search Grounding is ESSENTIAL**:
- Multi-category vendor search (booth builders, AV, catering, etc.)
- Local vendor discovery (Dublin vs Amsterdam)
- Real-time availability checking
- Portfolio verification (search their past work)

**Model Requirements**:
- ✅ JSON mode (required)
- 🔍 Search grounding (critical)
- 📏 Very long context (1M ideal for 30+ vendors)
- 💰 Cost-effective (runs per event)

**Recommended**:
- **Primary**: `gemini-3-flash-preview` (1M context + search + cheap)
- **Alternative**: `kimi-latest` (200K context)

---

### 10. Excel Table Generator
**Search Grounding**: ❌ Not needed
**Web Fetch**: ❌ Not needed
**Current Pattern**: DataFrame formatting
**Notes**: Pure data transformation

**Model Requirements**: JSON mode only
**Recommended**: `open-fast` or `glm-flash` (cheapest)

---

## Search Grounding Capabilities by Model

### Models with Native Search Grounding

| Model | Provider | Native Search | Notes |
|-------|----------|---------------|-------|
| `gemini-3.1-pro` | Google | ✅ Yes | Google Search integration, real-time |
| `gemini-3-flash-preview` | Google | ✅ Yes | Same search as Pro, faster & cheaper |
| `gemini-3-pro-preview` | Google | ✅ Yes | Preview with search |

### Models Without Native Search (Manual Feed Required)

| Model | Provider | Workaround |
|-------|----------|------------|
| `claude-opus-4-6` | Anthropic | Feed search results via tool use |
| `claude-sonnet-4-6` | Anthropic | Feed search results via tool use |
| `claude-sonnet-4-5` | Anthropic | Feed search results via tool use |
| `claude-haiku-4-5` | Anthropic | Feed search results via tool use |
| `kimi-latest` | Moonshot | Feed search results via context |
| `glm-latest` | Zhipu | Feed search results via context |
| `open-large` | OpenAI-compat | Feed search results via context |
| `open-fast` | OpenAI-compat | Feed search results via context |

---

## Updated Model Assignments (Considering Search)

### Scenario A: Maximum Performance (Use Gemini for Search-Heavy Agents)

| Agent | Model | Rationale |
|-------|-------|-----------|
| **intent_understanding** | `claude-opus-4-6` | Best reasoning, search not critical |
| **event_discovery** | `gemini-3-flash-preview` | Search grounding + 1M context + cheap |
| **event_intelligence** | `gemini-3.1-pro` | Search grounding critical + 1M context |
| **vendor_discovery** | `gemini-3-flash-preview` | Search grounding critical + 1M context + cheap |
| **event_qualification** | `claude-sonnet-4-6` | High reasoning, search beneficial but not critical |
| **event_website_scraper** | `gemini-3-flash-preview` | Vision support for complex sites |
| **outreach_email** | `claude-sonnet-4-5` | Best writing quality |
| **event_prioritization** | `claude-haiku-4-5` | Simple sorting task |
| **schema_initialization** | `glm-flash` | Cheapest JSON generation |
| **excel_table_generator** | `open-fast` | Fastest structured output |

**Cost Estimate (per 1000 pipelines)**: ~$120

---

### Scenario B: Balanced Approach (Hybrid)

| Agent | Model | Rationale |
|-------|-------|-----------|
| **intent_understanding** | `claude-opus-4-6` | Critical reasoning |
| **event_discovery** | `claude-sonnet-4-5` | Balance quality/cost (manual search) |
| **event_intelligence** | `kimi-latest` | 200K context for manual search feed |
| **vendor_discovery** | `gemini-3-flash-preview` | Search grounding essential |
| **event_qualification** | `claude-sonnet-4-6` | Quality judgment |
| **event_website_scraper** | `glm-flash` | Cheapest extraction |
| **outreach_email** | `claude-sonnet-4-5` | Writing quality |
| **event_prioritization** | `claude-haiku-4-5` | Fast ranking |
| **schema_initialization** | `claude-haiku-4-5` | Simple JSON |
| **excel_table_generator** | `open-fast` | Structured data |

**Cost Estimate (per 1000 pipelines)**: ~$160

---

### Scenario C: Cost Optimized (Maximum Gemini Usage)

| Agent | Model | Rationale |
|-------|-------|-----------|
| **intent_understanding** | `gemini-3.1-pro` | Good reasoning + search |
| **event_discovery** | `gemini-3-flash-preview` | Search + cheap |
| **event_intelligence** | `gemini-3-flash-preview` | Search + 1M context |
| **vendor_discovery** | `gemini-3-flash-preview` | Search + cheap |
| **event_qualification** | `gemini-3.1-pro` | Search for verification |
| **event_website_scraper** | `gemini-3-flash-preview` | Vision + cheap |
| **outreach_email** | `gemini-3.1-pro` | Search for personalization |
| **event_prioritization** | `gemini-3-flash-preview` | Fast + cheap |
| **schema_initialization** | `gemini-3-flash-preview` | JSON mode |
| **excel_table_generator** | `open-fast` | Structured output |

**Cost Estimate (per 1000 pipelines)**: ~$65

---

## Implementation Recommendations

### Phase 1: Quick Wins (Immediate Value)

**Agents to migrate to Gemini (for search grounding)**:
1. **vendor_discovery** → `gemini-3-flash-preview`
   - Highest impact: Real-time vendor discovery
   - Cost: Cheapest option
   - Context: 1M tokens for 30+ vendors

2. **event_intelligence** → `gemini-3.1-pro`
   - Second highest impact: Competitive intelligence
   - Justifies Pro: Strategic insights worth premium

### Phase 2: Quality Agents (Reasoning-Critical)

Keep on Claude for reasoning quality:
- **intent_understanding** → `claude-opus-4-6`
- **event_qualification** → `claude-sonnet-4-6`
- **outreach_email** → `claude-sonnet-4-5`

### Phase 3: Cost-Optimized Agents

Migrate to cheapest models:
- **event_website_scraper** → `glm-flash`
- **event_prioritization** → `claude-haiku-4-5`
- **schema_initialization** → `glm-flash`
- **excel_table_generator** → `open-fast`

---

## Search Grounding Implementation Strategy

### Option 1: Native Grounding (If Grid AI Supports Gemini-Style)

If your Grid AI endpoint supports search grounding parameters:
```python
# Enhanced LLM client with search grounding
response = llm.complete(
    prompt="Find fintech events in Dublin",
    model="gemini-3-flash-preview",
    tools=[{"type": "search"}],  # Enable search grounding
    search_config={
        "max_results": 10,
        "recency_days": 365
    }
)
```

### Option 2: Manual Search Feed (Current Architecture)

Keep current separation but optimize:
```python
# Agent orchestrates search + LLM
search_results = search_tool.search(query, max_results=20)
response = llm.complete(
    prompt=f"Analyze these events: {search_results}",
    model="kimi-latest",  # 200K context for large result sets
    max_tokens=4000
)
```

### Option 3: Hybrid (Recommended)

Use native grounding where available, manual feed elsewhere:
```python
if model in GEMINI_MODELS and supports_search_grounding:
    # Use native search
    response = llm.complete_with_search(prompt)
else:
    # Manual search + Claude reasoning
    search_results = search_tool.search(query)
    response = llm.complete(prompt_with_results)
```

---

## Key Takeaways

### Agents That Benefit MOST from Search Grounding

1. **vendor_discovery** (Critical) - Real-time vendor discovery across categories
2. **event_intelligence** (Critical) - Competitive intelligence, sponsor research
3. **event_discovery** (High) - Dynamic search refinement, broader discovery

### Agents That DON'T Need Search

1. **schema_initialization** - Static templates
2. **event_prioritization** - Data processing only
3. **excel_table_generator** - Data formatting only

### Best Value Models for Your Use Case

| Use Case | Model | Why |
|----------|-------|-----|
| Search + Long Context | `gemini-3-flash-preview` | 1M context, search, cheap |
| Search + Quality | `gemini-3.1-pro` | Best search results |
| Reasoning (no search) | `claude-opus-4-6` | Best judgment |
| Cheapest JSON | `glm-flash` | Ultra-low cost |

---

## Next Steps

1. **Confirm Grid AI search capabilities**:
   - Do Gemini models have native search grounding?
   - Or do you need to use manual search feed?

2. **Pilot with 2 agents**:
   - Migrate `vendor_discovery` to `gemini-3-flash-preview`
   - Migrate `event_intelligence` to `gemini-3.1-pro`
   - Compare results vs current approach

3. **Measure impact**:
   - Vendor discovery: More vendors found? Better quality?
   - Intelligence: More strategic insights? Better sponsor lists?

**Ready to implement once you confirm search grounding availability!**
