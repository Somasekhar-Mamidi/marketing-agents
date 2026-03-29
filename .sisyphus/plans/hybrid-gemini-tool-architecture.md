# Plan: Hybrid Architecture - Gemini Native + Tool-Based Fallback

## TL;DR
> **Summary**: Use Gemini as primary for research (native web access), fallback to GLM/Kimi with tool calling + DuckDuckGo when Gemini $5 limit reached. Eliminate paid services (Tavily, Serper, Search1API).
> **Deliverables**: Updated models.yaml, fallback logic, cost-optimized configuration
> **Effort**: Quick
> **Parallel**: NO - Sequential config updates
> **Critical Path**: Config → Fallback logic → Test → Verify

## Context

### User Requirements
- **Primary**: Gemini for research agents (native web access, no external APIs)
- **Fallback**: GLM/Kimi with tool calling + DuckDuckGo when Gemini limit reached
- **Reasoning agents**: Non-Gemini models (no web needed)
- **Goal**: Eliminate paid services, keep DuckDuckGo as free fallback

### Current State
- Gemini confirmed to have native web access via Grid AI
- GLM, Kimi, Claude, open-large confirmed to support tool calling
- DuckDuckGo search implemented and working (free, no API key)
- Tavily, Serper, Search1API currently integrated (to be removed)

### Fallback Strategy
```
User Query → Check Gemini Budget
    ↓
[If under $5 limit] → Gemini (native web) → Answer
    ↓
[If limit reached] → GLM/Kimi + tools → DuckDuckGo → Answer
```

## Work Objectives

### Core Objective
Implement cost-optimized hybrid architecture with automatic fallback from Gemini to tool-based models.

### Deliverables
1. Updated `config/models.yaml` with tiered model assignments
2. Fallback configuration for when Gemini budget exhausted
3. Updated `utils/search.py` (DuckDuckGo only, remove paid services)
4. Updated `requirements.txt` (remove paid service dependencies)
5. Documentation of fallback mechanism

### Definition of Done
- [ ] Research agents prefer Gemini, fallback to GLM/Kimi
- [ ] Tool-based fallback works when triggered
- [ ] No Tavily/Serper/Search1API dependencies
- [ ] DuckDuckGo works as free fallback
- [ ] Reasoning agents use non-Gemini models

### Must Have
- Gemini as primary for research agents
- GLM/Kimi fallback with tool calling
- DuckDuckGo as search backend for fallback
- Non-Gemini models for reasoning agents

### Must NOT Have
- Breaking existing agent functionality
- Hard dependency on paid search services
- Complex fallback logic that's hard to debug

## Verification Strategy
- Test Gemini path (normal operation)
- Test fallback path (simulated budget limit)
- Verify DuckDuckGo search works
- Check no paid API keys needed
- Evidence: .sisyphus/evidence/hybrid-*.json

## Execution Strategy

### Sequential Updates
1. Update models.yaml with hybrid configuration
2. Simplify search.py to DuckDuckGo-only
3. Update requirements.txt
4. Test both paths
5. Document architecture

## TODOs

- [ ] 1. Update models.yaml - Hybrid Configuration

  **What to do**: Update config/models.yaml with:
  - Research agents: Gemini primary, GLM/Kimi fallback
  - Reasoning agents: Non-Gemini models
  - Fallback triggers and conditions
  
  **Must NOT do**: Remove existing agents, only update model assignments
  
  **Recommended Agent Profile**:
  - Category: `quick` — Reason: Config file update
  - Skills: []
  
  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [2,3,4,5] | Blocked By: []
  
  **References**:
  - Current config: `config/models.yaml`
  - Gemini capabilities: Confirmed native web access
  - Tool system: `utils/tools.py`
  
  **Acceptance Criteria**:
  - [ ] event_discovery: Gemini primary, glm-latest fallback
  - [ ] event_intelligence: Gemini primary, kimi-latest fallback
  - [ ] vendor_discovery: Gemini primary, glm-latest fallback
  - [ ] intent_understanding: claude-opus-4-6 (no web)
  - [ ] event_qualification: claude-sonnet-4-6 (no web)
  - [ ] Fallback logic documented
  
  **QA Scenarios**:
  ```
  Scenario: Gemini path works
    Tool: Bash
    Steps: Query event_discovery with Gemini model
    Expected: Returns results with native web data
    Evidence: .sisyphus/evidence/task-1-gemini-path.json
  
  Scenario: Fallback path works
    Tool: Bash
    Steps: Force fallback, query with GLM + tools
    Expected: Returns results via DuckDuckGo
    Evidence: .sisyphus/evidence/task-1-fallback-path.json
  ```
  
  **Commit**: YES | Message: `config: hybrid architecture - Gemini primary, tool-based fallback` | Files: [config/models.yaml]

---

