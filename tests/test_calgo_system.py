"""Tests for Calgo System Core state machine"""
import pytest
from src.calgo_system import CalgoSystem
from src.models import SystemState


class TestCalgoSystemStateMachine:
    """Test suite for Calgo system state machine"""
    
    def test_initial_state_is_initializing(self):
        """System should start in INITIALIZING state"""
        system = CalgoSystem()
        assert system.state == SystemState.INITIALIZING
    
    def test_valid_transition_from_initializing_to_ready(self):
        """Should allow transition from INITIALIZING to READY"""
        system = CalgoSystem()
        result = system.transition_to(SystemState.READY)
        
        assert result.is_ok()
        assert system.state == SystemState.READY
    
    def test_valid_transition_from_ready_to_running(self):
        """Should allow transition from READY to RUNNING"""
        system = CalgoSystem()
        system.transition_to(SystemState.READY)
        result = system.transition_to(SystemState.RUNNING)
        
        assert result.is_ok()
        assert system.state == SystemState.RUNNING
    
    def test_valid_transition_from_running_to_halted(self):
        """Should allow transition from RUNNING to HALTED"""
        system = CalgoSystem()
        system.transition_to(SystemState.READY)
        system.transition_to(SystemState.RUNNING)
        result = system.transition_to(SystemState.HALTED)
        
        assert result.is_ok()
        assert system.state == SystemState.HALTED
    
    def test_valid_transition_from_halted_to_ready(self):
        """Should allow transition from HALTED back to READY"""
        system = CalgoSystem()
        system.transition_to(SystemState.READY)
        system.transition_to(SystemState.RUNNING)
        system.transition_to(SystemState.HALTED)
        result = system.transition_to(SystemState.READY)
        
        assert result.is_ok()
        assert system.state == SystemState.READY
    
    def test_valid_transition_to_shutdown_from_any_state(self):
        """Should allow transition to SHUTDOWN from any non-terminal state"""
        # From INITIALIZING
        system = CalgoSystem()
        result = system.transition_to(SystemState.SHUTDOWN)
        assert result.is_ok()
        assert system.state == SystemState.SHUTDOWN
        
        # From READY
        system = CalgoSystem()
        system.transition_to(SystemState.READY)
        result = system.transition_to(SystemState.SHUTDOWN)
        assert result.is_ok()
        
        # From RUNNING
        system = CalgoSystem()
        system.transition_to(SystemState.READY)
        system.transition_to(SystemState.RUNNING)
        result = system.transition_to(SystemState.SHUTDOWN)
        assert result.is_ok()
        
        # From HALTED
        system = CalgoSystem()
        system.transition_to(SystemState.READY)
        system.transition_to(SystemState.RUNNING)
        system.transition_to(SystemState.HALTED)
        result = system.transition_to(SystemState.SHUTDOWN)
        assert result.is_ok()
    
    def test_invalid_transition_from_initializing_to_running(self):
        """Should reject transition from INITIALIZING directly to RUNNING"""
        system = CalgoSystem()
        result = system.transition_to(SystemState.RUNNING)
        
        assert result.is_err()
        assert system.state == SystemState.INITIALIZING
        assert "Invalid state transition" in result.unwrap_err()
    
    def test_invalid_transition_from_ready_to_halted(self):
        """Should reject transition from READY directly to HALTED"""
        system = CalgoSystem()
        system.transition_to(SystemState.READY)
        result = system.transition_to(SystemState.HALTED)
        
        assert result.is_err()
        assert system.state == SystemState.READY
    
    def test_invalid_transition_from_shutdown(self):
        """Should reject any transition from SHUTDOWN (terminal state)"""
        system = CalgoSystem()
        system.transition_to(SystemState.SHUTDOWN)
        
        result = system.transition_to(SystemState.READY)
        assert result.is_err()
        assert system.state == SystemState.SHUTDOWN
    
    def test_can_transition_to_returns_correct_value(self):
        """can_transition_to should correctly identify valid transitions"""
        system = CalgoSystem()
        
        # From INITIALIZING
        assert system.can_transition_to(SystemState.READY)
        assert system.can_transition_to(SystemState.SHUTDOWN)
        assert not system.can_transition_to(SystemState.RUNNING)
        assert not system.can_transition_to(SystemState.HALTED)
        
        # From READY
        system.transition_to(SystemState.READY)
        assert system.can_transition_to(SystemState.RUNNING)
        assert system.can_transition_to(SystemState.SHUTDOWN)
        assert not system.can_transition_to(SystemState.HALTED)
    
    def test_get_valid_transitions_returns_correct_list(self):
        """get_valid_transitions should return all valid target states"""
        system = CalgoSystem()
        
        # From INITIALIZING
        valid = system.get_valid_transitions()
        assert SystemState.READY in valid
        assert SystemState.SHUTDOWN in valid
        assert len(valid) == 2
        
        # From READY
        system.transition_to(SystemState.READY)
        valid = system.get_valid_transitions()
        assert SystemState.RUNNING in valid
        assert SystemState.SHUTDOWN in valid
        assert len(valid) == 2
        
        # From SHUTDOWN (terminal)
        system.transition_to(SystemState.SHUTDOWN)
        valid = system.get_valid_transitions()
        assert len(valid) == 0
    
    def test_state_machine_full_lifecycle(self):
        """Test complete lifecycle: INITIALIZING -> READY -> RUNNING -> HALTED -> READY -> RUNNING -> SHUTDOWN"""
        system = CalgoSystem()
        
        assert system.state == SystemState.INITIALIZING
        
        system.transition_to(SystemState.READY)
        assert system.state == SystemState.READY
        
        system.transition_to(SystemState.RUNNING)
        assert system.state == SystemState.RUNNING
        
        system.transition_to(SystemState.HALTED)
        assert system.state == SystemState.HALTED
        
        system.transition_to(SystemState.READY)
        assert system.state == SystemState.READY
        
        system.transition_to(SystemState.RUNNING)
        assert system.state == SystemState.RUNNING
        
        system.transition_to(SystemState.SHUTDOWN)
        assert system.state == SystemState.SHUTDOWN
