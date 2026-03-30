"""FastAPI backend for Marketing Agents Next.js frontend."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator

# Import marketing agents modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import get_database, Database
from checkpoint.manager import (
    get_checkpoint_manager, CheckpointManager,
    CheckpointType, CheckpointStatus
)
from agents.intent_understanding import IntentUnderstandingAgent
from agents.event_discovery import EventDiscoveryAgent
from agents.event_qualification import EventQualificationAgent
from agents.event_website_scraper import EventWebsiteScraperAgent
from agents.event_intelligence import EventIntelligenceAgent
from agents.event_prioritization import EventPrioritizationAgent
from agents.outreach_email import OutreachEmailAgent
from agents.vendor_discovery import VendorDiscoveryAgent
from utils.health import HealthChecker
from utils.metrics import MetricsCollector
from utils.logging_config import get_logger
from utils.configurable_llm_client import get_llm_client

# Import experiment and model routers
from api.experiments import router as experiments_router

# Configure logging
logger = get_logger(__name__)

# Global instances
db: Optional[Database] = None
checkpoint_mgr: Optional[CheckpointManager] = None
health_checker: Optional[HealthChecker] = None
metrics: Optional[MetricsCollector] = None

# Pipeline run storage (in-memory for active runs)
active_runs: Dict[str, Dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db, checkpoint_mgr, health_checker, metrics
    
    # Startup
    logger.info("Starting Marketing Agents API...")
    db = get_database()
    checkpoint_mgr = get_checkpoint_manager()
    health_checker = HealthChecker()
    metrics = MetricsCollector()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Marketing Agents API...")


app = FastAPI(
    title="Marketing Agents API",
    description="Backend API for Event Discovery and Marketing Pipeline",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Root endpoint - redirects to API documentation."""
    return {
        "message": "Marketing Agents API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "/health",
            "/metrics",
            "/events",
            "/vendors",
            "/discover",
            "/pipeline/*",
            "/checkpoints/*",
            "/reports/*"
        ]
    }

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include experiment and model management routers
app.include_router(experiments_router)


# ==================== Pydantic Models ====================

class EventBase(BaseModel):
    """Base event model."""
    event_name: str
    event_website: str
    city: Optional[str] = None
    country: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    theme: str
    organizer: Optional[str] = None
    overall_score: float = 0.0
    priority_tier: str = "Tier 4 - Low Priority"
    status: str = "discovered"


class EventCreate(EventBase):
    """Event creation model."""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventResponse(EventBase):
    """Event response model."""
    id: int
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class VendorBase(BaseModel):
    """Base vendor model."""
    vendor_name: str
    vendor_website: Optional[str] = None
    vendor_type: str = "sponsor"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    relevance_score: float = 0.0
    event_id: Optional[int] = None
    status: str = "identified"


class VendorResponse(VendorBase):
    """Vendor response model."""
    id: int
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class EmailBase(BaseModel):
    """Base email model."""
    recipient_type: str
    recipient_id: int
    subject: str
    body: str
    status: str = "draft"
    gmail_draft_id: Optional[str] = None


class EmailResponse(EmailBase):
    """Email response model."""
    id: int
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class CheckpointResponse(BaseModel):
    """Checkpoint response model."""
    id: str
    pipeline_id: str
    type: str
    name: str
    status: str
    data: Dict[str, Any]
    created_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None


class CheckpointReviewRequest(BaseModel):
    """Checkpoint review request."""
    reviewed_by: str
    review_notes: Optional[str] = ""


class PipelineStartRequest(BaseModel):
    """Pipeline start request."""
    query: str
    industry: Optional[str] = None
    region: Optional[str] = None
    theme: Optional[str] = None
    enable_checkpoints: bool = False
    auto_approve: bool = True


class PipelineStatusResponse(BaseModel):
    """Pipeline status response."""
    pipeline_id: str
    status: str
    query: str
    industry: Optional[str] = None
    region: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    current_agent: Optional[str] = None
    progress_percent: int = 0
    events_count: int = 0
    vendors_count: int = 0
    errors: List[str] = Field(default_factory=list)


class DiscoveryRequest(BaseModel):
    """Event discovery request."""
    query: str
    industry: Optional[str] = None
    region: Optional[str] = None
    max_results: int = 20


