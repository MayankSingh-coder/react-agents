"""Unified Memory Manager - Coordinates all memory systems."""

import json
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from .memory_store import MemoryStore, MemoryType, MemoryEntry
from .episodic_memory import EpisodicMemory, Episode
from .context_manager import ContextManager, ReasoningStep, ToolContext
from .vector_memory import VectorMemory


class MemoryOperation(Enum):
    """Types of memory operations."""
    STORE = "store"
    RETRIEVE = "retrieve"
    SEARCH = "search"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class MemoryRequest:
    """Request for memory operation."""
    operation: MemoryOperation
    memory_type: Optional[MemoryType] = None
    content: Optional[Any] = None
    query: Optional[str] = None
    memory_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    importance: float = 0.5
    limit: int = 10


@dataclass
class MemoryResponse:
    """Response from memory operation."""
    success: bool
    data: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    count: int = 0


class UnifiedMemoryManager:
    """Unified manager for all memory systems."""
    
    def __init__(self, memory_store: Optional[MemoryStore] = None,
                 vector_memory: Optional[VectorMemory] = None,
                 episodic_memory: Optional[EpisodicMemory] = None,
                 context_manager: Optional[ContextManager] = None):
        # Initialize memory systems
        self.memory_store = memory_store or MemoryStore()
        self.vector_memory = vector_memory or VectorMemory()
        self.episodic_memory = episodic_memory or EpisodicMemory(self.memory_store, self.vector_memory)
        self.context_manager = context_manager or ContextManager(self.memory_store, self.episodic_memory)
        
        # Cross-system synchronization
        self._sync_enabled = True
        self._sync_queue = []
    
    async def process_memory_request(self, request: MemoryRequest) -> MemoryResponse:
        """Process a unified memory request."""
        try:
            if request.operation == MemoryOperation.STORE:
                return await self._store_memory(request)
            elif request.operation == MemoryOperation.RETRIEVE:
                return await self._retrieve_memory(request)
            elif request.operation == MemoryOperation.SEARCH:
                return await self._search_memory(request)
            elif request.operation == MemoryOperation.UPDATE:
                return await self._update_memory(request)
            elif request.operation == MemoryOperation.DELETE:
                return await self._delete_memory(request)
            else:
                return MemoryResponse(
                    success=False,
                    error=f"Unknown memory operation: {request.operation}"
                )
                
        except Exception as e:
            return MemoryResponse(
                success=False,
                error=f"Memory operation failed: {str(e)}"
            )
    
    async def _store_memory(self, request: MemoryRequest) -> MemoryResponse:
        """Store memory across appropriate systems."""
        results = {}
        
        # Store in memory store
        if request.memory_type:
            memory_id = await self.memory_store.remember(
                content=request.content,
                memory_type=request.memory_type,
                importance=request.importance,
                metadata=request.metadata or {}
            )
            results["memory_store"] = memory_id
        
        # Store in vector memory for semantic search
        if request.content and isinstance(request.content, (str, dict)):
            content_text = json.dumps(request.content) if isinstance(request.content, dict) else str(request.content)
            vector_id = self.vector_memory.add_entry(
                content=content_text,
                metadata=request.metadata or {},
                importance=request.importance
            )
            results["vector_memory"] = vector_id
        
        # Sync to context manager if relevant
        if request.memory_type in [MemoryType.WORKING, MemoryType.TOOL_CONTEXT]:
            await self._sync_to_context_manager(request)
        
        return MemoryResponse(
            success=True,
            data=results,
            metadata={"stored_in": list(results.keys())},
            count=len(results)
        )
    
    async def _retrieve_memory(self, request: MemoryRequest) -> MemoryResponse:
        """Retrieve memory from appropriate system."""
        if not request.memory_id:
            return MemoryResponse(
                success=False,
                error="Memory ID required for retrieval"
            )
        
        # Try memory store first
        memory_entry = await self.memory_store.recall(request.memory_id)
        if memory_entry:
            return MemoryResponse(
                success=True,
                data=memory_entry.to_dict(),
                metadata={"source": "memory_store"},
                count=1
            )
        
        # Try episodic memory
        if request.memory_id in self.episodic_memory.episodes:
            episode = self.episodic_memory.episodes[request.memory_id]
            return MemoryResponse(
                success=True,
                data=episode.to_dict(),
                metadata={"source": "episodic_memory"},
                count=1
            )
        
        return MemoryResponse(
            success=False,
            error=f"Memory not found: {request.memory_id}"
        )
    
    async def _search_memory(self, request: MemoryRequest) -> MemoryResponse:
        """Search across all memory systems."""
        if not request.query:
            return MemoryResponse(
                success=False,
                error="Query required for search"
            )
        
        all_results = []
        
        # Search memory store
        memory_results = await self.memory_store.search_memories(
            query=request.query,
            memory_type=request.memory_type,
            limit=request.limit
        )
        all_results.extend([
            {
                "source": "memory_store",
                "type": result.memory_type.value,
                "content": result.content,
                "relevance": result.importance,
                "timestamp": result.timestamp,
                "id": result.id
            }
            for result in memory_results
        ])
        
        # Search episodic memory
        if not request.memory_type or request.memory_type == MemoryType.EPISODIC:
            episodic_results = await self.episodic_memory.find_similar_episodes(
                query=request.query,
                top_k=request.limit // 2
            )
            all_results.extend([
                {
                    "source": "episodic_memory",
                    "type": "episode",
                    "content": {
                        "query": episode.query,
                        "response": episode.response,
                        "tools_used": episode.tools_used
                    },
                    "relevance": similarity,
                    "timestamp": episode.timestamp,
                    "id": episode.id
                }
                for episode, similarity in episodic_results
            ])
        
        # Search vector memory
        vector_results = self.vector_memory.search_similar(
            query=request.query,
            top_k=request.limit // 2
        )
        all_results.extend([
            {
                "source": "vector_memory",
                "type": "vector_entry",
                "content": entry.content,
                "relevance": similarity,
                "timestamp": entry.metadata.get("timestamp", time.time()),
                "id": f"vector_{i}"
            }
            for i, (entry, similarity) in enumerate(vector_results)
        ])
        
        # Sort by relevance
        all_results.sort(key=lambda x: x["relevance"], reverse=True)
        all_results = all_results[:request.limit]
        
        return MemoryResponse(
            success=True,
            data=all_results,
            metadata={"search_query": request.query},
            count=len(all_results)
        )
    
    async def _update_memory(self, request: MemoryRequest) -> MemoryResponse:
        """Update memory entry."""
        if not request.memory_id:
            return MemoryResponse(
                success=False,
                error="Memory ID required for update"
            )
        
        # Try to update in memory store
        memory_entry = await self.memory_store.recall(request.memory_id)
        if memory_entry:
            # Update content and metadata
            if request.content is not None:
                memory_entry.content = request.content
            if request.metadata:
                memory_entry.metadata.update(request.metadata)
            memory_entry.importance = request.importance
            memory_entry.last_accessed = time.time()
            
            # Re-store the updated entry
            await self.memory_store.store.store(memory_entry)
            
            return MemoryResponse(
                success=True,
                data=memory_entry.to_dict(),
                metadata={"updated_in": "memory_store"},
                count=1
            )
        
        return MemoryResponse(
            success=False,
            error=f"Memory not found for update: {request.memory_id}"
        )
    
    async def _delete_memory(self, request: MemoryRequest) -> MemoryResponse:
        """Delete memory from all systems."""
        if not request.memory_id:
            return MemoryResponse(
                success=False,
                error="Memory ID required for deletion"
            )
        
        deleted_from = []
        
        # Delete from memory store
        if await self.memory_store.forget(request.memory_id):
            deleted_from.append("memory_store")
        
        # Delete from episodic memory
        if request.memory_id in self.episodic_memory.episodes:
            del self.episodic_memory.episodes[request.memory_id]
            deleted_from.append("episodic_memory")
        
        if not deleted_from:
            return MemoryResponse(
                success=False,
                error=f"Memory not found for deletion: {request.memory_id}"
            )
        
        return MemoryResponse(
            success=True,
            data={"deleted_from": deleted_from},
            metadata={"memory_id": request.memory_id},
            count=len(deleted_from)
        )
    
    async def _sync_to_context_manager(self, request: MemoryRequest):
        """Sync memory to context manager if relevant."""
        if request.memory_type == MemoryType.WORKING and isinstance(request.content, dict):
            # Check if it's a reasoning step
            if "thought" in request.content:
                step = ReasoningStep(
                    step_number=request.content.get("step_number", 0),
                    thought=request.content["thought"],
                    planned_action=request.content.get("planned_action"),
                    confidence=request.content.get("confidence", 0.5)
                )
                await self.context_manager.add_reasoning_step(step)
        
        elif request.memory_type == MemoryType.TOOL_CONTEXT and isinstance(request.content, dict):
            # Check if it's a tool context
            if "tool_name" in request.content:
                tool_context = ToolContext(
                    tool_name=request.content["tool_name"],
                    input_data=request.content.get("input"),
                    output_data=request.content.get("output"),
                    success=request.content.get("success", True),
                    execution_time=request.content.get("execution_time", 0.0)
                )
                await self.context_manager.add_tool_context(tool_context)
    
    # Convenience methods for common operations
    
    async def store_conversation(self, user_query: str, assistant_response: str, 
                               tools_used: List[str], reasoning_steps: List[Dict],
                               success: bool, duration: float) -> str:
        """Store a complete conversation episode."""
        episode_id = str(uuid.uuid4())
        episode = Episode(
            id=episode_id,
            query=user_query,
            response=assistant_response,
            reasoning_steps=reasoning_steps,
            tools_used=tools_used,
            success=success,
            duration=duration,
            timestamp=time.time(),
            importance=0.8 if success else 0.3,
            metadata={"conversation": True}
        )
        
        await self.episodic_memory.store_episode(episode)
        return episode_id
    
    async def get_conversation_history(self, limit: int = 10, success_only: bool = False) -> List[Dict]:
        """Get recent conversation history."""
        episodes = list(self.episodic_memory.episodes.values())
        
        if success_only:
            episodes = [ep for ep in episodes if ep.success]
        
        episodes.sort(key=lambda x: x.timestamp, reverse=True)
        return [ep.to_dict() for ep in episodes[:limit]]
    
    async def find_similar_conversations(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """Find conversations similar to the query."""
        similar_episodes = await self.episodic_memory.find_similar_episodes(query, top_k)
        return [(ep.to_dict(), similarity) for ep, similarity in similar_episodes]
    
    async def get_shared_context(self, tool_name: str = None) -> Dict[str, Any]:
        """Get current shared context."""
        if tool_name:
            return await self.context_manager.get_relevant_context(tool_name, tool_name)
        else:
            return {
                "shared_variables": self.context_manager.get_all_shared_variables(),
                "reasoning_steps": [step.__dict__ for step in self.context_manager.reasoning_steps[-5:]],
                "tool_contexts": {
                    tool: [tc.__dict__ for tc in contexts[-3:]]
                    for tool, contexts in self.context_manager.tool_contexts.items()
                }
            }
    
    async def set_shared_variable(self, key: str, value: Any, source_tool: str = None):
        """Set a shared variable."""
        self.context_manager.set_shared_variable(key, value, source_tool)
        
        # Also store in memory store for persistence
        await self.memory_store.remember(
            content={"key": key, "value": value, "source_tool": source_tool},
            memory_type=MemoryType.TOOL_CONTEXT,
            importance=0.6,
            metadata={"shared_variable": True, "key": key}
        )
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        episodic_stats = await self.episodic_memory.get_episode_stats()
        
        memory_counts = {}
        for memory_type in MemoryType:
            memories = await self.memory_store.store.get_by_type(memory_type, limit=1000)
            memory_counts[memory_type.value] = len(memories)
        
        vector_count = len(self.vector_memory.entries)
        
        context_stats = {
            "reasoning_steps": len(self.context_manager.reasoning_steps),
            "shared_variables": len(self.context_manager.shared_variables),
            "tool_contexts": sum(len(contexts) for contexts in self.context_manager.tool_contexts.values())
        }
        
        return {
            "episodic_memory": episodic_stats,
            "memory_store": memory_counts,
            "vector_memory": {"entries": vector_count},
            "context_manager": context_stats,
            "total_memories": sum(memory_counts.values()) + episodic_stats["total_episodes"] + vector_count
        }
    
    def enable_sync(self):
        """Enable cross-system synchronization."""
        self._sync_enabled = True
    
    def disable_sync(self):
        """Disable cross-system synchronization."""
        self._sync_enabled = False
    
    async def cleanup_old_memories(self, days_old: int = 30):
        """Clean up old memories to free space."""
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        # Clean up memory store (it handles this automatically)
        # Clean up old episodes with low importance
        episodes_to_remove = []
        for episode_id, episode in self.episodic_memory.episodes.items():
            if episode.timestamp < cutoff_time and episode.importance < 0.3:
                episodes_to_remove.append(episode_id)
        
        for episode_id in episodes_to_remove:
            del self.episodic_memory.episodes[episode_id]
        
        return {
            "cleaned_episodes": len(episodes_to_remove),
            "cutoff_date": cutoff_time
        }