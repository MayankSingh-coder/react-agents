#!/usr/bin/env python3
"""Demo script for streaming agent capabilities."""

import asyncio
import sys
from datetime import datetime
from streaming_agent import StreamingChatbot, EventType


async def demo_streaming():
    """Demo the streaming agent capabilities."""
    print("🧠 AI Agent Streaming Demo")
    print("=" * 50)
    print("This demo shows real-time thinking process of the AI agent.")
    print("Watch as the agent thinks, plans, and executes actions!")
    print("=" * 50)
    
    # Create streaming chatbot
    chatbot = StreamingChatbot(verbose=False, mode="hybrid")
    
    # Demo queries
    demo_queries = [
        "Calculate the square root of 144 and tell me about that number in mathematics",
        "Search for information about artificial intelligence and store the key points",
        "What is 15 * 23? Then store the result in the database.",
        "Find information about Python programming"
    ]
    
    print("\nAvailable demo queries:")
    for i, query in enumerate(demo_queries, 1):
        print(f"{i}. {query}")
    
    while True:
        try:
            print("\n" + "=" * 50)
            choice = input("\nChoose a demo query (1-4) or enter your own query (or 'quit' to exit): ").strip()
            
            if choice.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Select query
            if choice.isdigit() and 1 <= int(choice) <= len(demo_queries):
                query = demo_queries[int(choice) - 1]
            else:
                query = choice
            
            if not query:
                continue
            
            print(f"\n🤖 Processing: {query}")
            print("-" * 50)
            
            # Stream the response
            step_count = 0
            start_time = datetime.now()
            
            async for event in chatbot.chat_stream(query):
                timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S.%f")[:-3]
                
                if event.type == EventType.THINKING_START:
                    step_count += 1
                    print(f"\n[{timestamp}] 🤔 Step {step_count}: Starting to think...")
                    
                elif event.type == EventType.THINKING:
                    thought = event.data.get("thought", "")
                    print(f"[{timestamp}] 💭 Thought:")
                    # Print thought with proper formatting
                    for line in thought.split('\n'):
                        if line.strip():
                            print(f"    {line}")
                    
                elif event.type == EventType.ACTION_PLANNED:
                    action = event.data.get("action", "")
                    action_input = event.data.get("input", "")
                    print(f"[{timestamp}] 📋 Action Planned: {action}")
                    if action_input:
                        print(f"    Input: {action_input}")
                        
                elif event.type == EventType.ACTION_START:
                    action = event.data.get("action", "")
                    print(f"[{timestamp}] 🔧 Executing Tool: {action}")
                    
                elif event.type == EventType.ACTION_RESULT:
                    tool = event.data.get("tool", "")
                    result = event.data.get("result", {})
                    print(f"[{timestamp}] 📤 Tool Result from {tool}:")
                    if result.get("success"):
                        data = result.get("data", "")
                        # Truncate long results
                        if len(str(data)) > 200:
                            print(f"    ✅ Success: {str(data)[:200]}...")
                        else:
                            print(f"    ✅ Success: {data}")
                    else:
                        print(f"    ❌ Error: {result.get('error', 'Unknown error')}")
                        
                elif event.type == EventType.OBSERVATION:
                    observation = event.data.get("observation", "")
                    print(f"[{timestamp}] 👁️ Observation:")
                    # Print observation with proper formatting
                    for line in observation.split('\n'):
                        if line.strip():
                            print(f"    {line}")
                            
                elif event.type == EventType.PLAN_CREATED:
                    plan = event.data.get("plan", {})
                    print(f"[{timestamp}] 📋 Plan Created:")
                    print(f"    Description: {plan.get('description', 'No description')}")
                    
                    steps = plan.get("steps", [])
                    if steps:
                        print("    Steps:")
                        for i, step in enumerate(steps, 1):
                            print(f"      {i}. {step.get('tool', 'Unknown')}: {step.get('description', 'No description')}")
                            
                elif event.type == EventType.PLAN_STEP_START:
                    step_desc = event.data.get("step_description", "")
                    tool = event.data.get("tool", "")
                    plan_step = event.data.get("plan_step", 0)
                    total_steps = event.data.get("total_steps", 0)
                    print(f"[{timestamp}] 🎯 Plan Step {plan_step}/{total_steps}: {tool}")
                    print(f"    {step_desc}")
                    
                elif event.type == EventType.COMPLETE:
                    response = event.data.get("response", {})
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    print(f"\n[{timestamp}] ✅ Task Completed! (Duration: {duration:.2f}s)")
                    print("-" * 50)
                    print("🤖 Final Response:")
                    print(response.get("output", "No output"))
                    
                elif event.type == EventType.ERROR:
                    error = event.data.get("error", "Unknown error")
                    print(f"[{timestamp}] ❌ Error: {error}")
                
                # Small delay to make it more readable
                await asyncio.sleep(0.05)
            
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main function."""
    try:
        asyncio.run(demo_streaming())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    main()