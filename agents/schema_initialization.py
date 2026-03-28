"""Schema Initialization Agent - Agent 0 in the pipeline.

This agent initializes the workflow with a standard JSON schema.
It creates an empty event data structure and ensures downstream agents
receive valid input, preventing undefined data errors.
"""

import logging
from agents.base import BaseAgent, AgentInput, AgentOutput
from schema import get_empty_schema, EVENT_SCHEMA

logger = logging.getLogger(__name__)


class SchemaInitializationAgent(BaseAgent):
    """Initializes the pipeline with a standard JSON schema.
    
    This is Agent 0 - the first agent in the pipeline.
    It creates the empty event data structure that all other agents
    will populate as they execute their tasks.
    
    Responsibilities:
    - Create empty event data structure
    - Ensure downstream agents receive valid input
    - Prevent undefined data errors
    
    Input:
        None - this is the first agent in the pipeline
    
    Output:
        {"events": []} - empty events array with full schema structure
    """
    
    name = "schema_initialization"
    description = "Initializes the workflow with a standard JSON schema"
    
    def __init__(self) -> None:
        """Initialize the schema initialization agent."""
        self.schema = get_empty_schema()
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute the schema initialization.
        
        Creates an empty event data structure for the pipeline.
        
        Args:
            input_data: Input data (query, context, parameters)
            
        Returns:
            AgentOutput with empty events array
        """
        self.validate_input(input_data)
        
        logger.info("Schema Initialization Agent: Creating empty event schema")
        
        # Get parameters from input
        params = input_data.parameters
        industry = params.get("industry", "")
        region = params.get("region", "")
        theme = params.get("theme", "")
        time_range = params.get("time_range", "12")
        
        # Create the empty schema with metadata
        findings = {
            "events": [],
            "metadata": {
                "initialized": True,
                "industry": industry,
                "region": region,
                "theme": theme,
                "time_range_months": time_range,
                "schema_version": "1.0"
            }
        }
        
        logger.info(f"Schema initialized with params: industry={industry}, region={region}, "
                   f"theme={theme}, time_range={time_range} months")
        
        return AgentOutput(
            agent_name=self.name,
            findings=findings,
            metadata={
                "agent": self.name,
                "schema_fields": list(EVENT_SCHEMA.get("events", [{}])[0].keys()) if EVENT_SCHEMA.get("events") else [],
                "initialized": True
            },
            status="success"
        )
    
    def validate_input(self, input_data: AgentInput) -> bool:
        """Validate input before execution.
        
        Schema initialization doesn't require any specific input,
        so this always returns True.
        
        Args:
            input_data: The input to validate
            
        Returns:
            True always - no validation needed for schema init
        """
        return True
