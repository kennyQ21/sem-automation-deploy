"""
Base agent class for all SEM automation agents using LangGraph.
"""
from typing import Dict, Any, Optional
from openai import OpenAI
from src.schemas.state import GlobalState

class BaseAgent:
    """Base class for LangGraph nodes in the system."""
    
    def __init__(self, openai_client=None):
        """Initialize with OpenAI client."""
        if openai_client is not None:
            self.client = openai_client
        else:
            # Will be initialized by parent classes with proper API key
            self.client = None
        
    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        """
        Main entry point for node execution.
        Returns a dictionary of state updates rather than full state.
        """
        raise NotImplementedError("Nodes must implement __call__")
        
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate node output against expected schema."""
        raise NotImplementedError("Nodes must implement validate_output")
        
    def handle_error(self, error: Exception, state: GlobalState) -> Optional[Dict[str, Any]]:
        """Handle errors during node execution."""
        error_msg = f"{self.__class__.__name__} error: {str(error)}"
        return {
            "error_log": state.error_log + [error_msg]
        }
        
    def get_state_value(self, state: GlobalState, key: str, default: Any = None) -> Any:
        """Safely get a value from state with default."""
        return getattr(state, key, default)