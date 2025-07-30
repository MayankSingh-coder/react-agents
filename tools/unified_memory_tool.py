"""Unified Memory Tool - Single interface for all memory operations."""

import json
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .base_tool import BaseTool, ToolResult
from memory.memory_store import MemoryStore, MemoryType
from memory.episodic_memory import EpisodicMemory
from memory.context_manager import ContextManager
from memory.vector_memory import VectorMemory


class UnifiedMemoryTool(BaseTool):
    """Unified tool for all memory operations including conversation history, episodic memory, and context."""
    
    def __init__(self, memory_store: MemoryStore, episodic_memory: EpisodicMemory, 
                 context_manager: ContextManager, vector_memory: VectorMemory):
        super().__init__(
            name="memory",
            description="""Access all types of memory including:
        - Conversation history (previous questions/answers)
        - Episodic memory (past experiences and episodes)
        - Working memory (current session context)
        - Shared variables between tools
        - Semantic search across all memory types
        
        Use this when you need to:
        - Reference previous conversations or results
        - Find similar past experiences
        - Access shared context or variables
        - Search for specific information across memory
        
        Input format: {"type": "conversation|episodic|context|search|shared_vars", "query": "...", "limit": 10}"""
        )
        self.memory_store = memory_store
        self.episodic_memory = episodic_memory
        self.context_manager = context_manager
        self.vector_memory = vector_memory
    
    def get_required_params(self) -> List[str]:
        return ["type"]
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the schema for this tool."""
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["conversation", "episodic", "context", "search", "shared_vars", "similar", "stats"],
                        "description": "Type of memory operation to perform"
                    },
                    "query": {
                        "type": "string",
                        "description": "Query string for search operations or context description"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["short_term", "working", "episodic", "semantic", "procedural", "tool_context", "plan_memory"],
                        "description": "Specific memory type to search (for search operations)"
                    },
                    "success_only": {
                        "type": "boolean",
                        "description": "Only return successful episodes/conversations",
                        "default": false
                    }
                },
                "required": ["type"]
            }
        }
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute memory operation."""
        try:
            # Parse query as JSON if it's a string, otherwise use kwargs
            if isinstance(query, str):
                try:
                    params = json.loads(query)
                except json.JSONDecodeError:
                    # If not JSON, treat as search query
                    params = {"type": "search", "query": query}
            else:
                params = query if isinstance(query, dict) else kwargs
            
            operation_type = params.get("type", "search")
            search_query = params.get("query", "")
            limit = params.get("limit", 10)
            memory_type_str = params.get("memory_type")
            success_only = params.get("success_only", False)
            
            # Convert memory type string to enum if provided
            memory_type = None
            if memory_type_str:
                try:
                    memory_type = MemoryType(memory_type_str)
                except ValueError:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Invalid memory type: {memory_type_str}"
                    )
            
            if operation_type == "conversation":
                result = await self._get_conversation_history(search_query, limit, success_only)
                
            elif operation_type == "episodic":
                result = await self._get_episodic_memories(search_query, limit, success_only)
                
            elif operation_type == "context":
                result = await self._get_context_information(search_query)
                
            elif operation_type == "search":
                result = await self._search_all_memories(search_query, memory_type, limit)
                
            elif operation_type == "shared_vars":
                result = await self._get_shared_variables(search_query)
                
            elif operation_type == "similar":
                result = await self._find_similar_experiences(search_query, limit)
                
            elif operation_type == "stats":
                result = await self._get_memory_stats()
                
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown memory operation: {operation_type}. Available: conversation, episodic, context, search, shared_vars, similar, stats"
                )
            
            return ToolResult(
                success=True,
                data=result["formatted_output"],
                metadata={
                    "operation": operation_type,
                    "raw_data": result.get("raw_data", {}),
                    "count": result.get("count", 0),
                    "query": search_query
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Memory operation failed: {str(e)}"
            )
    
    async def _get_conversation_history(self, query: str, limit: int, success_only: bool) -> Dict[str, Any]:
        """Get conversation history (recent or search)."""
        # Try to get from episodic memory first
        episodes = list(self.episodic_memory.episodes.values())
        
        if query:
            # Search for specific conversations
            query_lower = query.lower()
            matching_episodes = [
                ep for ep in episodes 
                if query_lower in ep.query.lower() or query_lower in ep.response.lower()
            ]
        else:
            # Get recent conversations
            matching_episodes = sorted(episodes, key=lambda x: x.timestamp, reverse=True)
        
        if success_only:
            matching_episodes = [ep for ep in matching_episodes if ep.success]
        
        matching_episodes = matching_episodes[:limit]
        
        if not matching_episodes:
            return {
                "formatted_output": "No conversation history found matching your criteria.",
                "raw_data": [],
                "count": 0
            }
        
        formatted_parts = [f"Found {len(matching_episodes)} conversation(s):"]
        
        for i, episode in enumerate(matching_episodes, 1):
            dt = datetime.fromtimestamp(episode.timestamp)
            success_indicator = "✅" if episode.success else "❌"
            
            formatted_parts.append(f"\n{i}. {success_indicator} [{dt.strftime('%H:%M:%S')}]")
            formatted_parts.append(f"   User: {episode.query}")
            
            # Truncate long responses
            response = episode.response
            if len(response) > 200:
                response = response[:200] + "..."
            formatted_parts.append(f"   Assistant: {response}")
            
            if episode.tools_used:
                formatted_parts.append(f"   Tools used: {', '.join(episode.tools_used)}")
        
        return {
            "formatted_output": "\n".join(formatted_parts),
            "raw_data": [ep.to_dict() for ep in matching_episodes],
            "count": len(matching_episodes)
        }
    
    async def _get_episodic_memories(self, query: str, limit: int, success_only: bool) -> Dict[str, Any]:
        """Get episodic memories with detailed reasoning steps."""
        if query:
            similar_episodes = await self.episodic_memory.find_similar_episodes(query, limit)
            episodes_with_similarity = [(ep, sim) for ep, sim in similar_episodes]
        else:
            episodes = list(self.episodic_memory.episodes.values())
            if success_only:
                episodes = [ep for ep in episodes if ep.success]
            episodes = sorted(episodes, key=lambda x: x.importance, reverse=True)[:limit]
            episodes_with_similarity = [(ep, 1.0) for ep in episodes]
        
        if not episodes_with_similarity:
            return {
                "formatted_output": "No episodic memories found matching your criteria.",
                "raw_data": [],
                "count": 0
            }
        
        formatted_parts = [f"Found {len(episodes_with_similarity)} episodic memor(y/ies):"]
        
        for i, (episode, similarity) in enumerate(episodes_with_similarity, 1):
            dt = datetime.fromtimestamp(episode.timestamp)
            success_indicator = "✅" if episode.success else "❌"
            
            formatted_parts.append(f"\n{i}. {success_indicator} Episode [{dt.strftime('%H:%M:%S')}] (Similarity: {similarity:.2f})")
            formatted_parts.append(f"   Query: {episode.query}")
            formatted_parts.append(f"   Duration: {episode.duration:.2f}s")
            formatted_parts.append(f"   Tools: {', '.join(episode.tools_used)}")
            formatted_parts.append(f"   Reasoning steps: {len(episode.reasoning_steps)}")
            
            # Show key reasoning insights
            if episode.reasoning_steps:
                formatted_parts.append("   Key insights:")
                for j, step in enumerate(episode.reasoning_steps[:3], 1):
                    thought = step.get("thought", "")[:100] + "..." if len(step.get("thought", "")) > 100 else step.get("thought", "")
                    formatted_parts.append(f"     {j}. {thought}")
        
        return {
            "formatted_output": "\n".join(formatted_parts),
            "raw_data": [(ep.to_dict(), sim) for ep, sim in episodes_with_similarity],
            "count": len(episodes_with_similarity)
        }
    
    async def _get_context_information(self, tool_name: str) -> Dict[str, Any]:
        """Get current context information for a tool or general context."""
        if tool_name:
            context = await self.context_manager.get_relevant_context(tool_name, tool_name)
        else:
            # Get general context
            context = {
                "shared_variables": self.context_manager.get_all_shared_variables(),
                "reasoning_history": [
                    {
                        "thought": step.thought,
                        "action": step.planned_action,
                        "confidence": step.confidence
                    }
                    for step in self.context_manager.reasoning_steps[-5:]
                ],
                "tool_contexts": {
                    tool: [tc.__dict__ for tc in contexts[-3:]]  # Last 3 contexts per tool
                    for tool, contexts in self.context_manager.tool_contexts.items()
                }
            }
        
        # Format the output
        formatted_parts = ["Current Context Information:"]
        
        # Shared variables
        shared_vars = context.get("shared_variables", {})
        if shared_vars:
            formatted_parts.append("\n📊 Shared Variables:")
            for key, value in shared_vars.items():
                formatted_parts.append(f"   • {key}: {value}")
        
        # Reasoning history
        reasoning = context.get("reasoning_history", [])
        if reasoning:
            formatted_parts.append("\n🧠 Recent Reasoning:")
            for i, step in enumerate(reasoning[-3:], 1):
                formatted_parts.append(f"   {i}. {step.get('thought', 'No thought')[:100]}...")
                if step.get('action'):
                    formatted_parts.append(f"      Action: {step['action']}")
        
        # Tool results
        tool_results = context.get("previous_tool_results", {})
        if tool_results:
            formatted_parts.append("\n🛠️ Recent Tool Results:")
            for tool, result in tool_results.items():
                formatted_parts.append(f"   • {tool}: Success")
        
        return {
            "formatted_output": "\n".join(formatted_parts),
            "raw_data": context,
            "count": len(shared_vars) + len(reasoning) + len(tool_results)
        }
    
    async def _search_all_memories(self, query: str, memory_type: Optional[MemoryType], limit: int) -> Dict[str, Any]:
        """Search across all memory systems."""
        results = []
        
        # Search memory store
        memory_results = await self.memory_store.search_memories(query, memory_type, limit)
        results.extend([("memory_store", memory) for memory in memory_results])
        
        # Search episodic memory
        if not memory_type or memory_type == MemoryType.EPISODIC:
            episodic_results = await self.episodic_memory.find_similar_episodes(query, limit // 2)
            results.extend([("episodic", (episode, similarity)) for episode, similarity in episodic_results])
        
        # Search vector memory
        vector_results = self.vector_memory.search_similar(query, top_k=limit // 2)
        results.extend([("vector", entry_sim) for entry_sim in vector_results])
        
        # Sort by relevance/similarity
        def get_score(item):
            source, data = item
            if source == "episodic":
                return data[1]  # similarity score
            elif source == "vector":
                return data[1]  # similarity score
            else:
                return data.importance  # importance score
        
        results.sort(key=get_score, reverse=True)
        results = results[:limit]
        
        if not results:
            return {
                "formatted_output": f"No memories found matching '{query}'",
                "raw_data": [],
                "count": 0
            }
        
        formatted_parts = [f"Found {len(results)} memor(y/ies) matching '{query}':"]
        
        for i, (source, data) in enumerate(results, 1):
            if source == "episodic":
                episode, similarity = data
                dt = datetime.fromtimestamp(episode.timestamp)
                formatted_parts.append(f"\n{i}. [EPISODIC] {episode.query[:100]}... [{dt.strftime('%H:%M:%S')}] (sim: {similarity:.2f})")
            elif source == "vector":
                entry, similarity = data
                formatted_parts.append(f"\n{i}. [VECTOR] {str(entry.content)[:100]}... (sim: {similarity:.2f})")
            else:
                memory = data
                dt = datetime.fromtimestamp(memory.timestamp)
                formatted_parts.append(f"\n{i}. [MEMORY] {str(memory.content)[:100]}... [{dt.strftime('%H:%M:%S')}] (imp: {memory.importance:.2f})")
        
        return {
            "formatted_output": "\n".join(formatted_parts),
            "raw_data": results,
            "count": len(results)
        }
    
    async def _get_shared_variables(self, filter_key: str) -> Dict[str, Any]:
        """Get shared variables, optionally filtered."""
        all_vars = self.context_manager.get_all_shared_variables()
        
        if filter_key:
            # Filter variables by key pattern
            filtered_vars = {k: v for k, v in all_vars.items() if filter_key.lower() in k.lower()}
        else:
            filtered_vars = all_vars
        
        if not filtered_vars:
            return {
                "formatted_output": "No shared variables found" + (f" matching '{filter_key}'" if filter_key else ""),
                "raw_data": {},
                "count": 0
            }
        
        formatted_parts = [f"Shared Variables ({len(filtered_vars)} found):"]
        
        for key, value in filtered_vars.items():
            formatted_parts.append(f"\n📊 {key}:")
            formatted_parts.append(f"   Value: {value}")
        
        return {
            "formatted_output": "\n".join(formatted_parts),
            "raw_data": filtered_vars,
            "count": len(filtered_vars)
        }
    
    async def _find_similar_experiences(self, query: str, limit: int) -> Dict[str, Any]:
        """Find similar past experiences across all memory types."""
        # Get successful patterns from episodic memory
        patterns = await self.episodic_memory.get_successful_patterns(query)
        
        formatted_parts = [f"Found {len(patterns)} similar successful pattern(s):"]
        
        for i, pattern in enumerate(patterns[:limit], 1):
            formatted_parts.append(f"\n{i}. Success Pattern (similarity: {pattern['similarity']:.2f})")
            formatted_parts.append(f"   Tools sequence: {' → '.join(pattern['tools_sequence'])}")
            formatted_parts.append(f"   Key reasoning: {pattern['reasoning_approach'][0][:100]}..." if pattern['reasoning_approach'] else "   No reasoning available")
        
        return {
            "formatted_output": "\n".join(formatted_parts),
            "raw_data": patterns,
            "count": len(patterns)
        }
    
    async def _get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        # Episodic memory stats
        episodic_stats = await self.episodic_memory.get_episode_stats()
        
        # Memory store stats by type
        memory_counts = {}
        for memory_type in MemoryType:
            memories = await self.memory_store.store.get_by_type(memory_type, limit=1000)
            memory_counts[memory_type.value] = len(memories)
        
        # Context manager stats
        context_stats = {
            "reasoning_steps": len(self.context_manager.reasoning_steps),
            "shared_variables": len(self.context_manager.shared_variables),
            "tool_contexts": len(self.context_manager.tool_contexts),
            "current_session": self.context_manager.current_session_id
        }
        
        formatted_parts = [
            "Memory System Statistics:",
            f"\n📊 Episodic Memory:",
            f"   • Total episodes: {episodic_stats['total_episodes']}",
            f"   • Success rate: {episodic_stats['success_rate']:.1%}",
            f"   • Average duration: {episodic_stats['average_duration']:.2f}s",
            f"\n🧠 Memory Store:",
        ]
        
        for mem_type, count in memory_counts.items():
            if count > 0:
                formatted_parts.append(f"   • {mem_type}: {count} entries")
        
        formatted_parts.extend([
            f"\n🔄 Current Context:",
            f"   • Session ID: {context_stats['current_session']}",
            f"   • Reasoning steps: {context_stats['reasoning_steps']}",
            f"   • Shared variables: {context_stats['shared_variables']}",
            f"   • Active tool contexts: {context_stats['tool_contexts']}"
        ])
        
        if episodic_stats['tools_usage']:
            formatted_parts.append(f"\n🛠️ Tool Usage:")
            for tool, count in sorted(episodic_stats['tools_usage'].items(), key=lambda x: x[1], reverse=True)[:5]:
                formatted_parts.append(f"   • {tool}: {count} times")
        
        return {
            "formatted_output": "\n".join(formatted_parts),
            "raw_data": {
                "episodic_stats": episodic_stats,
                "memory_counts": memory_counts,
                "context_stats": context_stats
            },
            "count": sum(memory_counts.values()) + episodic_stats['total_episodes']
        }