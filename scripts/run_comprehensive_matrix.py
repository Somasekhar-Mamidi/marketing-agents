"""
Comprehensive Agent-Model Matrix Testing
Tests ALL agents with ALL working models to determine optimal configurations.
"""

import os
import sys
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.configurable_llm_client import get_llm_client
from utils.experiment_models import ExperimentDatabase, Experiment, ExperimentVariant, ExperimentStatus, ExperimentExecution
from agents.base import AgentInput

# Import all agents
from agents.intent_understanding import IntentUnderstandingAgent
from agents.event_discovery import EventDiscoveryAgent
from agents.event_qualification import EventQualificationAgent
from agents.event_website_scraper import EventWebsiteScraperAgent
from agents.event_intelligence import EventIntelligenceAgent
from agents.event_prioritization import EventPrioritizationAgent
from agents.outreach_email import OutreachEmailAgent
from agents.vendor_discovery import VendorDiscoveryAgent
from agents.schema_initialization import SchemaInitializationAgent
from agents.excel_table_generator import ExcelTableGeneratorAgent


# Working models from accessibility audit
WORKING_MODELS = [
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-sonnet-4-5",
    "claude-haiku-4-5-20251001",
    "gemini-3.1-pro",
    "gemini-3-flash-preview",
    "glm-latest",
    "glm-flash-experimental",
    "open-fast"
]

# Agent test configurations
AGENT_TESTS = {
    "intent_understanding": {
        "agent_class": IntentUnderstandingAgent,
        "test_queries": [
            "Find fintech conferences in Europe 2025",
            "What are the best AI events in San Francisco?",
            "Healthcare technology conferences in Asia"
        ],
        "evaluation_fn": "evaluate_intent"
    },
    "event_discovery": {
        "agent_class": EventDiscoveryAgent,
        "test_queries": [
            "fintech conferences Europe 2025",
            "AI events San Francisco",
            "healthcare conferences Asia"
        ],
        "evaluation_fn": "evaluate_discovery"
    },
    "event_qualification": {
        "agent_class": EventQualificationAgent,
        "test_queries": [
            "Evaluate this event: Fintech Summit 2025, 5000 attendees, $100k sponsorship",
            "Score: AI Conference, 2000 attendees, high industry reputation",
            "Assess: Healthcare Expo, 10000 attendees, global reach"
        ],
        "evaluation_fn": "evaluate_qualification"
    },
    "event_website_scraper": {
        "agent_class": EventWebsiteScraperAgent,
        "test_queries": [
            "Extract data from https://example-conference.com",
            "Parse event page: dates, location, speakers",
            "Scrape conference website for details"
        ],
        "evaluation_fn": "evaluate_scraper"
    },
    "event_intelligence": {
        "agent_class": EventIntelligenceAgent,
        "test_queries": [
            "Analyze Fintech Summit for sponsorship ROI",
            "Strategic value of AI Conference 2025",
            "Competitive analysis: Healthcare Expo vs competitors"
        ],
        "evaluation_fn": "evaluate_intelligence"
    },
    "event_prioritization": {
        "agent_class": EventPrioritizationAgent,
        "test_queries": [
            "Rank 10 fintech events by priority",
            "Prioritize: AI conferences with high attendance",
            "Sort events: Tier 1, Tier 2, Tier 3"
        ],
        "evaluation_fn": "evaluate_prioritization"
    },
    "outreach_email": {
        "agent_class": OutreachEmailAgent,
        "test_queries": [
            "Draft sponsorship email for Fintech Summit",
            "Write outreach: AI Conference partnership",
            "Email template: Healthcare Expo booth inquiry"
        ],
        "evaluation_fn": "evaluate_email"
    },
    "vendor_discovery": {
        "agent_class": VendorDiscoveryAgent,
        "test_queries": [
            "Find booth builders for Dublin Tech Summit",
            "Discover AV vendors for AI Conference",
            "Locate catering services for Fintech Expo"
        ],
        "evaluation_fn": "evaluate_vendor"
    },
    "schema_initialization": {
        "agent_class": SchemaInitializationAgent,
        "test_queries": [
            "Initialize event schema",
            "Create vendor schema structure",
            "Setup email template schema"
        ],
        "evaluation_fn": "evaluate_schema"
    },
    "excel_table_generator": {
        "agent_class": ExcelTableGeneratorAgent,
        "test_queries": [
            "Format events data as Excel table",
            "Create CSV export: vendor list",
            "Generate summary table: event metrics"
        ],
        "evaluation_fn": "evaluate_excel"
    }
}


def evaluate_basic(agent_name: str, query: str, output: dict) -> float:
    """Basic evaluation - check if output exists and has findings."""
    if not output or not output.get("findings"):
        return 0.0
    
    findings = output.get("findings", {})
    
    # Check for errors
    if findings.get("error") or output.get("status") == "error":
        return 0.0
    
    # Check for actual content
    if findings.get("events") or findings.get("vendors") or findings.get("intent") or findings.get("email"):
        return 1.0
    
    return 0.5


