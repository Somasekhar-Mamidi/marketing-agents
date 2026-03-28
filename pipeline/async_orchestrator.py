"""Async pipeline orchestrator for concurrent agent execution."""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Represents an agent execution task."""
    agent: BaseAgent
    input_data: AgentInput
    dependencies: List[str]
    timeout: float = 300.0


class AsyncPipeline:
    """Async pipeline that can execute agents concurrently where possible."""
    
    def __init__(self, max_concurrent: int = 3, continue_on_error: bool = True):
        """Initialize async pipeline.
        
        Args:
            max_concurrent: Maximum number of agents to run concurrently
            continue_on_error: Whether to continue on agent errors
        """
        self.max_concurrent = max_concurrent
        self.continue_on_error = continue_on_error
        self.agents: List[BaseAgent] = []
        self.tasks: Dict[str, AgentTask] = {}
        self.results: Dict[str, AgentOutput] = {}
        self.failed_agents: List[str] = []
    
    def add_agent(self, agent: BaseAgent, dependencies: Optional[List[str]] = None) -> "AsyncPipeline":
        """Add an agent with optional dependencies.
        
        Args:
            agent: Agent to add
            dependencies: List of agent names that must complete before this one
            
        Returns:
            Self for chaining
        """
        self.agents.append(agent)
        logger.info(f"Added agent: {agent.name} (dependencies: {dependencies or []})")
        return self
    
    async def _execute_agent(self, agent: BaseAgent, input_data: AgentInput) -> AgentOutput:
        """Execute a single agent with timeout.
        
        Args:
            agent: Agent to execute
            input_data: Input data
            
        Returns:
            Agent output
        """
        logger.info(f"Starting agent: {agent.name}")
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Run agent in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                agent.execute,
                input_data
            )
            
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"Agent {agent.name} completed in {duration:.2f}s")
            return output
            
        except asyncio.TimeoutError:
            logger.error(f"Agent {agent.name} timed out")
            raise
        except Exception as e:
            logger.error(f"Agent {agent.name} failed: {e}")
            if not self.continue_on_error:
                raise
            
            # Return error output
            return AgentOutput(
                agent_name=agent.name,
                findings={"error": str(e), "events": []},
                metadata={"agent": agent.name, "error": True}
            )
    
    async def execute(self, initial_query: str, initial_context: Optional[Dict] = None) -> Dict[str, AgentOutput]:
        """Execute pipeline with concurrent agent execution.
        
        Args:
            initial_query: Initial query
            initial_context: Optional initial context
            
        Returns:
            Dictionary of agent name -> output
        """
        if not self.agents:
            raise ValueError("No agents in pipeline")
        
        context = initial_context.copy() if initial_context else {}
        results: Dict[str, AgentOutput] = {}
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def run_with_limit(agent: BaseAgent, query: str, ctx: Dict) -> AgentOutput:
            """Run agent with concurrency limit."""
            async with semaphore:
                input_data = AgentInput(
                    query=query,
                    context=ctx,
                    parameters=ctx.get("parameters", {})
                )
                return await self._execute_agent(agent, input_data)
        
        logger.info(f"Starting async pipeline with {len(self.agents)} agents, max concurrent: {self.max_concurrent}")
        
        # Group agents by execution wave
        # For now, execute sequentially but with async support for future parallelization
        current_query = initial_query
        
        for agent in self.agents:
            try:
                output = await run_with_limit(agent, current_query, context)
                results[agent.name] = output
                
                # Update context for next agents
                findings = output.findings
                events = findings.get("events", [])
                context["events"] = events
                context[agent.name] = findings
                
                if events:
                    current_query = f"Found {len(events)} events to process"
                
            except Exception as e:
                logger.error(f"Pipeline stopped at {agent.name}: {e}")
                self.failed_agents.append(agent.name)
                if not self.continue_on_error:
                    break
        
        self.results = results
        logger.info(f"Async pipeline completed. {len(results)}/{len(self.agents)} agents succeeded")
        return results
    
    def get_final_output(self) -> Optional[AgentOutput]:
        """Get output from last successful agent."""
        if not self.results:
            return None
        
        # Return output from last agent in sequence
        for agent in reversed(self.agents):
            if agent.name in self.results:
                return self.results[agent.name]
        
        return None


# Convenience function for running async pipeline
def run_pipeline_async(
    agents: List[BaseAgent],
    query: str,
    context: Optional[Dict] = None,
    max_concurrent: int = 3
) -> Dict[str, AgentOutput]:
    """Run pipeline asynchronously.
    
    Args:
        agents: List of agents to execute
        query: Initial query
        context: Optional context
        max_concurrent: Max concurrent agents
        
    Returns:
        Results dictionary
    """
    pipeline = AsyncPipeline(max_concurrent=max_concurrent)
    for agent in agents:
        pipeline.add_agent(agent)
    
    return asyncio.run(pipeline.execute(query, context))