"""Context manager for sharing information between tools and reasoning steps."""

import json
import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from .memory_store import MemoryStore, MemoryType


@dataclass
class ToolContext:
    """Context information for a specific tool execution."""
    tool_name: str
    input_data: Any
    output_data: Any
    success: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningStep:
    """A single step in the reasoning process."""
    step_number: int
    thought: str
    planned_action: Optional[str] = None
    action_input: Optional[Any] = None
    tool_context: Optional[ToolContext] = None
    observation: Optional[str] = None
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """Manages context and information flow between tools and reasoning steps."""
    
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self.current_session_id: Optional[str] = None
        self.reasoning_steps: List[ReasoningStep] = []
        self.tool_contexts: Dict[str, List[ToolContext]] = {}
        self.shared_variables: Dict[str, Any] = {}
        self.entity_tracker: Dict[str, Any] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
    
    def start_session(self, session_id: str, initial_query: str):
        """Start a new reasoning session."""
        self.current_session_id = session_id
        self.reasoning_steps = []
        self.tool_contexts = {}
        self.shared_variables = {
            "initial_query": {
                "value": initial_query,
                "source_tool": None,
                "timestamp": time.time()
            }
        }
        self.entity_tracker = {}
        self.dependency_graph = {}
    
    async def add_reasoning_step(self, step: ReasoningStep):
        """Add a reasoning step to the current session."""
        self.reasoning_steps.append(step)
        
        # Store in memory for future reference
        await self.memory_store.remember(
            content={
                "step_number": step.step_number,
                "thought": step.thought,
                "planned_action": step.planned_action,
                "confidence": step.confidence
            },
            memory_type=MemoryType.WORKING,
            importance=step.confidence,
            metadata={
                "session_id": self.current_session_id,
                "step_type": "reasoning"
            }
        )
    
    async def add_tool_context(self, tool_context: ToolContext):
        """Add tool execution context."""
        if tool_context.tool_name not in self.tool_contexts:
            self.tool_contexts[tool_context.tool_name] = []
        
        self.tool_contexts[tool_context.tool_name].append(tool_context)
        
        # Store successful tool results in memory
        if tool_context.success:
            await self.memory_store.remember(
                content={
                    "tool_name": tool_context.tool_name,
                    "input": tool_context.input_data,
                    "output": tool_context.output_data,
                    "execution_time": tool_context.execution_time
                },
                memory_type=MemoryType.TOOL_CONTEXT,
                importance=0.7 if tool_context.success else 0.3,
                metadata={
                    "session_id": self.current_session_id,
                    "tool_name": tool_context.tool_name,
                    "success": tool_context.success
                }
            )
    
    def set_shared_variable(self, key: str, value: Any, source_tool: Optional[str] = None):
        """Set a shared variable that can be used by other tools."""
        self.shared_variables[key] = {
            "value": value,
            "source_tool": source_tool,
            "timestamp": time.time()
        }
    
    def get_shared_variable(self, key: str) -> Any:
        """Get a shared variable."""
        var_data = self.shared_variables.get(key)
        return var_data["value"] if var_data else None
    
    def get_all_shared_variables(self) -> Dict[str, Any]:
        """Get all shared variables."""
        return {k: v["value"] for k, v in self.shared_variables.items()}
    
    async def get_relevant_context(self, current_tool: str, query: str) -> Dict[str, Any]:
        """Get relevant context for a tool execution."""
        context = {
            "shared_variables": self.get_all_shared_variables(),
            "previous_tool_results": {},
            "entity_mentions": self.entity_tracker,
            "reasoning_history": [],
            "similar_past_executions": []
        }
        
        # Get previous tool results
        for tool_name, contexts in self.tool_contexts.items():
            if contexts:
                latest_context = contexts[-1]
                if latest_context.success:
                    context["previous_tool_results"][tool_name] = {
                        "output": latest_context.output_data,
                        "metadata": latest_context.metadata
                    }
        
        # Get recent reasoning steps
        context["reasoning_history"] = [
            {
                "thought": step.thought,
                "action": step.planned_action,
                "confidence": step.confidence
            }
            for step in self.reasoning_steps[-5:]
        ]
        
        # Search for similar past tool executions
        similar_memories = await self.memory_store.search_memories(
            query=f"{current_tool} {query}",
            memory_type=MemoryType.TOOL_CONTEXT,
            limit=3
        )
        
        context["similar_past_executions"] = [
            {
                "tool_name": memory.content.get("tool_name"),
                "input": memory.content.get("input"),
                "output": memory.content.get("output"),
                "success_rate": memory.importance
            }
            for memory in similar_memories
        ]
        
        return context
    
    async def end_session(self):
        """End the current session and store episodic memory."""
        if self.current_session_id:
            session_summary = {
                "session_id": self.current_session_id,
                "total_reasoning_steps": len(self.reasoning_steps),
                "tools_used": list(self.tool_contexts.keys()),
                "shared_variables_count": len(self.shared_variables),
                "entities_tracked": len(self.entity_tracker)
            }
            
            # Store the entire session as episodic memory
            await self.memory_store.remember(
                content={
                    "session_summary": session_summary,
                    "reasoning_steps": [
                        {
                            "thought": step.thought,
                            "action": step.planned_action,
                            "success": step.tool_context.success if step.tool_context else None
                        }
                        for step in self.reasoning_steps
                    ],
                    "final_shared_variables": self.get_all_shared_variables()
                },
                memory_type=MemoryType.EPISODIC,
                importance=0.7,
                metadata={
                    "session_id": self.current_session_id,
                    "tools_used": session_summary["tools_used"]
                }
            )