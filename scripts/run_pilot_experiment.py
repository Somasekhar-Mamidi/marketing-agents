"""
Pilot Experiment: Intent Understanding Model Comparison
Tests 3 models on 50 queries to determine optimal configuration.
"""

import os
import sys
import json
import uuid
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.configurable_llm_client import get_llm_client, LLMResponse
from utils.experiment_models import ExperimentDatabase, Experiment, ExperimentVariant, ExperimentStatus, ExperimentExecution
from agents.intent_understanding import IntentUnderstandingAgent
from agents.base import AgentInput


# 50 test queries for intent understanding
TEST_QUERIES = [
    "Find fintech conferences in Europe 2025",
    "What are the best AI events in San Francisco?",
    "Looking for healthcare technology conferences in Asia",
    "Payments industry events in London",
    "Crypto and blockchain conferences in Dubai",
    "Retail technology expos in New York",
    "Developer conferences for Python programmers",
    "Marketing automation events in Chicago",
    "E-commerce conferences in Singapore",
    "Cybersecurity summits in Berlin",
    "Data science conferences in Bangalore",
    "Cloud computing events in Seattle",
    "DevOps conferences in Amsterdam",
    "SaaS industry events in Boston",
    "Mobile app development conferences in Barcelona",
    "API conferences in San Jose",
    "Machine learning workshops in Toronto",
    "Digital transformation events in Paris",
    "Open source conferences in Europe",
    "Technology leadership summits in Austin",
    "Blockchain events in Hong Kong",
    "AI ethics conferences in Vancouver",
    "Quantum computing events in Zurich",
    "Robotics conferences in Tokyo",
    "Green technology events in Copenhagen",
    "5G technology conferences in Seoul",
    "Edge computing events in Frankfurt",
    "IoT conferences in Helsinki",
    "AR/VR events in Los Angeles",
    "Gaming industry conferences in Las Vegas",
    "Fintech events in Sydney",
    "Insurtech conferences in Zurich",
    "Regtech events in Luxembourg",
    "Wealth management technology events in Geneva",
    "Digital banking conferences in Singapore",
    "Lending technology events in Mumbai",
    "Payments innovation events in Amsterdam",
    "Investment technology conferences in New York",
    "Financial inclusion events in Nairobi",
    "Sustainable finance events in Oslo",
    "Cryptocurrency events in Miami",
    "DeFi conferences in Lisbon",
    "NFT events in Miami",
    "Web3 conferences in Lisbon",
    "Metaverse events in Los Angeles",
    "Digital identity conferences in Brussels",
    "Privacy technology events in Berlin",
    "Regulatory technology events in London",
    "Compliance technology conferences in New York",
    "Risk management technology events in Chicago"
]


def evaluate_intent_output(query: str, output: dict) -> dict:
    """Evaluate quality of intent understanding output."""
    scores = {}
    intent = output.get("intent", {})
    
    # 1. JSON Validity
    scores["json_validity"] = 1.0 if output and "intent" in output else 0.0
    
    # 2. Required Fields Present
    required = ["industry", "region", "themes"]
    present = sum(1 for f in required if intent.get(f))
    scores["completeness"] = present / len(required)
    
    # 3. Query Relevance
    query_lower = query.lower()
    themes = intent.get("themes", [])
    industry = intent.get("industry", "").lower()
    
    # Check if extracted themes/industry match query
    matches = 0
    if industry and industry in query_lower:
        matches += 1
    if themes:
        for theme in themes:
            if isinstance(theme, str) and theme.lower() in query_lower:
                matches += 1
                break
    scores["query_relevance"] = min(matches / 2, 1.0)
    
    # 4. Industry Recognition
    valid_industries = [
        "fintech", "payments", "ai", "technology", "healthcare",
        "retail", "travel", "education", "manufacturing", "crypto",
        "blockchain", "saas", "e-commerce", "cybersecurity", "devops",
        "cloud", "mobile", "data science", "gaming", "marketing"
    ]
    industry_val = intent.get("industry", "").lower()
    scores["industry_validity"] = 1.0 if any(ind in industry_val for ind in valid_industries) else 0.5
    
    # 5. Confidence Score
    confidence = intent.get("intent_confidence", 0)
    scores["confidence_normalized"] = min(float(confidence) if confidence else 0, 1.0)
    
    # Calculate overall
    overall = sum(scores.values()) / len(scores)
    
    return {
        "overall": round(overall, 3),
        **scores
    }


