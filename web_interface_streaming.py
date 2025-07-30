"""Streamlit web interface with real-time thinking display."""

# Import gRPC configuration first to suppress warnings
import grpc_config

import streamlit as st
import asyncio
import json
import time
import nest_asyncio
from datetime import datetime
from typing import Dict, Any, List

from streaming_agent import StreamingChatbot, EventType, StreamingEvent
from async_utils import run_async_safe

# Enable nested event loops for Streamlit compatibility
nest_asyncio.apply()


class ThinkingDisplay:
    """Manages the real-time thinking display."""
    
    def __init__(self):
        self.current_step = 0
        self.thinking_container = None
        self.status_container = None
    
    def initialize_containers(self):
        """Initialize Streamlit containers for display."""
        self.status_container = st.empty()
        self.thinking_container = st.empty()
    
    def update_status(self, message: str, status_type: str = "info"):
        """Update the status display."""
        if self.status_container:
            if status_type == "thinking":
                self.status_container.info(f"🤔 {message}")
            elif status_type == "action":
                self.status_container.warning(f"🔧 {message}")
            elif status_type == "success":
                self.status_container.success(f"✅ {message}")
            elif status_type == "error":
                self.status_container.error(f"❌ {message}")
            else:
                self.status_container.info(f"ℹ️ {message}")
    
    def add_event(self, event: StreamingEvent):
        """Add an event to the display."""
        st.session_state.current_thinking_events.append(event)
        # Don't render in real-time to avoid duplication
        # self._render_thinking()
    
    def render_final_thinking(self):
        """Render the final thinking process after completion."""
        if not st.session_state.current_thinking_events:
            return
            
        st.markdown("### 🧠 Agent Thinking Process")
        
        # Group events by step
        steps = {}
        for event in st.session_state.current_thinking_events:
            step = event.step
            if step not in steps:
                steps[step] = []
            steps[step].append(event)
        
        # Display each step
        for step_num in sorted(steps.keys()):
            if step_num == 0:
                continue
                
            step_events = steps[step_num]
            
            with st.expander(f"Step {step_num}", expanded=False):
                for event in step_events:
                    self._render_event(event)
    
    def _render_thinking(self):
        """Render the current thinking process."""
        if not self.thinking_container or not st.session_state.current_thinking_events:
            return
        
        # Only update the thinking container content, don't recreate it
        with self.thinking_container.container():
            st.markdown("### 🧠 Agent Thinking Process")
            
            # Group events by step
            steps = {}
            for event in st.session_state.current_thinking_events:
                step = event.step
                if step not in steps:
                    steps[step] = []
                steps[step].append(event)
            
            # Display each step
            for step_num in sorted(steps.keys()):
                if step_num == 0:
                    continue
                    
                step_events = steps[step_num]
                
                with st.expander(f"Step {step_num}", expanded=(step_num == max(steps.keys()))):
                    for event in step_events:
                        self._render_event(event)
    
    def _render_event(self, event: StreamingEvent):
        """Render a single event."""
        timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S.%f")[:-3]
        
        if event.type == EventType.THINKING_START:
            st.markdown(f"**{timestamp}** - 🤔 Starting to think...")
            
        elif event.type == EventType.THINKING:
            thought = event.data.get("thought", "")
            st.markdown(f"**{timestamp}** - 💭 **Thought:**")
            st.markdown(f"```\n{thought}\n```")
            
        elif event.type == EventType.ACTION_PLANNED:
            action = event.data.get("action", "")
            action_input = event.data.get("input", "")
            st.markdown(f"**{timestamp}** - 📋 **Action Planned:** `{action}`")
            if action_input:
                st.markdown(f"**Input:** `{action_input}`")
                
        elif event.type == EventType.ACTION_START:
            action = event.data.get("action", "")
            st.markdown(f"**{timestamp}** - 🔧 **Executing Action:** `{action}`")
            
        elif event.type == EventType.ACTION_RESULT:
            tool = event.data.get("tool", "")
            result = event.data.get("result", {})
            st.markdown(f"**{timestamp}** - 📤 **Tool Result from {tool}:**")
            if result.get("success"):
                st.success(f"Success: {result.get('data', 'No data')}")
            else:
                st.error(f"Error: {result.get('error', 'Unknown error')}")
                
        elif event.type == EventType.OBSERVATION:
            observation = event.data.get("observation", "")
            st.markdown(f"**{timestamp}** - 👁️ **Observation:**")
            st.markdown(f"```\n{observation}\n```")
            
        elif event.type == EventType.PLAN_CREATED:
            plan = event.data.get("plan", {})
            st.markdown(f"**{timestamp}** - 📋 **Plan Created:**")
            st.markdown(f"**Description:** {plan.get('description', 'No description')}")
            
            steps = plan.get("steps", [])
            if steps:
                st.markdown("**Steps:**")
                for i, step in enumerate(steps, 1):
                    st.markdown(f"{i}. **{step.get('tool', 'Unknown')}**: {step.get('description', 'No description')}")
                    
        elif event.type == EventType.PLAN_STEP_START:
            step_desc = event.data.get("step_description", "")
            tool = event.data.get("tool", "")
            plan_step = event.data.get("plan_step", 0)
            total_steps = event.data.get("total_steps", 0)
            st.markdown(f"**{timestamp}** - 🎯 **Plan Step {plan_step}/{total_steps}:** `{tool}`")
            st.markdown(f"_{step_desc}_")
            
        elif event.type == EventType.PLAN_STEP_COMPLETE:
            st.markdown(f"**{timestamp}** - ✅ **Plan Execution Complete**")
            
        elif event.type == EventType.STRATEGY_SELECTION:
            query = event.data.get("query", "")
            status = event.data.get("status", "")
            method = event.data.get("method", "")
            
            if status == "analyzing":
                st.markdown(f"**{timestamp}** - 🧠 **Analyzing Query for Optimal Strategy**")
                st.markdown(f"**Method:** {method.upper()}")
                query_preview = query[:60] + "..." if len(query) > 60 else query
                st.markdown(f"**Query:** {query_preview}")
                
            elif status == "completed":
                selected_strategy = event.data.get("selected_strategy", "")
                reasoning = event.data.get("reasoning", "")
                confidence = event.data.get("confidence", 0.0)
                selection_time = event.data.get("selection_time", 0.0)
                complexity_score = event.data.get("complexity_score", 0.0)
                urgency_score = event.data.get("urgency_score", 0.0)
                criticality_score = event.data.get("criticality_score", 0.0)
                key_factors = event.data.get("key_factors", [])
                
                st.markdown(f"**{timestamp}** - 🎯 **Strategy Selected: {selected_strategy}**")
                
                # Show confidence with color coding
                if confidence >= 0.8:
                    st.success(f"**Confidence:** {confidence:.2f} (High)")
                elif confidence >= 0.6:
                    st.info(f"**Confidence:** {confidence:.2f} (Medium)")
                else:
                    st.warning(f"**Confidence:** {confidence:.2f} (Low)")
                
                st.markdown(f"**Selection Time:** {selection_time:.3f}s")
                st.markdown(f"**Method:** {method.upper()}")
                
                # Show analysis scores
                if complexity_score > 0 or urgency_score > 0 or criticality_score > 0:
                    st.markdown("**Analysis Scores:**")
                    if complexity_score > 0:
                        st.markdown(f"  • Complexity: {complexity_score:.2f}")
                    if urgency_score > 0:
                        st.markdown(f"  • Urgency: {urgency_score:.2f}")
                    if criticality_score > 0:
                        st.markdown(f"  • Criticality: {criticality_score:.2f}")
                
                # Show reasoning
                if reasoning:
                    st.markdown(f"**Reasoning:** {reasoning}")
                
                # Show key factors
                if key_factors:
                    st.markdown("**Key Decision Factors:**")
                    for factor in key_factors:
                        st.markdown(f"  • {factor}")
            
        elif event.type == EventType.REFLECTION_START:
            original_response = event.data.get("original_response", "")
            quality_threshold = event.data.get("quality_threshold", 0.7)
            st.markdown(f"**{timestamp}** - 🔍 **Starting Reflection Process**")
            st.markdown(f"**Quality Threshold:** {quality_threshold:.2f}")
            if original_response:
                st.markdown(f"**Original Response Preview:** {original_response[:100]}{'...' if len(original_response) > 100 else ''}")
                
        elif event.type == EventType.REFLECTION_CRITIQUE:
            iteration = event.data.get("iteration", 1)
            critique = event.data.get("critique", {})
            st.markdown(f"**{timestamp}** - 🤔 **Reflection Critique - Iteration {iteration}:**")
            
            quality = critique.get("overall_quality", 0.0)
            confidence = critique.get("confidence", 0.0)
            needs_refinement = critique.get("needs_refinement", False)
            
            # Quality score with color coding
            if quality >= 0.8:
                st.success(f"Quality Score: {quality:.2f} (Excellent)")
            elif quality >= 0.7:
                st.info(f"Quality Score: {quality:.2f} (Good)")
            elif quality >= 0.5:
                st.warning(f"Quality Score: {quality:.2f} (Needs Improvement)")
            else:
                st.error(f"Quality Score: {quality:.2f} (Poor)")
            
            st.markdown(f"**Confidence:** {confidence:.2f}")
            st.markdown(f"**Needs Refinement:** {'Yes' if needs_refinement else 'No'}")
            
            # Show issues if any
            issues = critique.get("issues", [])
            if issues:
                st.markdown("**Issues Found:**")
                for i, issue in enumerate(issues, 1):
                    issue_type = issue.get("type", "unknown")
                    severity = issue.get("severity", "unknown")
                    description = issue.get("description", "No description")
                    suggestion = issue.get("suggestion", "No suggestion")
                    
                    severity_emoji = {
                        "critical": "🔴",
                        "major": "🟠", 
                        "minor": "🟡",
                        "suggestion": "🔵"
                    }.get(severity.lower(), "⚪")
                    
                    st.markdown(f"  {severity_emoji} **{issue_type.title()}** ({severity}): {description}")
                    st.markdown(f"    💡 *Suggestion: {suggestion}*")
            
            # Show strengths if any
            strengths = critique.get("strengths", [])
            if strengths:
                st.markdown("**Strengths:**")
                for strength in strengths:
                    st.markdown(f"  ✅ {strength}")
                    
            # Show reasoning
            reasoning = critique.get("reasoning", "")
            if reasoning:
                st.markdown(f"**Reasoning:** {reasoning}")
                
        elif event.type == EventType.REFLECTION_REFINEMENT:
            improvements = event.data.get("improvements", [])
            quality_improvement = event.data.get("quality_improvement", 0.0)
            st.markdown(f"**{timestamp}** - ✨ **Response Refinement:**")
            
            if quality_improvement > 0:
                st.success(f"Quality Improvement: +{quality_improvement:.2f}")
            
            if improvements:
                st.markdown("**Improvements Made:**")
                for improvement in improvements:
                    st.markdown(f"  🔧 {improvement}")
                    
        elif event.type == EventType.REFLECTION_COMPLETE:
            final_quality = event.data.get("final_quality_score", 0.0)
            threshold_met = event.data.get("threshold_met", False)
            iterations = event.data.get("reflection_iterations", 0)
            total_improvements = event.data.get("total_improvements", 0)
            
            st.markdown(f"**{timestamp}** - 🎉 **Reflection Complete**")
            
            if threshold_met:
                st.success(f"✅ Quality threshold met! Final score: {final_quality:.2f}")
            else:
                st.warning(f"⚠️ Quality threshold not met. Final score: {final_quality:.2f}")
            
            st.markdown(f"**Reflection Iterations:** {iterations}")
            st.markdown(f"**Total Improvements:** {total_improvements}")