class DiscoveryResponse(BaseModel):
    """Discovery response."""
    events_found: int
    events: List[Dict[str, Any]]
    search_queries: List[str]


class ScoringRequest(BaseModel):
    """Event scoring request."""
    event_id: int
    criteria: Dict[str, float]  # criterion_name -> score


class ScoringBreakdown(BaseModel):
    """Detailed scoring breakdown."""
    criterion: str
    score: float
    max_points: int
    explanation: str


class EventScoreResponse(BaseModel):
    """Event score response."""
    event_id: int
    total_score: float
    max_score: int = 100
    tier: str
    breakdown: List[ScoringBreakdown]


class ReportRequest(BaseModel):
    """Report generation request."""
    report_type: str  # "events", "vendors", "pipeline"
    pipeline_id: Optional[str] = None
    event_ids: Optional[List[int]] = None
    format: str = "markdown"  # "markdown", "json"


class ReportResponse(BaseModel):
    """Report response."""
    report_id: str
    report_type: str
    content: str
    generated_at: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    checks: Dict[str, Any]


class MetricsResponse(BaseModel):
    """Metrics response."""
    total_events_discovered: int
    total_vendors_identified: int
    total_emails_generated: int
    average_event_score: float
    pipelines_completed: int
    pipelines_failed: int
    agent_execution_counts: Dict[str, int]


