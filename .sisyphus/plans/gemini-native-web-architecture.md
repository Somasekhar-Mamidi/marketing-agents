# Plan: Switch to Gemini Native Web Access

## TL;DR
> **Summary**: Eliminate external search APIs (Tavily, Serper, DuckDuckGo) by using Gemini's native web search/fetch capabilities for research-heavy agents.
> **Deliverables**: Updated models.yaml, simplified architecture, reduced costs
> **Effort**: Quick
> **Parallel**: NO - Sequential updates
> **Critical Path**: Config update → Test → Verify

## Context

### Original Request
User wants to eliminate Tavily, Serper, and other search APIs and completely rely on LLMs for web search, fetch, scraping, and crawling.

### Research Findings

**Confirmed: Gemini has native web access via Grid AI**
- Tested: gemini-3-flash-preview returns current, specific data (dates, prices, sponsors)
- Example: "Money20/20 Europe: June 3-5, 2025, Amsterdam" - not in training data
- Example: "Sibos 2025: Sept 29 - Oct 2, 2025, Frankfurt" - real-time data
- Example: "FinovateEurope pricing: £1,099 - £2,599" - current pricing

**Claude does NOT have native web access**
- Explicitly states: "I'm not able to visit URLs or browse the internet"
- Uses Brave Search under the hood (still external)
- Costs $10/1000 searches on top of token costs

**GLM/Kimi do NOT have native web access**
- Need tool calling with backend search

### Metis Review (gaps addressed)
- Gemini native access confirmed via live testing
- Cost comparison: Gemini (free search) vs Claude ($10/1000 searches)
- Architecture simplification validated

## Work Objectives

### Core Objective
Eliminate external search dependencies for research-heavy agents by using Gemini's native web capabilities.

### Deliverables
1. Updated `config/models.yaml` with Gemini-first research config
2. Updated `utils/search.py` to remove Tavily/Serper/Search1API dependencies
3. Updated `requirements.txt` to remove unused search dependencies
4. Documentation of new architecture

### Definition of Done
- [ ] Research agents use Gemini with native web access
- [ ] No Tavily/Serper/Search1API API keys needed
- [ ] DuckDuckGo available as fallback for non-Gemini models
- [ ] All agents tested with new configuration

### Must Have
- Gemini models for: event_discovery, event_intelligence, vendor_discovery
- Native web access flag in config
- Fallback to DuckDuckGo for non-Gemini models

### Must NOT Have
- Breaking existing non-research agents
- Removing all search capabilities
- Complex tool-calling for Gemini (not needed)

## Verification Strategy
- Test each research agent with real queries
- Verify Gemini returns current, specific data
- Compare output quality vs old approach
- Evidence: .sisyphus/evidence/gemini-native-*.json

## Execution Strategy

### Sequential Updates (dependency chain)
1. Update models.yaml (defines which models agents use)
2. Update requirements.txt (remove unused deps)
3. Simplify search.py (DuckDuckGo fallback only)
4. Test all research agents
5. Document new architecture

## TODOs

- [ ] 1. Update models.yaml with Gemini-Native Configuration

  **What to do**: Update config/models.yaml to use gemini-3-flash-preview for research-heavy agents with native_web_access flag.
  
  **Must NOT do**: Remove existing agent configurations, only update research agents.
  
  **Recommended Agent Profile**:
  - Category: `quick` — Reason: Simple config file update
  - Skills: [] — No special skills needed
  
  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [2,3,4,5] | Blocked By: []
  
  **References**:
  - Config: `config/models.yaml` — Current agent model assignments
  - Test results: Gemini native web access confirmed
  
  **Acceptance Criteria**:
  - [ ] event_discovery uses gemini-3-flash-preview with native_web_access: true
  - [ ] event_intelligence uses gemini-3.1-pro with native_web_access: true
  - [ ] vendor_discovery uses gemini-3-flash-preview with native_web_access: true
  - [ ] Other agents unchanged
  
  **QA Scenarios**:
  ```
  Scenario: Gemini agent returns current data
    Tool: Bash
    Steps: Query event_discovery with "Find payment conferences 2025"
    Expected: Returns specific dates, locations, sponsors
    Evidence: .sisyphus/evidence/task-1-gemini-native.json
  ```
  
  **Commit**: YES | Message: `config: use Gemini native web access for research agents` | Files: [config/models.yaml]

---

- [ ] 2. Update requirements.txt - Remove Unused Search Dependencies

  **What to do**: Comment out or remove tavily-python, google-serp-api, and other search API dependencies that are no longer primary.
  
  **Must NOT do**: Remove httpx, beautifulsoup4 (still needed for DuckDuckGo fallback)
  
  **Recommended Agent Profile**:
  - Category: `quick` — Reason: Simple requirements update
  - Skills: []
  
  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [4] | Blocked By: [1]
  
  **References**:
  - File: `requirements.txt` — Python dependencies
  - Keep: httpx>=0.24.0, beautifulsoup4>=4.12.0
  
  **Acceptance Criteria**:
  - [ ] tavily-python commented out with note
  - [ ] Unused search API deps removed or commented
  - [ ] Core dependencies (httpx, bs4) retained
  
  **QA Scenarios**:
  ```
  Scenario: App starts without missing dependencies
    Tool: Bash
    Steps: pip install -r requirements.txt && python -c "from utils.search import WebSearchTool"
    Expected: No import errors
    Evidence: .sisyphus/evidence/task-2-deps-ok.txt
  ```
  
  **Commit**: YES | Message: `deps: remove unused search API dependencies` | Files: [requirements.txt]

