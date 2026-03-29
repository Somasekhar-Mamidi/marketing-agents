"""Proof of Concept: Tool-Based Search vs Manual Search

This script compares two approaches for event discovery:
1. OLD: Manual search with pre-defined queries + separate LLM parsing
2. NEW: LLM-driven tool calling (LLM decides when/what to search)
"""

import os
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from utils.search import WebSearchTool
from utils.tools import get_tool_registry, get_research_tools


class ManualSearchApproach:
    """OLD: Manual search with pre-defined queries."""
    
    def __init__(self):
        self.search_tool = WebSearchTool(provider="duckduckgo")
    
    def discover_events(self, industry: str, region: str = "") -> dict:
        """Discover events using pre-defined queries."""
        start_time = time.time()
        
        # Pre-defined queries (fixed, not dynamic)
        queries = [
            f"{industry} conferences 2025",
            f"{industry} summit {region} 2025" if region else f"{industry} summit 2025",
            f"{industry} expo 2025",
            f"{industry} forum 2026",
            f"{industry} events {region}" if region else f"{industry} events",
        ]
        
        all_results = []
        for query in queries:
            results = self.search_tool.search(query, max_results=5)
            all_results.extend(results)
        
        elapsed = time.time() - start_time
        
        return {
            "approach": "Manual (Pre-defined Queries)",
            "queries_made": len(queries),
            "total_results": len(all_results),
            "elapsed_seconds": round(elapsed, 2),
            "results": [{"title": r.get("title"), "url": r.get("url")} for r in all_results[:5]]
        }


class ToolBasedApproach:
    """NEW: LLM-driven tool calling."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://grid.ai.juspay.net",
            api_key=api_key
        )
        self.tool_registry = get_tool_registry()
        self.model = "glm-latest"  # Test with a fast model
    
    def discover_events_with_tools(self, industry: str, region: str = "") -> dict:
        """Discover events using LLM-driven tool calling."""
        start_time = time.time()
        
        tools = get_research_tools()
        
        system_prompt = """You are an event discovery assistant. You have access to web search.
When the user asks for events, use the web_search tool to find current information.
Be specific in your search queries - include year, industry, and location.
After searching, synthesize the results into a clear answer."""
        
        user_prompt = f"Find {industry} conferences and events"
        if region:
            user_prompt += f" in {region}"
        user_prompt += " for 2025-2026."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        tool_calls_count = 0
        max_iterations = 5
        
        for iteration in range(max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=1000,
                timeout=60
            )
            
            message = response.choices[0].message
            
            # Check if done
            if not message.tool_calls:
                elapsed = time.time() - start_time
                return {
                    "approach": "Tool-Based (LLM-Driven)",
                    "model": self.model,
                    "tool_calls_made": tool_calls_count,
                    "iterations": iteration + 1,
                    "elapsed_seconds": round(elapsed, 2),
                    "final_answer": message.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens
                    }
                }
            
            # Model wants to call tools
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })
            
            # Execute tool calls
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                
                result = self.tool_registry.execute(tool_name, args)
                tool_calls_count += 1
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        
        elapsed = time.time() - start_time
        return {
            "approach": "Tool-Based (LLM-Driven)",
            "model": self.model,
            "tool_calls_made": tool_calls_count,
            "iterations": max_iterations,
            "elapsed_seconds": round(elapsed, 2),
            "final_answer": "Max iterations reached",
            "incomplete": True
        }


def run_comparison():
    """Run side-by-side comparison."""
    
    api_key = os.environ.get("GRID_AI_API_KEY")
    if not api_key:
        print("❌ GRID_AI_API_KEY not set")
        return
    
    print("=" * 80)
    print("PROOF OF CONCEPT: Manual vs Tool-Based Search")
    print("=" * 80)
    print()
    print("Test Query: Find payment conferences in Europe for 2025")
    print()
    
    # Test 1: Manual approach
    print("-" * 80)
    print("🔄 APPROACH 1: Manual Search (Pre-defined Queries)")
    print("-" * 80)
    
    manual = ManualSearchApproach()
    manual_result = manual.discover_events("payments", "Europe")
    
    print(f"Approach: {manual_result['approach']}")
    print(f"Queries Made: {manual_result['queries_made']}")
    print(f"Results Found: {manual_result['total_results']}")
    print(f"Time: {manual_result['elapsed_seconds']}s")
    print()
    print("Sample Results:")
    for r in manual_result['results'][:3]:
        print(f"  • {r['title'][:60]}...")
    
    # Test 2: Tool-based approach
    print()
    print("-" * 80)
    print("🔄 APPROACH 2: Tool-Based (LLM-Driven)")
    print("-" * 80)
    
    tool_based = ToolBasedApproach(api_key)
    tool_result = tool_based.discover_events_with_tools("payment", "Europe")
    
    print(f"Approach: {tool_result['approach']}")
    print(f"Model: {tool_result['model']}")
    print(f"Tool Calls Made: {tool_result['tool_calls_made']}")
    print(f"Iterations: {tool_result['iterations']}")
    print(f"Time: {tool_result['elapsed_seconds']}s")
    if 'usage' in tool_result:
        print(f"Tokens: {tool_result['usage']['prompt_tokens']} in / {tool_result['usage']['completion_tokens']} out")
    print()
    print("LLM Response (first 500 chars):")
    print(tool_result['final_answer'][:500] if tool_result['final_answer'] else "No answer")
    
    # Comparison summary
    print()
    print("=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print()
    
    print(f"{'Metric':<30} {'Manual':<20} {'Tool-Based':<20}")
    print("-" * 70)
    print(f"{'Time (seconds)':<30} {manual_result['elapsed_seconds']:<20} {tool_result['elapsed_seconds']:<20}")
    print(f"{'Search Operations':<30} {manual_result['queries_made']:<20} {tool_result['tool_calls_made']:<20}")
    print(f"{'Results Quality':<30} {'Raw list':<20} {'Synthesized':<20}")
    print(f"{'Query Strategy':<30} {'Fixed':<20} {'Dynamic':<20}")
    
    print()
    print("Key Differences:")
    print("  • Manual: Pre-defined queries, all executed regardless of relevance")
    print("  • Tool-Based: LLM decides what to search based on initial results")
    print("  • Manual: Returns raw search results")
    print("  • Tool-Based: Returns synthesized answer with reasoning")
    
    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "query": "payment conferences Europe 2025",
        "manual_approach": manual_result,
        "tool_based_approach": tool_result
    }
    
    filename = f"search_comparison_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print(f"💾 Full results saved to: {filename}")


if __name__ == "__main__":
    run_comparison()
