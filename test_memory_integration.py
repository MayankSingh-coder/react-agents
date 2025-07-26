#!/usr/bin/env python3
"""Test script to verify memory integration in ReAct agent."""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.react_agent import ReactAgent


async def test_memory_integration():
    """Test that the agent can remember calculations and use them in subsequent queries."""
    print("🧪 Testing Memory Integration in ReAct Agent")
    print("=" * 50)
    
    # Initialize agent
    agent = ReactAgent(verbose=True, mode="react")
    
    # Test 1: Perform a calculation
    print("\n📝 Test 1: Performing a calculation")
    print("-" * 30)
    
    result1 = await agent.run("Calculate 15 * 8 + 7")
    print(f"✅ Result 1: {result1['output']}")
    print(f"Success: {result1['success']}")
    
    # Test 2: Ask about the number just calculated
    print("\n📝 Test 2: Asking about the number just calculated")
    print("-" * 30)
    
    result2 = await agent.run("Search for information about the number I just calculated")
    print(f"✅ Result 2: {result2['output']}")
    print(f"Success: {result2['success']}")
    
    # Test 3: Check if memory context was used
    print("\n📝 Test 3: Checking memory context usage")
    print("-" * 30)
    
    # Check if the agent has the calculation in memory
    shared_vars = agent.context_manager.get_all_shared_variables()
    print(f"Shared variables in memory: {shared_vars}")
    
    if 'last_calculation_result' in shared_vars:
        print("✅ Memory integration working: Calculation result stored in context")
    else:
        print("❌ Memory integration issue: Calculation result not found in context")
    
    # Test 4: Another calculation and reference
    print("\n📝 Test 4: Another calculation and reference")
    print("-" * 30)
    
    result3 = await agent.run("Calculate 25 / 5")
    print(f"✅ Result 3: {result3['output']}")
    
    result4 = await agent.run("What was the result of my previous calculation?")
    print(f"✅ Result 4: {result4['output']}")
    
    print("\n🎯 Memory Integration Test Complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_memory_integration())