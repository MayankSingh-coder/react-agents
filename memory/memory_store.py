"""Industry-standard memory store implementation."""

import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


class MemoryType(Enum):
    """Types of memory in the agent system."""
    SHORT_TERM = "short_term"      # Current conversation/session
    WORKING = "working"            # Active reasoning context
    EPISODIC = "episodic"         # Past experiences/conversations
    SEMANTIC = "semantic"         # Factual knowledge
    PROCEDURAL = "procedural"     # How-to knowledge/patterns
    TOOL_CONTEXT = "tool_context" # Context shared between tools
    PLAN_MEMORY = "plan_memory"   # Planning and execution history


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    content: Any
    memory_type: MemoryType
    timestamp: float
    metadata: Dict[str, Any]
    importance: float = 0.5  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary."""
        data['memory_type'] = MemoryType(data['memory_type'])
        return cls(**data)


class BaseMemoryStore(ABC):
    """Abstract base class for memory stores."""
    
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry."""
        pass
    
    @abstractmethod
    async def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory entry."""
        pass
    
    @abstractmethod
    async def search(self, query: str, memory_type: Optional[MemoryType] = None, 
                    limit: int = 10) -> List[MemoryEntry]:
        """Search memory entries."""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        pass


class InMemoryStore(BaseMemoryStore):
    """In-memory implementation of memory store."""
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.memories: Dict[str, MemoryEntry] = {}
        self.type_index: Dict[MemoryType, List[str]] = {
            memory_type: [] for memory_type in MemoryType
        }
    
    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry."""
        # Generate ID if not provided
        if not entry.id:
            entry.id = self._generate_id(entry.content)
        
        # Update timestamps
        entry.timestamp = time.time()
        entry.last_accessed = entry.timestamp
        
        # Store the entry
        self.memories[entry.id] = entry
        
        # Update type index
        if entry.id not in self.type_index[entry.memory_type]:
            self.type_index[entry.memory_type].append(entry.id)
        
        # Cleanup if needed
        await self._cleanup_if_needed()
        
        return entry.id
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory entry."""
        entry = self.memories.get(memory_id)
        if entry:
            entry.access_count += 1
            entry.last_accessed = time.time()
        return entry
    
    async def search(self, query: str, memory_type: Optional[MemoryType] = None, 
                    limit: int = 10) -> List[MemoryEntry]:
        """Search memory entries."""
        query_lower = query.lower()
        results = []
        
        # Determine which entries to search
        if memory_type:
            search_ids = self.type_index[memory_type]
        else:
            search_ids = list(self.memories.keys())
        
        # Search and score entries
        scored_results = []
        for memory_id in search_ids:
            entry = self.memories[memory_id]
            score = self._calculate_relevance_score(entry, query_lower)
            if score > 0:
                scored_results.append((score, entry))
        
        # Sort by relevance and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_results[:limit]]
    
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        if memory_id in self.memories:
            entry = self.memories[memory_id]
            del self.memories[memory_id]
            
            # Remove from type index
            if memory_id in self.type_index[entry.memory_type]:
                self.type_index[entry.memory_type].remove(memory_id)
            
            return True
        return False
    
    async def get_by_type(self, memory_type: MemoryType, limit: int = 100) -> List[MemoryEntry]:
        """Get entries by memory type."""
        memory_ids = self.type_index[memory_type][:limit]
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def _generate_id(self, content: Any) -> str:
        """Generate a unique ID for content."""
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _calculate_relevance_score(self, entry: MemoryEntry, query: str) -> float:
        """Calculate relevance score for search."""
        content_str = json.dumps(entry.content, default=str).lower()
        metadata_str = json.dumps(entry.metadata, default=str).lower()
        
        # Simple keyword matching with weights
        content_score = sum(1 for word in query.split() if word in content_str)
        metadata_score = sum(0.5 for word in query.split() if word in metadata_str)
        
        # Factor in importance and recency
        importance_boost = entry.importance
        recency_boost = max(0, 1 - (time.time() - entry.timestamp) / 86400)  # Decay over 24h
        
        total_score = (content_score + metadata_score) * (1 + importance_boost + recency_boost * 0.1)
        return total_score
    
    async def _cleanup_if_needed(self):
        """Clean up old entries if memory is full."""
        if len(self.memories) > self.max_entries:
            # Remove least important, least accessed, oldest entries
            entries_to_remove = []
            
            for entry in self.memories.values():
                score = (entry.importance * 0.4 + 
                        min(entry.access_count / 10, 1.0) * 0.3 +
                        max(0, 1 - (time.time() - entry.timestamp) / 86400) * 0.3)
                entries_to_remove.append((score, entry.id))
            
            # Sort by score and remove lowest scoring entries
            entries_to_remove.sort()
            remove_count = len(self.memories) - int(self.max_entries * 0.9)
            
            for _, memory_id in entries_to_remove[:remove_count]:
                await self.delete(memory_id)


class MemoryStore:
    """Main memory store interface."""
    
    def __init__(self, store: Optional[BaseMemoryStore] = None):
        self.store = store or InMemoryStore()
    
    async def remember(self, content: Any, memory_type: MemoryType, 
                      importance: float = 0.5, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a new memory."""
        entry = MemoryEntry(
            id="",  # Will be generated
            content=content,
            memory_type=memory_type,
            timestamp=time.time(),
            metadata=metadata or {},
            importance=importance
        )
        return await self.store.store(entry)
    
    async def recall(self, memory_id: str) -> Optional[MemoryEntry]:
        """Recall a specific memory."""
        return await self.store.retrieve(memory_id)
    
    async def search_memories(self, query: str, memory_type: Optional[MemoryType] = None, 
                             limit: int = 10) -> List[MemoryEntry]:
        """Search for relevant memories."""
        return await self.store.search(query, memory_type, limit)
    
    async def forget(self, memory_id: str) -> bool:
        """Delete a memory."""
        return await self.store.delete(memory_id)
    
    async def get_context_memories(self, limit: int = 50) -> List[MemoryEntry]:
        """Get memories relevant for current context."""
        # Get recent working memory and important episodic memories
        working_memories = await self.store.get_by_type(MemoryType.WORKING, limit // 2)
        episodic_memories = await self.store.get_by_type(MemoryType.EPISODIC, limit // 2)
        
        # Sort by importance and recency
        all_memories = working_memories + episodic_memories
        all_memories.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        
        return all_memories[:limit]