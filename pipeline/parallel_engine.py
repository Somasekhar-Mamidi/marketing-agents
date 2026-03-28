"""Async pipeline orchestrator for concurrent agent execution."""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Represents an agent execution task."""
    agent: BaseAgent
    input_data: AgentInput
    dependencies: List[str]
    timeout: float = 300.0


@dataclass
class PipelineProgress:
    """Progress information for pipeline."""
    pipeline_id: str
    overall_progress: int
    agents: List[Dict[str, Any]]
    events_found: int
    vendors_found: int
    elapsed_time: str
    status: str


class ParallelPipelineEngine:
    """Engine for executing agents in parallel with dependency management."""
    
    def __init__(self, max_concurrent: int = 4):
        """Initialize parallel pipeline engine.
        
        Args:
            max_concurrent: Maximum number of agents to run simultaneously
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.agents: List[BaseAgent] = []
        self.results: Dict[str, AgentOutput] = {}
        self.progress_callbacks: List[Callable] = []
        self.logs: List[Dict] = []
        self.events_found = 0
        self.vendors_found = 0
        self.start_time: Optional[datetime] = None
        
    def add_agent(self, agent: BaseAgent) -> "ParallelPipelineEngine":
        """Add an agent to the pipeline.
        
        Args:
            agent: Agent instance to add
            
        Returns:
            Self for chaining
        """
        self.agents.append(agent)
        logger.info(f"Added agent: {agent.name}")
        return self
    
    def on_progress(self, callback: Callable) -> "ParallelPipelineEngine":
        """Register progress callback.
        
        Args:
            callback: Function to call with progress updates
            
        Returns:
            Self for chaining
        """
        self.progress_callbacks.append(callback)
        return self
    
    def _emit_progress(self, pipeline_id: str):
        """Emit progress to all callbacks."""
        progress = self._get_progress(pipeline_id)
        for callback in self.progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def _get_progress(self, pipeline_id: str) -> PipelineProgress:
        """Get current pipeline progress."""
        elapsed = "0:00"
        if self.start_time:
            delta = datetime.utcnow() - self.start_time
            elapsed = f"{delta.seconds // 60}:{delta.seconds % 60:02d}"
        
        total_progress = sum(
            self.results.get(agent.name, AgentOutput(agent_name=agent.name, findings={}, metadata={})).metadata.get("progress", 0)
            for agent in self.agents
        ) / max(len(self.agents), 1)
        
        return PipelineProgress(
            pipeline_id=pipeline_id,
            overall_progress=int(total_progress),
            agents=[
                {
                    "name": agent.name,
                    "status": "completed" if agent.name in self.results else "pending",
                    "progress": self.results.get(agent.name, AgentOutput(agent_name=agent.name, findings={}, metadata={})).metadata.get("progress", 0),
                }
                for agent in self.agents
            ],
            events_found=self.events_found,
            vendors_found=self.vendors_found,
            elapsed_time=elapsed,
            status="running" if len(self.results) < len(self.agents) else "completed"
        )
    
    async def _execute_agent_with_semaphore(
        self,
        agent: BaseAgent,
        input_data: AgentInput,
        pipeline_id: str
    ) -> AgentOutput:
        """Execute agent with concurrency control.
        
        Args:
            agent: Agent to execute
            input_data: Input data
            pipeline_id: Pipeline identifier
            
        Returns:
            Agent output
        """
        async with self.semaphore:
            logger.info(f"Starting agent: {agent.name}")
            self._emit_progress(pipeline_id)
            
            try:
                # Run agent in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                output = await loop.run_in_executor(
                    None,
                    agent.execute,
                    input_data
                )
                
                # Update counts
                findings = output.findings
                if "events" in findings:
                    self.events_found += len(findings["events"])
                if "vendors" in findings:
                    self.vendors_found += len(findings["vendors"])
                
                logger.info(f"Completed agent: {agent.name}")
                self._emit_progress(pipeline_id)
                return output
                
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")
                return AgentOutput(
                    agent_name=agent.name,
                    findings={"error": str(e), "events": []},
                    metadata={"agent": agent.name, "error": True, "progress": 0}
                )
    
    async def execute(self, pipeline_id: str, initial_query: str, initial_context: Optional[Dict] = None) -> Dict[str, AgentOutput]:
        """Execute pipeline with parallel agent execution.
        
        Args:
            pipeline_id: Unique pipeline identifier
            initial_query: Initial search query
            initial_context: Optional initial context
            
        Returns:
            Dictionary of agent name to output
        """
        if not self.agents:
            raise ValueError("No agents in pipeline")
        
        self.start_time = datetime.utcnow()
        context = initial_context.copy() if initial_context else {}
        
        logger.info(f"Starting pipeline {pipeline_id} with {len(self.agents)} agents")
        
        # Execute agents sequentially for now (can be made parallel with DAG)
        # TODO: Implement DAG-based parallel execution
        for idx, agent in enumerate(self.agents):
            input_data = AgentInput(
                query=initial_query if idx == 0 else f"Processing from {self.agents[idx-1].name}",
                context=context,
                parameters=context.get("parameters", {})
            )
            
            output = await self._execute_agent_with_semaphore(agent, input_data, pipeline_id)
            self.results[agent.name] = output
            
            # Update context for next agents
            findings = output.findings
            if "events" in findings:
                context["events"] = findings["events"]
            context[agent.name] = findings
        
        logger.info(f"Pipeline {pipeline_id} completed")
        self._emit_progress(pipeline_id)
        return self.results
    
    def get_final_output(self) -> Optional[AgentOutput]:
        """Get output from last successful agent."""
        if not self.results:
            return None
        
        for agent in reversed(self.agents):
            if agent.name in self.results:
                return self.results[agent.name]
        
        return None


# Global engine instance
_engine: Optional[ParallelPipelineEngine] = None


def get_parallel_engine(max_concurrent: int = 4) -> ParallelPipelineEngine:
    """Get or create global parallel engine instance.
    
    Args:
        max_concurrent: Maximum concurrent agents
        
    Returns:
        ParallelPipelineEngine instance
    """
    global _engine
    if _engine is None:
        _engine = ParallelPipelineEngine(max_concurrent=max_concurrent)
    return _engine
