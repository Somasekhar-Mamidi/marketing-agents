# DEEP PLAN 2: Parallel Agent Execution System

## Executive Summary
Transform the current sequential pipeline into a true parallel execution system where multiple agents run simultaneously, with real-time progress updates flowing to the frontend for visual feedback.

## Timeline: 2.5 weeks

---

## Phase 1: Backend Architecture (Days 1-4)

### 1.1 Async Infrastructure Setup
- [ ] Install async dependencies
```bash
pip install asyncio aiohttp httpx
pip install celery redis  # For distributed tasks (optional)
```
- [ ] Create `pipeline/async_orchestrator.py` base class
- [ ] Design agent dependency graph (DAG)
- [ ] Implement agent task queue
- [ ] Create async execution context manager

### 1.2 Agent Parallelization Analysis
```
Current Sequential Flow:
Schema → Intent → Discovery → Scraper → Intelligence → Prioritization → Email → Excel

Optimized Parallel Flow:
Phase 1: Schema + Intent (can run in parallel)
Phase 2: Discovery (depends on Intent)
Phase 3: Scraper (parallel for each event found)
Phase 4: Intelligence (parallel for each event)
Phase 5: Prioritization (depends on all Intelligence)
Phase 6: Email + Excel (can run in parallel)
```

### 1.3 Async Base Agent Class
- [ ] Create `agents/base_async.py`
- [ ] Abstract async `execute()` method
- [ ] Progress callback mechanism
- [ ] Error handling with retry logic
- [ ] Timeout management per agent

```python
class AsyncBaseAgent(ABC):
    @abstractmethod
    async def execute(self, input_data: AgentInput, progress_callback: Callable) -> AgentOutput:
        pass
    
    async def run_with_timeout(self, timeout: int = 300):
        # Implementation
```

### 1.4 State Management
- [ ] Design shared context store (Redis/SQLite)
- [ ] Implement event aggregation from parallel agents
- [ ] Create checkpoint/snapshot mechanism
- [ ] Handle partial failures gracefully

### 1.5 Concurrency Configuration
- [ ] Define max concurrent agents (default: 3-4)
- [ ] Rate limiting per search provider
- [ ] Connection pool management
- [ ] Memory usage controls

**Deliverable:** Async backend foundation ready for agent migration

---

## Phase 2: Async Pipeline Implementation (Days 5-9)

### 2.1 Migrate Existing Agents to Async

#### Agent 1: Schema Initialization (Async)
- [ ] Convert to async (already fast, but for consistency)
- [ ] Add progress callback (0% → 100%)

#### Agent 2: Intent Understanding (Async)
- [ ] Async LLM API calls (if using OpenAI)
- [ ] Parallel keyword matching
- [ ] Progress tracking

#### Agent 3: Event Discovery (Async) - **CRITICAL**
- [ ] Parallel search queries per region
- [ ] Concurrent API calls to Tavily/Serper
- [ ] Async result aggregation
- [ ] Real-time event count updates
```python
async def search_all_regions(queries: List[str]):
    tasks = [search_single_region(q) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return merge_results(results)
```

#### Agent 4: Website Scraper (Async) - **CRITICAL**
- [ ] Concurrent HTTP requests with httpx
- [ ] Parallel scraping of multiple events
- [ ] Rate limiting (max 10 concurrent)
- [ ] Progress per event scraped

#### Agent 5: Event Intelligence (Async)
- [ ] Parallel analysis per event
- [ ] Async LLM calls for insights
- [ ] Score calculation in parallel

#### Agent 6: Prioritization (Async)
- [ ] Sort events (fast, but async for consistency)
- [ ] Tier assignment

#### Agent 7: Outreach Email (Async)
- [ ] Parallel email generation
- [ ] Async LLM calls for personalization

#### Agent 8: Excel Export (Async)
- [ ] Async file I/O
- [ ] Streaming generation for large datasets

### 2.2 Parallel Orchestrator Engine
- [ ] Create `pipeline/parallel_engine.py`
- [ ] Implement DAG-based execution
- [ ] Priority queue for agent scheduling
- [ ] Resource-aware scheduling

```python
class ParallelPipelineEngine:
    def __init__(self, max_concurrent: int = 4):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.agent_graph = self._build_dependency_graph()
    
    async def execute(self, pipeline_id: str, query: str):
        # Execute agents in parallel based on DAG
```

### 2.3 Progress Tracking System
- [ ] Create `pipeline/progress_tracker.py`
- [ ] Per-agent progress (0-100%)
- [ ] Overall pipeline progress
- [ ] Event discovery count (live updates)
- [ ] Vendor discovery count (live updates)
- [ ] Time elapsed/estimated remaining

### 2.4 Error Handling & Recovery
- [ ] Individual agent retry logic (3 attempts)
- [ ] Circuit breaker for failing agents
- [ ] Partial result saving on failure
- [ ] Resume from checkpoint capability

**Deliverable:** All 8 agents running asynchronously with parallel execution

---

## Phase 3: Real-time Updates (Days 10-13)

### 3.1 Server-Sent Events (SSE) Implementation