- [ ] 2. Simplify search.py - DuckDuckGo Only

  **What to do**: Remove Tavily, Serper, Search1API code. Keep DuckDuckGo as sole search provider.
  
  **Must NOT do**: Remove DuckDuckGo, break WebSearchTool API
  
  **Recommended Agent Profile**:
  - Category: `quick` — Reason: Code cleanup
  - Skills: []
  
  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [4] | Blocked By: [1]
  
  **References**:
  - File: `utils/search.py`
  - DuckDuckGo: `utils/duckduckgo_search.py`
  
  **Acceptance Criteria**:
  - [ ] Tavily code commented/removed
  - [ ] Serper code commented/removed
  - [ ] Search1API code commented/removed
  - [ ] DuckDuckGo remains as default
  - [ ] WebSearchTool API unchanged
  
  **QA Scenarios**:
  ```
  Scenario: Search works without API keys
    Tool: Bash
    Steps: python -c "from utils.search import WebSearchTool; w = WebSearchTool(); print(w.search('test'))"
    Expected: Returns DuckDuckGo results
    Evidence: .sisyphus/evidence/task-2-ddg-only.json
  ```
  
  **Commit**: YES | Message: `refactor: remove paid search services, DuckDuckGo only` | Files: [utils/search.py]

---

- [ ] 3. Update requirements.txt

  **What to do**: Remove or comment out tavily-python, google-serp-api, search1api dependencies
  
  **Must NOT do**: Remove httpx, beautifulsoup4, openai
  
  **Recommended Agent Profile**:
  - Category: `quick` — Reason: Dependency cleanup
  - Skills: []
  
  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [4] | Blocked By: [1]
  
  **Acceptance Criteria**:
  - [ ] tavily-python removed/commented
  - [ ] google-serp-api removed/commented
  - [ ] search1api removed/commented
  - [ ] Core deps preserved
  
  **QA Scenarios**:
  ```
  Scenario: App installs without paid deps
    Tool: Bash
    Steps: pip install -r requirements.txt
    Expected: No errors, no paid API packages
    Evidence: .sisyphus/evidence/task-3-deps-clean.txt
  ```
  
  **Commit**: YES | Message: `deps: remove paid search service dependencies` | Files: [requirements.txt]

---

- [ ] 4. Test Hybrid Architecture

  **What to do**: Test both Gemini path and fallback path with real queries
  
  **Must NOT do**: Skip testing fallback path
  
  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: Integration testing
  - Skills: []
  
  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: [5] | Blocked By: [2,3]
  
  **Acceptance Criteria**:
  - [ ] Gemini path returns current web data
  - [ ] Fallback path returns DuckDuckGo results
  - [ ] Tool calling works with GLM/Kimi
  - [ ] No paid API calls made
  
  **QA Scenarios**:
  ```
  Scenario: End-to-end hybrid test
    Tool: Bash
    Steps: Run test queries on both paths
    Expected: Both paths return valid results
    Evidence: .sisyphus/evidence/task-4-hybrid-test.json
  ```
  
  **Commit**: YES | Message: `test: verify hybrid architecture works` | Files: [test results]

---

- [ ] 5. Document Architecture

  **What to do**: Document the hybrid architecture, fallback logic, and cost optimization
  
  **Must NOT do**: Create redundant docs
  
  **Recommended Agent Profile**:
  - Category: `writing` — Reason: Documentation
  - Skills: []
  
  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: [] | Blocked By: [4]
  
  **Acceptance Criteria**:
  - [ ] Architecture diagram
  - [ ] Fallback logic explained
  - [ ] Cost optimization documented
  - [ ] Migration guide included
  
  **Commit**: YES | Message: `docs: document hybrid architecture and fallback` | Files: [docs/]

---

## Final Verification Wave (MANDATORY)
- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high
- [ ] F3. Real Manual QA — unspecified-high
- [ ] F4. Scope Fidelity Check — deep

## Model Assignments (Hybrid Architecture)

### Research Agents (Need Web Access)
| Agent | Primary | Fallback | Fallback Trigger |
|-------|---------|----------|------------------|
| event_discovery | gemini-3-flash-preview | glm-latest | Gemini $5 limit |
| event_intelligence | gemini-3.1-pro | kimi-latest | Gemini $5 limit |
| vendor_discovery | gemini-3-flash-preview | glm-latest | Gemini $5 limit |

### Reasoning Agents (No Web Needed)
| Agent | Model | Notes |
|-------|-------|-------|
| intent_understanding | claude-opus-4-6 | Best reasoning |
| event_qualification | claude-sonnet-4-6 | Good judgment |
| outreach_email | claude-sonnet-4-5 | Writing quality |
| excel_table_generator | glm-flash-experimental | Cheap formatting |

## Fallback Mechanism

### Primary Path (Gemini)
```
User Query → Gemini Model → Native Web Search → Answer
Cost: ~$0.002-0.01 per query
Limit: $5/month cap
```

### Fallback Path (Tool-Based)
```
User Query → GLM/Kimi → web_search Tool → DuckDuckGo → Results → LLM → Answer
Cost: ~$0.001-0.005 per query (cheaper!)
Limit: None (DuckDuckGo free)
```

### Fallback Trigger
- Gemini API returns budget limit error
- Explicit fallback flag set
- Gemini model unavailable

## Cost Optimization

### Before (Paid Services)
- Tavily: $50-200/month
- Serper: $20-100/month
- Search1API: Variable
- **Total: $70-300+/month**

### After (Hybrid)
- Gemini: $5/month (capped)
- Grid AI other models: Pay per use
- DuckDuckGo: $0
- **Total: ~$10-30/month**

### Savings: ~60-90%
