#!/usr/bin/env python3
"""Standalone demonstration of conversation history functionality."""

import streamlit as st
import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

# Import only the conversation history tool (no LangChain dependencies)
from tools.conversation_history_tool import ConversationHistoryTool


class MockAgent:
    """Mock agent for demonstration purposes."""
    
    def __init__(self):
        self.conversation_count = 0
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Simulate processing a query."""
        self.conversation_count += 1
        
        # Simulate different types of responses
        query_lower = query.lower()
        
        if "hello" in query_lower or "hi" in query_lower:
            response = f"Hello! I'm a demo agent. This is conversation #{self.conversation_count}."
            success = True
            steps = 1
            
        elif "calculate" in query_lower or any(op in query_lower for op in ['+', '-', '*', '/', 'math']):
            # Simple calculation simulation
            if "2+2" in query_lower or "2 + 2" in query_lower:
                response = "2 + 2 = 4. This is basic addition."
            elif "15*23" in query_lower or "15 * 23" in query_lower:
                response = "15 * 23 = 345. This is multiplication."
            else:
                response = "I can help with basic calculations. Try asking '2+2' or '15*23'."
            success = True
            steps = 2
            
        elif "history" in query_lower or "previous" in query_lower or "before" in query_lower:
            response = "I'll use the conversation history tool to check our previous conversations."
            success = True
            steps = 1
            
        elif "ai" in query_lower or "artificial intelligence" in query_lower:
            response = "AI (Artificial Intelligence) refers to computer systems that can perform tasks typically requiring human intelligence, such as learning, reasoning, and problem-solving."
            success = True
            steps = 3
            
        elif "error" in query_lower:
            response = "This is a simulated error for testing purposes."
            success = False
            steps = 1
            
        else:
            response = f"I received your message: '{query}'. This is a demo response from conversation #{self.conversation_count}."
            success = True
            steps = 1
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        return {
            "input": query,
            "output": response,
            "success": success,
            "steps": [{"step": i+1, "thought": f"Processing step {i+1}..."} for i in range(steps)]
        }


class ConversationDemo:
    """Demo chatbot with conversation history support."""
    
    def __init__(self):
        self.agent = MockAgent()
        self.conversation_history = []
        self.conversation_tool = ConversationHistoryTool(self)
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Process a chat message."""
        try:
            # Check if this is a conversation history query
            message_lower = message.lower()
            if any(keyword in message_lower for keyword in [
                'history', 'previous', 'before', 'last', 'earlier', 'what did', 'show me'
            ]):
                # Try to use conversation history tool
                try:
                    if 'search' in message_lower and 'ai' in message_lower:
                        result = await self.conversation_tool.execute('{"action": "search", "query": "AI"}')
                    elif 'last' in message_lower and any(word in message_lower for word in ['result', 'answer', 'response']):
                        result = await self.conversation_tool.execute('{"action": "get_last_result"}')
                    elif 'summary' in message_lower:
                        result = await self.conversation_tool.execute('{"action": "get_summary"}')
                    else:
                        count = 3 if 'all' in message_lower else 3
                        result = await self.conversation_tool.execute(f'{{"action": "get_recent", "count": {count}}}')
                    
                    if result.success:
                        response = {
                            "input": message,
                            "output": f"Here's the conversation history:\n\n{result.data}",
                            "success": True,
                            "steps": [{"step": 1, "thought": "Using conversation history tool..."}],
                            "tool_used": "conversation_history"
                        }
                    else:
                        response = await self.agent.process_query(message)
                except Exception as e:
                    response = await self.agent.process_query(message)
            else:
                # Process normally with mock agent
                response = await self.agent.process_query(message)
            
            # Add to conversation history
            conversation_entry = {
                "user": message,
                "assistant": response["output"],
                "success": response["success"],
                "steps": len(response["steps"]),
                "timestamp": time.time(),
                "tool_used": response.get("tool_used")
            }
            
            self.conversation_history.append(conversation_entry)
            
            # Keep only last 20 conversations
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return response
            
        except Exception as e:
            error_response = {
                "input": message,
                "output": f"Error: {str(e)}",
                "success": False,
                "steps": []
            }
            
            self.conversation_history.append({
                "user": message,
                "assistant": error_response["output"],
                "success": False,
                "steps": 0,
                "timestamp": time.time()
            })
            
            return error_response


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Conversation History Demo",
        page_icon="💬",
        layout="wide"
    )
    
    st.title("💬 Conversation History Demo")
    st.markdown("*Demonstrating conversation memory without full React Agent dependencies*")
    
    # Initialize demo chatbot
    if 'demo_chatbot' not in st.session_state:
        st.session_state.demo_chatbot = ConversationDemo()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Sidebar with information
    with st.sidebar:
        st.header("🛠️ Demo Features")
        st.write("This demo shows conversation history functionality:")
        
        st.subheader("💡 Try These Examples")
        examples = [
            "Hello there!",
            "What is 2+2?",
            "Tell me about AI",
            "Calculate 15*23",
            "Show me our conversation history",
            "What did we talk about before?",
            "Give me a summary of our chat",
            "Search our history for AI"
        ]
        
        for example in examples:
            if st.button(f"📝 {example}", key=f"ex_{hash(example)}"):
                # Add user message
                st.session_state.messages.append({"role": "user", "content": example})
                
                # Process and add assistant response
                with st.spinner("Processing..."):
                    response = asyncio.run(st.session_state.demo_chatbot.chat(example))
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response["output"],
                        "metadata": {
                            "success": response["success"],
                            "steps": len(response["steps"]),
                            "tool_used": response.get("tool_used")
                        }
                    })
                st.rerun()
        
        st.divider()
        
        # Show conversation stats
        st.subheader("📊 Session Stats")
        chatbot = st.session_state.demo_chatbot
        total_conversations = len(chatbot.conversation_history)
        successful = sum(1 for conv in chatbot.conversation_history if conv["success"])
        
        st.metric("Total Conversations", total_conversations)
        st.metric("Successful", successful)
        if total_conversations > 0:
            st.metric("Success Rate", f"{(successful/total_conversations*100):.1f}%")
        
        if st.button("🗑️ Clear History"):
            st.session_state.demo_chatbot = ConversationDemo()
            st.session_state.messages = []
            st.rerun()
    
    # Chat interface
    st.subheader("💭 Chat Interface")
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Show metadata for assistant messages
            if message["role"] == "assistant" and "metadata" in message:
                metadata = message["metadata"]
                cols = st.columns(3)
                with cols[0]:
                    st.caption(f"✅ Success: {metadata['success']}")
                with cols[1]:
                    st.caption(f"🔧 Steps: {metadata['steps']}")
                with cols[2]:
                    if metadata.get("tool_used"):
                        st.caption(f"🛠️ Tool: {metadata['tool_used']}")
    
    # Chat input
    if prompt := st.chat_input("Ask me anything or try asking about our conversation history..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Show user message immediately
        with st.chat_message("user"):
            st.write(prompt)
        
        # Process and show assistant response
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                response = asyncio.run(st.session_state.demo_chatbot.chat(prompt))
                st.write(response["output"])
                
                # Show metadata
                cols = st.columns(3)
                with cols[0]:
                    st.caption(f"✅ Success: {response['success']}")
                with cols[1]:
                    st.caption(f"🔧 Steps: {len(response['steps'])}")
                with cols[2]:
                    if response.get("tool_used"):
                        st.caption(f"🛠️ Tool: {response['tool_used']}")
        
        # Add assistant message to session
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response["output"],
            "metadata": {
                "success": response["success"],
                "steps": len(response["steps"]),
                "tool_used": response.get("tool_used")
            }
        })
        
        st.rerun()


if __name__ == "__main__":
    main()