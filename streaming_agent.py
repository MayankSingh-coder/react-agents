"""Streaming React Agent that emits real-time thinking events."""

import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from agent.react_agent import ReactAgent
from agent.agent_state import AgentState


class EventType(Enum):
    """Types of events emitted by the streaming agent."""
    THINKING_START = "thinking_start"
    THINKING = "thinking"
    ACTION_PLANNED = "action_planned"
    ACTION_START = "action_start"
    ACTION_RESULT = "action_result"
    OBSERVATION = "observation"
    PLAN_CREATED = "plan_created"
    PLAN_STEP_START = "plan_step_start"
    PLAN_STEP_COMPLETE = "plan_step_complete"
    REFLECTION_START = "reflection_start"
    REFLECTION_CRITIQUE = "reflection_critique"
    REFLECTION_REFINEMENT = "reflection_refinement"
    REFLECTION_COMPLETE = "reflection_complete"
    ERROR = "error"
    COMPLETE = "complete"


@dataclass
class StreamingEvent:
    """Event emitted by the streaming agent."""
    type: EventType
    data: Dict[str, Any]
    timestamp: float
    step: int
    metadata: Optional[Dict[str, Any]] = None


class StreamingReactAgent(ReactAgent):
    """React Agent that emits real-time thinking events."""
    
    def __init__(self, verbose: bool = True, mode: str = "hybrid", enable_reflection: bool = True):
        super().__init__(verbose, mode, enable_reflection=enable_reflection)
        self._event_queue = None
        self._current_step = 0
    
    async def run_stream(self, query: str, max_steps: int = None) -> AsyncGenerator[StreamingEvent, None]:
        """Run the agent and yield real-time events."""
        self._event_queue = asyncio.Queue()
        self._current_step = 0
        
        # Start the agent execution in a background task
        task = asyncio.create_task(self._run_with_events(query, max_steps))
        
        try:
            # Yield events as they come
            while True:
                try:
                    # Wait for next event with timeout
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                    yield event
                    
                    # If this is the completion event, break
                    if event.type in [EventType.COMPLETE, EventType.ERROR]:
                        break
                        
                except asyncio.TimeoutError:
                    # Check if task is still running
                    if task.done():
                        break
                    continue
                    
        finally:
            # Ensure the task is cancelled if we exit early
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def _run_with_events(self, query: str, max_steps: int = None):
        """Run the agent and emit events."""
        try:
            # Run the normal agent
            response = await super().run(query, max_steps)
            
            # Emit completion event
            await self._emit_event(EventType.COMPLETE, {
                "response": response,
                "success": response["success"]
            })
            
        except Exception as e:
            # Emit error event
            await self._emit_event(EventType.ERROR, {
                "error": str(e),
                "success": False
            })
    
    async def _emit_event(self, event_type: EventType, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Emit an event to the queue."""
        if self._event_queue:
            event = StreamingEvent(
                type=event_type,
                data=data,
                timestamp=time.time(),
                step=self._current_step,
                metadata=metadata or {}
            )
            await self._event_queue.put(event)
    
    # Override key methods to emit events
    
    async def _think_node(self, state: AgentState) -> AgentState:
        """Think node with event emission."""
        self._current_step = state['current_step'] + 1
        
        # Emit thinking start event
        await self._emit_event(EventType.THINKING_START, {
            "step": self._current_step,
            "input": state["input"]  # Changed from "query" to "input"
        })
        
        # Call the original think node
        result_state = await super()._think_node(state)
        
        # Emit thinking event with the actual thought
        if result_state["thoughts"]:
            latest_thought = result_state["thoughts"][-1]
            await self._emit_event(EventType.THINKING, {
                "thought": latest_thought,
                "step": self._current_step
            })
        
        # If an action was planned, emit action planned event
        if result_state["actions"]:
            latest_action = result_state["actions"][-1]
            await self._emit_event(EventType.ACTION_PLANNED, {
                "action": latest_action.get("name", latest_action.get("action", "unknown")),
                "input": latest_action.get("input", latest_action.get("action_input", {})),
                "step": self._current_step
            })
        
        return result_state
    
    async def _act_node(self, state: AgentState) -> AgentState:
        """Act node with event emission."""
        if not state["actions"]:
            return state
        
        current_action = state["actions"][-1]
        action_name = current_action.get("name", "unknown")
        action_input = current_action.get("input", "")
        
        # Emit action start event
        await self._emit_event(EventType.ACTION_START, {
            "action": action_name,
            "input": action_input,
            "step": self._current_step
        })
        
        # Call the original act node
        result_state = await super()._act_node(state)
        
        # Emit action result event
        if result_state["tool_results"]:
            latest_result = result_state["tool_results"][-1]
            await self._emit_event(EventType.ACTION_RESULT, {
                "tool": latest_result.get("tool", "unknown"),
                "result": latest_result.get("result", {}),
                "step": self._current_step
            })
        
        return result_state
    
    async def _observe_node(self, state: AgentState) -> AgentState:
        """Observe node with event emission."""
        # Call the original observe node
        result_state = await super()._observe_node(state)
        
        # Emit observation event
        if result_state["observations"]:
            latest_observation = result_state["observations"][-1]
            await self._emit_event(EventType.OBSERVATION, {
                "observation": latest_observation,
                "step": self._current_step
            })
        
        return result_state
    
    async def _plan_node(self, state: AgentState) -> AgentState:
        """Plan node with event emission."""
        # Call the original plan node
        result_state = await super()._plan_node(state)
        
        # Emit plan created event
        if result_state.get("current_plan"):
            plan = result_state["current_plan"]
            await self._emit_event(EventType.PLAN_CREATED, {
                "plan": {
                    "description": getattr(plan, 'description', 'No description'),
                    "confidence": getattr(plan, 'confidence', 0.0),
                    "steps": [
                        {
                            "id": getattr(step, 'id', f"step_{i}"),
                            "description": getattr(step, 'description', 'No description'),
                            "tool": getattr(step, 'tool', 'unknown')
                        }
                        for i, step in enumerate(getattr(plan, 'steps', []))
                    ]
                },
                "step": self._current_step
            })
        
        return result_state
    
    async def _execute_node(self, state: AgentState) -> AgentState:
        """Execute node with event emission."""
        if state.get("current_plan"):
            plan = state["current_plan"]
            
            # Emit plan step start events
            steps = getattr(plan, 'steps', [])
            for i, step in enumerate(steps):
                await self._emit_event(EventType.PLAN_STEP_START, {
                    "step_id": getattr(step, 'id', f"step_{i}"),
                    "step_description": getattr(step, 'description', 'No description'),
                    "tool": getattr(step, 'tool', 'unknown'),
                    "plan_step": i + 1,
                    "total_steps": len(steps)
                })
        
        # Call the original execute node
        result_state = await super()._execute_node(state)
        
        # Emit plan completion event based on execution result
        if result_state.get("is_complete"):
            await self._emit_event(EventType.PLAN_STEP_COMPLETE, {
                "status": "completed",
                "step": self._current_step
            })
        elif result_state.get("plan_failed"):
            await self._emit_event(EventType.PLAN_STEP_COMPLETE, {
                "status": "failed",
                "step": self._current_step
            })
        
        return result_state
    
    async def _reflect_node(self, state: AgentState) -> AgentState:
        """Reflection node with event emission."""
        # Check if reflection is enabled
        if not self.reflection_module:
            return state
            
        # Emit reflection start event
        await self._emit_event(EventType.REFLECTION_START, {
            "original_response": state.get("output", ""),
            "quality_threshold": self.reflection_module.quality_threshold,
            "step": self._current_step
        })
        
        # Call the original reflection node
        result_state = await super()._reflect_node(state)
        
        # Extract reflection metadata from the result
        reflection_metadata = result_state.get("metadata", {}).get("reflection", {})
        
        if reflection_metadata:
            # Emit reflection critique events for each iteration
            reflection_history = reflection_metadata.get("reflection_history", [])
            for iteration_data in reflection_history:
                critique = iteration_data.get("critique")
                if critique:
                    # Handle both CritiqueResult objects and dictionaries
                    if hasattr(critique, '__dict__'):
                        critique_data = {
                            "overall_quality": critique.overall_quality,
                            "confidence": critique.confidence,
                            "issues_count": len(critique.issues),
                            "strengths_count": len(critique.strengths),
                            "needs_refinement": critique.needs_refinement,
                            "reasoning": critique.reasoning,
                            "issues": [
                                {
                                    "type": issue.type.value if hasattr(issue.type, 'value') else str(issue.type),
                                    "severity": issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity),
                                    "description": issue.description,
                                    "suggestion": issue.suggestion,
                                    "confidence": issue.confidence
                                } for issue in critique.issues
                            ],
                            "strengths": critique.strengths
                        }
                    else:
                        # Dictionary fallback
                        critique_data = {
                            "overall_quality": critique.get("overall_quality", 0.0),
                            "confidence": critique.get("confidence", 0.0),
                            "issues_count": len(critique.get("issues", [])),
                            "strengths_count": len(critique.get("strengths", [])),
                            "needs_refinement": critique.get("needs_refinement", False),
                            "reasoning": critique.get("reasoning", ""),
                            "issues": critique.get("issues", []),
                            "strengths": critique.get("strengths", [])
                        }
                    
                    await self._emit_event(EventType.REFLECTION_CRITIQUE, {
                        "iteration": iteration_data.get("iteration", 1),
                        "critique": critique_data,
                        "step": self._current_step
                    })
            
            # Emit refinement events if improvements were made
            improvements = reflection_metadata.get("total_improvements", [])
            if improvements:
                await self._emit_event(EventType.REFLECTION_REFINEMENT, {
                    "improvements": improvements,
                    "quality_improvement": reflection_metadata.get("final_quality_score", 0.0) - 0.5,  # Rough estimate
                    "original_response": state.get("original_response", ""),
                    "refined_response": result_state.get("output", ""),
                    "step": self._current_step
                })
        
        # Emit reflection complete event
        await self._emit_event(EventType.REFLECTION_COMPLETE, {
            "final_quality_score": reflection_metadata.get("final_quality_score", 0.0),
            "reflection_iterations": reflection_metadata.get("reflection_iterations", 0),
            "threshold_met": reflection_metadata.get("threshold_met", False),
            "total_improvements": len(reflection_metadata.get("total_improvements", [])),
            "step": self._current_step
        })
        
        return result_state


class StreamingChatbot:
    """Chatbot interface that supports streaming responses."""
    
    def __init__(self, verbose: bool = False, mode: str = "hybrid", enable_reflection: bool = True):
        self.agent = StreamingReactAgent(verbose=verbose, mode=mode, enable_reflection=enable_reflection)
        self.conversation_history = []
        
        # Connect this chatbot instance to the tool manager so the conversation history tool can access it
        if hasattr(self.agent, 'tool_manager'):
            self.agent.tool_manager.set_chatbot_instance(self)
    
    async def chat_stream(self, message: str) -> AsyncGenerator[StreamingEvent, None]:
        """Process a chat message and yield real-time events."""
        try:
            async for event in self.agent.run_stream(message):
                yield event
                
                # If this is the completion event, add to history
                if event.type == EventType.COMPLETE:
                    response = event.data["response"]
                    # Add to conversation history
                    conversation_entry = {
                        "user": message,
                        "assistant": response["output"],
                        "success": response["success"],
                        "steps": len(response["steps"]),
                        "timestamp": time.time()
                    }
                    self.conversation_history.append(conversation_entry)
                    
                    # Also notify the conversation history tool (backup method)
                    self._notify_conversation_tool(conversation_entry)
                    
        except Exception as e:
            # Yield error event
            yield StreamingEvent(
                type=EventType.ERROR,
                data={
                    "error": str(e),
                    "success": False
                },
                timestamp=time.time(),
                step=0
            )
            
            # Add error to conversation history
            error_entry = {
                "user": message,
                "assistant": f"Error: {str(e)}",
                "success": False,
                "steps": 0,
                "timestamp": time.time()
            }
            self.conversation_history.append(error_entry)
            
            # Also notify the conversation history tool (backup method)
            self._notify_conversation_tool(error_entry)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chatbot statistics."""
        total_conversations = len(self.conversation_history)
        successful_conversations = sum(1 for conv in self.conversation_history if conv["success"])
        
        return {
            "total_conversations": total_conversations,
            "successful_conversations": successful_conversations,
            "success_rate": successful_conversations / total_conversations if total_conversations > 0 else 0
        }
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        
        # Also clear the conversation history tool's cache
        if hasattr(self.agent, 'tool_manager'):
            conversation_tool = self.agent.tool_manager.get_tool("conversation_history")
            if conversation_tool:
                conversation_tool._conversation_cache.clear()
    
    def _notify_conversation_tool(self, conversation_entry: Dict[str, Any]):
        """Notify the conversation history tool about new conversation (backup method)."""
        try:
            if hasattr(self.agent, 'tool_manager'):
                conversation_tool = self.agent.tool_manager.get_tool("conversation_history")
                if conversation_tool and not hasattr(conversation_tool, 'chatbot_instance'):
                    # Only use cache if tool doesn't have chatbot instance
                    conversation_tool.add_conversation_to_cache(
                        conversation_entry["user"],
                        conversation_entry["assistant"],
                        conversation_entry["success"],
                        conversation_entry["steps"]
                    )
        except Exception as e:
            # Silently fail - this is just a backup method
            pass
    
    def get_conversation_count(self) -> int:
        """Get the number of conversations in history."""
        return len(self.conversation_history)
    
    def get_recent_conversations(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversations."""
        return self.conversation_history[-count:] if self.conversation_history else []