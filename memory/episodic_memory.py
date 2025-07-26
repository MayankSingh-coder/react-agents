"""Episodic memory for storing and retrieving past experiences."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from .memory_store import MemoryStore, MemoryType
from .vector_memory import VectorMemory


@dataclass
class Episode:
    """Represents a complete interaction episode."""
    id: str
    query: str
    response: str
    reasoning_steps: List[Dict[str, Any]]
    tools_used: List[str]
    success: bool
    duration: float
    timestamp: float
    importance: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class EpisodicMemory:
    """Manages episodic memories of past interactions."""
    
    def __init__(self, memory_store: MemoryStore, vector_memory: VectorMemory):
        self.memory_store = memory_store
        self.vector_memory = vector_memory
        self.episodes: Dict[str, Episode] = {}
    
    async def store_episode(self, episode: Episode) -> str:
        """Store a complete episode."""
        # Store in local cache
        self.episodes[episode.id] = episode
        
        # Store in memory store
        await self.memory_store.remember(
            content=episode.to_dict(),
            memory_type=MemoryType.EPISODIC,
            importance=episode.importance,
            metadata={
                "episode_id": episode.id,
                "success": episode.success,
                "tools_used": episode.tools_used,
                "duration": episode.duration
            }
        )
        
        # Store in vector memory for similarity search
        episode_text = f"Query: {episode.query}\nResponse: {episode.response}\nTools: {', '.join(episode.tools_used)}"
        self.vector_memory.add_entry(
            content=episode_text,
            metadata={
                "episode_id": episode.id,
                "success": episode.success,
                "tools_used": episode.tools_used
            },
            importance=episode.importance
        )
        
        return episode.id
    
    async def find_similar_episodes(self, query: str, top_k: int = 5) -> List[Tuple[Episode, float]]:
        """Find episodes similar to the current query."""
        # Search using vector similarity
        similar_entries = self.vector_memory.search_similar(query, top_k=top_k)
        
        results = []
        for entry, similarity in similar_entries:
            episode_id = entry.metadata.get("episode_id")
            if episode_id and episode_id in self.episodes:
                episode = self.episodes[episode_id]
                results.append((episode, similarity))
        
        return results
    
    async def get_successful_patterns(self, query: str) -> List[Dict[str, Any]]:
        """Get patterns from successful episodes similar to the query."""
        similar_episodes = await self.find_similar_episodes(query, top_k=10)
        
        successful_patterns = []
        for episode, similarity in similar_episodes:
            if episode.success and similarity > 0.3:
                pattern = {
                    "tools_sequence": episode.tools_used,
                    "reasoning_approach": [step.get("thought", "") for step in episode.reasoning_steps],
                    "similarity": similarity,
                    "success_rate": 1.0,
                    "episode_id": episode.id
                }
                successful_patterns.append(pattern)
        
        return successful_patterns
    
    async def get_episode_stats(self) -> Dict[str, Any]:
        """Get statistics about stored episodes."""
        total_episodes = len(self.episodes)
        successful_episodes = sum(1 for ep in self.episodes.values() if ep.success)
        failed_episodes = total_episodes - successful_episodes
        
        if total_episodes == 0:
            return {
                "total_episodes": 0,
                "successful_episodes": 0,
                "failed_episodes": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "tools_usage": {},
                "recent_episodes": []
            }
        
        # Calculate average duration
        avg_duration = sum(ep.duration for ep in self.episodes.values()) / total_episodes
        
        # Count tool usage
        tools_usage = {}
        for episode in self.episodes.values():
            for tool in episode.tools_used:
                tools_usage[tool] = tools_usage.get(tool, 0) + 1
        
        # Get recent episodes (last 5)
        recent_episodes = sorted(
            self.episodes.values(), 
            key=lambda x: x.timestamp, 
            reverse=True
        )[:5]
        
        recent_episode_info = [
            {
                "id": ep.id,
                "query": ep.query[:100] + "..." if len(ep.query) > 100 else ep.query,
                "success": ep.success,
                "duration": ep.duration,
                "tools_used": ep.tools_used
            }
            for ep in recent_episodes
        ]
        
        return {
            "total_episodes": total_episodes,
            "successful_episodes": successful_episodes,
            "failed_episodes": failed_episodes,
            "success_rate": successful_episodes / total_episodes if total_episodes > 0 else 0.0,
            "average_duration": avg_duration,
            "tools_usage": tools_usage,
            "recent_episodes": recent_episode_info
        }