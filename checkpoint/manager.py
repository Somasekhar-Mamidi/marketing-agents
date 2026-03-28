"""Human-in-the-loop checkpoint system for pipeline approval."""

import json
import logging
from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class CheckpointStatus(Enum):
    """Status of a checkpoint."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class CheckpointType(Enum):
    """Types of checkpoints."""
    EVENT_REVIEW = "event_review"
    VENDOR_REVIEW = "vendor_review"
    EMAIL_REVIEW = "email_review"


@dataclass
class Checkpoint:
    """Represents a checkpoint in the pipeline."""
    id: str
    pipeline_id: str
    type: CheckpointType
    name: str
    status: CheckpointStatus
    data: Dict  # Events, vendors, or emails for review
    created_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'pipeline_id': self.pipeline_id,
            'type': self.type.value,
            'name': self.name,
            'status': self.status.value,
            'data': self.data,
            'created_at': self.created_at,
            'reviewed_at': self.reviewed_at,
            'reviewed_by': self.reviewed_by,
            'review_notes': self.review_notes
        }


class CheckpointManager:
    """Manages human-in-the-loop checkpoints."""
    
    def __init__(self, checkpoint_dir: str = ".checkpoints/human_review"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoints: Dict[str, Checkpoint] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
    
    def create_checkpoint(
        self,
        pipeline_id: str,
        checkpoint_type: CheckpointType,
        name: str,
        data: Dict
    ) -> Checkpoint:
        """Create a new checkpoint requiring human review.
        
        Args:
            pipeline_id: Unique pipeline identifier
            checkpoint_type: Type of checkpoint
            name: Human-readable name
            data: Data requiring review (events, vendors, or emails)
            
        Returns:
            Created checkpoint
        """
        checkpoint_id = f"{pipeline_id}_{checkpoint_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        checkpoint = Checkpoint(
            id=checkpoint_id,
            pipeline_id=pipeline_id,
            type=checkpoint_type,
            name=name,
            status=CheckpointStatus.PENDING,
            data=data,
            created_at=datetime.utcnow().isoformat()
        )
        
        self._checkpoints[checkpoint_id] = checkpoint
        self._save_checkpoint(checkpoint)
        
        logger.info(f"Created checkpoint: {checkpoint_id} ({name})")
        
        return checkpoint
    
    def _save_checkpoint(self, checkpoint: Checkpoint):
        """Save checkpoint to disk."""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint.id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint.to_dict(), f, indent=2)
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from disk."""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            return None
        
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        
        return Checkpoint(
            id=data['id'],
            pipeline_id=data['pipeline_id'],
            type=CheckpointType(data['type']),
            name=data['name'],
            status=CheckpointStatus(data['status']),
            data=data['data'],
            created_at=data['created_at'],
            reviewed_at=data.get('reviewed_at'),
            reviewed_by=data.get('reviewed_by'),
            review_notes=data.get('review_notes')
        )
    
    def approve_checkpoint(
        self,
        checkpoint_id: str,
        reviewed_by: str = "system",
        notes: str = ""
    ) -> Optional[Checkpoint]:
        """Approve a pending checkpoint.
        
        Args:
            checkpoint_id: Checkpoint identifier
            reviewed_by: Name of reviewer
            notes: Review notes
            
        Returns:
            Updated checkpoint or None if not found
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        if not checkpoint:
            checkpoint = self.load_checkpoint(checkpoint_id)
        
        if not checkpoint:
            logger.error(f"Checkpoint not found: {checkpoint_id}")
            return None
        
        checkpoint.status = CheckpointStatus.APPROVED
        checkpoint.reviewed_at = datetime.utcnow().isoformat()
        checkpoint.reviewed_by = reviewed_by
        checkpoint.review_notes = notes
        
        self._checkpoints[checkpoint_id] = checkpoint
        self._save_checkpoint(checkpoint)
        
        logger.info(f"Checkpoint approved: {checkpoint_id} by {reviewed_by}")
        
        # Trigger callbacks
        self._trigger_callbacks(checkpoint)
        
        return checkpoint
    
    def reject_checkpoint(
        self,
        checkpoint_id: str,
        reviewed_by: str = "system",
        notes: str = ""
    ) -> Optional[Checkpoint]:
        """Reject a checkpoint.
        
        Args:
            checkpoint_id: Checkpoint identifier
            reviewed_by: Name of reviewer
            notes: Rejection reason
            
        Returns:
            Updated checkpoint or None
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        if not checkpoint:
            checkpoint = self.load_checkpoint(checkpoint_id)
        
        if not checkpoint:
            return None
        
        checkpoint.status = CheckpointStatus.REJECTED
        checkpoint.reviewed_at = datetime.utcnow().isoformat()
        checkpoint.reviewed_by = reviewed_by
        checkpoint.review_notes = notes
        
        self._checkpoints[checkpoint_id] = checkpoint
        self._save_checkpoint(checkpoint)
        
        logger.info(f"Checkpoint rejected: {checkpoint_id} by {reviewed_by}")
        
        return checkpoint
    
    def is_checkpoint_pending(self, checkpoint_id: str) -> bool:
        """Check if a checkpoint is pending approval."""
        checkpoint = self._checkpoints.get(checkpoint_id)
        if not checkpoint:
            checkpoint = self.load_checkpoint(checkpoint_id)
        
        if checkpoint:
            return checkpoint.status == CheckpointStatus.PENDING
        return False
    
    def wait_for_approval(
        self,
        checkpoint_id: str,
        poll_interval: int = 5,
        timeout: int = 3600
    ) -> bool:
        """Wait for checkpoint approval (blocking).
        
        Args:
            checkpoint_id: Checkpoint to wait for
            poll_interval: Seconds between checks
            timeout: Maximum seconds to wait
            
        Returns:
            True if approved, False if rejected or timeout
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            checkpoint = self.load_checkpoint(checkpoint_id)
            
            if not checkpoint:
                logger.error(f"Checkpoint disappeared: {checkpoint_id}")
                return False
            
            if checkpoint.status == CheckpointStatus.APPROVED:
                return True
            elif checkpoint.status == CheckpointStatus.REJECTED:
                logger.warning(f"Checkpoint rejected: {checkpoint_id}")
                return False
            
            time.sleep(poll_interval)
        
        logger.warning(f"Checkpoint approval timeout: {checkpoint_id}")
        return False
    
    def on_approval(self, checkpoint_id: str, callback: Callable):
        """Register a callback for when checkpoint is approved."""
        if checkpoint_id not in self._callbacks:
            self._callbacks[checkpoint_id] = []
        self._callbacks[checkpoint_id].append(callback)
    
    def _trigger_callbacks(self, checkpoint: Checkpoint):
        """Trigger registered callbacks."""
        callbacks = self._callbacks.get(checkpoint.id, [])
        for callback in callbacks:
            try:
                callback(checkpoint)
            except Exception as e:
                logger.error(f"Callback error for {checkpoint.id}: {e}")
    
    def get_pending_checkpoints(self, pipeline_id: Optional[str] = None) -> List[Checkpoint]:
        """Get all pending checkpoints."""
        checkpoints = []
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                checkpoint = self.load_checkpoint(checkpoint_file.stem)
                if checkpoint and checkpoint.status == CheckpointStatus.PENDING:
                    if pipeline_id is None or checkpoint.pipeline_id == pipeline_id:
                        checkpoints.append(checkpoint)
            except Exception as e:
                logger.warning(f"Failed to load checkpoint {checkpoint_file}: {e}")
        
        return checkpoints
    
    def generate_review_summary(self, checkpoint_id: str) -> str:
        """Generate human-readable summary for review."""
        checkpoint = self.load_checkpoint(checkpoint_id)
        if not checkpoint:
            return "Checkpoint not found"
        
        summary = f"""
