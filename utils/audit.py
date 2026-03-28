"""Audit trail logging for tracking decisions and changes."""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Types of audit actions."""
    EVENT_DISCOVERED = "event_discovered"
    EVENT_QUALIFIED = "event_qualified"
    EVENT_DEDUPLICATED = "event_deduplicated"
    EVENT_FILTERED = "event_filtered"
    EVENT_SCRAPED = "event_scraped"
    SCORE_ASSIGNED = "score_assigned"
    TIER_ASSIGNED = "tier_assigned"
    RECOMMENDATION_MADE = "recommendation_made"
    EMAIL_GENERATED = "email_generated"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    API_CALLED = "api_called"


@dataclass
class AuditEntry:
    """Single audit trail entry."""
    timestamp: str
    action: str
    agent: str
    event_id: Optional[str]
    details: Dict[str, Any]
    correlation_id: Optional[str] = None


class AuditLogger:
    """Logger for audit trail."""
    
    def __init__(self, log_dir: str = ".audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current log file based on date
        self.current_date = datetime.utcnow().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"audit_{self.current_date}.jsonl"
    
    def _get_current_log_file(self) -> Path:
        """Get current log file, rotating if date changed."""
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        if current_date != self.current_date:
            self.current_date = current_date
            self.log_file = self.log_dir / f"audit_{current_date}.jsonl"
        return self.log_file
    
    def log(
        self,
        action: AuditAction,
        agent: str,
        event_id: Optional[str] = None,
        details: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ):
        """Log an audit entry.
        
        Args:
            action: Type of action
            agent: Name of the agent
            event_id: Optional event identifier
            details: Optional additional details
            correlation_id: Optional correlation ID
        """
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            action=action.value,
            agent=agent,
            event_id=event_id,
            details=details or {},
            correlation_id=correlation_id
        )
        
        log_file = self._get_current_log_file()
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(asdict(entry)) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def log_event_decision(
        self,
        agent: str,
        event_id: str,
        decision: str,
        reason: str,
        previous_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        correlation_id: Optional[str] = None
    ):
        """Log a decision made about an event.
        
        Args:
            agent: Agent making the decision
            event_id: Event identifier
            decision: Type of decision
            reason: Reason for the decision
            previous_value: Previous value (if changed)
            new_value: New value (if changed)
            correlation_id: Optional correlation ID
        """
        self.log(
            action=AuditAction(decision) if decision in [a.value for a in AuditAction] else AuditAction.EVENT_FILTERED,
            agent=agent,
            event_id=event_id,
            details={
                "reason": reason,
                "previous_value": previous_value,
                "new_value": new_value
            },
            correlation_id=correlation_id
        )
    
    def log_agent_execution(
        self,
        agent: str,
        success: bool,
        duration_ms: float,
        events_processed: int,
        correlation_id: Optional[str] = None
    ):
        """Log agent execution.
        
        Args:
            agent: Agent name
            success: Whether execution succeeded
            duration_ms: Execution duration in milliseconds
            events_processed: Number of events processed
            correlation_id: Optional correlation ID
        """
        action = AuditAction.AGENT_COMPLETED if success else AuditAction.AGENT_FAILED
        
        self.log(
            action=action,
            agent=agent,
            details={
                "duration_ms": duration_ms,
                "events_processed": events_processed,
                "success": success
            },
            correlation_id=correlation_id
        )
    
    def log_cache_operation(
        self,
        cache_type: str,
        key: str,
        hit: bool,
        correlation_id: Optional[str] = None
    ):
        """Log cache operation.
        
        Args:
            cache_type: Type of cache
            key: Cache key
            hit: Whether it was a cache hit
            correlation_id: Optional correlation ID
        """
        action = AuditAction.CACHE_HIT if hit else AuditAction.CACHE_MISS
        
        self.log(
            action=action,
            agent="cache",
            details={
                "cache_type": cache_type,
                "key": key[:50]  # Truncate long keys
            },
            correlation_id=correlation_id
        )
    
    def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        agent: Optional[str] = None,
        event_id: Optional[str] = None,
        action: Optional[AuditAction] = None
    ) -> list:
        """Query audit log entries.
        
        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            agent: Filter by agent
            event_id: Filter by event ID
            action: Filter by action type
            
        Returns:
            List of matching audit entries
        """
        results = []
        
        for log_file in self.log_dir.glob("audit_*.jsonl"):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        
                        if start_time and entry_time < start_time:
                            continue
                        if end_time and entry_time > end_time:
                            continue
                        if agent and entry["agent"] != agent:
                            continue
                        if event_id and entry["event_id"] != event_id:
                            continue
                        if action and entry["action"] != action.value:
                            continue
                        
                        results.append(entry)
            except Exception as e:
                logger.warning(f"Failed to read {log_file}: {e}")
        
        return sorted(results, key=lambda x: x["timestamp"])
    
    def get_event_history(self, event_id: str) -> list:
        """Get complete audit history for an event.
        
        Args:
            event_id: Event identifier
            
        Returns:
            List of audit entries for the event
        """
        return self.query(event_id=event_id)
    
    def get_summary(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> dict:
        """Get summary of audit log activity.
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            Summary dictionary
        """
        entries = self.query(start_time=start_time, end_time=end_time)
        
        action_counts = {}
        agent_counts = {}
        
        for entry in entries:
            action = entry["action"]
            agent = entry["agent"]
            
            action_counts[action] = action_counts.get(action, 0) + 1
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        return {
            "total_entries": len(entries),
            "action_breakdown": action_counts,
            "agent_breakdown": agent_counts,
            "date_range": {
                "start": entries[0]["timestamp"] if entries else None,
                "end": entries[-1]["timestamp"] if entries else None
            }
        }


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_audit(
    action: AuditAction,
    agent: str,
    event_id: Optional[str] = None,
    details: Optional[Dict] = None
):
    """Convenience function to log an audit entry."""
    get_audit_logger().log(action, agent, event_id, details)
