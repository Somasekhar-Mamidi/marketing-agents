# Model Experimentation & Performance Scoring Framework

## Executive Summary

A systematic approach to test, measure, and optimize model-agent pairings through:
- **A/B Testing**: Run same agent with different models side-by-side
- **Performance Metrics**: Track latency, cost, quality, success rate
- **Scoring System**: Automated evaluation of agent outputs
- **Dashboard**: Visual comparison of model performance
- **Convergence**: Data-driven model selection

---

## Phase 1: Experimentation Infrastructure

### 1.1 Model Experiment Configuration

```yaml
# config/model_experiments.yaml
experiments:
  # Experiment definitions
  intent_understanding_models:
    name: "Intent Understanding - Model Comparison"
    description: "Test which model best extracts intent from queries"
    agent: "intent_understanding"
    enabled: true
    
    # Models to test
    variants:
      - name: "claude_opus"
        model: "claude-opus-4-6"
        provider: grid_ai
        weight: 33  # Traffic allocation %
        
      - name: "claude_sonnet"
        model: "claude-sonnet-4-6"
        provider: grid_ai
        weight: 33
        
      - name: "gemini_pro"
        model: "gemini-3.1-pro"
        provider: grid_ai
        weight: 34
    
    # Evaluation criteria
    evaluation:
      metrics:
        - json_validity        # Is output valid JSON?
        - intent_accuracy      # Did it capture correct industry/region?
        - confidence_score     # How confident is the model?
        - latency_ms          # Response time
        - cost_usd            # Token cost
      
      success_threshold: 0.8  # Min score to count as success
      min_samples: 50        # Min runs before conclusion
      
  event_discovery_models:
    name: "Event Discovery - Search vs Non-Search"
    description: "Compare Gemini with search grounding vs Claude with manual search"
    agent: "event_discovery"
    enabled: true
    
    variants:
      - name: "gemini_flash_search"
        model: "gemini-3-flash-preview"
        provider: grid_ai
        use_search_grounding: true
        weight: 50
        
      - name: "claude_sonnet_manual"
        model: "claude-sonnet-4-5"
        provider: grid_ai
        use_search_grounding: false  # Manual search feed
        weight: 50
    
    evaluation:
      metrics:
        - events_found_count       # How many events discovered?
        - event_relevance_score    # Are events relevant to query?
        - unique_events_ratio      # % non-duplicate events
        - search_coverage          # Did it find events across regions?
        - latency_ms
        - cost_usd
        - search_api_calls         # Efficiency metric
      
      success_threshold: 0.75
      min_samples: 100

  event_intelligence_models:
    name: "Event Intelligence - Strategic Analysis Quality"
    description: "Test which model produces best strategic insights"
    agent: "event_intelligence"
    enabled: true
    
    variants:
      - name: "gemini_pro_search"
        model: "gemini-3.1-pro"
        provider: grid_ai
        use_search_grounding: true
        weight: 40
        
      - name: "kimi_large_context"
        model: "kimi-latest"
        provider: grid_ai
        use_search_grounding: false
        weight: 30
        
      - name: "claude_opus"
        model: "claude-opus-4-6"
        provider: grid_ai
        use_search_grounding: false
        weight: 30
    
    evaluation:
      metrics:
        - insight_depth            # Quality of strategic insights
        - sponsor_accuracy         # Correct past sponsors?
        - audience_match_score     # Target audience accuracy
        - roi_prediction_quality   # ROI estimates reasonable?
        - completeness_score       # All fields filled?
        - latency_ms
        - cost_usd
      
      success_threshold: 0.8
      min_samples: 50

# Global experiment settings
settings:
  auto_promote_winner: false    # Auto-switch to winning model?
  confidence_threshold: 0.95     # Statistical confidence needed
  max_experiment_duration: "7d"  # Max time to run
  sample_size_per_variant: 100  # Target samples before evaluation
```

---

## Phase 2: Performance Tracking System

### 2.1 Enhanced Metrics Collector