def test_agent_with_model(agent_name: str, agent_class, model_id: str, test_queries: list) -> Dict:
    """Test a single agent with a single model."""
    print(f"  Testing {agent_name} with {model_id}...", end=" ", flush=True)
    
    # Temporarily override model config
    import yaml
    config_path = Path(__file__).parent.parent / "config" / "models.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    original_model = config["llm"]["agent_models"].get(agent_name, {}).get("model", "")
    if agent_name not in config["llm"]["agent_models"]:
        config["llm"]["agent_models"][agent_name] = {}
    config["llm"]["agent_models"][agent_name]["model"] = model_id
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    try:
        results = []
        latencies = []
        
        for query in test_queries:
            start_time = time.time()
            
            try:
                agent = agent_class()
                input_data = AgentInput(query=query, context={}, parameters={})
                output = agent.execute(input_data)
                
                latency_ms = int((time.time() - start_time) * 1000)
                latencies.append(latency_ms)
                
                # Evaluate output
                score = evaluate_basic(agent_name, query, output.__dict__ if hasattr(output, '__dict__') else output)
                
                results.append({
                    "query": query,
                    "success": output.status == "success" if hasattr(output, 'status') else True,
                    "score": score,
                    "latency_ms": latency_ms
                })
                
            except Exception as e:
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "latency_ms": int((time.time() - start_time) * 1000)
                })
        
        # Calculate aggregate metrics
        successful = [r for r in results if r.get("success")]
        success_rate = len(successful) / len(results) if results else 0
        avg_score = sum(r.get("score", 0) for r in successful) / len(successful) if successful else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        print(f"Success: {success_rate*100:.0f}%, Score: {avg_score:.2f}, Latency: {avg_latency:.0f}ms")
        
        return {
            "agent": agent_name,
            "model": model_id,
            "success_rate": success_rate,
            "avg_score": avg_score,
            "avg_latency_ms": avg_latency,
            "total_tests": len(test_queries),
            "results": results
        }
        
    finally:
        # Restore original config
        if original_model:
            config["llm"]["agent_models"][agent_name]["model"] = original_model
        with open(config_path, 'w') as f:
            yaml.dump(config, f)


def run_comprehensive_matrix():
    """Run full matrix testing."""
    print("="*80)
    print("COMPREHENSIVE AGENT-MODEL MATRIX TESTING")
    print("="*80)
    print()
    print(f"Agents: {len(AGENT_TESTS)}")
    print(f"Models: {len(WORKING_MODELS)}")
    print(f"Total combinations: {len(AGENT_TESTS) * len(WORKING_MODELS)}")
    print()
    
    matrix_results = []
    
    for agent_name, agent_config in AGENT_TESTS.items():
        print(f"\n{'='*80}")
        print(f"Testing Agent: {agent_name}")
        print(f"{'='*80}")
        
        agent_class = agent_config["agent_class"]
        test_queries = agent_config["test_queries"]
        
        for model_id in WORKING_MODELS:
            result = test_agent_with_model(agent_name, agent_class, model_id, test_queries)
            matrix_results.append(result)
            time.sleep(0.2)  # Rate limiting
    
    # Generate matrix report
    print("\n" + "="*80)
    print("MATRIX RESULTS SUMMARY")
    print("="*80)
    print()
    
    # Create matrix view
    print(f"{'Agent':<25}", end="")
    for model_id in WORKING_MODELS:
        print(f"{model_id[:12]:<12}", end="")
    print()
    print("-" * 130)
    
    for agent_name in AGENT_TESTS.keys():
        print(f"{agent_name:<25}", end="")
        for model_id in WORKING_MODELS:
            # Find result for this agent-model combo
            result = next((r for r in matrix_results if r["agent"] == agent_name and r["model"] == model_id), None)
            if result:
                success_rate = result["success_rate"] * 100
                score = result["avg_score"]
                display = f"{success_rate:.0f}%/{score:.2f}"
                print(f"{display:<12}", end="")
            else:
                print(f"{'N/A':<12}", end="")
        print()
    
    # Determine optimal model per agent
    print("\n" + "="*80)
    print("OPTIMAL MODEL RECOMMENDATIONS")
    print("="*80)
    print()
    
    recommendations = []
    
    for agent_name in AGENT_TESTS.keys():
        agent_results = [r for r in matrix_results if r["agent"] == agent_name]
        
        if not agent_results:
            continue
        
        # Score = success_rate * avg_score
        best = max(agent_results, key=lambda r: r["success_rate"] * r["avg_score"])
        
        recommendations.append({
            "agent": agent_name,
            "recommended_model": best["model"],
            "success_rate": best["success_rate"],
            "avg_score": best["avg_score"],
            "avg_latency_ms": best["avg_latency_ms"]
        })
        
        print(f"{agent_name:<25} -> {best['model']:<25} (Score: {best['avg_score']:.2f}, Success: {best['success_rate']*100:.0f}%)")
    
    # Save report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "agents_tested": len(AGENT_TESTS),
            "models_tested": len(WORKING_MODELS),
            "total_combinations": len(matrix_results)
        },
        "matrix_results": matrix_results,
        "recommendations": recommendations
    }
    
    report_file = f"comprehensive_matrix_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_file}")
    
    return report


if __name__ == "__main__":
    report = run_comprehensive_matrix()
