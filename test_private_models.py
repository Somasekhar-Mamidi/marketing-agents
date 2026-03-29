"""Test private models: glm-private and private-large."""
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

api_key = os.environ.get("GRID_AI_API_KEY")
if not api_key:
    print("ERROR: GRID_AI_API_KEY not found")
    sys.exit(1)

client = OpenAI(base_url="https://grid.ai.juspay.net", api_key=api_key)

# Test scenarios representing different agent workloads
tests = [
    {
        "name": "intent_understanding",
        "desc": "Complex reasoning",
        "system": "Extract structured intent from user queries for event marketing.",
        "prompt": "Parse: 'Find payment conferences in USA 2025, exclude small events'",
        "max_tokens": 400
    },
    {
        "name": "event_discovery", 
        "desc": "Data extraction",
        "system": "Extract event details from search results.",
        "prompt": "Extract from: 'Money20/20 USA, Oct 26-29 2025, Las Vegas, 10,000 attendees'",
        "max_tokens": 200
    },
    {
        "name": "event_qualification",
        "desc": "Judgment/Scoring", 
        "system": "Score event sponsorship opportunities 0-100.",
        "prompt": "Score Money20/20 for payments company: 10K attendees, C-level focus",
        "max_tokens": 500
    },
    {
        "name": "outreach_email",
        "desc": "Creative writing",
        "system": "Write professional sponsorship emails.",
        "prompt": "Write 2-sentence sponsorship inquiry for Money20/20 from PayFlow",
        "max_tokens": 200
    }
]

models = ["glm-private", "private-large"]

print("="*70)
print("PRIVATE MODELS TEST")
print("="*70)
print(f"Models: {', '.join(models)}")
print(f"Tests: {len(tests)} scenarios")
print()

results = {}

for model in models:
    print(f"\n{'='*70}")
    print(f"TESTING: {model}")
    print(f"{'='*70}")
    
    model_results = []
    for test in tests:
        print(f"\n  {test['name']} ({test['desc']})")
        try:
            start = time.time()
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": test["system"]},
                    {"role": "user", "content": test["prompt"]}
                ],
                max_tokens=test["max_tokens"],
                temperature=0.3,
                timeout=45
            )
            latency = (time.time() - start) * 1000
            
            content = resp.choices[0].message.content
            usage = resp.usage
            
            print(f"    ✅ {latency:.0f}ms | {usage.total_tokens} tokens")
            print(f"       {content[:60].replace(chr(10), ' ')}...")
            
            model_results.append({
                "test": test["name"],
                "status": "SUCCESS",
                "latency_ms": round(latency, 2),
                "tokens": usage.total_tokens
            })
        except Exception as e:
            err = str(e)[:80]
            print(f"    ❌ {err}")
            model_results.append({
                "test": test["name"],
                "status": "FAILED",
                "error": err
            })
    
    results[model] = model_results

# Summary
print(f"\n\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")

for model, model_results in results.items():
    success = [r for r in model_results if r["status"] == "SUCCESS"]
    if success:
        avg_lat = sum(r["latency_ms"] for r in success) / len(success)
        avg_tokens = sum(r["tokens"] for r in success) / len(success)
        print(f"\n{model}:")
        print(f"  Success: {len(success)}/{len(model_results)}")
        print(f"  Avg Latency: {avg_lat:.0f}ms")
        print(f"  Avg Tokens: {avg_tokens:.0f}")
        
        # Best at
        if success:
            fastest = min(success, key=lambda x: x["latency_ms"])
            print(f"  Fastest: {fastest['test']} ({fastest['latency_ms']:.0f}ms)")

# Save
filename = f"private_models_detailed_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, 'w') as f:
    json.dump({
        "timestamp": datetime.utcnow().isoformat(),
        "models": models,
        "tests": [t["name"] for t in tests],
        "results": results
    }, f, indent=2)
print(f"\n💾 Saved to: {filename}")
