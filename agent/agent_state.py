"""Agent state management for the React Agent."""

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel


class ThoughtActionObservation(BaseModel):
    """Represents a single thought-action-observation cycle."""
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    step: int


class AgentState(TypedDict):
    """State of the React Agent during execution."""
    
    # Input and output
    input: str
    output: Optional[str]
    
    # Reasoning chain
    thoughts: List[str]
    actions: List[Dict[str, Any]]
    observations: List[str]
    
    # Current step information
    current_step: int
    max_steps: int
    
    # Tool execution results
    tool_results: List[Dict[str, Any]]
    
    # Agent status
    is_complete: bool
    has_error: bool
    error_message: Optional[str]
    
    # Metadata
    metadata: Dict[str, Any]


class AgentMemory:
    """Memory system for the React Agent."""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.conversation_history: List[Dict[str, Any]] = []
        self.tool_usage_stats: Dict[str, int] = {}
        self.successful_patterns: List[Dict[str, Any]] = []
    
    def add_conversation(self, input_text: str, output_text: str, steps: List[ThoughtActionObservation]):
        """Add a conversation to memory."""
        conversation = {
            "input": input_text,
            "output": output_text,
            "steps": [step.dict() for step in steps],
            "timestamp": self._get_timestamp(),
            "success": True
        }
        
        self.conversation_history.append(conversation)
        
        # Keep only recent conversations
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
        
        # Update tool usage stats
        for step in steps:
            if step.action:
                self.tool_usage_stats[step.action] = self.tool_usage_stats.get(step.action, 0) + 1
    
    def get_relevant_history(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant conversation history based on the query."""
        # Simple relevance scoring based on keyword overlap
        scored_conversations = []
        query_words = set(query.lower().split())
        
        for conv in self.conversation_history:
            input_words = set(conv["input"].lower().split())
            output_words = set(conv["output"].lower().split())
            
            # Calculate relevance score
            input_overlap = len(query_words.intersection(input_words))
            output_overlap = len(query_words.intersection(output_words))
            score = input_overlap + output_overlap * 0.5
            
            if score > 0:
                scored_conversations.append((score, conv))
        
        # Sort by relevance and return top results
        scored_conversations.sort(key=lambda x: x[0], reverse=True)
        return [conv for _, conv in scored_conversations[:limit]]
    
    def get_tool_stats(self) -> Dict[str, int]:
        """Get tool usage statistics."""
        return self.tool_usage_stats.copy()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        import datetime
        return datetime.datetime.now().isoformat()


def create_initial_state(input_text: str, max_steps: int = 10) -> AgentState:
    """Create initial agent state."""
    return AgentState(
        input=input_text,
        output=None,
        thoughts=[],
        actions=[],
        observations=[],
        current_step=0,
        max_steps=max_steps,
        tool_results=[],
        is_complete=False,
        has_error=False,
        error_message=None,
        metadata={}
    )