async def run_streaming_chat(chatbot: StreamingChatbot, prompt: str, thinking_display: ThinkingDisplay):
    """Run streaming chat and update display in real-time."""
    final_response = None
    
    try:
        thinking_display.update_status("Starting to process your request...", "thinking")
        
        async for event in chatbot.chat_stream(prompt):
            # Update status based on event type
            if event.type == EventType.THINKING_START:
                thinking_display.update_status(f"Step {event.step}: Thinking about your request...", "thinking")
                
            elif event.type == EventType.ACTION_START:
                action = event.data.get("action", "")
                thinking_display.update_status(f"Executing tool: {action}", "action")
                
            elif event.type == EventType.PLAN_CREATED:
                plan = event.data.get("plan", {})
                steps_count = len(plan.get("steps", []))
                thinking_display.update_status(f"Created plan with {steps_count} steps", "thinking")
                
            elif event.type == EventType.STRATEGY_SELECTION:
                status = event.data.get("status", "")
                if status == "analyzing":
                    method = event.data.get("method", "")
                    thinking_display.update_status(f"🧠 Analyzing query complexity ({method})...", "thinking")
                elif status == "completed":
                    selected_strategy = event.data.get("selected_strategy", "")
                    confidence = event.data.get("confidence", 0.0)
                    thinking_display.update_status(f"🎯 Selected {selected_strategy} strategy (confidence: {confidence:.2f})", "success")
                
            elif event.type == EventType.REFLECTION_START:
                thinking_display.update_status("Starting reflection and self-critique...", "thinking")
                
            elif event.type == EventType.REFLECTION_CRITIQUE:
                iteration = event.data.get("iteration", 1)
                critique = event.data.get("critique", {})
                quality = critique.get("overall_quality", 0.0)
                thinking_display.update_status(f"Reflection iteration {iteration}: Quality {quality:.2f}", "thinking")
                
            elif event.type == EventType.REFLECTION_REFINEMENT:
                improvements = event.data.get("improvements", [])
                thinking_display.update_status(f"Refining response with {len(improvements)} improvements", "action")
                
            elif event.type == EventType.REFLECTION_COMPLETE:
                final_quality = event.data.get("final_quality_score", 0.0)
                threshold_met = event.data.get("threshold_met", False)
                if threshold_met:
                    thinking_display.update_status(f"Reflection complete! Quality: {final_quality:.2f}", "success")
                else:
                    thinking_display.update_status(f"Reflection complete. Quality: {final_quality:.2f}", "thinking")
                
            elif event.type == EventType.COMPLETE:
                thinking_display.update_status("Task completed successfully!", "success")
                final_response = event.data.get("response")
                st.session_state.thinking_complete = True
                
            elif event.type == EventType.ERROR:
                thinking_display.update_status(f"Error: {event.data.get('error', 'Unknown error')}", "error")
                final_response = {
                    "output": f"I apologize, but I encountered an error: {event.data.get('error', 'Unknown error')}",
                    "success": False,
                    "error": event.data.get("error", "Unknown error"),
                    "steps": []
                }
                st.session_state.thinking_complete = True
            
            # Add event to thinking display
            thinking_display.add_event(event)
            
            # Small delay to make the streaming visible
            await asyncio.sleep(0.1)
            
    except Exception as e:
        thinking_display.update_status(f"Unexpected error: {str(e)}", "error")
        final_response = {
            "output": f"I apologize, but I encountered an unexpected error: {str(e)}",
            "success": False,
            "error": str(e),
            "steps": []
        }
        st.session_state.thinking_complete = True
    
    return final_response


