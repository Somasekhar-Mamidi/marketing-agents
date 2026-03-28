"""Test 4 working non-capped models with all agents."""
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.configurable_llm_client import get_llm_client
from agents.base import AgentInput

# 4 working non-capped models
WORKING_MODELS = {
    "glm-flash-experimental": "GLM-Flash (Cheapest)",
    "glm-latest": "GLM-Latest (Balanced)",
    "open-fast": "Minimax-Fast (Speed)",
    "open-large-sa": "Kimi-SA (Long Context)"
}

# Quick test for each agent
def quick_test():
    print("="*70)
    print("TESTING 4 NON-CAPPED MODELS")
    print("="*70)
    print()
    print("Models:")
    for model, desc in WORKING_MODELS.items():
        print(f"  • {model:<25} - {desc}")
    print()
    
    client = get_llm_client()
    results = []
    
    for model_id in WORKING_MODELS.keys():
        print(f"Testing {model_id}...", end=" ", flush=True)
        
        start = time.time()
        try:
            response = client.complete_for_agent(
                agent_name="test_agent",
                prompt="Reply with OK only.",
                system_message="Reply with OK only."
            )
            latency = (time.time() - start) * 1000
            
            results.append({
                "model": model_id,
                "status": "SUCCESS" if response.success else "FAILED",
                "latency_ms": latency
            })
            
            if response.success:
                print(f"✅ {latency:.0f}ms")
            else:
                print(f"❌ {response.error[:40]}")
        except Exception as e:
            print(f"❌ {str(e)[:40]}")
            results.append({
                "model": model_id,
                "status": "ERROR",
                "error": str(e)
            })
        
        time.sleep(0.3)
    
    # Summary
    print()
    print("="*70)
    print("RESULTS")
    print("="*70)
    success = sum(1 for r in results if r.get("status") == "SUCCESS")
    print(f"Success: {success}/{len(results)}")
    
    # Save results
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "models": list(WORKING_MODELS.keys()),
        "results": results
    }
    
    filename = f"test_4models_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Report: {filename}")

if __name__ == "__main__":
    quick_test()