def run_experiment_variant(variant_name: str, model_id: str, queries: list, experiment_id: str, variant_id: str):
    """Run experiment for a single model variant."""
    print(f"\n{'='*80}")
    print(f"Testing Variant: {variant_name} (Model: {model_id})")
    print(f"{'='*80}\n")
    
    # Temporarily override the agent's model
    import yaml
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent / "config" / "models.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Store original config
    original_model = config["llm"]["agent_models"]["intent_understanding"]["model"]
    
    # Set test model
    config["llm"]["agent_models"]["intent_understanding"]["model"] = model_id
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    try:
        client = get_llm_client()
        db = ExperimentDatabase()
        
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] Testing: {query[:50]}...", end=" ", flush=True)
            
            start_time = time.time()
            
            try:
                # Create agent and execute
                agent = IntentUnderstandingAgent()
                input_data = AgentInput(query=query, context={}, parameters={})
                
                output = agent.execute(input_data)
                
                # Get model info from response
                model_info = agent.get_model_info()
                actual_model = model_info.get("model", model_id)
                
                # Calculate metrics
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Evaluate quality
                quality_metrics = evaluate_intent_output(query, output.findings)
                overall_score = quality_metrics["overall"]
                
                # Get token usage (estimate if not tracked)
                llm_usage = output.llm_usage if hasattr(output, 'llm_usage') else {}
                tokens = llm_usage.get("tokens", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
                
                # Calculate cost
                cost_per_1k_input = 0.015 if "opus" in model_id else 0.003 if "sonnet" in model_id else 0.0035
                cost_per_1k_output = 0.075 if "opus" in model_id else 0.015 if "sonnet" in model_id else 0.0105
                
                cost_usd = (tokens.get("prompt_tokens", 0) / 1000 * cost_per_1k_input + 
                           tokens.get("completion_tokens", 0) / 1000 * cost_per_1k_output)
                
                # Record execution
                execution = ExperimentExecution(
                    id=None,
                    experiment_id=experiment_id,
                    variant_id=variant_id,
                    agent_name="intent_understanding",
                    model_id=actual_model,
                    started_at=datetime.utcnow().isoformat(),
                    completed_at=datetime.utcnow().isoformat(),
                    latency_ms=latency_ms,
                    input_tokens=tokens.get("prompt_tokens", 0),
                    output_tokens=tokens.get("completion_tokens", 0),
                    total_tokens=tokens.get("total_tokens", 0),
                    cost_usd=cost_usd,
                    success=output.status == "success",
                    error_message=None if output.status == "success" else str(output.findings.get("error")),
                    quality_score=overall_score,
                    quality_metrics=quality_metrics,
                    input_query=query,
                    output_sample=json.dumps(output.findings)[:500]
                )
                
                db.record_execution(execution)
                
                print(f"✅ Score: {overall_score:.2f}, Latency: {latency_ms}ms")
                
                results.append({
                    "query": query,
                    "success": True,
                    "quality_score": overall_score,
                    "latency_ms": latency_ms,
                    "cost_usd": cost_usd
                })
                
            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}")
                
                # Record failure
                execution = ExperimentExecution(
                    id=None,
                    experiment_id=experiment_id,
                    variant_id=variant_id,
                    agent_name="intent_understanding",
                    model_id=model_id,
                    started_at=datetime.utcnow().isoformat(),
                    completed_at=datetime.utcnow().isoformat(),
                    latency_ms=int((time.time() - start_time) * 1000),
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    cost_usd=0,
                    success=False,
                    error_message=str(e),
                    quality_score=0,
                    quality_metrics={},
                    input_query=query,
                    output_sample=""
                )
                db.record_execution(execution)
                
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e)
                })
            
            # Rate limiting
            time.sleep(0.5)
        
        # Calculate aggregate metrics
        successful = [r for r in results if r.get("success")]
        if successful:
            avg_quality = sum(r["quality_score"] for r in successful) / len(successful)
            avg_latency = sum(r["latency_ms"] for r in successful) / len(successful)
            total_cost = sum(r.get("cost_usd", 0) for r in successful)
            success_rate = len(successful) / len(results)
        else:
            avg_quality = avg_latency = total_cost = success_rate = 0
        
        print(f"\nVariant Summary: {variant_name}")
        print(f"  Success Rate: {success_rate*100:.1f}%")
        print(f"  Avg Quality: {avg_quality:.3f}")
        print(f"  Avg Latency: {avg_latency:.0f}ms")
        print(f"  Total Cost: ${total_cost:.4f}")
        
        return {
            "variant": variant_name,
            "model": model_id,
            "success_rate": success_rate,
            "avg_quality": avg_quality,
            "avg_latency_ms": avg_latency,
            "total_cost_usd": total_cost,
            "results": results
        }
        
    finally:
        # Restore original config
        config["llm"]["agent_models"]["intent_understanding"]["model"] = original_model
        with open(config_path, 'w') as f:
            yaml.dump(config, f)


