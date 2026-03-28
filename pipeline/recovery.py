"""Pipeline checkpoint recovery system for resuming interrupted pipelines."""

import json
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from checkpoint.manager import CheckpointManager, CheckpointType, CheckpointStatus

logger = logging.getLogger(__name__)


@dataclass
class PipelineState:
    """Serializable pipeline state for recovery."""
    pipeline_id: str
    query: str
    industry: Optional[str]
    region: Optional[str]
    theme: Optional[str]
    status: str
    current_agent: Optional[str]
    progress_percent: int
    events: List[Dict]
    vendors: List[Dict]
    completed_agents: List[str]
    pending_agents: List[str]
    context: Dict[str, Any]
    created_at: str
    updated_at: str


class PipelineRecoveryManager:
    """Manages pipeline checkpoint recovery and resumption."""
    
    def __init__(self, recovery_dir: str = ".checkpoints/pipeline_recovery"):
        self.recovery_dir = Path(recovery_dir)
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_mgr = CheckpointManager()
    
    def save_state(self, state: PipelineState) -> str:
        """Save pipeline state to disk.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Path to saved state file
        """
        state_file = self.recovery_dir / f"{state.pipeline_id}.json"
        state.updated_at = datetime.utcnow().isoformat()
        
        with open(state_file, 'w') as f:
            json.dump(asdict(state), f, indent=2)
        
        logger.info(f"Saved pipeline state: {state.pipeline_id}")
        return str(state_file)
    
    def load_state(self, pipeline_id: str) -> Optional[PipelineState]:
        """Load pipeline state from disk.
        
        Args:
            pipeline_id: Pipeline identifier
            
        Returns:
            PipelineState or None if not found
        """
        state_file = self.recovery_dir / f"{pipeline_id}.json"
        
        if not state_file.exists():
            return None
        
        with open(state_file, 'r') as f:
            data = json.load(f)
        
        return PipelineState(**data)
    
    def list_recoverable_pipelines(self, status: Optional[str] = None) -> List[Dict]:
        """List pipelines that can be resumed.
        
        Args:
            status: Filter by status (optional)
            
        Returns:
            List of pipeline summaries
        """
        pipelines = []
        
        for state_file in self.recovery_dir.glob("*.json"):
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)
                
                if status and data.get('status') != status:
                    continue
                
                pipelines.append({
                    'pipeline_id': data['pipeline_id'],
                    'query': data['query'],
                    'status': data['status'],
                    'current_agent': data.get('current_agent'),
                    'progress_percent': data.get('progress_percent', 0),
                    'updated_at': data.get('updated_at')
                })
            except Exception as e:
                logger.warning(f"Failed to load state file {state_file}: {e}")
        
        return sorted(pipelines, key=lambda x: x['updated_at'], reverse=True)
    
    def can_resume(self, pipeline_id: str) -> bool:
        """Check if a pipeline can be resumed.
        
        Args:
            pipeline_id: Pipeline identifier
            
        Returns:
            True if pipeline can be resumed
        """
        state = self.load_state(pipeline_id)
        if not state:
            return False
        
        return state.status in ['running', 'waiting_for_approval', 'paused']
    
    def mark_agent_complete(self, pipeline_id: str, agent_name: str, context: Dict):
        """Mark an agent as completed and update state.
        
        Args:
            pipeline_id: Pipeline identifier
            agent_name: Name of completed agent
            context: Current pipeline context
        """
        state = self.load_state(pipeline_id)
        if not state:
            logger.warning(f"Cannot mark agent complete - state not found: {pipeline_id}")
            return
        
        if agent_name not in state.completed_agents:
            state.completed_agents.append(agent_name)
        
        if agent_name in state.pending_agents:
            state.pending_agents.remove(agent_name)
        
        state.context.update(context)
        state.updated_at = datetime.utcnow().isoformat()
        
        self.save_state(state)
        logger.info(f"Marked agent complete: {agent_name} for pipeline: {pipeline_id}")
    
    def delete_state(self, pipeline_id: str):
        """Delete pipeline state after completion or failure.
        
        Args:
            pipeline_id: Pipeline identifier
        """
        state_file = self.recovery_dir / f"{pipeline_id}.json"
        
        if state_file.exists():
            state_file.unlink()
            logger.info(f"Deleted pipeline state: {pipeline_id}")
    
    def initialize_state(
        self,
        pipeline_id: str,
        query: str,
        industry: Optional[str] = None,
        region: Optional[str] = None,
        theme: Optional[str] = None,
        agent_sequence: List[str] = None
    ) -> PipelineState:
        """Initialize new pipeline state.
        
        Args:
            pipeline_id: Unique pipeline identifier
            query: Search query
            industry: Industry filter
            region: Region filter
            theme: Theme filter
            agent_sequence: Ordered list of agents to execute
            
        Returns:
            Initialized PipelineState
        """
        now = datetime.utcnow().isoformat()
        
        state = PipelineState(
            pipeline_id=pipeline_id,
            query=query,
            industry=industry,
            region=region,
            theme=theme,
            status='running',
            current_agent=None,
            progress_percent=0,
            events=[],
            vendors=[],
            completed_agents=[],
            pending_agents=agent_sequence or [],
            context={},
            created_at=now,
            updated_at=now
        )
        
        self.save_state(state)
        return state


# Global instance
_recovery_mgr: Optional[PipelineRecoveryManager] = None


def get_recovery_manager() -> PipelineRecoveryManager:
    """Get global recovery manager instance."""
    global _recovery_mgr
    if _recovery_mgr is None:
        _recovery_mgr = PipelineRecoveryManager()
    return _recovery_mgr