---

- [ ] 3. Simplify utils/search.py - DuckDuckGo Fallback Only

  **What to do**: Simplify WebSearchTool to use DuckDuckGo as primary (for non-Gemini fallback). Comment out Tavily, Serper, Search1API provider code.
  
  **Must NOT do**: Remove DuckDuckGo functionality, break existing API
  
  **Recommended Agent Profile**:
  - Category: `quick` — Reason: Code simplification
  - Skills: []
  
  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [4] | Blocked By: [1]
  
  **References**:
  - File: `utils/search.py` — Multi-provider search tool
  - File: `utils/duckduckgo_search.py` — DuckDuckGo implementation
  
  **Acceptance Criteria**:
  - [ ] Tavily/Serper/Search1API code commented out
  - [ ] DuckDuckGo works as fallback
  - [ ] No API keys required for basic search
  
  **QA Scenarios**:
  ```
  Scenario: DuckDuckGo search works
    Tool: Bash
    Steps: python -c "from utils.search import WebSearchTool; w = WebSearchTool(); print(w.search('test'))"
    Expected: Returns search results without API keys
    Evidence: .sisyphus/evidence/task-3-ddg-search.json
  ```
  
  **Commit**: YES | Message: `refactor: simplify search to DuckDuckGo fallback only` | Files: [utils/search.py]

---

- [ ] 4. Test Research Agents with Gemini Native Access

  **What to do**: Run integration tests for event_discovery, event_intelligence, vendor_discovery with Gemini to verify native web access works.
  
  **Must NOT do**: Test with outdated/expected data, use mocked responses
  
  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: Requires verification and testing
  - Skills: []
  
  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: [5] | Blocked By: [2, 3]
  
  **References**:
  - Test: Run agents with real queries
  - Compare: Results should have specific current data
  
  **Acceptance Criteria**:
  - [ ] event_discovery returns events with specific dates
  - [ ] event_intelligence returns sponsor/attendee data
  - [ ] vendor_discovery finds actual vendors
  - [ ] All without external search APIs
  
  **QA Scenarios**:
  ```
  Scenario: Full pipeline with Gemini native access
    Tool: Bash
    Steps: Run full pipeline test with "Find payment conferences 2025"
    Expected: Complete results with current data
    Evidence: .sisyphus/evidence/task-4-gemini-pipeline.json
  ```
  
  **Commit**: YES | Message: `test: verify Gemini native web access works` | Files: [test results]

---

- [ ] 5. Document New Architecture

  **What to do**: Update docs/TOOL_BASED_SEARCH_ARCHITECTURE.md or create new doc explaining Gemini native web access approach.
  
  **Must NOT do**: Create redundant documentation
  
  **Recommended Agent Profile**:
  - Category: `writing` — Reason: Documentation task
  - Skills: []
  
  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: [] | Blocked By: [4]
  
  **References**:
  - Existing: `docs/TOOL_BASED_SEARCH_ARCHITECTURE.md`
  - Test results from task 4
  
  **Acceptance Criteria**:
  - [ ] Architecture diagram updated
  - [ ] Model recommendations documented
  - [ ] Migration guide for non-Gemini models
  
  **QA Scenarios**:
  ```
  Scenario: Documentation is complete and accurate
    Tool: Read
    Steps: Review documentation
    Expected: Clear explanation of new architecture
    Evidence: .sisyphus/evidence/task-5-docs.md
  ```
  
  **Commit**: YES | Message: `docs: document Gemini native web access architecture` | Files: [docs/]

---

## Final Verification Wave (MANDATORY)
- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high
- [ ] F3. Real Manual QA — unspecified-high
- [ ] F4. Scope Fidelity Check — deep

## Commit Strategy
- Atomic commits per task
- Clear commit messages referencing the change
- Push after all tasks complete

## Success Criteria
1. Research agents work with Gemini native web access
2. No external search API keys required
3. DuckDuckGo available as fallback
4. All tests pass
5. Documentation updated

## Model Assignments After Update

| Agent | Model | Method |
|-------|-------|--------|
| event_discovery | gemini-3-flash-preview | Native web search |
| event_intelligence | gemini-3.1-pro | Native web search |
| vendor_discovery | gemini-3-flash-preview | Native web search |
| intent_understanding | claude-opus-4-6 | No search needed |
| event_qualification | claude-sonnet-4-6 | No search needed |
| outreach_email | claude-sonnet-4-5 | Optional Gemini search |
| event_website_scraper | glm-flash | DuckDuckGo fallback |