# ==================== API Endpoints ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    checks = {
        "database": "healthy" if db else "unhealthy",
        "checkpoint_manager": "healthy" if checkpoint_mgr else "unhealthy"
    }
    
    all_healthy = all(c == "healthy" for c in checks.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        checks=checks
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    events = db.get_events()
    vendors = db.get_vendors()
    
    scores = [e.get('overall_score', 0) for e in events if e.get('overall_score')]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return MetricsResponse(
        total_events_discovered=len(events),
        total_vendors_identified=len(vendors),
        total_emails_generated=0,  # TODO: Query emails table
        average_event_score=avg_score,
        pipelines_completed=sum(1 for r in active_runs.values() if r.get('status') == 'completed'),
        pipelines_failed=sum(1 for r in active_runs.values() if r.get('status') == 'failed'),
        agent_execution_counts={}  # TODO: Track agent executions
    )


# ==================== Event Endpoints ====================

@app.get("/events", response_model=List[EventResponse])
async def list_events(
    status: Optional[str] = Query(None, description="Filter by status"),
    tier: Optional[str] = Query(None, description="Filter by priority tier"),
    search: Optional[str] = Query(None, description="Search in event name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """List events with optional filtering."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    events = db.get_events(status=status, tier=tier)
    
    if search:
        search_lower = search.lower()
        events = [e for e in events if search_lower in e.get('event_name', '').lower()]
    
    total = len(events)
    events = events[offset:offset + limit]
    
    return [EventResponse(**e) for e in events]


@app.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int):
    """Get a single event by ID."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    events = db.get_events()
    event = next((e for e in events if e['id'] == event_id), None)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return EventResponse(**event)


@app.post("/events", response_model=EventResponse)
async def create_event(event: EventCreate):
    """Create a new event."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    event_dict = event.dict()
    event_id = db.save_event(event_dict)
    
    events = db.get_events()
    created = next(e for e in events if e['id'] == event_id)
    
    return EventResponse(**created)


@app.put("/events/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, event: EventCreate):
    """Update an existing event."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Check if event exists
    events = db.get_events()
    existing = next((e for e in events if e['id'] == event_id), None)
    
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event_dict = event.dict()
    event_dict['id'] = event_id
    db.save_event(event_dict)
    
    events = db.get_events()
    updated = next(e for e in events if e['id'] == event_id)
    
    return EventResponse(**updated)


@app.delete("/events/{event_id}")
async def delete_event(event_id: int):
    """Delete an event."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    success = db.delete_event(event_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event deleted successfully", "event_id": event_id}


@app.get("/events/{event_id}/vendors", response_model=List[VendorResponse])
async def get_event_vendors(event_id: int):
    """Get vendors for a specific event."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    vendors = db.get_vendors(event_id=event_id)
    return [VendorResponse(**v) for v in vendors]


@app.get("/events/{event_id}/score", response_model=EventScoreResponse)
async def get_event_score(event_id: int):
    """Get detailed scoring for an event."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    events = db.get_events()
    event = next((e for e in events if e['id'] == event_id), None)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Build scoring breakdown from event metadata
    metadata = event.get('metadata', {})
    breakdown = []
    
    criteria = [
        ("audience_relevance_score", "Audience Quality", 25),
        ("industry_reputation_score", "Industry Reputation", 20),
        ("attendance_score", "Attendance", 20),
        ("sponsor_value_score", "Sponsor Value", 15),
        ("regional_importance_score", "Regional Importance", 10),
        ("competition_score", "Competition", 10),
    ]
    
    total = 0
    for key, name, max_pts in criteria:
        score = metadata.get(key, 0)
        if isinstance(score, str):
            try:
                score = float(score)
            except:
                score = 0
        breakdown.append(ScoringBreakdown(
            criterion=name,
            score=score,
            max_points=max_pts,
            explanation=metadata.get(f"{key}_explanation", "")
        ))
        total += score
    
    # Determine tier
    if total >= 80:
        tier = "Tier 1 - Must Attend"
    elif total >= 65:
        tier = "Tier 2 - High Priority"
    elif total >= 50:
        tier = "Tier 3 - Medium Priority"
    else:
        tier = "Tier 4 - Low Priority"
    
    return EventScoreResponse(
        event_id=event_id,
        total_score=total,
        tier=tier,
        breakdown=breakdown
    )


# ==================== Vendor Endpoints ====================

@app.get("/vendors", response_model=List[VendorResponse])
async def list_vendors(
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    vendor_type: Optional[str] = Query(None, description="Filter by vendor type"),
    limit: int = Query(50, ge=1, le=200)
):
    """List vendors with optional filtering."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    vendors = db.get_vendors(event_id=event_id)
    
    if vendor_type:
        vendors = [v for v in vendors if v.get('vendor_type') == vendor_type]
    
    return [VendorResponse(**v) for v in vendors[:limit]]


@app.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: int):
    """Get a single vendor by ID."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    vendors = db.get_vendors()
    vendor = next((v for v in vendors if v['id'] == vendor_id), None)
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return VendorResponse(**vendor)


# ==================== Discovery Endpoints ====================

@app.post("/discover", response_model=DiscoveryResponse)
async def discover_events(request: DiscoveryRequest):
    """Run event discovery agent."""
    logger.info(f"Starting event discovery: {request.query}")
    
    try:
        agent = EventDiscoveryAgent()
        
        from agents.base import AgentInput
        input_data = AgentInput(
            query=request.query,
            context={
                "industry": request.industry or "",
                "region": request.region or "",
                "max_results": request.max_results
            }
        )
        
        output = agent.execute(input_data)
        events = output.findings.get("events", [])
        
        # Save discovered events to database
        saved_events = []
        for event in events:
            if db:
                event_id = db.save_event(event)
                event['id'] = event_id
            saved_events.append(event)
        
        return DiscoveryResponse(
            events_found=len(saved_events),
            events=saved_events,
            search_queries=output.findings.get("search_queries", [])
        )
    
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Pipeline Endpoints ====================

@app.post("/pipeline/start", response_model=PipelineStatusResponse)
async def start_pipeline(
    request: PipelineStartRequest,
    background_tasks: BackgroundTasks
):
    """Start a new pipeline run."""
    pipeline_id = str(uuid.uuid4())
    
    active_runs[pipeline_id] = {
        "pipeline_id": pipeline_id,
        "status": "running",
        "query": request.query,
        "industry": request.industry,
        "region": request.region,
        "started_at": datetime.utcnow().isoformat(),
        "current_agent": None,
        "progress_percent": 0,
        "events_count": 0,
        "vendors_count": 0,
        "errors": [],
        "agent_outputs": {},
        "completed_agents": [],
        "enable_checkpoints": request.enable_checkpoints,
        "auto_approve": request.auto_approve
    }
    
    # Start pipeline in background
    background_tasks.add_task(run_pipeline, pipeline_id, request)
    
    logger.info(f"Pipeline started: {pipeline_id}")
    
    return PipelineStatusResponse(
        pipeline_id=pipeline_id,
        status="running",
        query=request.query,
        industry=request.industry,
        region=request.region,
        started_at=active_runs[pipeline_id]["started_at"],
        current_agent=None,
        progress_percent=0,
        events_count=0,
        vendors_count=0
    )


def _is_vendor_only_search(query: str, industry: str) -> bool:
    query_lower = query.lower()
    vendor_keywords = ['vendor', 'vendors', 'booth', 'booths', 'contractor', 'contractors',
                       'service provider', 'service providers', 'exhibitor', 'exhibitors',
                       'sponsor', 'sponsors', 'builder', 'builders', 'stand builder']
    has_vendor_keyword = any(kw in query_lower for kw in vendor_keywords)
    event_keywords = ['event', 'events', 'conference', 'conferences', 'summit', 'summits',
                      'expo', 'expos', 'trade show', 'trade shows', 'forum', 'forums']
    has_event_keyword = any(kw in query_lower for kw in event_keywords)
    return has_vendor_keyword and not has_event_keyword


async def run_pipeline(pipeline_id: str, request: PipelineStartRequest):
    """Run the full pipeline in background."""
    run = active_runs.get(pipeline_id)
    if not run:
        return
    
    try:
        is_vendor_search = _is_vendor_only_search(request.query, request.industry or "")
        if is_vendor_search:
            await _run_vendor_pipeline(pipeline_id, request, run)
        else:
            await _run_event_pipeline(pipeline_id, request, run)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        run["status"] = "failed"
        run["errors"].append(str(e))
        run["completed_at"] = datetime.utcnow().isoformat()


async def _run_vendor_pipeline(pipeline_id: str, request: PipelineStartRequest, run: dict):
    """Run pipeline optimized for vendor/service provider searches."""
    from agents.base import AgentInput
    import asyncio
    
    run["current_agent"] = "intent_understanding"
    run["progress_percent"] = 10
    await asyncio.sleep(0.5)
    
    intent_agent = IntentUnderstandingAgent()
    intent_input = AgentInput(
        query=request.query,
        context={"industry": request.industry or "", "region": request.region or ""}
    )
    intent_output = intent_agent.execute(intent_input)
    _store_agent_output(run, "intent_understanding", intent_output)
    
    run["current_agent"] = "vendor_discovery"
    run["progress_percent"] = 40
    await asyncio.sleep(0.5)
    
    vendor_discovery_agent = VendorDiscoveryAgent(max_vendors_per_event=15)
    
    query_lower = request.query.lower()
    service_category = "vendor"
    if 'booth' in query_lower or 'stand' in query_lower:
        service_category = "booth_builder"
    elif 'catering' in query_lower:
        service_category = "catering"
    
    location = request.region or ""
    if not location:
        intent_data = intent_output.findings.get("intent", {})
        regions = intent_data.get("regions", [])
        if regions:
            location = regions[0]
    
    vendor_input = AgentInput(
        query=request.query,
        context={},
        parameters={"service_category": service_category, "location": location}
    )
    vendor_output = vendor_discovery_agent.execute(vendor_input)
    _store_agent_output(run, "vendor_discovery", vendor_output)
    vendors = vendor_output.findings.get("vendors", [])
    
    run["vendors_count"] = len(vendors)
    run["progress_percent"] = 70
    await asyncio.sleep(0.5)
    
    for vendor in vendors:
        if db:
            db.save_vendor(vendor)
    
    run["current_agent"] = "event_intelligence"
    run["progress_percent"] = 80
    await asyncio.sleep(0.3)
    
    run["current_agent"] = "outreach_email"
    run["progress_percent"] = 90
    await asyncio.sleep(0.3)
    
    if vendors:
        email_agent = OutreachEmailAgent()
        email_input = AgentInput(query=request.query, context={"vendors": vendors[:5]})
        email_output = email_agent.execute(email_input)
        _store_agent_output(run, "outreach_email", email_output)
    
    run["progress_percent"] = 100
    run["status"] = "completed"
    run["completed_at"] = datetime.utcnow().isoformat()


async def _run_event_pipeline(pipeline_id: str, request: PipelineStartRequest, run: dict):
    """Run standard event-focused pipeline."""
    import asyncio
    try:
        # LLM connectivity check
        try:
            from utils.configurable_llm_client import get_llm_client
            client = get_llm_client()
            provider = list(client._providers.values())[0] if client._providers else None
            if not provider or not provider.is_available():
                logger.warning("LLM provider not available - pipeline will use fallback heuristics")
                run["errors"].append("LLM provider not available, using fallback heuristics")
        except Exception as e:
            logger.warning(f"LLM connectivity check failed: {e}")

        # Step 1: Intent Understanding
        run["current_agent"] = "intent_understanding"
        run["progress_percent"] = 5
        
        intent_agent = IntentUnderstandingAgent()
        from agents.base import AgentInput
        
        intent_input = AgentInput(
            query=request.query,
            context={"industry": request.industry or "", "region": request.region or ""}
        )
        intent_output = intent_agent.execute(intent_input)
        _store_agent_output(run, "intent_understanding", intent_output)
        intent_data = intent_output.findings.get("intent", {})
        await asyncio.sleep(0.1)  # yield for SSE polling
        
        logger.info(f"Intent understood with {intent_data.get('confidence', 0)}% confidence")
        
        # Step 2: Event Discovery (with intent data)
        run["current_agent"] = "event_discovery"
        run["progress_percent"] = 15
        
        discovery_agent = EventDiscoveryAgent()
        
        discovery_input = AgentInput(
            query=request.query,
            context={
                "industry": request.industry or "",
                "region": request.region or "",
                "intent": intent_data  # Pass intent to discovery agent
            }
        )
        discovery_output = discovery_agent.execute(discovery_input)
        _store_agent_output(run, "event_discovery", discovery_output)
        events = discovery_output.findings.get("events", [])
        await asyncio.sleep(0.1)  # yield for SSE polling
        
        # Save events
        for event in events:
            if db:
                db.save_event(event)
        
        run["events_count"] = len(events)
        run["progress_percent"] = 25

        # Step 3: Event Qualification
        run["current_agent"] = "event_qualification"
        run["progress_percent"] = 35
        
        qualified_events = []
        if events:
            qualification_agent = EventQualificationAgent()
            qualification_input = AgentInput(
                query=request.query,
                context={"events": events, "intent": intent_data}
            )
            qualification_output = qualification_agent.execute(qualification_input)
            _store_agent_output(run, "event_qualification", qualification_output)
            qualified_events = qualification_output.findings.get("events", events)
        await asyncio.sleep(0.1)  # yield for SSE polling
        
        # Step 4: Vendor Discovery (for service providers like booth builders)
        run["current_agent"] = "vendor_discovery"
        run["progress_percent"] = 50
        
        vendor_discovery_agent = VendorDiscoveryAgent(max_vendors_per_event=10)
        
        # Check if user is looking for service providers directly
        query_lower = request.query.lower()
        service_keywords = ['booth', 'vendor', 'contractor', 'exhibitor', 'sponsor', 'service provider']
        is_service_search = any(kw in query_lower for kw in service_keywords)
        
        vendors = []
        if is_service_search and request.region:
            vendor_input = AgentInput(
                query=f"Find {request.industry or 'event'} service providers in {request.region}",
                context={"events": qualified_events},
                parameters={
                    "service_category": "booth_builder",
                    "location": request.region
                }
            )
            vendor_output = vendor_discovery_agent.execute(vendor_input)
            _store_agent_output(run, "vendor_discovery", vendor_output)
            vendors = vendor_output.findings.get("vendors", [])
        elif qualified_events:
            # Traditional vendor discovery for events
            vendor_input = AgentInput(
                query=request.query,
                context={"events": qualified_events}
            )
            vendor_output = vendor_discovery_agent.execute(vendor_input)
            vendors = vendor_output.findings.get("vendors", [])
        
        run["vendors_count"] = len(vendors)
        
        # Save vendors to database
        for vendor in vendors:
            if db:
                db.save_vendor(vendor)
        await asyncio.sleep(0.1)  # yield for SSE polling
        
        # Step 5: Website Scraping (for events)
        run["current_agent"] = "event_website_scraper"
        run["progress_percent"] = 65
        
        if qualified_events:
            scraper_agent = EventWebsiteScraperAgent()
            scraper_input = AgentInput(
                query=request.query,
                context={"events": qualified_events}
            )
            scraper_output = scraper_agent.execute(scraper_input)
            _store_agent_output(run, "event_website_scraper", scraper_output)
            scraped_events = scraper_output.findings.get("events", qualified_events)
            qualified_events = scraped_events  # Feed enriched events forward
        await asyncio.sleep(0.1)  # yield for SSE polling
        
        # Step 6: Event Intelligence
        run["current_agent"] = "event_intelligence"
        run["progress_percent"] = 75
        
        if qualified_events:
            intelligence_agent = EventIntelligenceAgent()
            intel_input = AgentInput(
                query=request.query,
                context={"events": qualified_events}
            )
            intel_output = intelligence_agent.execute(intel_input)
            _store_agent_output(run, "event_intelligence", intel_output)
            intel_events = intel_output.findings.get("events", qualified_events)
            qualified_events = intel_events
        await asyncio.sleep(0.1)

        # Step 7: Event Prioritization
        run["current_agent"] = "event_prioritization"
        run["progress_percent"] = 85

        if qualified_events:
            prioritization_agent = EventPrioritizationAgent()
            priority_input = AgentInput(
                query=request.query,
                context={"events": qualified_events}
            )
            priority_output = prioritization_agent.execute(priority_input)
            _store_agent_output(run, "event_prioritization", priority_output)
            prioritized_events = priority_output.findings.get("events", qualified_events)
            qualified_events = prioritized_events
        await asyncio.sleep(0.1)  # yield for SSE polling
        
        # Step 8: Outreach Email
        run["current_agent"] = "outreach_email"
        run["progress_percent"] = 95
        
        if vendors or qualified_events:
            email_agent = OutreachEmailAgent()
            email_input = AgentInput(
                query=request.query,
                context={
                    "events": qualified_events[:5] if qualified_events else [],
                    "vendors": vendors[:5] if vendors else []
                }
            )
            email_output = email_agent.execute(email_input)
            _store_agent_output(run, "outreach_email", email_output)
        await asyncio.sleep(0.1)  # yield for SSE polling
        
        # Final checkpoint: review all results before completing
        if request.enable_checkpoints:
            checkpoint = checkpoint_mgr.create_checkpoint(
                pipeline_id=pipeline_id,
                checkpoint_type=CheckpointType.EVENT_REVIEW,
                name="Review Final Pipeline Results",
                data={
                    "events": qualified_events if qualified_events else events,
                    "vendors": vendors,
                }
            )
            checkpoint_id = checkpoint.id

            if request.auto_approve:
                checkpoint_mgr.approve_checkpoint(checkpoint_id, "auto", "Auto-approved")
            else:
                run["status"] = "waiting_for_approval"
                run["checkpoint_id"] = checkpoint_id
                run["progress_percent"] = 98
                approved = checkpoint_mgr.wait_for_approval(checkpoint_id, poll_interval=5)
                if not approved:
                    run["status"] = "rejected"
                    return
                run["status"] = "running"

        run["progress_percent"] = 100
        run["status"] = "completed"
        run["completed_at"] = datetime.utcnow().isoformat()

        logger.info(f"Pipeline completed: {pipeline_id}")
    
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        run["status"] = "failed"
        run["errors"].append(str(e))
        run["completed_at"] = datetime.utcnow().isoformat()


def _store_agent_output(run: dict, agent_name: str, output: any):
    # Store per-agent outputs into the active run state.
    if "agent_outputs" not in run:
        run["agent_outputs"] = {}
    if "completed_agents" not in run:
        run["completed_agents"] = []
    run["agent_outputs"][agent_name] = {
        "findings": output.findings if hasattr(output, 'findings') else {},
        "metadata": output.metadata if hasattr(output, 'metadata') else {},
        "status": output.status if hasattr(output, 'status') else 'success'
    }
    if agent_name not in run["completed_agents"]:
        run["completed_agents"].append(agent_name)

@app.get("/pipeline/{pipeline_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(pipeline_id: str):
    """Get pipeline status."""
    run = active_runs.get(pipeline_id)
    
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return PipelineStatusResponse(**run)


@app.get("/pipeline/runs", response_model=List[PipelineStatusResponse])
async def list_pipeline_runs(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """List recent pipeline runs."""
    runs = list(active_runs.values())
    
    if status:
        runs = [r for r in runs if r.get("status") == status]
    
    # Sort by started_at desc
    runs.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    
    return [PipelineStatusResponse(**r) for r in runs[:limit]]


@app.post("/pipeline/{pipeline_id}/cancel")
async def cancel_pipeline(pipeline_id: str):
    """Cancel a running pipeline."""
    run = active_runs.get(pipeline_id)
    
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    if run["status"] not in ["running", "waiting_for_approval"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel pipeline with status: {run['status']}")
    
    run["status"] = "cancelled"
    run["completed_at"] = datetime.utcnow().isoformat()
    
    return {"message": "Pipeline cancelled", "pipeline_id": pipeline_id}


# ==================== Checkpoint Endpoints ====================

@app.get("/checkpoints", response_model=List[CheckpointResponse])
async def list_checkpoints(
    pipeline_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """List checkpoints with optional filtering."""
    if not checkpoint_mgr:
        raise HTTPException(status_code=503, detail="Checkpoint manager not available")
    
    checkpoints = []
    
    # Load all checkpoints from disk
    for checkpoint_file in checkpoint_mgr.checkpoint_dir.glob("*.json"):
        try:
            checkpoint = checkpoint_mgr.load_checkpoint(checkpoint_file.stem)
            if checkpoint:
                if pipeline_id and checkpoint.pipeline_id != pipeline_id:
                    continue
                if status and checkpoint.status.value != status:
                    continue
                checkpoints.append(checkpoint)
        except Exception as e:
            logger.warning(f"Failed to load checkpoint {checkpoint_file}: {e}")
    
    # Sort by created_at desc
    checkpoints.sort(key=lambda x: x.created_at, reverse=True)
    
    return [CheckpointResponse(**c.to_dict()) for c in checkpoints]


@app.get("/checkpoints/{checkpoint_id}", response_model=CheckpointResponse)
async def get_checkpoint(checkpoint_id: str):
    """Get a single checkpoint."""
    if not checkpoint_mgr:
        raise HTTPException(status_code=503, detail="Checkpoint manager not available")
    
    checkpoint = checkpoint_mgr.load_checkpoint(checkpoint_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    
    return CheckpointResponse(**checkpoint.to_dict())


@app.post("/checkpoints/{checkpoint_id}/approve", response_model=CheckpointResponse)
async def approve_checkpoint(checkpoint_id: str, request: CheckpointReviewRequest):
    """Approve a checkpoint."""
    if not checkpoint_mgr:
        raise HTTPException(status_code=503, detail="Checkpoint manager not available")
    
    checkpoint = checkpoint_mgr.approve_checkpoint(
        checkpoint_id,
        reviewed_by=request.reviewed_by,
        notes=request.review_notes or ""
    )
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    
    return CheckpointResponse(**checkpoint.to_dict())


@app.post("/checkpoints/{checkpoint_id}/reject", response_model=CheckpointResponse)
async def reject_checkpoint(checkpoint_id: str, request: CheckpointReviewRequest):
    """Reject a checkpoint."""
    if not checkpoint_mgr:
        raise HTTPException(status_code=503, detail="Checkpoint manager not available")
    
    checkpoint = checkpoint_mgr.reject_checkpoint(
        checkpoint_id,
        reviewed_by=request.reviewed_by,
        notes=request.review_notes or ""
    )
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    
    return CheckpointResponse(**checkpoint.to_dict())


@app.get("/checkpoints/{checkpoint_id}/summary")
async def get_checkpoint_summary(checkpoint_id: str):
    """Get human-readable summary for a checkpoint."""
    if not checkpoint_mgr:
        raise HTTPException(status_code=503, detail="Checkpoint manager not available")
    
    summary = checkpoint_mgr.generate_review_summary(checkpoint_id)
    
    return {"checkpoint_id": checkpoint_id, "summary": summary}


# ==================== Report Endpoints ====================

@app.post("/reports/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """Generate a report."""
    from reports.generator import ReportGenerator
    
    generator = ReportGenerator()
    report_id = str(uuid.uuid4())
    
    if request.report_type == "events":
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        events = db.get_events()
        if request.event_ids:
            events = [e for e in events if e['id'] in request.event_ids]
        
        content = generator.generate_event_report(events)
    
    elif request.report_type == "vendors":
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        vendors = db.get_vendors()
        content = generator.generate_vendor_report(vendors)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {request.report_type}")
    
    return ReportResponse(
        report_id=report_id,
        report_type=request.report_type,
        content=content,
        generated_at=datetime.utcnow().isoformat()
    )


@app.get("/reports/{report_id}/download")
async def download_report(report_id: str, format: str = "markdown"):
    """Download a generated report."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


# ==================== Real-time Updates (SSE) ====================

@app.get("/stream/pipeline/{pipeline_id}")
async def stream_pipeline_updates(pipeline_id: str):
    """Stream real-time pipeline updates via Server-Sent Events."""
    async def event_generator():
        last_status = None
        last_progress = -1
        last_completed_agents: List[str] = []
        
        while True:
            run = active_runs.get(pipeline_id)
            
            if not run:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Pipeline not found'})}\n\n"
                break
            
            current_status = run.get("status")
            current_progress = run.get("progress_percent", 0)
            
            # Emit updates on status/progress changes
            if current_status != last_status or current_progress != last_progress:
                last_status = current_status
                last_progress = current_progress
                
                data = {
                    "type": "update",
                    "pipeline_id": pipeline_id,
                    "status": current_status,
                    "progress": current_progress,
                    "current_agent": run.get("current_agent"),
                    "events_count": run.get("events_count", 0),
                    "vendors_count": run.get("vendors_count", 0),
                }
                yield f"data: {json.dumps(data, default=str)}\n\n"
            
            # Detect newly completed agents and stream their outputs
            completed_agents = run.get("completed_agents", [])
            newly_completed = [a for a in completed_agents if a not in last_completed_agents]
            for agent in newly_completed:
                yield f"data: {json.dumps({'type': 'agent_complete', 'pipeline_id': pipeline_id, 'completed_agent': agent, 'agent_output': run.get('agent_outputs', {}).get(agent, {})}, default=str)}\n\n"
            last_completed_agents = list(completed_agents)
            
            # If pipeline finished, emit final aggregated outputs and exit
            if current_status in ["completed", "failed", "cancelled"]:
                final_payload = {
                    'type': 'complete',
                    'status': current_status,
                    'agent_outputs': run.get('agent_outputs', {})
                }
                yield f"data: {json.dumps(final_payload, default=str)}\n\n"
                break
            
            await asyncio.sleep(1)  # Poll every 1s for smoother updates
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ==================== Logs API ====================

class LogsResponse(BaseModel):
    """Response model for logs endpoint."""
    lines: List[str]
    total_lines: int
    filename: str


@app.get("/logs", response_model=LogsResponse)
async def get_logs(
    lines: int = Query(100, ge=1, le=1000),
    filter: Optional[str] = Query(None, description="Filter lines by keyword")
):
    """Get recent application logs.
    
    Args:
        lines: Number of lines to return (1-1000)
        filter: Optional keyword to filter lines
    
    Returns:
        Recent log lines
    """
    log_file = "/tmp/fastapi.log"
    
    try:
        # Read last N lines from log file
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
        
        # Get last N lines
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # Apply filter if provided
        if filter:
            recent_lines = [line for line in recent_lines if filter.lower() in line.lower()]
        
        # Strip newlines and return
        return LogsResponse(
            lines=[line.rstrip('\n') for line in recent_lines],
            total_lines=len(all_lines),
            filename=log_file
        )
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Log file not found: {log_file}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")


@app.get("/logs/search")
async def search_logs(
    query: str = Query(..., description="Search query"),
    context: int = Query(3, ge=0, le=10, description="Lines of context around matches")
):
    """Search logs with context.
    
    Args:
        query: Search term
        context: Number of lines before/after match
    
    Returns:
        Matching log lines with context
    """
    log_file = "/tmp/fastapi.log"
    
    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
        
        matches = []
        for i, line in enumerate(all_lines):
            if query.lower() in line.lower():
                # Get context lines
                start = max(0, i - context)
                end = min(len(all_lines), i + context + 1)
                context_lines = all_lines[start:end]
                
                matches.append({
                    "line_number": i + 1,
                    "content": line.rstrip('\n'),
                    "context": [l.rstrip('\n') for l in context_lines],
                    "context_start": start + 1
                })
        
        return {
            "query": query,
            "matches": matches,
            "total_matches": len(matches)
        }
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Log file not found: {log_file}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching logs: {str(e)}")


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