```python
# utils/model_experiment_tracker.py

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from database.models import get_database

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to track."""
    LATENCY_MS = "latency_ms"
    COST_USD = "cost_usd"
    TOKEN_COUNT = "token_count"
    SUCCESS_RATE = "success_rate"
    QUALITY_SCORE = "quality_score"
    JSON_VALIDITY = "json_validity"


@dataclass
class ModelPerformanceRecord:
    """Single execution performance record."""
    # Identification
    experiment_id: str
    agent_name: str
    variant_name: str
    model_id: str
    provider: str
    
    # Timing
    timestamp: str
    latency_ms: int
    
    # Cost
    cost_usd: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
    # Quality
    success: bool
    error_message: Optional[str]
    quality_score: float  # 0.0 - 1.0
    
    # Agent-specific metrics
    metrics: Dict[str, Any]  # Flexible agent-specific metrics
    
    # Input/Output (for debugging)
    input_query: str
    output_sample: str  # Truncated output
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ModelExperimentTracker:
    """Tracks model performance for A/B testing."""
    
    def __init__(self):
        self.db = get_database()
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create necessary tables if not exist."""
        # SQLite schema for experiment tracking
        schema = """
        CREATE TABLE IF NOT EXISTS model_experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id TEXT NOT NULL,
            experiment_name TEXT,
            agent_name TEXT NOT NULL,
            variant_name TEXT NOT NULL,
            model_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            latency_ms INTEGER,
            cost_usd REAL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            success BOOLEAN,
            error_message TEXT,
            quality_score REAL,
            metrics_json TEXT,
            input_query TEXT,
            output_sample TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_experiment_id 
            ON model_experiments(experiment_id);
        CREATE INDEX IF NOT EXISTS idx_agent_model 
            ON model_experiments(agent_name, model_id);
        CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON model_experiments(timestamp);
        """
        
        conn = self.db._get_connection()
        conn.executescript(schema)
        conn.commit()
    
    def record_execution(
        self,
        experiment_id: str,
        agent_name: str,
        variant_name: str,
        model_id: str,
        provider: str,
        latency_ms: int,
        cost_usd: float,
        tokens: Dict[str, int],
        success: bool,
        quality_score: float,
        metrics: Dict[str, Any],
        input_query: str,
        output: str,
        error_message: Optional[str] = None
    ):
        """Record a single execution."""
        record = ModelPerformanceRecord(
            experiment_id=experiment_id,
            agent_name=agent_name,
            variant_name=variant_name,
            model_id=model_id,
            provider=provider,
            timestamp=datetime.utcnow().isoformat(),
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            input_tokens=tokens.get('input', 0),
            output_tokens=tokens.get('output', 0),
            total_tokens=tokens.get('total', 0),
            success=success,
            error_message=error_message,
            quality_score=quality_score,
            metrics=metrics,
            input_query=input_query[:500],  # Truncate
            output_sample=output[:1000] if output else ""  # Truncate
        )
        
        conn = self.db._get_connection()
        conn.execute("""
            INSERT INTO model_experiments 
            (experiment_id, agent_name, variant_name, model_id, provider,
             timestamp, latency_ms, cost_usd, input_tokens, output_tokens, total_tokens,
             success, error_message, quality_score, metrics_json, input_query, output_sample)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.experiment_id,
            record.agent_name,
            record.variant_name,
            record.model_id,
            record.provider,
            record.timestamp,
            record.latency_ms,
            record.cost_usd,
            record.input_tokens,
            record.output_tokens,
            record.total_tokens,
            record.success,
            record.error_message,
            record.quality_score,
            json.dumps(record.metrics),
            record.input_query,
            record.output_sample
        ))
        conn.commit()
        
        logger.info(f"Recorded execution: {agent_name}/{variant_name} - "
                   f"Score: {quality_score:.2f}, Latency: {latency_ms}ms")
    
    def get_experiment_stats(
        self,
        experiment_id: str,
        min_samples: int = 30
    ) -> Dict[str, Any]:
        """Get statistical comparison of experiment variants."""
        conn = self.db._get_connection()
        
        # Get all variants for this experiment
        cursor = conn.execute("""
            SELECT variant_name, model_id,
                   COUNT(*) as sample_size,
                   AVG(latency_ms) as avg_latency,
                   AVG(cost_usd) as avg_cost,
                   AVG(quality_score) as avg_quality,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
                   AVG(total_tokens) as avg_tokens
            FROM model_experiments
            WHERE experiment_id = ?
            GROUP BY variant_name, model_id
            HAVING COUNT(*) >= ?
        """, (experiment_id, min_samples))
        
        results = {}
        for row in cursor.fetchall():
            variant_name = row[0]
            results[variant_name] = {
                "model_id": row[1],
                "sample_size": row[2],
                "avg_latency_ms": round(row[3], 2),
                "avg_cost_usd": round(row[4], 4),
                "avg_quality_score": round(row[5], 3),
                "success_rate": round(row[6], 3),
                "avg_tokens": round(row[7], 1)
            }
        
        return results
    
    def get_winning_variant(
        self,
        experiment_id: str,
        min_samples: int = 50,
        confidence_threshold: float = 0.95
    ) -> Optional[str]:
        """Determine winning variant using statistical test."""
        import statistics
        
        conn = self.db._get_connection()
        
        # Get quality scores per variant
        cursor = conn.execute("""
            SELECT variant_name, quality_score
            FROM model_experiments
            WHERE experiment_id = ? AND success = TRUE
        """, (experiment_id,))
        
        variant_scores = {}
        for row in cursor.fetchall():
            variant = row[0]
            score = row[1]
            if variant not in variant_scores:
                variant_scores[variant] = []
            variant_scores[variant].append(score)
        
        # Check if we have enough samples
        for variant, scores in variant_scores.items():
            if len(scores) < min_samples:
                logger.info(f"Variant {variant} has only {len(scores)} samples, "
                           f"need {min_samples}")
                return None
        
        if len(variant_scores) < 2:
            return None
        
        # Simple comparison: highest mean with statistical significance
        # In production, use proper t-test or Bayesian analysis
        means = {v: statistics.mean(s) for v, s in variant_scores.items()}
        winner = max(means, key=means.get)
        
        # Check if winner is significantly better than others
        winner_scores = variant_scores[winner]
        winner_mean = means[winner]
        
        for variant, scores in variant_scores.items():
            if variant == winner:
                continue
            
            # Simple confidence check (mean + 2*std)
            other_mean = means[variant]
            other_std = statistics.stdev(scores) if len(scores) > 1 else 0
            
            if winner_mean < (other_mean + 2 * other_std):
                logger.info(f"Winner {winner} not significantly better than {variant}")
                return None
        
        return winner
    
    def export_experiment_data(
        self,
        experiment_id: str,
        format: str = "json"
    ) -> str:
        """Export experiment data for analysis."""
        conn = self.db._get_connection()
        
        cursor = conn.execute("""
            SELECT * FROM model_experiments
            WHERE experiment_id = ?
        """, (experiment_id,))
        
        rows = cursor.fetchall()
        
        if format == "json":
            data = []
            for row in rows:
                data.append({
                    "id": row[0],
                    "experiment_id": row[1],
                    "agent_name": row[3],
                    "variant_name": row[4],
                    "model_id": row[5],
                    "timestamp": row[7],
                    "latency_ms": row[8],
                    "cost_usd": row[9],
                    "quality_score": row[15],
                    "success": row[13]
                })
            return json.dumps(data, indent=2)
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "id", "experiment_id", "agent_name", "variant_name", "model_id",
                "timestamp", "latency_ms", "cost_usd", "quality_score", "success"
            ])
            
            for row in rows:
                writer.writerow([
                    row[0], row[1], row[3], row[4], row[5],
                    row[7], row[8], row[9], row[15], row[13]
                ])
            
            return output.getvalue()
        
        return ""
```

