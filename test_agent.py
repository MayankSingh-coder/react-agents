"""Test script for the React Agent."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_basic_functionality():
    """Test basic agent functionality without external APIs."""
    print("🧪 Testing React Agent Basic Functionality")
    print("=" * 50)
    
    try:
        from agent import ReactAgent
        
        # Test with mock/local tools only
        agent = ReactAgent(verbose=True)
        
        # Test 1: Calculator tool
        print("\n📊 Test 1: Calculator Tool")
        print("-" * 30)
        response = await agent.run("What is 15 * 8 + 32?")
        print(f"Success: {response['success']}")
        if response['success']:
            print(f"Answer: {response['output']}")
        else:
            print(f"Error: {response['error']}")
        
        # Test 2: Database tool
        print("\n💾 Test 2: Database Tool")
        print("-" * 30)
        response = await agent.run("Store my favorite color as blue in the database")
        print(f"Success: {response['success']}")
        if response['success']:
            print(f"Answer: {response['output']}")
        else:
            print(f"Error: {response['error']}")
        
        # Test 3: Database retrieval
        print("\n🔍 Test 3: Database Retrieval")
        print("-" * 30)
        response = await agent.run("List all the keys in the database")
        print(f"Success: {response['success']}")
        if response['success']:
            print(f"Answer: {response['output']}")
        else:
            print(f"Error: {response['error']}")
        
        # Test 4: Complex reasoning
        print("\n🧠 Test 4: Complex Reasoning")
        print("-" * 30)
        response = await agent.run("Calculate the square root of 144, then store that result in the database as 'sqrt_result'")
        print(f"Success: {response['success']}")
        if response['success']:
            print(f"Answer: {response['output']}")
        else:
            print(f"Error: {response['error']}")
        
        print("\n✅ Basic functionality tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_with_external_apis():
    """Test with external APIs if available."""
    print("\n🌐 Testing External API Integration")
    print("=" * 50)
    
    # Check if API keys are available
    google_api_key = os.getenv("GOOGLE_API_KEY")
    serper_api_key = os.getenv("SERPER_API_KEY")
    
    if not google_api_key:
        print("⚠️ GOOGLE_API_KEY not found. Skipping external API tests.")
        print("   Set GOOGLE_API_KEY in your .env file to test with Gemini.")
        return
    
    try:
        from agent import ReactAgent
        
        agent = ReactAgent(verbose=True)
        
        # Test Wikipedia (should work without additional API key)
        print("\n📚 Test: Wikipedia Tool")
        print("-" * 30)
        response = await agent.run("Tell me about artificial intelligence from Wikipedia")
        print(f"Success: {response['success']}")
        if response['success']:
            print(f"Answer: {response['output'][:200]}...")  # Truncate for readability
        else:
            print(f"Error: {response['error']}")
        
        # Test web search if API key is available
        if serper_api_key:
            print("\n🔍 Test: Web Search Tool")
            print("-" * 30)
            response = await agent.run("Search for the latest news about artificial intelligence")
            print(f"Success: {response['success']}")
            if response['success']:
                print(f"Answer: {response['output'][:200]}...")
            else:
                print(f"Error: {response['error']}")
        else:
            print("\n⚠️ SERPER_API_KEY not found. Skipping web search test.")
        
        print("\n✅ External API tests completed!")
        
    except Exception as e:
        print(f"❌ External API test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_multiagent_framework():
    """Test the multiagent framework."""
    print("\n🤖 Testing Multiagent Framework")
    print("=" * 50)
    
    try:
        from extensions.multiagent_framework import (
            MultiAgentSystem,
            create_coordinator_agent,
            create_researcher_agent,
            create_analyst_agent
        )
        
        # Create multiagent system
        system = MultiAgentSystem()
        
        # Add agents
        coordinator = create_coordinator_agent("coord_1")
        researcher = create_researcher_agent("research_1")
        analyst = create_analyst_agent("analyst_1")
        
        system.add_agent(coordinator)
        system.add_agent(researcher)
        system.add_agent(analyst)
        
        # Test system stats
        stats = system.get_system_stats()
        print(f"System stats: {stats}")
        
        # Test task distribution
        research_task = {
            "type": "research",
            "query": "What is machine learning?"
        }
        
        print(f"\n📋 Distributing research task...")
        result = await system.distribute_task(research_task)
        print(f"Task result: {result['success'] if 'success' in result else 'completed'}")
        
        print("\n✅ Multiagent framework tests completed!")
        
    except Exception as e:
        print(f"❌ Multiagent test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("🚀 React Agent Test Suite")
    print("=" * 60)
    
    # Test basic functionality (should work without external APIs)
    await test_basic_functionality()
    
    # Test external APIs if available
    await test_external_apis()
    
    # Test multiagent framework
    await test_multiagent_framework()
    
    print("\n🎉 All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())