# Page configuration
st.set_page_config(
    page_title="AI Agent - Real-time Thinking",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "chatbot" not in st.session_state:
    st.session_state.chatbot = StreamingChatbot(verbose=False, mode="hybrid", enable_reflection=True, enable_llm_strategy_selection=True)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_thinking" not in st.session_state:
    st.session_state.show_thinking = True
if "current_thinking_events" not in st.session_state:
    st.session_state.current_thinking_events = []
if "thinking_complete" not in st.session_state:
    st.session_state.thinking_complete = False


def main():
    """Main Streamlit application."""
    
    # Title and description
    st.title("🧠 Octopus Prime AI Agent with Reflection")
    st.markdown("Watch the AI agent think, reason, and reflect in real-time as it processes your requests! 🔍✨")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Agent mode selection
        mode = st.selectbox(
            "Agent Mode",
            ["hybrid", "react", "plan_execute"],
            index=0,
            help="Choose how the agent processes requests"
        )
        
        # Reflection settings
        enable_reflection = st.checkbox(
            "Enable Reflection",
            value=True,
            help="Enable self-critique and response refinement"
        )
        
        # LLM Strategy Selection settings
        enable_llm_strategy = st.checkbox(
            "🧠 LLM-Based Strategy Selection",
            value=True,
            help="Use AI to intelligently select reflection strategies instead of regex patterns"
        )
        
        if not enable_llm_strategy:
            st.info("🔄 Using regex-based strategy selection (faster but less accurate)")
        else:
            st.success("🧠 Using LLM-based strategy selection (smarter but slower)")
        
        # Check if settings changed
        current_llm_strategy = getattr(st.session_state.chatbot.agent, 'enable_llm_strategy_selection', True)
        
        if (mode != st.session_state.chatbot.agent.mode or 
            enable_reflection != getattr(st.session_state.chatbot.agent, 'enable_reflection', True) or
            enable_llm_strategy != current_llm_strategy):
            
            st.session_state.chatbot = StreamingChatbot(
                verbose=False, 
                mode=mode, 
                enable_reflection=enable_reflection,
                enable_llm_strategy_selection=enable_llm_strategy
            )
            st.rerun()
        
        # Real-time thinking toggle
        st.session_state.show_thinking = st.checkbox(
            "Show real-time thinking", 
            value=st.session_state.show_thinking,
            help="Display the agent's thought process in real-time"
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
            st.session_state.current_thinking_events = []
            st.session_state.thinking_complete = False
            st.session_state.chatbot.clear_history()
            st.rerun()
        
        st.divider()
        
        # Available tools
        st.header("🔧 Available Tools")
        tools = st.session_state.chatbot.agent.tool_manager.get_tool_descriptions()
        for tool_name, description in tools.items():
            st.write(f"**{tool_name}**: {description}")
            
        st.divider()
        
        # Example queries
        st.header("💡 Example Queries")
        examples = [
            "Explain quantum computing and its applications",
            "What is machine learning and how does it work?",
            "Search for recent developments in artificial intelligence",
            "Calculate compound interest and explain the formula",
            "Compare different programming languages for beginners",
            "Analyze the benefits of renewable energy sources"
        ]
        
        # Conversation history examples
        st.header("🗨️ Conversation History Examples")
        history_examples = [
            "What did we discuss before?",
            "Show me the last 3 conversations",
            "What was my previous question about?",
            "Can you show me the last calculation result?",
            "What topics have we covered in this session?"
        ]
        
        for example in examples:
            if st.button(f"📝 {example[:30]}...", key=f"example_{hash(example)}"):
                st.session_state.example_query = example
                st.rerun()
        
        for example in history_examples:
            if st.button(f"💬 {example[:30]}...", key=f"history_{hash(example)}"):
                st.session_state.example_query = example
                st.rerun()
    
    # Main chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Handle example query
    if hasattr(st.session_state, 'example_query'):
        prompt = st.session_state.example_query
        delattr(st.session_state, 'example_query')
    else:
        # Chat input
        prompt = st.chat_input("Ask me anything...")
    
    if prompt:
        # Clear previous thinking events for new query
        st.session_state.current_thinking_events = []
        st.session_state.thinking_complete = False
        
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get assistant response with real-time thinking
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            if st.session_state.show_thinking:
                # Create thinking display (but don't initialize containers for real-time display)
                thinking_display = ThinkingDisplay()
                
                # Run streaming chat
                async def run_chat():
                    return await run_streaming_chat(st.session_state.chatbot, prompt, thinking_display)
                
                with st.spinner("🤔 Agent is thinking..."):
                    response = run_async_safe(run_chat())
            else:
                # Run without streaming
                async def run_simple_chat():
                    events = []
                    async for event in st.session_state.chatbot.chat_stream(prompt):
                        events.append(event)
                        st.session_state.current_thinking_events.append(event)
                        if event.type == EventType.COMPLETE:
                            st.session_state.thinking_complete = True
                            return event.data.get("response")
                        elif event.type == EventType.ERROR:
                            st.session_state.thinking_complete = True
                            return {
                                "output": f"Error: {event.data.get('error', 'Unknown error')}",
                                "success": False,
                                "error": event.data.get("error", "Unknown error"),
                                "steps": []
                            }
                    return None
                
                with st.spinner("Processing your request..."):
                    response = run_async_safe(run_simple_chat())
            
            # Display final response
            if response:
                if response["success"]:
                    response_placeholder.write(response["output"])
                    
                    # Add to session state
                    assistant_message = {
                        "role": "assistant", 
                        "content": response["output"]
                    }
                    st.session_state.messages.append(assistant_message)
                    
                else:
                    error_msg = f"❌ {response.get('error', 'Unknown error')}"
                    response_placeholder.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })
            else:
                error_msg = "❌ No response received"
                response_placeholder.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_msg
                })
            
            # Show thinking steps after completion (only when streaming was used)
            if st.session_state.show_thinking and st.session_state.thinking_complete and st.session_state.current_thinking_events:
                st.divider()
                thinking_display = ThinkingDisplay()
                thinking_display.render_final_thinking()


# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        🧠 Real-time AI Agent Thinking with Self-Reflection 🔍
    </div>
    """, 
    unsafe_allow_html=True
)


if __name__ == "__main__":
    main()