---

## Phase 3: Automated Quality Scoring

### 3.1 Agent-Specific Evaluators

```python
# utils/agent_evaluators.py

import json
import logging
from typing import Dict, Any, List
from abc import ABC, abstractmethod

from utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class AgentEvaluator(ABC):
    """Base class for agent output evaluation."""
    
    @abstractmethod
    def evaluate(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        agent_output_raw: str
    ) -> Dict[str, float]:
        """Evaluate agent output quality.
        
        Returns:
            Dict of metric names to scores (0.0 - 1.0)
        """
        pass


class IntentUnderstandingEvaluator(AgentEvaluator):
    """Evaluates intent understanding agent."""
    
    def evaluate(self, input_data, output_data, agent_output_raw) -> Dict[str, float]:
        scores = {}
        
        # 1. JSON Validity
        try:
            if isinstance(output_data, dict) and "intent" in output_data:
                scores["json_validity"] = 1.0
            else:
                scores["json_validity"] = 0.0
        except:
            scores["json_validity"] = 0.0
        
        # 2. Required Fields Present
        intent = output_data.get("intent", {})
        required_fields = ["industry", "region", "themes"]
        present_fields = sum(1 for f in required_fields if intent.get(f))
        scores["completeness"] = present_fields / len(required_fields)
        
        # 3. Industry Recognition (is it a known industry?)
        industry = intent.get("industry", "").lower()
        known_industries = [
            "fintech", "payments", "ai", "technology", "healthcare",
            "retail", "travel", "education", "manufacturing"
        ]
        scores["industry_validity"] = 1.0 if industry in known_industries else 0.5
        
        # 4. Confidence Score Extraction
        confidence = intent.get("intent_confidence", 0)
        scores["confidence_normalized"] = min(confidence, 1.0)
        
        # 5. Query Relevance (did it capture the query essence?)
        query = input_data.get("query", "").lower()
        themes = intent.get("themes", [])
        theme_overlap = any(t.lower() in query for t in themes if isinstance(t, str))
        scores["query_relevance"] = 1.0 if theme_overlap else 0.5
        
        return scores


class EventDiscoveryEvaluator(AgentEvaluator):
    """Evaluates event discovery agent."""
    
    def evaluate(self, input_data, output_data, agent_output_raw) -> Dict[str, float]:
        scores = {}
        
        events = output_data.get("events", [])
        query = input_data.get("query", "").lower()
        
        # 1. Event Count (more is generally better, but with diminishing returns)
        event_count = len(events)
        if event_count >= 20:
            scores["event_count"] = 1.0
        elif event_count >= 10:
            scores["event_count"] = 0.8
        elif event_count >= 5:
            scores["event_count"] = 0.6
        else:
            scores["event_count"] = event_count / 10
        
        # 2. Required Fields (each event should have name, dates, location)
        if events:
            complete_events = 0
            for event in events:
                has_name = bool(event.get("event_name"))
                has_location = bool(event.get("city") or event.get("country"))
                has_dates = bool(event.get("start_date"))
                if has_name and has_location and has_dates:
                    complete_events += 1
            scores["data_completeness"] = complete_events / len(events)
        else:
            scores["data_completeness"] = 0.0
        
        # 3. Query Relevance (do events match the query?)
        if events and query:
            relevant_events = 0
            query_terms = set(query.split())
            for event in event_data in events:
                event_text = f"{event.get('event_name', '')} {event.get('theme', '')}".lower()
                if any(term in event_text for term in query_terms):
                    relevant_events += 1
            scores["relevance"] = relevant_events / len(events)
        else:
            scores["relevance"] = 0.0
        
        # 4. Diversity (events across different regions/dates)
        if events:
            countries = set(e.get("country") for e in events if e.get("country"))
            scores["diversity"] = min(len(countries) / 3, 1.0)  # 3+ countries = full score
        else:
            scores["diversity"] = 0.0
        
        return scores


class EventIntelligenceEvaluator(AgentEvaluator):
    """Evaluates event intelligence agent using LLM-as-judge."""
    
    def __init__(self):
        self.llm = get_llm_client()
    
    def evaluate(self, input_data, output_data, agent_output_raw) -> Dict[str, float]:
        scores = {}
        
        events = output_data.get("events", [])
        if not events:
            return {k: 0.0 for k in [
                "insight_depth", "completeness", "actionability", "overall"
            ]}
        
        # Sample one event for detailed evaluation
        sample_event = events[0]
        
        # Use LLM to evaluate quality
        evaluation_prompt = f"""Rate the quality of this event intelligence analysis on a scale of 0-100:

Event: {sample_event.get('event_name', 'Unknown')}
Analysis:
- Attendee Roles: {sample_event.get('attendee_roles', 'N/A')}
- Companies Attending: {sample_event.get('companies_attending', 'N/A')}
- Strategic Value: {sample_event.get('strategic_value', 'N/A')}
- Potential ROI: {sample_event.get('potential_roi', 'N/A')}
- Ideal Sponsorship: {sample_event.get('ideal_sponsorship_format', 'N/A')}

Rate on these dimensions (0-100):
1. Insight Depth: Are the insights specific and actionable?
2. Completeness: Are all key fields populated with useful info?
3. Actionability: Would this help make a sponsorship decision?
4. Specificity: Is it specific to this event or generic fluff?

Return JSON: {{"insight_depth": X, "completeness": Y, "actionability": Z, "specificity": W, "overall": AVG}}"""
        
        try:
            response = self.llm.complete(
                prompt=evaluation_prompt,
                system_message="You are an expert evaluator of market intelligence. Be objective and critical.",
                response_format={"type": "json_object"}
            )
            
            if response.success:
                llm_scores = json.loads(response.content)
                # Normalize to 0-1
                scores = {k: min(v / 100, 1.0) for k, v in llm_scores.items()}
            else:
                scores = {k: 0.5 for k in [
                    "insight_depth", "completeness", "actionability", "specificity", "overall"
                ]}
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            scores = {k: 0.5 for k in [
                "insight_depth", "completeness", "actionability", "specificity", "overall"
            ]}
        
        return scores


class VendorDiscoveryEvaluator(AgentEvaluator):
    """Evaluates vendor discovery agent."""
    
    def evaluate(self, input_data, output_data, agent_output_raw) -> Dict[str, float]:
        scores = {}
        
        vendors = output_data.get("vendors", [])
        event_location = input_data.get("context", {}).get("event", {}).get("location", "")
        
        # 1. Vendor Count
        vendor_count = len(vendors)
        if vendor_count >= 10:
            scores["vendor_count"] = 1.0
        elif vendor_count >= 5:
            scores["vendor_count"] = 0.8
        else:
            scores["vendor_count"] = vendor_count / 10
        
        # 2. Location Relevance (are vendors near the event?)
        if vendors and event_location:
            location_matches = 0
            event_location_lower = event_location.lower()
            for vendor in vendors:
                vendor_location = vendor.get("location", "").lower()
                if any(loc in vendor_location for loc in event_location_lower.split(", ")):
                    location_matches += 1
            scores["location_relevance"] = location_matches / len(vendors)
        else:
            scores["location_relevance"] = 0.5
        
        # 3. Data Completeness
        if vendors:
            complete_vendors = 0
            for vendor in vendors:
                has_name = bool(vendor.get("vendor_name"))
                has_type = bool(vendor.get("vendor_type"))
                has_contact = bool(vendor.get("contact_email") or vendor.get("vendor_website"))
                if has_name and has_type and has_contact:
                    complete_vendors += 1
            scores["completeness"] = complete_vendors / len(vendors)
        else:
            scores["completeness"] = 0.0
        
        # 4. Category Diversity
        if vendors:
            categories = set(v.get("vendor_type") for v in vendors if v.get("vendor_type"))
            scores["diversity"] = min(len(categories) / 3, 1.0)
        else:
            scores["diversity"] = 0.0
        
        return scores


# Registry of evaluators
EVALUATORS = {
    "intent_understanding": IntentUnderstandingEvaluator,
    "event_discovery": EventDiscoveryEvaluator,
    "event_intelligence": EventIntelligenceEvaluator,
    "vendor_discovery": VendorDiscoveryEvaluator,
    # Add more as needed
}


def get_evaluator(agent_name: str) -> AgentEvaluator:
    """Get evaluator for agent."""
    evaluator_class = EVALUATORS.get(agent_name)
    if evaluator_class:
        return evaluator_class()
    
    # Default evaluator
    return DefaultEvaluator()


class DefaultEvaluator(AgentEvaluator):
    """Default evaluator for agents without specific evaluators."""
    
    def evaluate(self, input_data, output_data, agent_output_raw) -> Dict[str, float]:
        # Basic metrics
        scores = {}
        
        # JSON validity
        try:
            if isinstance(output_data, dict):
                scores["json_validity"] = 1.0
            else:
                scores["json_validity"] = 0.0
        except:
            scores["json_validity"] = 0.0
        
        # Output presence
        scores["has_output"] = 1.0 if output_data else 0.0
        
        # Findings presence
        if isinstance(output_data, dict):
            has_findings = bool(output_data.get("findings") or output_data.get("events") or 
                              output_data.get("vendors"))
            scores["has_findings"] = 1.0 if has_findings else 0.0
        else:
            scores["has_findings"] = 0.0
        
        return scores


def calculate_overall_score(metric_scores: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
    """Calculate weighted overall score."""
    if not metric_scores:
        return 0.0
    
    if weights is None:
        # Equal weights
        return sum(metric_scores.values()) / len(metric_scores)
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for metric, score in metric_scores.items():
        weight = weights.get(metric, 1.0)
        weighted_sum += score * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0
```

