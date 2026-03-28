"""Tests for pipeline recovery system."""

import pytest
import os
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from pipeline.recovery import (
    PipelineState, PipelineRecoveryManager,
    get_recovery_manager, _recovery_mgr
)


@pytest.fixture
def recovery_manager(tmp_path):
    """Create a recovery manager with temp directory."""
    return PipelineRecoveryManager(recovery_dir=str(tmp_path / "recovery"))


class TestPipelineState:
    """Test suite for PipelineState."""
    
    def test_state_creation(self):
        """Test creating a PipelineState."""
        state = PipelineState(
            pipeline_id="test-123",
            query="fintech events",
            industry="fintech",
            region="USA",
            theme="payments",
            status="running",
            current_agent="event_discovery",
            progress_percent=25,
            events=[{"event_name": "Test Event"}],
            vendors=[],
            completed_agents=["schema_init"],
            pending_agents=["event_discovery", "qualification"],
            context={"key": "value"},
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        assert state.pipeline_id == "test-123"
        assert state.query == "fintech events"
        assert len(state.completed_agents) == 1


class TestPipelineRecoveryManager:
    """Test suite for PipelineRecoveryManager."""
    
    def test_save_and_load_state(self, recovery_manager):
        """Test saving and loading pipeline state."""
        state = PipelineState(
            pipeline_id="test-save",
            query="test query",
            industry=None,
            region=None,
            theme=None,
            status="running",
            current_agent=None,
            progress_percent=0,
            events=[],
            vendors=[],
            completed_agents=[],
            pending_agents=["agent1"],
            context={},
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # Save state
        path = recovery_manager.save_state(state)
        assert Path(path).exists()
        
        # Load state
        loaded = recovery_manager.load_state("test-save")
        assert loaded is not None
        assert loaded.pipeline_id == "test-save"
        assert loaded.query == "test query"
    
    def test_load_nonexistent_state(self, recovery_manager):
        """Test loading state that doesn't exist."""
        loaded = recovery_manager.load_state("nonexistent")
        assert loaded is None
    
    def test_list_recoverable_pipelines(self, recovery_manager):
        """Test listing recoverable pipelines."""
        # Create multiple states
        for i in range(3):
            state = PipelineState(
                pipeline_id=f"pipe-{i}",
                query=f"query {i}",
                industry=None,
                region=None,
                theme=None,
                status="running" if i < 2 else "completed",
                current_agent=None,
                progress_percent=i * 10,
                events=[],
                vendors=[],
                completed_agents=[],
                pending_agents=[],
                context={},
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            recovery_manager.save_state(state)
        
        # List all
        all_pipes = recovery_manager.list_recoverable_pipelines()
        assert len(all_pipes) == 3
        
        # List only running
        running = recovery_manager.list_recoverable_pipelines(status="running")
        assert len(running) == 2
    
    def test_can_resume(self, recovery_manager):
        """Test checking if pipeline can be resumed."""
        # Create running state
        running_state = PipelineState(
            pipeline_id="can-resume",
            query="test",
            industry=None,
            region=None,
            theme=None,
            status="running",
            current_agent=None,
            progress_percent=50,
            events=[],
            vendors=[],
            completed_agents=[],
            pending_agents=[],
            context={},
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        recovery_manager.save_state(running_state)
        
        assert recovery_manager.can_resume("can-resume") is True
        assert recovery_manager.can_resume("nonexistent") is False
    
    def test_mark_agent_complete(self, recovery_manager):
        """Test marking agent as complete."""
        state = PipelineState(
            pipeline_id="mark-test",
            query="test",
            industry=None,
            region=None,
            theme=None,
            status="running",
            current_agent="agent1",
            progress_percent=0,
            events=[],
            vendors=[],
            completed_agents=[],
            pending_agents=["agent1", "agent2"],
            context={},
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        recovery_manager.save_state(state)
        
        # Mark agent complete
        recovery_manager.mark_agent_complete(
            "mark-test", "agent1", {"new_data": "value"}
        )
        
        # Verify
        loaded = recovery_manager.load_state("mark-test")
        assert "agent1" in loaded.completed_agents
        assert "agent1" not in loaded.pending_agents
        assert loaded.context.get("new_data") == "value"
    
    def test_delete_state(self, recovery_manager):
        """Test deleting pipeline state."""
        state = PipelineState(
            pipeline_id="delete-test",
            query="test",
            industry=None,
            region=None,
            theme=None,
            status="completed",
            current_agent=None,
            progress_percent=100,
            events=[],
            vendors=[],
            completed_agents=[],
            pending_agents=[],
            context={},
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        recovery_manager.save_state(state)
        
        # Delete
        recovery_manager.delete_state("delete-test")
        
        # Verify deleted
        assert recovery_manager.load_state("delete-test") is None
    
    def test_initialize_state(self, recovery_manager):
        """Test initializing new pipeline state."""
        state = recovery_manager.initialize_state(
            pipeline_id="init-test",
            query="fintech events",
            industry="fintech",
            region="USA",
            theme="payments",
            agent_sequence=["agent1", "agent2", "agent3"]
        )
        
        assert state.pipeline_id == "init-test"
        assert state.query == "fintech events"
        assert state.industry == "fintech"
        assert state.pending_agents == ["agent1", "agent2", "agent3"]
        assert state.status == "running"


class TestGetRecoveryManager:
    """Test suite for get_recovery_manager."""
    
    def setup_method(self):
        """Reset global instance before each test."""
        global _recovery_mgr
        _recovery_mgr = None
    
    def teardown_method(self):
        """Reset global instance after each test."""
        global _recovery_mgr
        _recovery_mgr = None
    
    def test_singleton_pattern(self):
        """Test that get_recovery_manager returns singleton."""
        mgr1 = get_recovery_manager()
        mgr2 = get_recovery_manager()
        
        assert mgr1 is mgr2