"""Conversation History Tool - Provides access to previous chat conversations."""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_tool import BaseTool, ToolResult


class ConversationHistoryTool(BaseTool):
    """Tool for accessing and searching conversation history."""
    
    def __init__(self, chatbot_instance=None):
        super().__init__(
            name="conversation_history",
            description="""Access previous chat conversations and history. Use this when the user refers to:
        - Previous questions or answers ("what did I ask before", "the last calculation", "what you told me earlier")
        - Continuing a previous topic ("continue with that", "tell me more about it", "what was that about")
        - Referring to past results ("the previous result", "what was the answer", "show me again")
        
        Input format: {"action": "get_recent", "count": 5} OR {"action": "search", "query": "search terms"}"""
        )
        self.chatbot_instance = chatbot_instance
        self._conversation_cache = []
    
    def get_required_params(self) -> List[str]:
        return ["action"]
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the schema for this tool."""
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get_recent", "search", "get_last_result", "get_summary"],
                        "description": "The action to perform"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of conversations to retrieve (for get_recent)",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 5
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (for search action)"
                    }
                },
                "required": ["action"]
            }
        }
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute conversation history retrieval."""
        try:
            # Parse query as JSON if it's a string, otherwise use kwargs
            if isinstance(query, str):
                try:
                    params = json.loads(query)
                except json.JSONDecodeError:
                    # If not JSON, treat as simple action
                    params = {"action": "get_recent", "count": 5}
            else:
                params = query if isinstance(query, dict) else kwargs
            
            action = params.get("action", "get_recent")
            
            # Get conversation history from chatbot instance
            conversations = self._get_conversations()
            
            if not conversations:
                return ToolResult(
                    success=True,
                    data="No previous conversations found in this session.",
                    metadata={"conversations": [], "count": 0}
                )
            
            if action == "get_recent":
                count = params.get("count", 5)
                result = self._get_recent_conversations(conversations, count)
                
            elif action == "search":
                search_query = params.get("query", "")
                if not search_query:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Search query is required when action is 'search'"
                    )
                result = self._search_conversations(conversations, search_query)
                
            elif action == "get_last_result":
                result = self._get_last_successful_result(conversations)
                
            elif action == "get_summary":
                result = self._get_conversation_summary(conversations)
                
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}. Available actions: get_recent, search, get_last_result, get_summary"
                )
            
            return ToolResult(
                success=True,
                data=result["formatted_output"],
                metadata={
                    "conversations": result["raw_conversations"],
                    "count": result["count"],
                    "action_performed": action
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error accessing conversation history: {str(e)}"
            )
    
    def _get_conversations(self) -> List[Dict[str, Any]]:
        """Get conversations from chatbot instance or cache."""
        if self.chatbot_instance and hasattr(self.chatbot_instance, 'conversation_history'):
            return self.chatbot_instance.conversation_history
        return self._conversation_cache
    
    def _get_recent_conversations(self, conversations: List[Dict[str, Any]], count: int) -> Dict[str, Any]:
        """Get the most recent conversations."""
        recent = conversations[-count:] if len(conversations) > count else conversations
        
        formatted_parts = ["Recent conversation history:"]
        
        for i, conv in enumerate(recent, 1):
            timestamp = ""
            if "timestamp" in conv:
                dt = datetime.fromtimestamp(conv["timestamp"])
                timestamp = f" ({dt.strftime('%H:%M:%S')})"
            
            success_indicator = "✅" if conv.get("success", True) else "❌"
            
            formatted_parts.append(f"\n{i}. {success_indicator} User{timestamp}: {conv['user']}")
            
            # Truncate long responses for readability
            assistant_response = conv['assistant']
            if len(assistant_response) > 200:
                assistant_response = assistant_response[:200] + "..."
            
            formatted_parts.append(f"   Assistant: {assistant_response}")
            
            if conv.get("steps", 0) > 0:
                formatted_parts.append(f"   (Used {conv['steps']} reasoning steps)")
        
        return {
            "formatted_output": "\n".join(formatted_parts),
            "raw_conversations": recent,
            "count": len(recent)
        }
    
    def _search_conversations(self, conversations: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Search conversations for specific content."""
        query_lower = query.lower()
        matching_conversations = []
        
        for conv in conversations:
            # Search in user message and assistant response
            if (query_lower in conv['user'].lower() or 
                query_lower in conv['assistant'].lower()):
                matching_conversations.append(conv)
        
        if not matching_conversations:
            return {
                "formatted_output": f"No conversations found matching '{query}'",
                "raw_conversations": [],
                "count": 0
            }
        
        formatted_parts = [f"Found {len(matching_conversations)} conversation(s) matching '{query}':"]
        
        for i, conv in enumerate(matching_conversations, 1):
            timestamp = ""
            if "timestamp" in conv:
                dt = datetime.fromtimestamp(conv["timestamp"])
                timestamp = f" ({dt.strftime('%H:%M:%S')})"
            
            success_indicator = "✅" if conv.get("success", True) else "❌"
            
            formatted_parts.append(f"\n{i}. {success_indicator} User{timestamp}: {conv['user']}")
            
            # Highlight matching parts in response
            assistant_response = conv['assistant']
            if len(assistant_response) > 300:
                # Try to find the matching part and show context around it
                match_index = assistant_response.lower().find(query_lower)
                if match_index >= 0:
                    start = max(0, match_index - 50)
                    end = min(len(assistant_response), match_index + len(query) + 50)
                    assistant_response = "..." + assistant_response[start:end] + "..."
                else:
                    assistant_response = assistant_response[:300] + "..."
            
            formatted_parts.append(f"   Assistant: {assistant_response}")
        
        return {
            "formatted_output": "\n".join(formatted_parts),
            "raw_conversations": matching_conversations,
            "count": len(matching_conversations)
        }
    
    def _get_last_successful_result(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get the last successful conversation result."""
        for conv in reversed(conversations):
            if conv.get("success", False):
                timestamp = ""
                if "timestamp" in conv:
                    dt = datetime.fromtimestamp(conv["timestamp"])
                    timestamp = f" at {dt.strftime('%H:%M:%S')}"
                
                formatted_output = f"Last successful result{timestamp}:\n\nUser: {conv['user']}\nAssistant: {conv['assistant']}"
                
                return {
                    "formatted_output": formatted_output,
                    "raw_conversations": [conv],
                    "count": 1
                }
        
        return {
            "formatted_output": "No successful conversations found in history.",
            "raw_conversations": [],
            "count": 0
        }
    
    def _get_conversation_summary(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get a summary of the conversation session."""
        if not conversations:
            return {
                "formatted_output": "No conversations in this session yet.",
                "raw_conversations": [],
                "count": 0
            }
        
        total = len(conversations)
        successful = sum(1 for conv in conversations if conv.get("success", True))
        failed = total - successful
        
        # Get topics discussed (simple keyword extraction)
        topics = set()
        for conv in conversations:
            # Extract potential topics from user messages
            words = conv['user'].lower().split()
            for word in words:
                if len(word) > 4 and word not in ['what', 'how', 'why', 'when', 'where', 'tell', 'explain', 'show']:
                    topics.add(word)
        
        topics_list = list(topics)[:10]  # Limit to first 10 topics
        
        if conversations[0].get("timestamp"):
            start_time = datetime.fromtimestamp(conversations[0]["timestamp"])
            end_time = datetime.fromtimestamp(conversations[-1]["timestamp"])
            duration = end_time - start_time
            duration_str = f"Session duration: {duration}"
        else:
            duration_str = "Session timing not available"
        
        summary_parts = [
            f"Conversation Session Summary:",
            f"- Total conversations: {total}",
            f"- Successful: {successful}",
            f"- Failed: {failed}",
            f"- Success rate: {(successful/total*100):.1f}%" if total > 0 else "- Success rate: 0%",
            f"- {duration_str}",
        ]
        
        if topics_list:
            summary_parts.append(f"- Topics discussed: {', '.join(topics_list[:5])}")
        
        return {
            "formatted_output": "\n".join(summary_parts),
            "raw_conversations": conversations,
            "count": total
        }
    
    def set_chatbot_instance(self, chatbot_instance):
        """Set the chatbot instance to access conversation history."""
        self.chatbot_instance = chatbot_instance
    
    def add_conversation_to_cache(self, user_message: str, assistant_response: str, 
                                success: bool = True, steps: int = 0):
        """Add conversation to internal cache (fallback if no chatbot instance)."""
        self._conversation_cache.append({
            "user": user_message,
            "assistant": assistant_response,
            "success": success,
            "steps": steps,
            "timestamp": time.time()
        })
        
        # Keep only last 50 conversations in cache
        if len(self._conversation_cache) > 50:
            self._conversation_cache = self._conversation_cache[-50:]