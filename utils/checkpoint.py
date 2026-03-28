"""Checkpointing for pipeline state persistence and recovery."""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Checkpoint:
    """Represents a pipeline checkpoint."""
    pipeline_id: str
    agent_index: int
    events: list
    context: dict
    timestamp: datetime
    metadata: dict


class CheckpointManager:
    """Manages pipeline checkpoints for recovery."""
    
    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(
        self,
        pipeline_id: str,
        agent_index: int,
        events: list,
        context: dict,
        metadata: Optional[dict] = None
    ) -> Path:
        """Save a checkpoint of current pipeline state.
        
        Args:
            pipeline_id: Unique identifier for the pipeline run
            agent_index: Index of the last completed agent
            events: Current list of events
            context: Current pipeline context
            metadata: Optional additional metadata
            
        Returns:
            Path to the saved checkpoint file
        """
        checkpoint = {
            "pipeline_id": pipeline_id,
            "agent_index": agent_index,
            "events": events,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        checkpoint_path = self.checkpoint_dir / f"{pipeline_id}.json"
        
        try:
            with open(checkpoint_path, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.info(f"Checkpoint saved: {checkpoint_path}")
            return checkpoint_path
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise
    
    def load_checkpoint(self, pipeline_id: str) -> Optional[Checkpoint]:
        """Load a checkpoint by pipeline ID.
        
        Args:
            pipeline_id: Pipeline identifier
            
        Returns:
            Checkpoint object or None if not found
        """
        checkpoint_path = self.checkpoint_dir / f"{pipeline_id}.json"
        
        if not checkpoint_path.exists():
            return None
        
        try:
            with open(checkpoint_path, 'r') as f:
                data = json.load(f)
            
            return Checkpoint(
                pipeline_id=data["pipeline_id"],
                agent_index=data["agent_index"],
                events=data["events"],
                context=data["context"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def list_checkpoints(self) -> list:
        """List all available checkpoints.
        
        Returns:
            List of checkpoint metadata dictionaries
        """
        checkpoints = []
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                
                checkpoints.append({
                    "pipeline_id": data["pipeline_id"],
                    "agent_index": data["agent_index"],
                    "timestamp": data["timestamp"],
                    "event_count": len(data.get("events", [])),
                    "file": str(checkpoint_file)
                })
            except Exception as e:
                logger.warning(f"Failed to read checkpoint {checkpoint_file}: {e}")
        
        return sorted(checkpoints, key=lambda x: x["timestamp"], reverse=True)
    
    def delete_checkpoint(self, pipeline_id: str) -> bool:
        """Delete a checkpoint.
        
        Args:
            pipeline_id: Pipeline identifier
            
        Returns:
            True if deleted, False if not found
        """
        checkpoint_path = self.checkpoint_dir / f"{pipeline_id}.json"
        
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            logger.info(f"Checkpoint deleted: {checkpoint_path}")
            return True
        
        return False
    
    def cleanup_old_checkpoints(self, max_age_days: int = 7) -> int:
        """Delete checkpoints older than specified days.
        
        Args:
            max_age_days: Maximum age in days
            
        Returns:
            Number of checkpoints deleted
        """
        from datetime import timedelta
        
        deleted = 0
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(checkpoint_file.stat().st_mtime)
                if mtime < cutoff:
                    checkpoint_file.unlink()
                    deleted += 1
            except Exception as e:
                logger.warning(f"Failed to cleanup {checkpoint_file}: {e}")
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old checkpoints")
        
        return deleted


# Global checkpoint manager instance
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """Get global checkpoint manager instance."""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager


class CheckpointContext:
    """Context manager for automatic checkpointing.
    
    Usage:
        with CheckpointContext("pipeline_123", events, context) as cp:
            # After each agent, checkpoint is saved automatically
            result = agent.execute(input_data)
    """
    
    def __init__(
        self,
        pipeline_id: str,
        events: list,
        context: dict,
        agent_index: int = 0
    ):
        self.pipeline_id = pipeline_id
        self.events = events
        self.context = context
        self.agent_index = agent_index
        self.manager = get_checkpoint_manager()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Always save checkpoint on exit
        self.manager.save_checkpoint(
            pipeline_id=self.pipeline_id,
            agent_index=self.agent_index,
            events=self.events,
            context=self.context
        )
    
    def update(self, agent_index: int, events: list, context: dict):
        """Update checkpoint after agent completion."""
        self.agent_index = agent_index
        self.events = events
        self.context = context
        
        self.manager.save_checkpoint(
            pipeline_id=self.pipeline_id,
            agent_index=agent_index,
            events=events,
            context=context
        )


def resume_from_checkpoint(pipeline_id: str) -> Optional[Checkpoint]:
    """Resume pipeline from a checkpoint.
    
    Args:
        pipeline_id: Pipeline identifier
        
    Returns:
        Checkpoint or None if not found
    """
    manager = get_checkpoint_manager()
    checkpoint = manager.load_checkpoint(pipeline_id)
    
    if checkpoint:
        logger.info(
            f"Resuming pipeline {pipeline_id} from agent {checkpoint.agent_index}"
        )
    
    return checkpoint