---

## Phase 4: Integration with Agent Execution

### 4.1 Enhanced Base Agent with Experiment Tracking

```python
# agents/base.py (enhanced version)

from abc import ABC, abstractmethod
from typing import Any, Optional, Callable, Dict
from pydantic import BaseModel, Field
import time

from utils.llm_client import LLMResponse, get_llm_client_for_agent
from utils.model_experiment_tracker import ModelExperimentTracker
from utils.agent_evaluators import get_evaluator, calculate_overall_score


class AgentInput(BaseModel):
    """Input data passed to an agent."""
    query: str = Field(description="The research query for this agent")
    context: dict[str, Any] = Field(default_factory=dict, description="Context from previous agents")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Agent-specific parameters")
    
    # Experiment tracking
    experiment_id: Optional[str] = Field(default=None, description="Experiment ID for A/B testing")
    variant_name: Optional[str] = Field(default=None, description="Model variant being tested")


class AgentOutput(BaseModel):
    """Output data returned by an agent."""
    agent_name: str = Field(description="Name of the agent that produced this output")
    findings: dict[str, Any] = Field(description="Research findings")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    status: str = Field(default="success", description="Execution status")
    llm_usage: dict[str, Any] = Field(default_factory=dict, description="LLM usage statistics")
    quality_score: float = Field(default=0.0, description="Output quality score (0-1)")


class BaseAgent(ABC):
    """Base class for all research agents with experiment tracking."""
    
    name: str = "base_agent"
    description: str = "Base agent - to be extended"
    
    def __init__(self):
        """Initialize agent with LLM client and experiment tracker."""
        self._llm_complete: Optional[Callable[..., LLMResponse]] = None
        self._llm_usage_stats: list = []
        self._experiment_tracker = ModelExperimentTracker()
        self._evaluator = get_evaluator(self.name)
    
    @property
    def llm(self) -> Callable[..., LLMResponse]:
        """Get LLM completion function for this agent."""
        if self._llm_complete is None:
            self._llm_complete = get_llm_client_for_agent(self.name)
        return self._llm_complete
    
    def get_model_info(self) -> dict[str, Any]:
        """Get model configuration for this agent."""
        from utils.llm_client import get_llm_client
        client = get_llm_client()
        return client.get_agent_model_info(self.name)
    
    @abstractmethod
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute the agent's research task."""
        pass
    
    def execute_with_tracking(self, input_data: AgentInput) -> AgentOutput:
        """Execute with full experiment tracking."""
        start_time = time.time()
        model_info = self.get_model_info()
        
        try:
            # Execute agent
            output = self.execute(input_data)
            success = output.status == "success"
            
            # Evaluate quality
            quality_metrics = self._evaluator.evaluate(
                input_data=input_data.dict(),
                output_data=output.findings,
                agent_output_raw=str(output.findings)
            )
            overall_quality = calculate_overall_score(quality_metrics)
            output.quality_score = overall_quality
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Calculate cost (simplified, use actual token costs)
            tokens = output.llm_usage.get("tokens", {})
            cost_usd = self._calculate_cost(
                model_id=model_info["model"],
                input_tokens=tokens.get("prompt_tokens", 0),
                output_tokens=tokens.get("completion_tokens", 0)
            )
            
            # Record to experiment tracker
            if input_data.experiment_id:
                self._experiment_tracker.record_execution(
                    experiment_id=input_data.experiment_id,
                    agent_name=self.name,
                    variant_name=input_data.variant_name or model_info["model"],
                    model_id=model_info["model"],
                    provider=model_info["provider"],
                    latency_ms=latency_ms,
                    cost_usd=cost_usd,
                    tokens=tokens,
                    success=success,
                    quality_score=overall_quality,
                    metrics=quality_metrics,
                    input_query=input_data.query,
                    output=str(output.findings)[:1000],
                    error_message=None if success else output.findings.get("error")
                )
            
            return output
            
        except Exception as e:
            # Record failure
            if input_data.experiment_id:
                self._experiment_tracker.record_execution(
                    experiment_id=input_data.experiment_id,
                    agent_name=self.name,
                    variant_name=input_data.variant_name or model_info["model"],
                    model_id=model_info["model"],
                    provider=model_info["provider"],
                    latency_ms=int((time.time() - start_time) * 1000),
                    cost_usd=0.0,
                    tokens={},
                    success=False,
                    quality_score=0.0,
                    metrics={},
                    input_query=input_data.query,
                    output="",
                    error_message=str(e)
                )
            raise
    
    def _calculate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for model usage."""
        # Cost per 1K tokens (adjust based on your Grid AI pricing)
        COSTS = {
            "claude-opus-4-6": {"input": 0.015, "output": 0.075},
            "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
            "claude-sonnet-4-5": {"input": 0.003, "output": 0.015},
            "claude-haiku-4-5-20251001": {"input": 0.00025, "output": 0.00125},
            "gemini-3.1-pro": {"input": 0.0035, "output": 0.0105},
            "gemini-3-flash-preview": {"input": 0.00035, "output": 0.00105},
            "kimi-latest": {"input": 0.002, "output": 0.008},
            "glm-latest": {"input": 0.003, "output": 0.009},
            "glm-flash-experimental": {"input": 0.0003, "output": 0.0009},
            "open-large": {"input": 0.005, "output": 0.015},
            "open-fast": {"input": 0.0005, "output": 0.0015},
        }
        
        costs = COSTS.get(model_id, {"input": 0.01, "output": 0.03})
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def validate_input(self, input_data: AgentInput) -> bool:
        """Validate input before execution."""
        if not input_data.query:
            raise ValueError("Query cannot be empty")
        return True
```

