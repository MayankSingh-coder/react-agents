"""Streamlit web interface for the React Agent."""

# Import gRPC configuration first to suppress warnings
import grpc_config

import streamlit as st
import asyncio
import json
import nest_asyncio
from datetime import datetime
from chatbot import ReactChatbot
from async_utils import run_async_safe

# Enable nested event loops for Streamlit compatibility
nest_asyncio.apply()


async def run_chatbot_safely(chatbot, prompt):
    """Safely run the chatbot with proper async handling."""
    try:
        return await chatbot.chat(prompt)
    except Exception as e:
        return {
            "input": prompt,
            "output": f"I apologize, but I encountered an error: {str(e)}",
            "steps": [],
            "success": False,
            "error": str(e),
            "metadata": {}
        }


# Page configuration
st.set_page_config(
    page_title="Octopus Prime Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "chatbot" not in st.session_state:
    st.session_state.chatbot = ReactChatbot(verbose=False)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_steps" not in st.session_state:
    st.session_state.show_steps = False
if "streaming_mode" not in st.session_state:
    st.session_state.streaming_mode = False


def main():
    """Main Streamlit application."""
    
    # Title and description
    st.title("🤖 Octopus Prime Chatbot")
    st.markdown("I am Octopus Prime, your intelligent assistant. I can help you with various tasks and provide information.")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Real-time thinking mode
        if st.button("🧠 Switch to Real-time Thinking Mode", type="primary"):
            st.switch_page("web_interface_streaming.py")
        
        st.divider()
        
        # Show reasoning steps toggle
        st.session_state.show_steps = st.checkbox(
            "Show reasoning steps", 
            value=st.session_state.show_steps,
            help="Display the agent's thought process and tool usage"
        )
        
        st.divider()
        
        # Statistics
        st.header("📊 Statistics")
        if st.button("Refresh Stats"):
            stats = st.session_state.chatbot.get_stats()
            st.json(stats)
        
        st.divider()
        
        # Clear conversation
        if st.button("🧹 Clear Conversation", type="secondary"):
            st.session_state.messages = []
            st.session_state.chatbot.clear_history()
            st.rerun()
        
        st.divider()
        
        # Available tools
        st.header("🔧 Available Tools")
        tools = st.session_state.chatbot.agent.tool_manager.get_tool_descriptions()
        for tool_name, description in tools.items():
            st.write(f"**{tool_name}**: {description}")
    
    # Main chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Show reasoning steps if enabled and available
                if (st.session_state.show_steps and 
                    message["role"] == "assistant" and 
                    "steps" in message):
                    
                    with st.expander("🧠 Reasoning Steps", expanded=False):
                        for i, step in enumerate(message["steps"], 1):
                            st.write(f"**Step {i}:**")
                            st.write(f"💭 **Thought**: {step['thought']}")
                            
                            if step.get('action'):
                                st.write(f"🔧 **Action**: {step['action']}")
                                st.write(f"📝 **Input**: {step['action_input']}")
                            
                            if step.get('observation'):
                                st.write(f"👁️ **Observation**: {step['observation']}")
                            
                            if i < len(message["steps"]):
                                st.divider()
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Run the chatbot asynchronously with proper event loop handling
                response = run_async_safe(run_chatbot_safely(st.session_state.chatbot, prompt))
                
                # Display response
                if response["success"]:
                    st.write(response["output"])
                    
                    # Add to session state with steps
                    assistant_message = {
                        "role": "assistant", 
                        "content": response["output"],
                        "steps": response["steps"] if st.session_state.show_steps else []
                    }
                    st.session_state.messages.append(assistant_message)
                    
                else:
                    error_msg = f"❌ Error: {response['error']}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })
        
        # Rerun to update the interface
        st.rerun()


if __name__ == "__main__":
    main()