def run_pilot_experiment():
    """Run the full pilot experiment."""
    print("="*80)
    print("PILOT EXPERIMENT: Intent Understanding Model Comparison")
    print("="*80)
    print()
    
    # Create experiment
    experiment_id = str(uuid.uuid4())[:8]
    experiment = Experiment(
        id=experiment_id,
        name="Intent Understanding - Model Comparison",
        description="Compare Claude Opus, Gemini Pro, and Claude Sonnet for intent extraction",
        agent_name="intent_understanding",
        status=ExperimentStatus.RUNNING,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
        config={"evaluation_criteria": ["json_validity", "completeness", "query_relevance"]}
    )
    
    db = ExperimentDatabase()
    db.create_experiment(experiment)
    
    print(f"Created Experiment: {experiment_id}")
    print()
    
    # Define variants (3 models to test)
    variants = [
        ("claude_opus", "claude-opus-4-6"),
        ("gemini_pro", "gemini-3.1-pro"),
        ("claude_sonnet", "claude-sonnet-4-5")
    ]
    
    variant_results = []
    
    for variant_name, model_id in variants:
        variant_id = str(uuid.uuid4())[:8]
        
        # Create variant record
        variant = ExperimentVariant(
            id=variant_id,
            experiment_id=experiment_id,
            name=variant_name,
            model_id=model_id,
            provider="grid_ai",
            weight=33,
            config={"temperature": 0.3, "max_tokens": 4000},
            is_active=True
        )
        db.add_variant(variant)
        
        # Run tests
        result = run_experiment_variant(variant_name, model_id, TEST_QUERIES, experiment_id, variant_id)
        variant_results.append(result)
    
    # Mark experiment as completed
    import sqlite3
    conn = db._get_connection()
    conn.execute(
        "UPDATE experiments SET status = ?, updated_at = ? WHERE id = ?",
        (ExperimentStatus.COMPLETED.value, datetime.utcnow().isoformat(), experiment_id)
    )
    conn.commit()
    
    # Generate comparison report
    print("\n" + "="*80)
    print("EXPERIMENT RESULTS - COMPARISON")
    print("="*80)
    print()
    
    print(f"{'Variant':<20} {'Model':<25} {'Success':<10} {'Quality':<10} {'Latency':<12} {'Cost':<10}")
    print("-" * 90)
    
    best_variant = None
    best_score = 0
    
    for result in variant_results:
        score = result["avg_quality"] * result["success_rate"]
        if score > best_score:
            best_score = score
            best_variant = result["variant"]
        
        print(f"{result['variant']:<20} {result['model']:<25} "
              f"{result['success_rate']*100:>6.1f}%    "
              f"{result['avg_quality']:>6.3f}    "
              f"{result['avg_latency_ms']:>8.0f}ms   "
              f"${result['total_cost_usd']:>6.4f}")
    
    print()
    print(f"🏆 WINNER: {best_variant} (Quality × Success Rate = {best_score:.3f})")
    print()
    
    # Save report
    report = {
        "experiment_id": experiment_id,
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_queries": len(TEST_QUERIES),
            "variants_tested": len(variants),
            "winner": best_variant
        },
        "results": variant_results
    }
    
    report_file = f"intent_understanding_experiment_{experiment_id}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Full report saved to: {report_file}")
    
    return report


if __name__ == "__main__":
    report = run_pilot_experiment()
