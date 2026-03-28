"""Pipeline orchestrator for sequential agent execution with error handling."""

import logging
from typing import Optional
from agents.base import BaseAgent, AgentInput, AgentOutput
from config.loader import load_pipeline_config
from utils.error_handler import ErrorHandler, ErrorSeverity

logger = logging.getLogger(__name__)


class Pipeline:
    """Sequential pipeline that executes agents one after another with graceful error handling.
    
    Each agent receives input and context from previous agents,
    passing its results to the next agent in the chain.
    """
    
    def __init__(self, config_path: Optional[str] = None, continue_on_error: bool = True):
        """Initialize the pipeline.
        
        Args:
            config_path: Optional path to pipeline configuration file
            continue_on_error: Whether to continue pipeline execution on agent errors
        """
        self.config = load_pipeline_config(config_path)
        self.agents: list[BaseAgent] = []
        self.execution_history: list[AgentOutput] = []
        self.error_handler = ErrorHandler(continue_on_error=continue_on_error)
        self.failed_agents: list[str] = []
    
    def add_agent(self, agent: BaseAgent) -> "Pipeline":
        """Add an agent to the pipeline.
        
        Args:
            agent: The agent to add
            
        Returns:
            Self for chaining
        """
        self.agents.append(agent)
        logger.info(f"Added agent: {agent.name}")
        return self
    
    def execute(self, initial_query: str, initial_context: Optional[dict] = None) -> AgentOutput:
        """Execute the pipeline with an initial query.
        
        Args:
            initial_query: The research query to start with
            initial_context: Optional initial context (can include 'parameters' dict)
            
        Returns:
            Final AgentOutput from the last successful agent
        """
        if not self.agents:
            raise ValueError("Pipeline has no agents. Add agents before executing.")
        
        context = initial_context.copy() if initial_context else {}
        current_query = initial_query
        last_successful_output: Optional[AgentOutput] = None
        
        initial_params = context.pop("parameters", {})
        
        logger.info(f"Starting pipeline with query: {initial_query}")
        
        for i, agent in enumerate(self.agents):
            logger.info(f"Executing agent {i+1}/{len(self.agents)}: {agent.name}")
            
            agent_config_params = self.config.get("agents", {}).get(agent.name, {}).get("parameters", {})
            params = {**initial_params, **agent_config_params}
            
            input_data = AgentInput(
                query=current_query,
                context=context,
                parameters=params
            )
            
            try:
                agent.validate_input(input_data)
                output = agent.execute(input_data)
                
                findings = output.findings
                events = findings.get("events", [])
                
                context["events"] = events
                context[agent.name] = findings
                
                if events:
                    current_query = f"Found {len(events)} events to process"
                else:
                    current_query = str(findings)
                
                self.execution_history.append(output)
                last_successful_output = output
                logger.info(f"Agent {agent.name} completed successfully")
                
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")
                self.failed_agents.append(agent.name)
                
                partial_results = getattr(agent, 'partial_results', None)
                
                severity = ErrorSeverity.ERROR
                if isinstance(e, (ValueError, TypeError)):
                    severity = ErrorSeverity.WARNING
                elif isinstance(e, (MemoryError, SystemError)):
                    severity = ErrorSeverity.CRITICAL
                
                self.error_handler.handle_error(
                    agent_name=agent.name,
                    error=e,
                    partial_results=partial_results,
                    severity=severity
                )
                
                if severity == ErrorSeverity.CRITICAL:
                    logger.error(f"Critical error in {agent.name}, stopping pipeline")
                    break
                
                if not self.error_handler.continue_on_error:
                    raise
        
        if last_successful_output:
            logger.info(f"Pipeline completed. Final output from: {last_successful_output.agent_name}")
            
            if self.failed_agents:
                last_successful_output.metadata["failed_agents"] = self.failed_agents
                last_successful_output.metadata["error_summary"] = self.error_handler.get_summary()
            
            return last_successful_output
        else:
            raise RuntimeError("Pipeline failed - no agents completed successfully")
    
    def get_history(self) -> list[AgentOutput]:
        """Get the execution history of all agents."""
        return self.execution_history
    
    def get_errors(self) -> list:
        """Get all errors that occurred during pipeline execution."""
        return self.error_handler.get_errors()
    
    def clear(self) -> None:
        """Clear the execution history and errors."""
        self.execution_history.clear()
        self.failed_agents.clear()
        self.error_handler.errors.clear()
        logger.info("Pipeline history and errors cleared")
