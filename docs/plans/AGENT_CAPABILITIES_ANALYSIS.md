# Agent Capabilities Analysis & Model Matching

## Agent Requirements Matrix

### 1. Schema Initialization
**Purpose**: Initialize data structures and schemas
**Complexity**: ⭐ Low
**Requirements**:
- ✅ JSON Mode: Required (structured schema output)
- ❌ Vision: Not needed
- 📏 Context: 4K-8K sufficient
- 🧠 Reasoning: Basic
- 💰 Cost Priority: Low cost (runs once per pipeline)

**Recommended**: `claude-haiku-4-5-20251001` or `glm-flash-experimental`

---

### 2. Intent Understanding
**Purpose**: Parse natural language queries to extract structured intent (industry, region, themes)
**Complexity**: ⭐⭐⭐⭐⭐ Critical
**Requirements**:
- ✅ JSON Mode: Required (structured intent output)
- ❌ Vision: Not needed
- 📏 Context: 16K-32K (for complex queries)
- 🧠 Reasoning: **HIGH** - Must understand nuanced intent
- 💰 Cost Priority: Worth premium (foundation of entire pipeline)

**Recommended**: `claude-opus-4-6` (best reasoning) or `claude-sonnet-4-6`

---

### 3. Event Discovery
**Purpose**: Search and find industry events across the web
**Complexity**: ⭐⭐⭐ Medium-High
**Requirements**:
- ✅ JSON Mode: Required (structured event data)
- ❌ Vision: Not needed
- 📏 Context: 16K-32K (multiple search results)
- 🧠 Reasoning: Moderate (filtering, relevance judgment)
- 💰 Cost Priority: Balanced (runs many times, volume matters)

**Recommended**: `claude-sonnet-4-5` or `gemini-3-flash-preview`

---

### 4. Event Qualification
**Purpose**: Score events against criteria (attendees, relevance, sponsor value)
**Complexity**: ⭐⭐⭐⭐ High
**Requirements**:
- ✅ JSON Mode: Required (scoring output)
- ❌ Vision: Rarely (unless analyzing event images)
- 📏 Context: 32K (event details + criteria)
- 🧠 Reasoning: **HIGH** - Multi-factor judgment
- 💰 Cost Priority: Quality over cost (affects final results)

**Recommended**: `claude-sonnet-4-6` or `kimi-latest`

---

### 5. Event Website Scraper
**Purpose**: Extract structured data from event websites (dates, venue, speakers)
**Complexity**: ⭐⭐ Medium
**Requirements**:
- ✅ JSON Mode: Required (structured extraction)
- ❌ Vision: Sometimes (if scraping visual info)
- 📏 Context: 8K-16K (HTML content)
- 🧠 Reasoning: Low-Medium (pattern extraction)
- 💰 Cost Priority: **Low cost** (runs for every event, high volume)

**Recommended**: `glm-flash-experimental` or `claude-haiku-4-5-20251001`

---

### 6. Event Intelligence
**Purpose**: Strategic analysis of events (target audience, past sponsors, opportunities)
**Complexity**: ⭐⭐⭐⭐⭐ Very High
**Requirements**:
- ✅ JSON Mode: Required (structured analysis)
- ❌ Vision: Sometimes (event logos, infographics)
- 📏 Context: **64K+** (large amounts of research data)
- 🧠 Reasoning: **VERY HIGH** - Strategic insights, competitive analysis
- 💰 Cost Priority: Premium acceptable (transforms data into insights)

**Recommended**: `kimi-latest` (200K context!) or `claude-opus-4-6`

---

### 7. Event Prioritization
**Purpose**: Rank and tier events based on scores
**Complexity**: ⭐⭐⭐ Medium
**Requirements**:
- ✅ JSON Mode: Required (ranked list)
- ❌ Vision: Not needed
- 📏 Context: 16K (multiple events + scoring)
- 🧠 Reasoning: Moderate (comparative analysis)
- 💰 Cost Priority: Balanced (runs once per pipeline)

**Recommended**: `claude-haiku-4-5-20251001` or `claude-sonnet-4-5`

