#!/usr/bin/env python3
"""Test script for streaming agent functionality."""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streaming_agent import StreamingChatbot, EventType


async def test_basic_streaming():
    """Test basic streaming functionality."""
    print("🧪 Testing Streaming Agent...")
    print("=" * 50)
    
    try:
        # Create streaming chatbot
        chatbot = StreamingChatbot(verbose=False, mode="react")
        
        # Simple test query
        query = "What is 2 + 2?"
        print(f"📤 Query: {query}")
        print("-" * 30)
        
        events_received = 0
        async for event in chatbot.chat_stream(query):
            events_received += 1
            print(f"[{events_received}] {event.type.value}: {event.data}")
            
            if event.type == EventType.COMPLETE:
                response = event.data.get("response", {})
                print(f"\n✅ Final Response: {response.get('output', 'No output')}")
                break
            elif event.type == EventType.ERROR:
                print(f"\n❌ Error: {event.data.get('error', 'Unknown error')}")
                break
            elif events_received > 20:  # Safety limit
                print("\n⚠️ Too many events, stopping...")
                break
        
        print(f"\n📊 Total events received: {events_received}")
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_basic_streaming())