# Checkpoint Review: {checkpoint.name}

**Status:** {checkpoint.status.value}
**Created:** {checkpoint.created_at}
**Type:** {checkpoint.type.value}

## Data for Review

"""
        
        if checkpoint.type == CheckpointType.EVENT_REVIEW:
            events = checkpoint.data.get('events', [])
            summary += f"### Events ({len(events)} total)\n\n"
            for event in events[:10]:  # Show first 10
                summary += f"- **{event.get('event_name')}** ({event.get('priority_tier')})\n"
                summary += f"  - Score: {event.get('overall_score')}/10\n"
                summary += f"  - Location: {event.get('city')}, {event.get('country')}\n"
                summary += f"  - Website: {event.get('event_website')}\n\n"
            
            if len(events) > 10:
                summary += f"*... and {len(events) - 10} more events*\n"
        
        elif checkpoint.type == CheckpointType.VENDOR_REVIEW:
            vendors = checkpoint.data.get('vendors', [])
            summary += f"### Vendors ({len(vendors)} total)\n\n"
            for vendor in vendors[:10]:
                summary += f"- **{vendor.get('vendor_name')}** ({vendor.get('vendor_type')})\n"
                summary += f"  - Relevance: {vendor.get('relevance_score')}/100\n"
                summary += f"  - Event: {vendor.get('event_name', 'N/A')}\n\n"
        
        elif checkpoint.type == CheckpointType.EMAIL_REVIEW:
            emails = checkpoint.data.get('emails', [])
            summary += f"### Emails ({len(emails)} total)\n\n"
            for email in emails[:5]:
                summary += f"#### To: {email.get('recipient_name', 'Unknown')}\n"
                summary += f"**Subject:** {email.get('subject')}\n\n"
                summary += f"```\n{email.get('body', '')[:500]}...\n```\n\n"
        
        return summary


# Global checkpoint manager
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """Get global checkpoint manager."""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager


def require_approval(
    checkpoint_type: CheckpointType,
    name: str,
    pipeline_id: str,
    data: Dict,
    auto_approve: bool = False
) -> str:
    """Create a checkpoint and optionally wait for approval.
    
    Args:
        checkpoint_type: Type of checkpoint
        name: Checkpoint name
        pipeline_id: Pipeline identifier
        data: Data for review
        auto_approve: If True, auto-approve without human review
        
    Returns:
        Checkpoint ID
    """
    manager = get_checkpoint_manager()
    checkpoint = manager.create_checkpoint(pipeline_id, checkpoint_type, name, data)
    
    if auto_approve:
        manager.approve_checkpoint(checkpoint.id, reviewed_by="auto", notes="Auto-approved")
    
    return checkpoint.id
