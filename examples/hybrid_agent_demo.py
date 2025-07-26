"""Demonstration of the hybrid ReAct + Plan-Execute agent."""

import asyncio
import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.react_agent import ReactAgent


async def demonstrate_hybrid_agent():
    """Demonstrate the hybrid agent with different types of queries."""
    
    print("🚀 Hybrid ReAct + Plan-Execute Agent Demo")
    print("=" * 60)
    
    # Initialize agents with different modes
    agents = {
        "ReAct": ReactAgent(verbose=True, mode="react"),
        "Plan-Execute": ReactAgent(verbose=True, mode="plan_execute"), 
        "Hybrid": ReactAgent(verbose=True, mode="hybrid")
    }
    
    # Test queries of different complexity
    test_queries = [

        {
            "query":"I want to plan a 7-day European vacation for 2 people with a $3000 budget. Research flight costs from New York, find affordable accommodations, create a daily itinerary with must-see attractions, and calculate the total estimated cost",
            "description": "Fibonacci calculation - should use hybrid approach",
            "expected_approach": "hybrid"
        }
        # },
        # {
        #     "query": "First calculate 15 + 25, then search for information about that number in mathematics, and finally store the result in the database",
        #     "description": "Complex multi-step task - should use Plan-Execute",
        #     "expected_approach": "Plan-Execute"
        # },
        # {
        #     "query": "Find information about artificial intelligence and calculate how many years it has been since 1956",
        #     "description": "Mixed complexity - hybrid should decide",
        #     "expected_approach": "Either"
        # },
        # {
        #     "query": "What is machine learning?",
        #     "description": "Simple information query - should use ReAct",
        #     "expected_approach": "ReAct"
        # }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print(f"Expected Approach: {test_case['expected_approach']}")
        print(f"{'='*60}")
        
        # Test with hybrid agent
        print(f"\n🤖 Testing with Hybrid Agent:")
        print("-" * 40)
        
        try:
            response = await agents["Hybrid"].run(test_case["query"])
            
            print(f"\n📊 Results:")
            print(f"Success: {response['success']}")
            print(f"Mode Used: {response['metadata'].get('mode', 'unknown')}")
            print(f"Chosen Approach: {response['metadata'].get('chosen_approach', 'unknown')}")
            print(f"Steps Taken: {len(response['steps'])}")
            print(f"Execution Time: {response['metadata'].get('execution_time', 0):.2f}s")
            
            if response['success']:
                print(f"Output: {response['output']}")
            else:
                print(f"Error: {response['error']}")
            
            # Show reasoning steps if verbose
            if response['steps']:
                print(f"\n🧠 Reasoning Steps:")
                for step in response['steps']:
                    print(f"  Step {step['step']}: {step['thought'][:100]}...")
                    if step.get('action'):
                        print(f"    Action: {step['action']} -> {step.get('observation', 'No observation')[:100]}...")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # Wait between tests
        await asyncio.sleep(2)
    
    # Show memory and execution statistics
    print(f"\n{'='*60}")
    print("📈 Agent Statistics")
    print(f"{'='*60}")
    
    for mode, agent in agents.items():
        print(f"\n{mode} Agent:")
        try:
            stats = await agent.get_memory_stats()
            print(f"  Memory Stats: {json.dumps(stats, indent=2, default=str)}")
        except Exception as e:
            print(f"  Stats Error: {str(e)}")


async def compare_approaches():
    """Compare different approaches on the same complex query."""
    
    print(f"\n{'='*60}")
    print("🔄 Approach Comparison")
    print(f"{'='*60}")
    
    complex_query = "Calculate the square root of 144, then search for information about that number in mathematics, and store both results in the database"
    
    agents = {
        "ReAct Only": ReactAgent(verbose=False, mode="react"),
        "Plan-Execute Only": ReactAgent(verbose=False, mode="plan_execute"),
        "Hybrid": ReactAgent(verbose=False, mode="hybrid")
    }
    
    results = {}
    
    for mode, agent in agents.items():
        print(f"\n🧪 Testing {mode}:")
        print("-" * 30)
        
        try:
            start_time = asyncio.get_event_loop().time()
            response = await agent.run(complex_query)
            end_time = asyncio.get_event_loop().time()
            
            results[mode] = {
                "success": response['success'],
                "steps": len(response['steps']),
                "execution_time": end_time - start_time,
                "output_length": len(str(response['output'])) if response['output'] else 0,
                "error": response.get('error'),
                "metadata": response.get('metadata', {})
            }
            
            print(f"  Success: {response['success']}")
            print(f"  Steps: {len(response['steps'])}")
            print(f"  Time: {end_time - start_time:.2f}s")
            
            if not response['success']:
                print(f"  Error: {response['error']}")
        
        except Exception as e:
            results[mode] = {
                "success": False,
                "error": str(e),
                "steps": 0,
                "execution_time": 0
            }
            print(f"  Failed: {str(e)}")
    
    # Summary comparison
    print(f"\n📊 Comparison Summary:")
    print("-" * 40)
    
    for mode, result in results.items():
        print(f"{mode}:")
        print(f"  Success Rate: {'✅' if result['success'] else '❌'}")
        print(f"  Steps: {result['steps']}")
        print(f"  Time: {result['execution_time']:.2f}s")
        if result.get('error'):
            print(f"  Error: {result['error'][:100]}...")
        print()


# async def test_cpp_median_execution():
#     """Test the C++ median finding code execution specifically."""
#
#     print(f"\n{'='*60}")
#     print("🔧 C++ Median Code Execution Test")
#     print(f"{'='*60}")
#
#     agent = ReactAgent(verbose=True, mode="hybrid")
#
#     cpp_query = """Execute this C++ code to find the median of two sorted arrays:
#
# #include <iostream>
# #include <vector>
# #include <algorithm>
# using namespace std;
#
# double medianOf2(vector<int>& a, vector<int>& b) {
#     // Merge both the arrays
#     vector<int> c(a.begin(), a.end());
#     c.insert(c.end(), b.begin(), b.end());
#     // Sort the concatenated array
#     sort(c.begin(), c.end());
#     int len = c.size();
#     // If length of array is even
#     if (len % 2 == 0)
#         return (c[len / 2] + c[len / 2 - 1]) / 2.0;
#     // If length of array is odd
#     else
#         return c[len / 2];
# }
#
# int main() {
#     vector<int> a = { -5, 3, 6, 12, 15 };
#     vector<int> b = { -12, -10, -6, -3, 4, 10 };
#     cout << medianOf2(a, b) << endl;
#     return 0;
# }"""
#
#     print("🚀 Executing C++ median finding code...")
#     print(f"Arrays: a = [-5, 3, 6, 12, 15], b = [-12, -10, -6, -3, 4, 10]")
#     print("Expected median: 1.5")
#
#     try:
#         response = await agent.run(cpp_query)
#
#         print(f"\n📊 Results:")
#         print(f"Success: {response['success']}")
#         print(f"Mode Used: {response['metadata'].get('mode', 'unknown')}")
#         print(f"Steps Taken: {len(response['steps'])}")
#         print(f"Execution Time: {response['metadata'].get('execution_time', 0):.2f}s")
#
#         if response['success']:
#             print(f"✅ Output: {response['output']}")
#
#             # Try to extract the numeric result
#             output_str = str(response['output'])
#             try:
#                 # Look for numeric values in the output
#                 import re
#                 numbers = re.findall(r'-?\d+\.?\d*', output_str)
#                 if numbers:
#                     result = float(numbers[-1])  # Take the last number found
#                     print(f"🎯 Calculated Median: {result}")
#                     if abs(result - 1.5) < 0.001:
#                         print("✅ Result matches expected value (1.5)!")
#                     else:
#                         print(f"⚠️ Result differs from expected value (1.5)")
#             except:
#                 print("ℹ️ Could not extract numeric result for comparison")
#         else:
#             print(f"❌ Error: {response['error']}")
#
#         # Show reasoning steps
#         if response['steps']:
#             print(f"\n🧠 Reasoning Steps:")
#             for i, step in enumerate(response['steps'], 1):
#                 print(f"  Step {i}: {step.get('thought', 'No thought')[:100]}...")
#                 if step.get('action'):
#                     print(f"    Action: {step['action']}")
#                     if step.get('observation'):
#                         print(f"    Result: {step['observation'][:100]}...")
#
#     except Exception as e:
#         print(f"❌ Test failed: {str(e)}")
#         import traceback
#         traceback.print_exc()
#

async def demonstrate_memory_context_sharing():
    """Demonstrate how memory and context are shared between tools."""
    
    print(f"\n{'='*60}")
    print("🧠 Memory & Context Sharing Demo")
    print(f"{'='*60}")
    
    agent = ReactAgent(verbose=True, mode="hybrid")
    
    # Sequence of related queries to show memory usage
    related_queries = [
        "provide the code of the uc browser"
        # "Store my name as 'Alice Johnson' in the database",
        # "Calculate 25 * 4 and store it as 'my_calculation'", 
        # "Search for information about the number I just calculated",
        # "List all the data I've stored in the database"
    ]
    
    print("🔗 Running related queries to demonstrate context sharing:")
    
    for i, query in enumerate(related_queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Query: {query}")
        
        try:
            response = await agent.run(query)
            
            print(f"Success: {response['success']}")
            if response['success']:
                print(f"Output: {response['output']}")
            else:
                print(f"Error: {response['error']}")
            
            # Show how context builds up
            print(f"Steps taken: {len(response['steps'])}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-" * 50)
        await asyncio.sleep(1)
    
    # Show final memory stats
    print(f"\n📈 Final Memory Statistics:")
    try:
        stats = await agent.get_memory_stats()
        print(json.dumps(stats, indent=2, default=str))
    except Exception as e:
        print(f"Stats error: {str(e)}")


async def main():
    """Main demonstration function."""
    
    print("🎯 Industry-Standard React Agent with Hybrid Approach")
    print("Features: ReAct + Plan-Execute + Advanced Memory + Context Sharing")
    print("=" * 80)
    
    try:
        # C++ median execution test
        # await test_cpp_median_execution()
        
        # Main hybrid agent demo
        await demonstrate_hybrid_agent()
        
        # Approach comparison
        await compare_approaches()
        
        # Memory and context demo
        await demonstrate_memory_context_sharing()
        
        print(f"\n🎉 Demo completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())