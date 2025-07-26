#!/usr/bin/env python3
"""
Multi-Agent Integration Demo

This script demonstrates how to integrate the multi-agent system with your existing ReactAgent.
It shows three different integration patterns:

1. Agents as Tools - Specialized agents appear as tools to your main ReactAgent
2. Direct Orchestration - Complex tasks go directly to the multi-agent orchestrator  
3. Hybrid Mode - Automatic switching between single-agent and multi-agent processing
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions.enhanced_multiagent import (
    MultiAgentReactAgent, 
    MultiAgentOrchestrator,
    create_researcher_agent,
    create_analyst_agent, 
    create_coder_agent,
    create_coordinator_agent,
    AgentTool
)


async def demo_pattern_1_agents_as_tools():
    """Pattern 1: Use specialized agents as tools within ReactAgent"""
    
    print("🔧 Pattern 1: Agents as Tools")
    print("=" * 50)
    
    # Create a MultiAgentReactAgent (extends your existing ReactAgent)
    agent = MultiAgentReactAgent(verbose=True)
    
    # Enable multi-agent tools - this adds specialized agents as tools
    agent.enable_multi_agent_tools()
    
    # Now your ReactAgent has access to researcher, analyst, and coder agents as tools
    test_queries = [
        "Use the researcher_agent to find information about quantum computing",
        "Have the analyst_agent analyze the pros and cons of different database types",
        "Ask the coder_agent to write a Python function for binary search"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = await agent.run(query)
        print(f"✅ Success: {result.get('success', False)}")
        print(f"📄 Output: {result.get('output', '')[:200]}...")
        
        if 'tool_results' in result:
            print(f"🔧 Tools used: {len(result['tool_results'])}")
    
    print(f"\n📊 Multi-Agent Stats:")
    stats = agent.get_multi_agent_stats()
    print(f"Total agents: {stats['total_agents']}")
    print(f"Tasks processed: {stats['total_tasks_processed']}")


async def demo_pattern_2_direct_orchestration():
    """Pattern 2: Direct orchestration for complex multi-agent tasks"""
    
    print("\n🎭 Pattern 2: Direct Orchestration")
    print("=" * 50)
    
    # Create orchestrator with specialized agents
    orchestrator = MultiAgentOrchestrator()
    
    # Create and register specialized agents
    agents = [
        create_researcher_agent("research_specialist"),
        create_analyst_agent("analysis_specialist"),
        create_coder_agent("coding_specialist"),
        create_coordinator_agent("task_coordinator")
    ]
    
    for agent in agents:
        orchestrator.register_agent(agent)
    
    print(f"✅ Registered {len(orchestrator.agents)} specialized agents")
    
    # Test complex queries that benefit from multi-agent collaboration
    complex_queries = [
        "Research the latest trends in AI and then analyze their potential impact on software development",
        "Find information about microservices architecture and then provide a detailed analysis of its pros and cons",
        "Research Python async programming best practices and create a comprehensive guide with code examples"
    ]
    
    for query in complex_queries:
        print(f"\n📝 Complex Query: {query}")
        result = await orchestrator.process_query(query)
        
        print(f"✅ Success: {result.get('success', False)}")
        print(f"🤖 Primary Agent: {result.get('agent_id', 'Unknown')}")
        
        if result.get('participating_agents'):
            print(f"🤝 Collaborating Agents: {result['participating_agents']}")
        
        print(f"📄 Result Preview: {result.get('output', '')[:300]}...")


async def demo_pattern_3_hybrid_mode():
    """Pattern 3: Hybrid mode - automatic switching between single and multi-agent"""
    
    print("\n🔄 Pattern 3: Hybrid Mode")
    print("=" * 50)
    
    # Create a hybrid ReactAgent that automatically chooses the best approach
    hybrid_agent = MultiAgentReactAgent(verbose=True, mode="hybrid")
    hybrid_agent.enable_multi_agent_tools()
    
    # Mix of simple and complex queries
    mixed_queries = [
        # Simple queries (should use single agent)
        "What is 25 * 34?",
        "Calculate the square root of 144",
        
        # Medium complexity (might use agent tools)
        "Search for information about machine learning algorithms",
        "Analyze the benefits of cloud computing",
        
        # Complex queries (should trigger orchestration)
        "Research artificial intelligence trends and then analyze how they might impact job markets",
        "Find the latest developments in quantum computing and provide a comprehensive analysis with potential applications"
    ]
    
    for query in mixed_queries:
        print(f"\n📝 Query: {query}")
        result = await hybrid_agent.run(query)
        
        print(f"✅ Success: {result.get('success', False)}")
        print(f"🤖 Processed by: {result.get('agent_id', 'Main ReactAgent')}")
        print(f"⏱️ Execution time: {result.get('execution_time', 0):.2f}s")
        
        # Check if multi-agent collaboration was used
        if result.get('participating_agents'):
            print(f"🤝 Multi-agent collaboration: {result['participating_agents']}")
        elif result.get('tool_results'):
            print(f"🔧 Tools used: {len(result['tool_results'])}")
        
        print(f"📄 Output preview: {result.get('output', '')[:150]}...")


async def demo_custom_agent_creation():
    """Demonstrate creating custom specialized agents"""
    
    print("\n🛠️ Custom Agent Creation")
    print("=" * 50)
    
    from extensions.enhanced_multiagent import EnhancedMultiAgent, AgentCapability
    from agent.react_agent import ReactAgent
    
    # Create a custom financial analysis agent
    financial_agent = EnhancedMultiAgent(
        agent_id="financial_analyst",
        capabilities=[AgentCapability.ANALYSIS, AgentCapability.RESEARCH],
        react_agent=ReactAgent(verbose=False)
    )
    
    # Create a custom creative writing agent
    creative_agent = EnhancedMultiAgent(
        agent_id="creative_writer", 
        capabilities=[AgentCapability.PLANNING, AgentCapability.EXECUTION],
        react_agent=ReactAgent(verbose=False)
    )
    
    # Connect them as peers for potential collaboration
    financial_agent.add_peer(creative_agent)
    creative_agent.add_peer(financial_agent)
    
    print("✅ Created custom financial and creative agents")
    
    # Test the custom agents
    financial_query = "Analyze the potential risks and benefits of cryptocurrency investments"
    creative_query = "Write a short story about a robot learning to paint"
    
    print(f"\n💰 Financial Query: {financial_query}")
    financial_result = await financial_agent.process_request(financial_query)
    print(f"✅ Success: {financial_result.get('success', False)}")
    print(f"📄 Analysis: {financial_result.get('output', '')[:200]}...")
    
    print(f"\n🎨 Creative Query: {creative_query}")
    creative_result = await creative_agent.process_request(creative_query)
    print(f"✅ Success: {creative_result.get('success', False)}")
    print(f"📄 Story: {creative_result.get('output', '')[:200]}...")
    
    # Show agent performance stats
    print(f"\n📊 Agent Performance:")
    print(f"Financial Agent: {financial_agent.get_performance_stats()}")
    print(f"Creative Agent: {creative_agent.get_performance_stats()}")


async def demo_agent_tool_integration():
    """Show how to integrate agents as tools in your existing ReactAgent"""
    
    print("\n🔗 Agent-Tool Integration")
    print("=" * 50)
    
    # Start with your existing ReactAgent
    from agent.react_agent import ReactAgent
    
    main_agent = ReactAgent(verbose=True)
    
    # Create specialized agents
    researcher = create_researcher_agent("demo_researcher")
    analyst = create_analyst_agent("demo_analyst")
    
    # Convert agents to tools
    research_tool = AgentTool(researcher, "research_specialist")
    analysis_tool = AgentTool(analyst, "analysis_specialist")
    
    # Register the agent tools with your main ReactAgent
    main_agent.tool_manager.register_tool(research_tool)
    main_agent.tool_manager.register_tool(analysis_tool)
    
    print("✅ Integrated specialized agents as tools")
    
    # Now your main agent can use these specialized agents as tools
    integration_queries = [
        "Use the research_specialist to find information about renewable energy",
        "Have the analysis_specialist analyze the environmental impact of electric vehicles"
    ]
    
    for query in integration_queries:
        print(f"\n📝 Integration Query: {query}")
        result = await main_agent.run(query)
        
        print(f"✅ Success: {result.get('success', False)}")
        print(f"📄 Output: {result.get('output', '')[:200]}...")
        
        # Show which tools (agents) were used
        if 'tool_results' in result:
            for tool_result in result['tool_results']:
                if 'metadata' in tool_result and 'agent_role' in tool_result['metadata']:
                    print(f"🤖 Used: {tool_result['metadata']['agent_role']} agent")


async def main():
    """Run all demonstration patterns"""
    
    print("🚀 Multi-Agent Integration Demonstration")
    print("=" * 60)
    print("This demo shows how to extend your existing ReactAgent to a multi-agent platform")
    print("=" * 60)
    
    try:
        # Run all demonstration patterns
        await demo_pattern_1_agents_as_tools()
        await demo_pattern_2_direct_orchestration()
        await demo_pattern_3_hybrid_mode()
        await demo_custom_agent_creation()
        await demo_agent_tool_integration()
        
        print("\n🎉 Multi-Agent Integration Demo Complete!")
        print("\n💡 Key Takeaways:")
        print("1. Your existing ReactAgent can be enhanced with specialized agent tools")
        print("2. Complex tasks can be orchestrated across multiple agents")
        print("3. Hybrid mode automatically chooses the best approach")
        print("4. Custom agents can be created for specific domains")
        print("5. Integration is backward compatible with your existing code")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the complete demonstration
    asyncio.run(main())