---

### 8. Outreach Email
**Purpose**: Generate personalized sponsorship outreach emails
**Complexity**: ⭐⭐⭐⭐ High
**Requirements**:
- ❌ JSON Mode: Not required (natural language)
- ❌ Vision: Not needed
- 📏 Context: 16K-32K (event details + template)
- 🧠 Reasoning: **HIGH** - Creative writing + professional tone
- 💰 Cost Priority: Quality matters (represents your brand)

**Recommended**: `claude-sonnet-4-5` or `claude-sonnet-4-6`

---

### 9. Vendor Discovery
**Purpose**: Find booth builders, sponsors, service providers for events
**Complexity**: ⭐⭐⭐ Medium
**Requirements**:
- ✅ JSON Mode: Required (vendor lists)
- ❌ Vision: Sometimes (vendor portfolios)
- 📏 Context: 32K-64K (multiple vendor sources)
- 🧠 Reasoning: Moderate (vendor relevance judgment)
- 💰 Cost Priority: Cost-effective (runs per event)

**Recommended**: `gemini-3-flash-preview` (1M context!) or `claude-sonnet-4-5`

---

### 10. Excel Table Generator
**Purpose**: Format events data into structured tables/Excel format
**Complexity**: ⭐ Low
**Requirements**:
- ✅ JSON Mode: Required (structured data)
- ❌ Vision: Not needed
- 📏 Context: 8K (data formatting)
- 🧠 Reasoning: Low (formatting, structuring)
- 💰 Cost Priority: **Lowest cost** (deterministic task)

**Recommended**: `open-fast` or `glm-flash-experimental`

---

## Model Capabilities Matrix

| Model | Provider | JSON | Vision | Context | Reasoning | Speed | Cost |
|-------|----------|------|--------|---------|-----------|-------|------|
| **claude-opus-4-6** | Anthropic | ✅ | ✅ | 200K | ⭐⭐⭐⭐⭐ | Medium | $$$ |
| **claude-sonnet-4-6** | Anthropic | ✅ | ✅ | 200K | ⭐⭐⭐⭐ | Fast | $$ |
| **claude-sonnet-4-5** | Anthropic | ✅ | ✅ | 200K | ⭐⭐⭐⭐ | Fast | $$ |
| **claude-haiku-4-5** | Anthropic | ✅ | ❌ | 200K | ⭐⭐⭐ | Very Fast | $ |
| **gemini-3.1-pro** | Google | ✅ | ✅ | 1M | ⭐⭐⭐⭐ | Medium | $$ |
| **gemini-3-flash** | Google | ✅ | ✅ | 1M | ⭐⭐⭐ | Very Fast | $ |
| **kimi-latest** | Moonshot | ✅ | ✅ | 200K | ⭐⭐⭐⭐ | Fast | $$ |
| **glm-latest** | Zhipu | ✅ | ✅ | 128K | ⭐⭐⭐⭐ | Medium | $$ |
| **glm-flash** | Zhipu | ✅ | ❌ | 128K | ⭐⭐⭐ | Very Fast | $ |
| **open-large** | OpenAI-compat | ✅ | ✅ | 128K | ⭐⭐⭐⭐ | Medium | $$ |
| **open-fast** | OpenAI-compat | ✅ | ❌ | 128K | ⭐⭐⭐ | Very Fast | $ |

---

## Optimized Agent-to-Model Assignments

### Tier 1: Critical Agents (Use Best Models)
| Agent | Assigned Model | Why |
|-------|---------------|-----|
| **intent_understanding** | `claude-opus-4-6` | Pipeline foundation, needs best reasoning |
| **event_intelligence** | `kimi-latest` | 200K context for large research datasets |

### Tier 2: Quality Agents (Balance Quality/Cost)
| Agent | Assigned Model | Why |
|-------|---------------|-----|
| **event_qualification** | `claude-sonnet-4-6` | High-quality judgment for scoring |
| **outreach_email** | `claude-sonnet-4-5` | Creative + professional writing |
| **event_discovery** | `claude-sonnet-4-5` | Balance of speed and accuracy |