---

## Phase 5: Dashboard & API

### 5.1 Experiment Dashboard API

```python
# api/experiments.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from utils.model_experiment_tracker import ModelExperimentTracker

router = APIRouter(prefix="/experiments", tags=["experiments"])


class ExperimentStatus(BaseModel):
    """Experiment status response."""
    experiment_id: str
    name: str
    agent_name: str
    status: str  # "running", "completed", "paused"
    total_executions: int
    variants: List[Dict[str, Any]]
    winning_variant: Optional[str]
    confidence_level: float


class VariantComparison(BaseModel):
    """Variant comparison data."""
    variant_name: str
    model_id: str
    sample_size: int
    avg_quality_score: float
    avg_latency_ms: float
    avg_cost_usd: float
    success_rate: float


@router.get("/", response_model=List[ExperimentStatus])
async def list_experiments():
    """List all active and completed experiments."""
    tracker = ModelExperimentTracker()
    
    # Query distinct experiments
    conn = tracker.db._get_connection()
    cursor = conn.execute("""
        SELECT DISTINCT experiment_id, agent_name, 
               COUNT(*) as total_runs,
               COUNT(DISTINCT variant_name) as variant_count
        FROM model_experiments
        GROUP BY experiment_id
        ORDER BY MAX(timestamp) DESC
    """)
    
    experiments = []
    for row in cursor.fetchall():
        exp_id, agent_name, total_runs, variant_count = row
        
        # Get experiment stats
        stats = tracker.get_experiment_stats(exp_id)
        winner = tracker.get_winning_variant(exp_id, min_samples=30)
        
        experiments.append(ExperimentStatus(
            experiment_id=exp_id,
            name=f"{agent_name} Model Test",
            agent_name=agent_name,
            status="running" if total_runs < 100 else "completed",
            total_executions=total_runs,
            variants=list(stats.values()),
            winning_variant=winner,
            confidence_level=0.95 if winner else 0.0
        ))
    
    return experiments


@router.get("/{experiment_id}/comparison", response_model=List[VariantComparison])
async def get_variant_comparison(experiment_id: str):
    """Get detailed comparison of experiment variants."""
    tracker = ModelExperimentTracker()
    stats = tracker.get_experiment_stats(experiment_id)
    
    comparisons = []
    for variant_name, data in stats.items():
        comparisons.append(VariantComparison(
            variant_name=variant_name,
            model_id=data["model_id"],
            sample_size=data["sample_size"],
            avg_quality_score=data["avg_quality_score"],
            avg_latency_ms=data["avg_latency_ms"],
            avg_cost_usd=data["avg_cost_usd"],
            success_rate=data["success_rate"]
        ))
    
    return comparisons


@router.get("/{experiment_id}/export")
async def export_experiment_data(experiment_id: str, format: str = "json"):
    """Export experiment data for analysis."""
    tracker = ModelExperimentTracker()
    data = tracker.export_experiment_data(experiment_id, format)
    
    if format == "csv":
        return {"content": data, "content_type": "text/csv"}
    
    return {"content": data, "content_type": "application/json"}


@router.post("/{experiment_id}/conclude")
async def conclude_experiment(experiment_id: str):
    """Conclude experiment and promote winning variant."""
    tracker = ModelExperimentTracker()
    winner = tracker.get_winning_variant(experiment_id, min_samples=50)
    
    if not winner:
        raise HTTPException(status_code=400, detail="No statistically significant winner yet")
    
    # Update config to use winning model (implement based on your config system)
    # ...
    
    return {
        "message": "Experiment concluded",
        "winner": winner,
        "action": "Updated config/models.yaml to use winning variant"
    }
```

