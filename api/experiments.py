"""Experiment API endpoints for dashboard and metrics."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import json
import csv
import io

from utils.experiment_models import ExperimentDatabase, Experiment, ExperimentVariant, ExperimentStatus

router = APIRouter(prefix="/experiments", tags=["experiments"])

# Initialize database
db = ExperimentDatabase()


# Pydantic models for API
class CreateExperimentRequest(BaseModel):
    name: str
    description: str
    agent_name: str
    config: Dict[str, Any]


class CreateVariantRequest(BaseModel):
    name: str
    model_id: str
    provider: str
    weight: int
    config: Dict[str, Any]


class ExperimentSummary(BaseModel):
    id: str
    name: str
    description: str
    agent_name: str
    status: str
    created_at: str
    updated_at: str
    variant_count: int
    execution_count: int


class VariantMetrics(BaseModel):
    variant_id: str
    model_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_latency_ms: float
    min_latency_ms: int
    max_latency_ms: int
    p50_latency_ms: int
    p95_latency_ms: int
    p99_latency_ms: int
    total_cost_usd: float
    avg_cost_per_execution: float
    avg_quality_score: float
    min_quality_score: float
    max_quality_score: float
    success_rate: float


class ExperimentDetail(BaseModel):
    id: str
    name: str
    description: str
    agent_name: str
    status: str
    created_at: str
    variants: List[Dict[str, Any]]
    metrics: List[VariantMetrics]
    winning_variant: Optional[str]
    confidence_level: float


class TimeSeriesPoint(BaseModel):
    timestamp: str
    variant_id: str
    model_id: str
    quality_score: float
    latency_ms: int
    cost_usd: float
    success: bool


@router.post("/", response_model=ExperimentSummary)
async def create_experiment(request: CreateExperimentRequest):
    """Create new experiment."""
    import uuid
    
    exp_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    experiment = Experiment(
        id=exp_id,
        name=request.name,
        description=request.description,
        agent_name=request.agent_name,
        status=ExperimentStatus.DRAFT,
        created_at=now,
        updated_at=now,
        config=request.config
    )
    
    db.create_experiment(experiment)
    
    return ExperimentSummary(
        id=exp_id,
        name=request.name,
        description=request.description,
        agent_name=request.agent_name,
        status="draft",
        created_at=now,
        updated_at=now,
        variant_count=0,
        execution_count=0
    )


@router.post("/{experiment_id}/variants")
async def add_variant(experiment_id: str, request: CreateVariantRequest):
    """Add variant to experiment."""
    import uuid
    
    variant_id = str(uuid.uuid4())[:8]
    
    variant = ExperimentVariant(
        id=variant_id,
        experiment_id=experiment_id,
        name=request.name,
        model_id=request.model_id,
        provider=request.provider,
        weight=request.weight,
        config=request.config,
        is_active=True
    )
    
    db.add_variant(variant)
    
    return {"variant_id": variant_id, "message": "Variant added successfully"}


@router.get("/", response_model=List[ExperimentSummary])
async def list_experiments(
    agent_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """List all experiments with summary stats."""
    experiments = db.list_experiments(agent_name)
    
    results = []
    for exp in experiments:
        if status and exp.get('status') != status:
            continue
            
        results.append(ExperimentSummary(
            id=exp['id'],
            name=exp['name'],
            description=exp.get('description', ''),
            agent_name=exp['agent_name'],
            status=exp['status'],
            created_at=exp['created_at'],
            updated_at=exp['updated_at'],
            variant_count=exp.get('variant_count', 0),
            execution_count=exp.get('execution_count', 0)
        ))
    
    return results


@router.get("/{experiment_id}", response_model=ExperimentDetail)
async def get_experiment(experiment_id: str):
    """Get detailed experiment data with metrics."""
    summary = db.get_experiment_summary(experiment_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    exp = summary['experiment']
    metrics_data = summary['metrics']
    
    # Determine winner based on quality score and success rate
    winning_variant = None
    confidence_level = 0.0
    
    if len(metrics_data) >= 2:
        # Simple winner determination: highest (quality_score * success_rate)
        best_score = 0
        for m in metrics_data:
            combined_score = m['avg_quality'] * m['success_rate']
            if combined_score > best_score and m['total_executions'] >= 30:
                best_score = combined_score
                winning_variant = m['variant_id']
                confidence_level = min(m['total_executions'] / 100, 0.99)
    
    metrics = []
    for m in metrics_data:
        metrics.append(VariantMetrics(
            variant_id=m['variant_id'],
            model_id=m['model_id'],
            total_executions=m['total_executions'],
            successful_executions=m['successful_executions'],
            failed_executions=m['failed_executions'],
            avg_latency_ms=m['avg_latency'],
            min_latency_ms=m['min_latency'],
            max_latency_ms=m['max_latency'],
            p50_latency_ms=m.get('p50_latency_ms', 0),
            p95_latency_ms=m.get('p95_latency_ms', 0),
            p99_latency_ms=m.get('p99_latency_ms', 0),
            total_cost_usd=m['total_cost'],
            avg_cost_per_execution=m['avg_cost'],
            avg_quality_score=m['avg_quality'],
            min_quality_score=m['min_quality'],
            max_quality_score=m['max_quality'],
            success_rate=m['success_rate']
        ))
    
    return ExperimentDetail(
        id=exp['id'],
        name=exp['name'],
        description=exp.get('description', ''),
        agent_name=exp['agent_name'],
        status=exp['status'],
        created_at=exp['created_at'],
        variants=summary['variants'],
        metrics=metrics,
        winning_variant=winning_variant,
        confidence_level=confidence_level
    )


@router.get("/{experiment_id}/timeseries")
async def get_timeseries(
    experiment_id: str,
    variant_id: Optional[str] = Query(None),
    metric: str = Query("quality_score"),
    limit: int = Query(100)
):
    """Get time-series data for charting."""
    import sqlite3
    
    conn = db._get_connection()
    
    if variant_id:
        cursor = conn.execute(
            """SELECT started_at, variant_id, model_id, quality_score, 
                      latency_ms, cost_usd, success
               FROM experiment_executions
               WHERE experiment_id = ? AND variant_id = ?
               ORDER BY started_at DESC
               LIMIT ?""",
            (experiment_id, variant_id, limit)
        )
    else:
        cursor = conn.execute(
            """SELECT started_at, variant_id, model_id, quality_score, 
                      latency_ms, cost_usd, success
               FROM experiment_executions
               WHERE experiment_id = ?
               ORDER BY started_at DESC
               LIMIT ?""",
            (experiment_id, limit)
        )
    
    points = []
    for row in cursor.fetchall():
        points.append(TimeSeriesPoint(
            timestamp=row[0],
            variant_id=row[1],
            model_id=row[2],
            quality_score=row[3],
            latency_ms=row[4],
            cost_usd=row[5],
            success=bool(row[6])
        ))
    
    return points


@router.get("/{experiment_id}/comparison")
async def get_variant_comparison(experiment_id: str):
    """Get side-by-side variant comparison."""
    summary = db.get_experiment_summary(experiment_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    metrics = summary['metrics']
    
    comparison = {
        "experiment_id": experiment_id,
        "experiment_name": summary['experiment']['name'],
        "variants": [],
        "winner": None,
        "recommendation": ""
    }
    
    best_variant = None
    best_score = 0
    
    for m in metrics:
        variant_data = {
            "variant_id": m['variant_id'],
            "model_id": m['model_id'],
            "total_executions": m['total_executions'],
            "success_rate": round(m['success_rate'] * 100, 1),
            "avg_quality": round(m['avg_quality'], 3),
            "avg_latency_ms": round(m['avg_latency'], 1),
            "avg_cost_usd": round(m['avg_cost'], 4),
            "total_cost_usd": round(m['total_cost'], 4),
            "cost_per_quality_point": round(m['avg_cost'] / max(m['avg_quality'], 0.01), 4),
            "p95_latency_ms": m.get('p95_latency_ms', 0)
        }
        
        comparison['variants'].append(variant_data)
        
        # Score = quality * success_rate / cost (higher is better)
        score = (m['avg_quality'] * m['success_rate']) / max(m['avg_cost'], 0.0001)
        if score > best_score and m['total_executions'] >= 30:
            best_score = score
            best_variant = m['variant_id']
    
    comparison['winner'] = best_variant
    
    if best_variant:
        comparison['recommendation'] = f"Variant {best_variant} shows best overall performance (quality * success_rate / cost)"
    else:
        comparison['recommendation'] = "Need more samples (>30 per variant) to determine winner"
    
    return comparison


@router.get("/{experiment_id}/export")
async def export_experiment(
    experiment_id: str,
    format: str = Query("json", enum=["json", "csv"])
):
    """Export experiment data."""
    summary = db.get_experiment_summary(experiment_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    if format == "json":
        return summary
    
    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            "experiment_id", "variant_id", "model_id", "started_at",
            "latency_ms", "cost_usd", "quality_score", "success"
        ])
        
        # Get all executions
        conn = db._get_connection()
        cursor = conn.execute(
            """SELECT experiment_id, variant_id, model_id, started_at,
                      latency_ms, cost_usd, quality_score, success
               FROM experiment_executions
               WHERE experiment_id = ?
               ORDER BY started_at""",
            (experiment_id,)
        )
        
        for row in cursor.fetchall():
            writer.writerow(row)
        
        return {
            "content": output.getvalue(),
            "content_type": "text/csv",
            "filename": f"experiment_{experiment_id}.csv"
        }


@router.post("/{experiment_id}/start")
async def start_experiment(experiment_id: str):
    """Start experiment (change status to running)."""
    conn = db._get_connection()
    conn.execute(
        "UPDATE experiments SET status = ?, updated_at = ? WHERE id = ?",
        (ExperimentStatus.RUNNING.value, datetime.utcnow().isoformat(), experiment_id)
    )
    conn.commit()
    
    return {"message": "Experiment started", "status": "running"}


@router.post("/{experiment_id}/pause")
async def pause_experiment(experiment_id: str):
    """Pause experiment."""
    conn = db._get_connection()
    conn.execute(
        "UPDATE experiments SET status = ?, updated_at = ? WHERE id = ?",
        (ExperimentStatus.PAUSED.value, datetime.utcnow().isoformat(), experiment_id)
    )
    conn.commit()
    
    return {"message": "Experiment paused", "status": "paused"}


@router.post("/{experiment_id}/conclude")
async def conclude_experiment(experiment_id: str):
    """Conclude experiment and mark winner."""
    # Get winning variant
    comparison = await get_variant_comparison(experiment_id)
    winner = comparison.get('winner')
    
    conn = db._get_connection()
    conn.execute(
        "UPDATE experiments SET status = ?, updated_at = ? WHERE id = ?",
        (ExperimentStatus.COMPLETED.value, datetime.utcnow().isoformat(), experiment_id)
    )
    conn.commit()
    
    return {
        "message": "Experiment concluded",
        "winner": winner,
        "recommendation": comparison.get('recommendation'),
        "status": "completed"
    }


@router.get("/agents/{agent_name}/recommendation")
async def get_agent_model_recommendation(agent_name: str):
    """Get recommended model for an agent based on completed experiments."""
    experiments = db.list_experiments(agent_name)
    
    completed = [e for e in experiments if e.get('status') == 'completed']
    
    if not completed:
        return {
            "agent_name": agent_name,
            "recommendation": "No completed experiments found",
            "suggested_model": None,
            "confidence": 0
        }
    
    # Get latest completed experiment
    latest = completed[0]
    summary = db.get_experiment_summary(latest['id'])
    
    if not summary or not summary['metrics']:
        return {
            "agent_name": agent_name,
            "recommendation": "No metrics available",
            "suggested_model": None,
            "confidence": 0
        }
    
    # Find best model
    best_model = None
    best_score = 0
    
    for m in summary['metrics']:
        score = m['avg_quality'] * m['success_rate']
        if score > best_score:
            best_score = score
            best_model = m['model_id']
    
    return {
        "agent_name": agent_name,
        "recommendation": f"Use {best_model} based on experiment {latest['id']}",
        "suggested_model": best_model,
        "experiment_id": latest['id'],
        "quality_score": best_score,
        "confidence": min(summary['metrics'][0]['total_executions'] / 100, 0.99)
    }
