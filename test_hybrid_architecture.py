"""Test hybrid architecture: Gemini primary + tool-based fallback."""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from utils.tools import get_tool_registry, get_research_tools


def test_gemini_native_path():
    """Test Gemini native web access (primary path)."""
    api_key = os.environ.get("GRID_AI_API_KEY")
    if not api_key:
        print("GRID_AI_API_KEY not set")
        return None
    
    client = OpenAI(base_url="https://grid.ai.juspay.net", api_key=api_key)
    
    print("\n" + "=" * 70)
    print("TEST 1: Gemini Native Web Access (Primary Path)")
    print("=" * 70)
    
    start = time.time()
    try:
        response = client.chat.completions.create(
            model="gemini-3-flash-preview",
            messages=[
                {"role": "user", "content": "Find 3 payment conferences in Europe for 2025 with specific dates"}
            ],
            max_tokens=800,
            timeout=30
        )
        elapsed = time.time() - start
        
        content = response.choices[0].message.content
        
        print(f"✓ SUCCESS - {elapsed:.1f}s")
        print(f"Model: {response.model}")
        print(f"Tokens: {response.usage.total_tokens}")
        print(f"\nResponse preview:\n{content[:500]}...")
        
        # Check if response has specific dates (indicates web access)
        has_dates = any(month in content for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
        has_year = "2025" in content
        
        print(f"\n✓ Has specific dates: {has_dates}")
        print(f"✓ Mentions 2025: {has_year}")
        
        return {
            "status": "SUCCESS",
            "path": "gemini_native",
            "elapsed_seconds": round(elapsed, 2),
            "tokens": response.usage.total_tokens,
            "has_dates": has_dates,
            "has_year": has_year,
            "response_preview": content[:300]
        }
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ FAILED - {elapsed:.1f}s")
        print(f"Error: {str(e)[:200]}")
        return {
            "status": "FAILED",
            "path": "gemini_native",
            "error": str(e)[:200]
        }


def test_fallback_path():
    """Test fallback path with GLM + tool calling."""
    api_key = os.environ.get("GRID_AI_API_KEY")
    if not api_key:
        print("GRID_AI_API_KEY not set")
        return None
    
    client = OpenAI(base_url="https://grid.ai.juspay.net", api_key=api_key)
    tool_registry = get_tool_registry()
    tools = get_research_tools()
    
    print("\n" + "=" * 70)
    print("TEST 2: Fallback Path (GLM + Tool Calling + DuckDuckGo)")
    print("=" * 70)
    
    system_msg = "You are a research assistant. Use web_search tool to find current information."
    user_msg = "Find fintech conferences in USA for 2025"
    
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]
    
    start = time.time()
    tool_calls_count = 0
    
    try:
        for iteration in range(3):
            response = client.chat.completions.create(
                model="glm-latest",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=800,
                timeout=60
            )
            
            message = response.choices[0].message
            
            if not message.tool_calls:
                elapsed = time.time() - start
                print(f"✓ SUCCESS - {elapsed:.1f}s")
                print(f"Model: {response.model}")
                print(f"Tool calls made: {tool_calls_count}")
                print(f"\nResponse preview:\n{message.content[:500]}...")
                
                return {
                    "status": "SUCCESS",
                    "path": "fallback_tool_based",
                    "model": "glm-latest",
                    "elapsed_seconds": round(elapsed, 2),
                    "tool_calls": tool_calls_count,
                    "response_preview": message.content[:300]
                }
            
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [{"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in message.tool_calls]
            })
            
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except:
                    args = {}
                
                result = tool_registry.execute(tool_name, args)
                tool_calls_count += 1
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        
        elapsed = time.time() - start
        print(f"⚠ MAX ITERATIONS - {elapsed:.1f}s")
        return {
            "status": "MAX_ITERATIONS",
            "path": "fallback_tool_based",
            "tool_calls": tool_calls_count
        }
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ FAILED - {elapsed:.1f}s")
        print(f"Error: {str(e)[:200]}")
        return {
            "status": "FAILED",
            "path": "fallback_tool_based",
            "error": str(e)[:200]
        }


def test_duckduckgo_only():
    """Test DuckDuckGo search works without API keys."""
    from utils.search import WebSearchTool
    
    print("\n" + "=" * 70)
    print("TEST 3: DuckDuckGo Search (No API Keys)")
    print("=" * 70)
    
    start = time.time()
    try:
        search = WebSearchTool(provider="duckduckgo")
        results = search.search("payment conferences 2025", max_results=5)
        elapsed = time.time() - start
        
        print(f"✓ SUCCESS - {elapsed:.1f}s")
        print(f"Results found: {len(results)}")
        print(f"\nSample results:")
        for r in results[:3]:
            print(f"  • {r.get('title', 'N/A')[:60]}...")
        
        return {
            "status": "SUCCESS",
            "path": "duckduckgo_only",
            "elapsed_seconds": round(elapsed, 2),
            "results_count": len(results),
            "sample_results": [{"title": r.get("title", "")[:60], "url": r.get("url", "")} for r in results[:3]]
        }
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ FAILED - {elapsed:.1f}s")
        print(f"Error: {str(e)[:200]}")
        return {
            "status": "FAILED",
            "path": "duckduckgo_only",
            "error": str(e)[:200]
        }


def run_all_tests():
    """Run all hybrid architecture tests."""
    print("=" * 70)
    print("HYBRID ARCHITECTURE TEST SUITE")
    print("=" * 70)
    print("\nTesting: Gemini primary + Tool-based fallback + DuckDuckGo")
    
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tests": {}
    }
    
    # Test 1: Gemini native
    results["tests"]["gemini_native"] = test_gemini_native_path()
    
    # Test 2: Fallback path
    results["tests"]["fallback_tool_based"] = test_fallback_path()
    
    # Test 3: DuckDuckGo only
    results["tests"]["duckduckgo_only"] = test_duckduckgo_only()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, result in results["tests"].items():
        status = result.get("status", "UNKNOWN")
        icon = "✓" if status == "SUCCESS" else "✗" if status == "FAILED" else "⚠"
        print(f"{icon} {test_name}: {status}")
    
    all_passed = all(r.get("status") == "SUCCESS" for r in results["tests"].values())
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED - Hybrid architecture working correctly")
    else:
        print("\n⚠ SOME TESTS FAILED - Review results above")
    
    # Save results
    filename = f"hybrid_test_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
