"""Streaming React Agent that emits real-time thinking events."""

import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Any, Optional
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
    
    def __init__(self, verbose: bool = True, mode: str = "hybrid"):
        super().__init__(verbose, mode)
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
        if result_state.get("plan"):
            plan = result_state["plan"]
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
        if state.get("plan"):
            plan = state["plan"]
            
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


class StreamingChatbot:
    """Chatbot interface that supports streaming responses."""
    
    def __init__(self, verbose: bool = False, mode: str = "hybrid"):
        self.agent = StreamingReactAgent(verbose=verbose, mode=mode)
        self.conversation_history = []
    
    async def chat_stream(self, message: str) -> AsyncGenerator[StreamingEvent, None]:
        """Process a chat message and yield real-time events."""
        try:
            async for event in self.agent.run_stream(message):
                yield event
                
                # If this is the completion event, add to history
                if event.type == EventType.COMPLETE:
                    response = event.data["response"]
                    self.conversation_history.append({
                        "user": message,
                        "assistant": response["output"],
                        "success": response["success"],
                        "steps": len(response["steps"])
                    })
                    
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
            
            self.conversation_history.append({
                "user": message,
                "assistant": f"Error: {str(e)}",
                "success": False,
                "steps": 0
            })
    
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