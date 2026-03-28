# Marketing Agents - Event Discovery Platform
## Product Requirements Document (PRD) & Implementation Plan

**Version:** 2.0  
**Date:** March 27, 2026  
**Status:** Production Ready

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Overview](#2-product-overview)
3. [System Architecture](#3-system-architecture)
4. [Agent Workflow (Detailed)](#4-agent-workflow-detailed)
5. [Technical Specifications](#5-technical-specifications)
6. [Database Schema](#6-database-schema)
7. [API Specifications](#7-api-specifications)
8. [Frontend Specifications](#8-frontend-specifications)
9. [Implementation Plan](#9-implementation-plan)
10. [Deployment Guide](#10-deployment-guide)
11. [Testing Strategy](#11-testing-strategy)
12. [Appendices](#12-appendices)

---

## 1. Executive Summary

### 1.1 Product Vision
Marketing Agents is an AI-powered event discovery and marketing pipeline that automates the identification, qualification, and prioritization of industry events for sponsorship opportunities. The system uses an 8-agent workflow with human-in-the-loop checkpoints to ensure high-quality event recommendations.

### 1.2 Key Features
- **8-Agent Pipeline:** Automated event discovery, qualification, and prioritization
- **Human Checkpoints:** 3 approval gates for quality control
- **Intelligent Search:** Multi-provider search (DuckDuckGo, Tavily, Serper) with fallback
- **Real-time Monitoring:** Live pipeline progress tracking via SSE
- **Comprehensive Reports:** Markdown summaries + Excel exports
- **Web UI:** Modern Next.js frontend with real-time updates

### 1.3 Target Users
- Marketing teams seeking sponsorship opportunities
- Event managers looking for relevant conferences
- Business development teams
- Startup founders seeking visibility

---

## 2. Product Overview

### 2.1 User Journey

```
User Input → Intent Analysis → Event Discovery → Checkpoint 1 → 
Qualification → Scraping → Intelligence → Prioritization → Checkpoint 2 → 
Vendor Discovery → Outreach → Checkpoint 3 → Reports & Export
```

### 2.2 Core Use Cases

**UC1: Event Discovery**
- User inputs query: "fintech conferences in Europe Q2 2026"
- System discovers 20-50 relevant events
- Events are scored and ranked

**UC2: Vendor Research**
- For each qualified event, find sponsors/exhibitors
- Extract contact information
- Score vendor relevance

**UC3: Outreach Campaign**
- Generate personalized outreach emails
- Create Gmail drafts
- Track outreach status

**UC4: Human Review**
- Review discovered events at Checkpoint 1
- Approve/reject with notes
- Pipeline continues or stops based on decision

### 2.3 Success Metrics
- **Discovery Accuracy:** >80% relevant events
- **Processing Speed:** <5 minutes for full pipeline
- **Human Approval Rate:** >70% at checkpoints
- **System Uptime:** >99%

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │   Next.js    │ │  React Query │ │  Tailwind    │            │
│  │  (Pages Router)│ │   (State)    │ │     CSS      │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API + SSE
┌────────────────────────▼────────────────────────────────────────┐
│                        BACKEND LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                    │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │   Routers   │ │ Middleware  │ │  Services   │        │  │
│  │  │  (27 API    │ │  (Auth,     │ │  (Pipeline, │        │  │
│  │  │   endpoints)│ │   CORS)     │ │   Agents)   │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│   AGENT      │ │  DATABASE   │ │   CACHE     │
│   LAYER      │ │   LAYER     │ │   LAYER     │
│  (8 Agents)  │ │  (SQLite)   │ │  (SQLite)   │
└──────────────┘ └─────────────┘ └─────────────┘
        │
┌───────▼──────────────────────────────────────┐
│            EXTERNAL SERVICES                 │
│  DuckDuckGo  │  Tavily  │  OpenAI  │  Gmail │
└──────────────────────────────────────────────┘
```

### 3.2 Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                     AGENT PIPELINE                              │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ Schema   │───▶│ Intent   │───▶│ Event    │───▶│   CP1    │ │
│  │  Init    │    │Understand│    │Discovery │    │(Review)  │ │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘ │
│                                                        │       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │       │
│  │   CP3    │◀───│ Outreach │◀───│ Vendor   │◀────────┘       │
│  │(Review)  │    │  Email   │    │Discovery │                 │
│  └────┬─────┘    └──────────┘    └──────────┘                 │
│       │                                                        │
│       ▼                                                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│  │  Reports │◀───│   CP2    │◀───│ Prioritize│                 │
│  │  & Export│    │(Review)  │    │           │                 │
│  └──────────┘    └──────────┘    └──────────┘                 │
│                                                                 │
│  Intermediate Agents:                                          │
│  • Qualification  • Scraping  • Intelligence                   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Agent Workflow (Detailed)

### 4.1 Agent 0: Schema Initialization
**Purpose:** Validate configuration and initialize pipeline context

**Input:**
```json
{
  "query": "fintech conferences Europe Q2 2026",
  "industry": "fintech",
  "region": "Europe",
  "enable_checkpoints": true,
  "auto_approve": true
}
```

**Process:**
1. Validate required fields (query)
2. Normalize industry/region strings
3. Generate correlation ID
4. Create pipeline context object
5. Initialize metrics tracking

**Output:**
```json
{
  "pipeline_id": "uuid",
  "status": "initialized",
  "context": {
    "query": "normalized query",
    "parameters": {...},
    "metadata": {...}
  }
}
```

**Implementation:**
```python
# File: agents/schema_init.py
class SchemaInitAgent(BaseAgent):
    def execute(self, input_data: AgentInput) -> AgentOutput:
        # Validation logic
        # Context creation
        # Return initialized schema
```

---

### 4.2 Agent 1: Intent Understanding
**Purpose:** Parse user query into structured search parameters

**Input:** User natural language query

**Process:**
1. Extract industry using keyword matching
2. Identify regions from location keywords
3. Parse date ranges (Q2 2026 → specific dates)
4. Determine event types (conference, summit, expo)
5. Extract audience targets (executives, technical, etc.)
6. Identify strategic objectives (lead gen, brand awareness)
7. Generate optimized search queries (15 queries)
8. Define quality thresholds

**Output:**
```json
{
  "intent": {
    "primary_goal": "Event Discovery",
    "industry": "fintech",
    "sub_industries": ["payments", "banking"],
    "regions": ["europe"],
    "event_types": ["conference", "summit"],
    "date_range": {
      "type": "quarter",
      "quarter": 2,
      "year": 2026,
      "start": "2026-04-01",
      "end": "2026-06-30"
    },
    "audience_target": {
      "seniority_levels": ["decision_makers"],
      "company_size": "enterprise"
    },
    "search_queries": [
      "fintech conference europe 2026",
      "fintech summit europe 2026",
      "..."
    ],
    "quality_requirements": {
      "min_attendees": 500,
      "relevance_threshold": 0.6
    }
  }
}
```

**Implementation:**
```python
# File: agents/intent_understanding.py
class IntentUnderstandingAgent(BaseAgent):
    INDUSTRY_KEYWORDS = {...}
    REGIONS = {...}
    EVENT_TYPES = {...}
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        # Intent extraction logic
        # Query generation
        # Return structured intent
```

---

### 4.3 Agent 2: Event Discovery
**Purpose:** Find industry events using web search

**Input:** Intent data with search queries

**Process:**
1. Execute search queries (up to 15 queries)
2. Parse search results into event schema
3. Apply filters:
   - Exclude vendor-specific events (Google I/O, AWS re:Invent)
   - Check URL patterns
   - Verify industry keywords
4. Remove duplicates
5. Score events by intent alignment:
   - Industry match (25%)
   - Region match (20%)
   - Event type match (15%)
   - Date quality (15%)
   - Content richness (15%)
   - Exclusion penalty (-variable)
6. Sort by score (highest first)
7. Return top N events

**Output:**
```json
{
  "events": [
    {
      "event_name": "Money20/20 Europe",
      "event_website": "https://money2020.com/europe",
      "city": "Amsterdam",
      "country": "Netherlands",
      "start_date": "2026-06-08",
      "end_date": "2026-06-10",
      "theme": "fintech",
      "organizer": "Money20/20",
      "summary": "...",
      "discovery_score": 92,
      "discovery_score_breakdown": {
        "industry_match": 0.25,
        "region_match": 0.20,
        "event_type_match": 0.15,
        "date_quality": 0.15,
        "content_richness": 0.17
      },
      "status": "Discovered"
    }
  ],
  "search_queries_used": 15,
  "total_discovered": 42
}
```

**Implementation:**
```python
# File: agents/event_discovery.py
class EventDiscoveryAgent(BaseAgent):
    EXCLUDED_COMPANIES = ["google", "aws", "microsoft", ...]
    EXCLUDED_KEYWORDS = ["launch", "keynote", "build", ...]
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        # Check for intent data
        # Execute searches
        # Filter and score events
        # Return ranked events
    
    def _score_events_by_intent(self, events, intent_data):
        # Scoring logic
        # Return scored events
```

---

### 4.4 Checkpoint 1: Event Review
**Purpose:** Human approval of discovered events

**Trigger:** After Event Discovery completes (25% progress)

**Process:**
1. Create checkpoint with discovered events
2. Generate review summary (markdown)
3. If auto_approve=True: Automatically approve
4. If auto_approve=False: 
   - Set status to "waiting_for_approval"
   - Poll for approval every 5 seconds
   - Timeout after 1 hour
5. On approval: Continue pipeline
6. On rejection: Pipeline ends

**API Endpoints:**
```
POST /checkpoints/{id}/approve
POST /checkpoints/{id}/reject
GET /checkpoints/{id}/summary
```

**Implementation:**
```python
# File: checkpoint/manager.py
class CheckpointManager:
    def create_checkpoint(self, pipeline_id, type, name, data):
        # Create checkpoint
        
    def wait_for_approval(self, checkpoint_id, poll_interval=5):
        # Blocking poll loop
```

---

### 4.5 Agent 3: Event Qualification
**Purpose:** Filter events by business relevance

**Process:**
1. Filter by date range (future events only)
2. Verify location relevance
3. Check industry alignment
4. Validate event type
5. Apply size/scale thresholds

---

### 4.6 Agent 4: Website Scraping
**Purpose:** Extract detailed event information

**Process:**
1. Scrape event websites using BeautifulSoup
2. Extract:
   - Exact dates and venue
   - Speaker lists
   - Sponsor/exhibitor lists
   - Pricing information
   - Agenda highlights
3. Rate limit: 1 req/sec
4. Cache results (7-day TTL)

---

### 4.7 Agent 5: Intelligence Gathering
**Purpose:** AI-powered analysis of events

**Process:**
1. Analyze audience quality
2. Identify competitors
3. Extract technology themes
4. Find past attendee companies
5. Assess strategic value

**LLM Prompt:**
```
Analyze this event and extract:
- Target audience seniority
- Competitor presence
- Technology themes
- Strategic value (1-10)
- Recommended sponsorship level
```

---

### 4.8 Agent 6: Prioritization
**Purpose:** Score and rank events objectively

**100-Point Scoring Rubric:**

| Criterion | Points | Assessment Factors |
|-----------|--------|-------------------|
| **Audience Quality** | 25 | Decision-makers %, Company size, Seniority levels |
| **Event Reputation** | 20 | Past attendance, Speaker quality, Reviews, History |
| **ROI Potential** | 20 | Lead quality, Deal size, Conversion rate |
| **Strategic Fit** | 15 | Product alignment, Roadmap match, Timing |
| **Geographic Importance** | 10 | Regional priority, Market size, Accessibility |
| **Competitive Presence** | 10 | Competitor attendance, Sponsorship level |

**Output:** Tier classification (S, A, B, C)

---

### 4.9 Checkpoint 2: Vendor Review
**Purpose:** Human approval of vendor list

**Trigger:** After Prioritization (75% progress)

---

### 4.10 Agent 7: Vendor Discovery
**Purpose:** Find sponsorship/exhibition opportunities

**Process:**
1. Scrape event "sponsors" pages
2. Extract company information
3. Find contact details (LinkedIn, email)
4. Score vendor relevance (0-100)

---

### 4.11 Agent 8: Outreach Email
**Purpose:** Generate personalized outreach

**Process:**
1. Generate personalized email per vendor
2. Include event-specific value props
3. Save to Gmail drafts
4. Track in database

---

### 4.12 Checkpoint 3: Email Review
**Purpose:** Human approval of email drafts

**Trigger:** After Outreach (95% progress)

---

### 4.13 Agent 9: Report Generation
**Purpose:** Create deliverables

**Outputs:**
- Markdown executive summary
- Detailed vendor analysis
- Email tracking report
- Excel export with all data

---

## 5. Technical Specifications

### 5.1 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 16, React, TypeScript | Web UI |
| **Styling** | Tailwind CSS, Heroicons | Styling |
| **State** | TanStack Query (React Query) | Data fetching |
| **Backend** | FastAPI, Python 3.11 | API server |
| **Validation** | Pydantic | Data models |
| **Database** | SQLite | Persistent storage |
| **Caching** | SQLite | Search/web cache |
| **Search** | DuckDuckGo, Tavily, Serper | Web search |
| **AI/ML** | OpenAI GPT | Intelligence, scoring |
| **Scraping** | BeautifulSoup, httpx | Web scraping |
| **Testing** | pytest | Unit tests |

### 5.2 File Structure

```
marketing_agents/
├── agents/
│   ├── __init__.py
│   ├── base.py                    # Base agent class
│   ├── schema_init.py             # Agent 0
│   ├── intent_understanding.py    # Agent 1 (NEW)
│   ├── event_discovery.py         # Agent 2
│   ├── event_qualification.py     # Agent 3
│   ├── event_website_scraper.py   # Agent 4
│   ├── event_intelligence.py      # Agent 5
│   ├── event_prioritization.py    # Agent 6
│   ├── vendor_discovery.py        # Agent 7
│   └── outreach_email.py          # Agent 8
├── api/
│   └── main.py                    # FastAPI application
├── checkpoint/
│   └── manager.py                 # Human checkpoint system
├── database/
│   └── models.py                  # SQLite models
├── frontend/                      # Next.js application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── events/
│   │   │   ├── pipeline/
│   │   │   ├── checkpoints/
│   │   │   ├── logs/
│   │   │   ├── reports/
│   │   │   └── metrics/
│   │   ├── components/
│   │   │   └── layout/
│   │   │       ├── DashboardLayout.tsx
│   │   │       └── Sidebar.tsx
│   │   └── lib/
│   │       ├── api.ts             # API client
│   │       ├── queryClient.ts     # React Query config
│   │       └── auth.ts            # Authentication
│   └── package.json
├── utils/
│   ├── search.py                  # Search tools
│   ├── web_scraper.py             # Scraping utilities
│   ├── cache.py                   # Caching layer
│   ├── retry.py                   # Retry logic
│   ├── circuit_breaker.py         # Circuit breaker
│   ├── metrics.py                 # Prometheus metrics
│   ├── logging_config.py          # Structured logging
│   └── health.py                  # Health checks
├── schema.py                      # JSON schemas
├── config/
│   └── loader.py                  # Config management
└── tests/                         # Test suite
```

---

## 6. Database Schema

### 6.1 Events Table
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    event_website TEXT,
    city TEXT,
    country TEXT,
    start_date TEXT,
    end_date TEXT,
    theme TEXT,
    organizer TEXT,
    overall_score REAL,
    priority_tier TEXT,
    status TEXT DEFAULT 'Discovered',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT  -- JSON blob
);
```

### 6.2 Vendors Table
```sql
CREATE TABLE vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT NOT NULL,
    vendor_website TEXT,
    vendor_type TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    linkedin_url TEXT,
    relevance_score REAL,
    event_id INTEGER,
    status TEXT DEFAULT 'Discovered',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT  -- JSON blob
);
```

### 6.3 Pipeline Runs Table
```sql
CREATE TABLE pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id TEXT UNIQUE NOT NULL,
    status TEXT,
    query TEXT,
    industry TEXT,
    region TEXT,
    progress_percent INTEGER,
    events_count INTEGER,
    vendors_count INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    errors TEXT  -- JSON array
);
```

### 6.4 Checkpoints Table
```sql
CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkpoint_id TEXT UNIQUE NOT NULL,
    pipeline_id TEXT,
    type TEXT,
    name TEXT,
    status TEXT,
    data TEXT,  -- JSON blob
    created_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by TEXT,
    review_notes TEXT
);
```

---

## 7. API Specifications

### 7.1 Core Endpoints

#### Health & Metrics
```
GET  /              # API info
GET  /health        # Health check
GET  /metrics       # Prometheus metrics
```

#### Events
```
GET    /events                    # List events
POST   /events                    # Create event
GET    /events/{id}               # Get event
PUT    /events/{id}               # Update event
DELETE /events/{id}               # Delete event
GET    /events/{id}/vendors       # Get event vendors
GET    /events/{id}/score         # Get event score
POST   /events/{id}/score         # Score event
```

#### Pipeline
```
POST   /pipeline/start            # Start pipeline
GET    /pipeline/{id}/status      # Get status
POST   /pipeline/{id}/cancel      # Cancel pipeline
GET    /pipeline/runs             # List runs
GET    /stream/pipeline/{id}      # SSE stream
```

#### Checkpoints
```
GET    /checkpoints               # List checkpoints
POST   /checkpoints/{id}/approve  # Approve checkpoint
POST   /checkpoints/{id}/reject   # Reject checkpoint
GET    /checkpoints/{id}/summary  # Get summary
```

#### Logs
```
GET    /logs?lines=100&filter=error  # Get logs
GET    /logs/search?query=exception  # Search logs
```

### 7.2 Request/Response Examples

#### Start Pipeline
**Request:**
```json
POST /pipeline/start
{
  "query": "fintech conferences Europe Q2 2026",
  "industry": "fintech",
  "region": "Europe",
  "enable_checkpoints": false,
  "auto_approve": true
}
```

**Response:**
```json
{
  "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "query": "fintech conferences Europe Q2 2026",
  "progress_percent": 0,
  "events_count": 0,
  "started_at": "2026-03-27T10:00:00Z"
}
```

---

## 8. Frontend Specifications

### 8.1 Page Structure

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | Dashboard | Overview stats, recent events |
| `/events` | EventList | Browse, search, filter events |
| `/events/[id]` | EventDetail | Event details, vendors, scores |
| `/pipeline` | PipelinePage | Start/monitor pipelines |
| `/checkpoints` | Checkpoints | Review approval queue |
| `/logs` | LogsViewer | View/search system logs |
| `/reports` | Reports | Generate/download reports |
| `/metrics` | Metrics | System health dashboard |

### 8.2 Key Components

#### DashboardLayout
```tsx
// Wraps all pages with sidebar + header
<DashboardLayout>
  {children}
</DashboardLayout>
```

#### Toast Notifications
```tsx
// Global toast system using react-hot-toast
// Shows: Loading, Success, Error states
```

#### Real-time Updates
```tsx
// React Query with polling
useQuery({
  queryKey: ['pipeline', id],
  queryFn: () => getPipelineStatus(id),
  refetchInterval: 3000  // Poll every 3s
})
```

### 8.3 State Management

```typescript
// Global auth state
const { user, login, logout } = useAuth()

// API queries
const { data, isLoading } = useQuery({...})
const mutation = useMutation({...})

// Toast notifications
toast.success('Pipeline started!')
toast.error('Failed: ' + error.message)
```

---

## 9. Implementation Plan

### Phase 1: Core Backend (Week 1-2)

**Week 1: Foundation**
- [ ] Set up Python project structure
- [ ] Install dependencies (FastAPI, Pydantic, etc.)
- [ ] Create base agent class
- [ ] Implement SchemaInitAgent
- [ ] Set up SQLite database
- [ ] Create FastAPI skeleton

**Week 2: Event Discovery**
- [ ] Implement IntentUnderstandingAgent
- [ ] Implement EventDiscoveryAgent
- [ ] Integrate DuckDuckGo search
- [ ] Add filtering logic
- [ ] Implement scoring algorithm
- [ ] Create API endpoints for events

**Deliverable:** Working event discovery API

### Phase 2: Pipeline & Checkpoints (Week 3-4)

**Week 3: Pipeline Orchestration**
- [ ] Implement remaining agents (Qualification → Prioritization)
- [ ] Create pipeline orchestrator
- [ ] Add checkpoint manager
- [ ] Implement human approval flow
- [ ] Add error handling & retries

**Week 4: Advanced Features**
- [ ] Implement VendorDiscoveryAgent
- [ ] Implement OutreachEmailAgent
- [ ] Add report generation
- [ ] Implement SSE streaming
- [ ] Add metrics collection
- [ ] Write comprehensive tests

**Deliverable:** Full pipeline with checkpoints

### Phase 3: Frontend (Week 5-6)

**Week 5: UI Foundation**
- [ ] Set up Next.js project
- [ ] Install Tailwind, React Query
- [ ] Create layout components
- [ ] Implement Dashboard page
- [ ] Implement Events list/detail
- [ ] Connect to backend API

**Week 6: Advanced UI**
- [ ] Implement Pipeline page with real-time updates
- [ ] Create Checkpoints review interface
- [ ] Build Logs viewer
- [ ] Add Reports page
- [ ] Implement toast notifications
- [ ] Add loading states & error handling

**Deliverable:** Complete web UI

### Phase 4: Reliability & Polish (Week 7-8)

**Week 7: Reliability**
- [ ] Implement caching layer
- [ ] Add circuit breaker pattern
- [ ] Set up structured logging
- [ ] Add health checks
- [ ] Implement rate limiting
- [ ] Performance optimization

**Week 8: Testing & Deployment**
- [ ] Write E2E tests
- [ ] Performance testing
- [ ] Security audit
- [ ] Create deployment scripts
- [ ] Documentation
- [ ] Production deployment

**Deliverable:** Production-ready system

---

## 10. Deployment Guide

### 10.1 Prerequisites
```bash
# Python 3.11+
python --version

# Node.js 18+
node --version

# Git
git --version
```

### 10.2 Backend Deployment

```bash
# 1. Clone repository
git clone <repo-url>
cd marketing_agents

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Initialize database
python -c "from database.models import init_db; init_db()"

# 6. Run server
python api/main.py
# Or with uvicorn:
# uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 10.3 Frontend Deployment

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Set up environment
cp .env.local.example .env.local
# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 4. Run development server
npm run dev

# 5. Build for production
npm run build
npm start
```

### 10.4 Production Deployment

**Using Docker:**
```dockerfile
# Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Dockerfile.frontend
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

**Environment Variables:**
```bash
# Backend (.env)
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=...
DATABASE_URL=sqlite:///./marketing_agents.db
LOG_LEVEL=INFO

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_NAME=Marketing Agents
```

---

## 11. Testing Strategy

### 11.1 Unit Tests
```python
# Test EventDiscoveryAgent
def test_event_discovery_filters():
    agent = EventDiscoveryAgent()
    # Test exclusion logic
    # Test scoring algorithm
    # Test duplicate detection
```

### 11.2 Integration Tests
```python
# Test full pipeline
def test_pipeline_execution():
    # Start pipeline
    # Verify each agent executes
    # Check final output
```

### 11.3 E2E Tests
```python
# Frontend tests with Playwright
def test_pipeline_start():
    # Navigate to pipeline page
    # Fill form
    # Click start
    # Verify success toast
```

### 11.4 Test Commands
```bash
# Backend tests
pytest tests/ -v --cov=agents --cov=utils

# Frontend tests
npm test

# E2E tests
npx playwright test
```

---

## 12. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **Agent** | Autonomous component that performs a specific task |
| **Checkpoint** | Human approval gate in the pipeline |
| **Pipeline** | Sequential workflow of agents |
| **SSE** | Server-Sent Events for real-time updates |
| **TTL** | Time To Live for cache entries |

### Appendix B: API Key Setup

**OpenAI:**
1. Go to https://platform.openai.com
2. Create API key
3. Add to `.env`

**Tavily (optional fallback):**
1. Go to https://tavily.com
2. Sign up for API key
3. Add to `.env`

### Appendix C: Troubleshooting

**Issue:** Pipeline fails at 25%
**Solution:** Check logs at `/logs`, likely checkpoint filename bug

**Issue:** Frontend can't connect to backend
**Solution:** Verify CORS settings and API_URL

**Issue:** Search returns no results
**Solution:** Check API keys, verify rate limits

### Appendix D: Monitoring

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Metrics:**
```bash
curl http://localhost:8000/metrics
```

**Logs:**
```bash
tail -f /tmp/fastapi.log
```

---

## Summary

This PRD provides a complete blueprint for building the Marketing Agents Event Discovery Platform. The system uses an 8-agent pipeline with human checkpoints to discover, qualify, and prioritize industry events for sponsorship opportunities.

**Key Innovations:**
- IntentUnderstandingAgent for semantic query parsing
- Real-time scoring during event discovery
- Human-in-the-loop approval system
- Comprehensive logging and monitoring
- Modern Next.js frontend with real-time updates

**Timeline:** 8 weeks from start to production

**Team Size:** 2-3 engineers (1 backend, 1 frontend, 1 DevOps)

---

**Document Owner:** Marketing Agents Team  
**Last Updated:** March 27, 2026  
**Version:** 2.0
