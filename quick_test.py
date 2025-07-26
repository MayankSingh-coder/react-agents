#!/usr/bin/env python3
"""Quick test to verify the real-time thinking is working."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streaming_agent import StreamingChatbot, EventType


async def quick_demo():
    """Quick demo of real-time thinking."""
    print("🧠 Real-time AI Thinking Demo")
    print("=" * 40)
    
    chatbot = StreamingChatbot(verbose=False, mode="hybrid")
    
    # Test with a more complex query
    query = "What is the square root of 144, and tell me something interesting about that number?"
    
    print(f"❓ Question: {query}")
    print("-" * 40)
    
    step_count = 0
    
    async for event in chatbot.chat_stream(query):
        if event.type == EventType.THINKING_START:
            step_count += 1
            print(f"\n🤔 Step {step_count}: Agent is thinking...")
            
        elif event.type == EventType.THINKING:
            thought = event.data.get("thought", "")
            print(f"💭 Thought: {thought[:100]}{'...' if len(thought) > 100 else ''}")
            
        elif event.type == EventType.ACTION_START:
            action = event.data.get("action", "")
            action_input = event.data.get("input", "")
            print(f"🔧 Using tool: {action} with input: {action_input}")
            
        elif event.type == EventType.ACTION_RESULT:
            result = event.data.get("result", {})
            if result.get("success"):
                print(f"✅ Tool succeeded!")
            else:
                print(f"❌ Tool failed: {result.get('error', 'Unknown error')}")
                
        elif event.type == EventType.COMPLETE:
            response = event.data.get("response", {})
            print(f"\n🎉 Final Answer:")
            print(f"📝 {response.get('output', 'No output')}")
            print(f"\n📊 Total steps: {step_count}")
            print(f"⚡ Success: {response.get('success', False)}")
            break
            
        elif event.type == EventType.ERROR:
            print(f"❌ Error: {event.data.get('error', 'Unknown error')}")
            break


if __name__ == "__main__":
    asyncio.run(quick_demo())