"""Command-line interface for the marketing agents swarm."""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.orchestrator import Pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_pipeline() -> Pipeline:
    """Create and configure the pipeline with agents.
    
    Returns:
        Configured Pipeline instance
    """
    pipeline = Pipeline()
    
    # Import and add your agents here
    # from agents.example import YourAgent
    # pipeline.add_agent(YourAgent())
    
    return pipeline


def run_command(args):
    """Run the pipeline with a prompt."""
    pipeline = create_pipeline()
    
    if not pipeline.agents:
        logger.error("No agents configured. Add agents before running.")
        sys.exit(1)
    
    logger.info(f"Running with prompt: {args.prompt}")
    
    try:
        result = pipeline.execute(args.prompt)
        
        print("\n" + "=" * 60)
        print("PIPELINE RESULT")
        print("=" * 60)
        print(f"Agent: {result.agent_name}")
        print(f"Status: {result.status}")
        print(f"\nFindings:")
        print(result.findings)
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


def list_agents_command(args):
    """List all available agents."""
    pipeline = create_pipeline()
    
    print("\nAvailable Agents:")
    print("-" * 40)
    
    if not pipeline.agents:
        print("  (No agents configured)")
    else:
        for i, agent in enumerate(pipeline.agents, 1):
            print(f"  {i}. {agent.name}")
            print(f"     {agent.description}")
            print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Marketing Agents Swarm - Research pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # run command
    run_parser = subparsers.add_parser("run", help="Run the pipeline with a prompt")
    run_parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="The research prompt/query"
    )
    run_parser.set_defaults(func=run_command)
    
    # list-agents command
    list_parser = subparsers.add_parser("list-agents", help="List available agents")
    list_parser.set_defaults(func=list_agents_command)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