---

## Implementation Roadmap

### Week 1: Foundation
- [ ] Create `ModelExperimentTracker` with database schema
- [ ] Implement basic evaluators for 3 key agents
- [ ] Add experiment tracking to base agent

### Week 2: Experiments
- [ ] Define experiment configurations
- [ ] Run pilot experiment: intent_understanding (3 models)
- [ ] Build comparison dashboard

### Week 3: Scale
- [ ] Run experiments for all 6+ key agents
- [ ] Collect 100+ samples per variant
- [ ] Analyze results

### Week 4: Conclude
- [ ] Determine winning models
- [ ] Update production config
- [ ] Document learnings

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Sample Size per Variant | ≥ 50 executions |
| Statistical Confidence | ≥ 95% |
| Quality Score Improvement | ≥ 10% vs baseline |
| Cost Reduction | ≥ 20% (if switching to cheaper model) |
| Latency Improvement | ≥ 15% (if optimizing for speed) |

---

## Summary

This framework enables **data-driven model selection** through:

1. **A/B Testing**: Run same agent with different models
2. **Automated Scoring**: Each output evaluated on multiple dimensions
3. **Statistical Analysis**: Confidence intervals, winner detection
4. **Cost Tracking**: Real cost per execution
5. **Dashboard**: Visual comparison of all metrics

**You'll empirically prove which model works best for each agent!**

Ready to implement Phase 1?
