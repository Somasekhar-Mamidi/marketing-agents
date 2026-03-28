"""Test script to verify all models in catalog are accessible via Grid AI."""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.configurable_llm_client import get_llm_client, ConfigurableLLMClient


def test_model_accessibility(model_id: str, provider: str = "grid_ai") -> Dict:
    """Test if a model is accessible via Grid AI.
    
    Returns:
        Dict with status, latency, error (if any)
    """
    client = get_llm_client()
    
    # Create temporary config for this model
    config = client.get_model_config("test_agent")
    config.model_id = model_id
    config.provider = provider
    
    start_time = time.time()
    
    try:
        # Direct provider test (not through agent config)
        provider_instance = client._providers.get(provider)
        if not provider_instance:
            return {
                "model": model_id,
                "status": "FAILED",
                "error": f"Provider {provider} not initialized",
                "latency_ms": 0
            }
        
        response = provider_instance.complete(
            prompt="Reply with 'OK' only. This is a connectivity test.",
            config=config,
            system_message="You are a test assistant. Reply with OK only.",
            response_format=None
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        if response.success:
            return {
                "model": model_id,
                "status": "SUCCESS",
                "error": None,
                "latency_ms": latency_ms,
                "response_preview": response.content[:50] if response.content else ""
            }
        else:
            return {
                "model": model_id,
                "status": "FAILED",
                "error": response.error,
                "latency_ms": latency_ms
            }
            
    except Exception as e:
        return {
            "model": model_id,
            "status": "ERROR",
            "error": str(e),
            "latency_ms": int((time.time() - start_time) * 1000)
        }


def get_all_models_from_config() -> List[Tuple[str, str]]:
    """Get all model IDs from config/models.yaml."""
    client = get_llm_client()
    models = []
    
    providers_config = client.config.get("llm", {}).get("providers", {})
    for provider_name, provider_config in providers_config.items():
        for model in provider_config.get("models", []):
            models.append((model["id"], provider_name))
    
    return models


def run_accessibility_audit(output_file: str = "model_accessibility_report.json"):
    """Run full accessibility audit on all models."""
    print("=" * 80)
    print("GRID AI MODEL ACCESSIBILITY AUDIT")
    print("=" * 80)
    print()
    
    models = get_all_models_from_config()
    print(f"Found {len(models)} models in configuration")
    print()
    
    results = []
    success_count = 0
    fail_count = 0
    
    # Group by provider for organized output
    providers = {}
    for model_id, provider in models:
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model_id)
    
    for provider, model_list in providers.items():
        print(f"\n{'='*80}")
        print(f"Testing {provider.upper()} Provider - {len(model_list)} models")
        print(f"{'='*80}\n")
        
        for model_id in model_list:
            print(f"Testing {model_id}...", end=" ", flush=True)
            
            result = test_model_accessibility(model_id, provider)
            results.append(result)
            
            if result["status"] == "SUCCESS":
                print(f"✅ SUCCESS ({result['latency_ms']}ms)")
                success_count += 1
            else:
                print(f"❌ {result['status']}: {result['error'][:60]}...")
                fail_count += 1
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
    
    # Generate summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total Models Tested: {len(models)}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"Success Rate: {(success_count/len(models)*100):.1f}%")
    print()
    
    # Group results by status
    working_models = [r for r in results if r["status"] == "SUCCESS"]
    failed_models = [r for r in results if r["status"] != "SUCCESS"]
    
    print("WORKING MODELS:")
    print("-" * 40)
    for r in working_models:
        print(f"  ✅ {r['model']} ({r['latency_ms']}ms)")
    
    if failed_models:
        print("\nFAILED MODELS:")
        print("-" * 40)
        for r in failed_models:
            print(f"  ❌ {r['model']}")
            print(f"     Error: {r['error']}")
    
    # Save report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total": len(models),
            "success": success_count,
            "failed": fail_count,
            "success_rate": success_count/len(models)
        },
        "results": results,
        "working_models": [r["model"] for r in working_models],
        "failed_models": [{"model": r["model"], "error": r["error"]} for r in failed_models]
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {output_file}")
    
    return report


if __name__ == "__main__":
    report = run_accessibility_audit()
    
    # Exit with error code if any models failed
    if report["summary"]["failed"] > 0:
        print(f"\n⚠️  {report['summary']['failed']} models failed accessibility test")
        sys.exit(1)
    else:
        print("\n🎉 All models are accessible!")
        sys.exit(0)