#### Backend SSE Endpoint
- [ ] Create `/api/pipeline/{id}/stream` endpoint
- [ ] Implement FastAPI SSE response
- [ ] Event serialization (JSON)
- [ ] Connection management (keep-alive)

```python
from fastapi.responses import StreamingResponse

@app.get("/pipeline/{pipeline_id}/stream")
async def stream_pipeline(pipeline_id: str):
    async def event_generator():
        while pipeline_active:
            progress = await get_progress(pipeline_id)
            yield f"data: {json.dumps(progress)}\n\n"
            await asyncio.sleep(1)  # Push every second
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

#### Event Types
```typescript
interface PipelineEvent {
  type: 'agent_start' | 'agent_progress' | 'agent_complete' | 'agent_error' | 'log' | 'complete';
  pipelineId: string;
  timestamp: string;
  data: {
    agentName?: string;
    progress?: number;
    eventsFound?: number;
    vendorsFound?: number;
    logMessage?: string;
    error?: string;
  };
}
```

### 3.2 WebSocket Alternative (Optional)
- [ ] Evaluate WebSocket for bidirectional communication
- [ ] Implement with `python-socketio` if needed
- [ ] Fallback to SSE if WebSocket fails

### 3.3 Frontend SSE Client
- [ ] Create `hooks/usePipelineStream.ts`
- [ ] EventSource API wrapper
- [ ] Automatic reconnection
- [ ] Error handling
- [ ] Cleanup on unmount

```typescript
export function usePipelineStream(pipelineId: string) {
  const [progress, setProgress] = useState(0);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  useEffect(() => {
    const eventSource = new EventSource(`/api/pipeline/${pipelineId}/stream`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleEvent(data);
    };
    
    return () => eventSource.close();
  }, [pipelineId]);
  
  return { progress, agents, logs };
}
```

### 3.4 State Synchronization
- [ ] Redis pub/sub for multi-server setups (optional)
- [ ] SQLite with polling fallback
- [ ] In-memory state for single-server

**Deliverable:** Real-time pipeline updates flowing from backend to frontend

---

## Phase 4: Frontend Visualization (Days 14-16)

### 4.1 Parallel Agent Grid Component
- [ ] 6-agent grid layout (2x3 on desktop, 1x6 on mobile)
- [ ] Individual agent cards with:
  - Animated progress bars
  - Status indicators (pending/running/completed/failed)
  - Color coding per agent
  - Event count badges
  - Pulse animation for running agents

### 4.2 Live Updates Integration
- [ ] Connect to SSE hook
- [ ] Smooth progress transitions (Framer Motion)
- [ ] Agent status changes with animations
- [ ] Log appending with auto-scroll

### 4.3 Performance Optimizations
- [ ] React.memo for agent cards
- [ ] Debounce rapid updates
- [ ] Virtualize log list if 1000+ entries
- [ ] Optimistic UI updates

### 4.4 User Controls
- [ ] Pause/Resume pipeline
- [ ] Cancel running pipeline
- [ ] Restart from checkpoint
- [ ] View logs in real-time

**Deliverable:** Fully functional parallel agent visualization UI

---

## Technical Architecture

### System Flow
```
User Request
    ↓
FastAPI Endpoint → Create Pipeline ID
    ↓
ParallelEngine → Build DAG
    ↓
Asyncio Gather → Run Agents
    ↓
Progress Tracker → Update State
    ↓
SSE Stream → Frontend
    ↓
UI Updates in Real-time
```

### Concurrency Model
```python
# Max 4 agents running simultaneously
semaphore = asyncio.Semaphore(4)

async def run_agent(agent, context):
    async with semaphore:
        return await agent.execute(context)
```

### Data Flow
1. **Discovery Phase:** Find events in parallel → Aggregate → Deduplicate
2. **Scraping Phase:** Scrape each event website in parallel
3. **Intelligence Phase:** Analyze each event in parallel
4. **Final Phases:** Sort, generate emails, export

---

## Testing Strategy

### Unit Tests
- [ ] Test individual async agents
- [ ] Test parallel execution with mocks
- [ ] Test progress tracking
- [ ] Test error handling

### Integration Tests
- [ ] Full pipeline execution
- [ ] SSE stream connectivity
- [ ] Frontend state updates
- [ ] Memory leak detection

### Load Tests
- [ ] 10 concurrent pipelines
- [ ] 100+ events discovered
- [ ] Long-running stability (1+ hour)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| API rate limits | Implement backoff, multiple keys, queue management |
| Memory overflow | Stream large datasets, limit concurrent operations |
| SSE disconnections | Auto-reconnect, checkpoint resume |
| Database locks | Use async SQLAlchemy, connection pooling |
| Agent failures | Individual retry, continue with partial results |

---

## Success Metrics
- [ ] Pipeline completes 3x faster than sequential
- [ ] UI updates every 1-2 seconds
- [ ] Zero memory leaks over 100 pipelines
- [ ] 99.9% uptime for SSE connections
- [ ] Handles 50+ concurrent users

---

## Estimated Effort
- **Total:** 16 days (3 weeks)
- **Backend:** 10 days
- **Frontend:** 4 days
- **Testing:** 2 days
