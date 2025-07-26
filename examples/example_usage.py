"""Example usage of the React Agent."""

import asyncio
import json
from agent import ReactAgent


async def run_examples():
    """Run example queries with the React Agent."""
    
    # Initialize the agent
    agent = ReactAgent(verbose=True)
    
    # Example queries
    examples = [
        "What is the capital of France and what's the current population?",
        "Calculate the square root of 144 and then search for information about that number in mathematics",
        "Store my name as 'John Doe' in the database and then retrieve all users",
        "What is machine learning and calculate 2^10",
        "Search the database for products and tell me about the most expensive one"
    ]
    
    print("🤖 React Agent Examples")
    print("=" * 60)
    
    for i, query in enumerate(examples, 1):
        print(f"\n📝 Example {i}: {query}")
        print("-" * 60)
        
        try:
            response = await agent.run(query)
            
            if response["success"]:
                print(f"✅ Success: {response['output']}")
                print(f"🔄 Steps taken: {len(response['steps'])}")
            else:
                print(f"❌ Failed: {response['error']}")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 60)
        
        # Wait a bit between examples
        await asyncio.sleep(1)
    
    # Show memory stats
    print(f"\n📊 Agent Memory Stats:")
    stats = agent.get_memory_stats()
    print(json.dumps(stats, indent=2))


async def interactive_mode():
    """Run the agent in interactive mode."""
    agent = ReactAgent(verbose=True)
    
    print("🤖 React Agent - Interactive Mode")
    print("=" * 50)
    print("Type 'quit' to exit")
    print("=" * 50)
    
    while True:
        try:
            query = input("\n👤 Enter your query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            print(f"\n🤖 Processing: {query}")
            print("-" * 50)
            
            response = await agent.run(query)
            
            if response["success"]:
                print(f"\n✅ Final Answer: {response['output']}")
            else:
                print(f"\n❌ Error: {response['error']}")
            
            print("-" * 50)
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


async def main():
    """Main function."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        await interactive_mode()
    else:
        await run_examples()


if __name__ == "__main__":
    asyncio.run(main())