### Tier 3: Volume Agents (Cost-Optimized)
| Agent | Assigned Model | Why |
|-------|---------------|-----|
| **event_prioritization** | `claude-haiku-4-5` | Fast ranking, less complexity |
| **vendor_discovery** | `gemini-3-flash-preview` | 1M context for vendor research, very cheap |

### Tier 4: Simple Agents (Lowest Cost)
| Agent | Assigned Model | Why |
|-------|---------------|-----|
| **schema_initialization** | `claude-haiku-4-5` | Simple JSON, runs once |
| **event_website_scraper** | `glm-flash-experimental` | Pattern extraction, high volume |
| **excel_table_generator** | `open-fast` | Deterministic formatting |

---

## Alternative Assignments by Priority

### If Cost is Primary Concern (Cheapest Options)
| Agent | Model | Est. Cost/1K calls |
|-------|-------|-------------------|
| intent_understanding | `claude-sonnet-4-5` | $18 |
| event_intelligence | `kimi-latest` | $10 |
| event_qualification | `claude-sonnet-4-5` | $18 |
| event_discovery | `gemini-3-flash` | $1.40 |
| event_website_scraper | `glm-flash` | $1.20 |
| vendor_discovery | `gemini-3-flash` | $1.40 |
| outreach_email | `claude-sonnet-4-5` | $18 |
| prioritization | `claude-haiku` | $1.50 |
| schema_init | `glm-flash` | $1.20 |
| excel_gen | `open-fast` | $2 |

**Total Est. Cost for 1000 pipelines**: ~$73

### If Quality is Primary Concern (Best Options)
| Agent | Model | Est. Cost/1K calls |
|-------|-------|-------------------|
| intent_understanding | `claude-opus-4-6` | $90 |
| event_intelligence | `claude-opus-4-6` | $90 |
| event_qualification | `claude-opus-4-6` | $90 |
| event_discovery | `claude-sonnet-4-6` | $18 |
| event_website_scraper | `claude-haiku` | $1.50 |
| vendor_discovery | `claude-sonnet-4-5` | $18 |
| outreach_email | `claude-opus-4-6` | $90 |
| prioritization | `claude-sonnet-4-5` | $18 |
| schema_init | `claude-haiku` | $1.50 |
| excel_gen | `open-fast` | $2 |

**Total Est. Cost for 1000 pipelines**: ~$419

### Recommended Balanced Approach
| Agent | Model | Est. Cost/1K calls |
|-------|-------|-------------------|
| intent_understanding | `claude-opus-4-6` | $90 |
| event_intelligence | `kimi-latest` | $10 |
| event_qualification | `claude-sonnet-4-6` | $18 |
| event_discovery | `claude-sonnet-4-5` | $18 |
| event_website_scraper | `glm-flash` | $1.20 |
| vendor_discovery | `gemini-3-flash` | $1.40 |
| outreach_email | `claude-sonnet-4-5` | $18 |
| prioritization | `claude-haiku` | $1.50 |
| schema_init | `claude-haiku` | $1.50 |
| excel_gen | `open-fast` | $2 |

**Total Est. Cost for 1000 pipelines**: ~$162

---

## Summary

### Critical Capabilities by Agent
1. **JSON Mode**: Required by all except `outreach_email`
2. **High Reasoning**: `intent_understanding`, `event_intelligence`, `event_qualification`
3. **Long Context**: `event_intelligence` (200K+), `vendor_discovery` (1M with Gemini)
4. **Creative Writing**: `outreach_email` only
5. **Vision**: Nice-to-have for `event_website_scraper`, `vendor_discovery`

### Model Sweet Spots
- **Ultra Reasoning**: `claude-opus-4-6` (intent, intelligence)
- **Long Context**: `kimi-latest` (200K), `gemini-3-flash` (1M)
- **Cost-Effective**: `glm-flash`, `gemini-3-flash`, `claude-haiku`
- **Balanced**: `claude-sonnet-4-5/4-6` (most agents)
