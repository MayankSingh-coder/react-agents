"""Demo script showing reflection optimization strategies and performance improvements."""

import asyncio
import time
import json
from typing import Dict, Any, List

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.react_agent import ReactAgent
from agent.reflection_factory import ReflectionStrategy, ReflectionFactory


class ReflectionOptimizationDemo:
    """Demo class for testing reflection optimization strategies."""
    
    def __init__(self):
        self.test_queries = {
            "simple": [
                "What is 2 + 2?",
                "What's the capital of France?",
                "Convert 100 Fahrenheit to Celsius",
                "Define photosynthesis"
            ],
            "moderate": [
                "Compare renewable energy sources and their efficiency",
                "Explain the steps to make chocolate chip cookies",
                "List the top 5 programming languages and their use cases",
                "How does machine learning work in simple terms?"
            ],
            "complex": [
                "Research the impact of climate change on ocean ecosystems and propose mitigation strategies",
                "Analyze the economic factors that led to the 2008 financial crisis and explain how similar crises could be prevented",
                "Create a comprehensive business plan for a sustainable tech startup in the AI space",
                "Compare different database architectures and recommend the best approach for a large-scale e-commerce platform"
            ]
        }
    
    async def run_strategy_comparison(self):
        """Compare different reflection strategies across query types."""
        
        print("🚀 Reflection Optimization Demo")
        print("=" * 50)
        
        strategies = [
            ReflectionStrategy.STANDARD,
            ReflectionStrategy.FAST, 
            ReflectionStrategy.BALANCED,
            ReflectionStrategy.OPTIMIZED,
            ReflectionStrategy.QUALITY_FIRST
        ]
        
        results = {}
        
        for strategy in strategies:
            print(f"\n🔍 Testing Strategy: {strategy.value.upper()}")
            print("-" * 30)
            
            strategy_info = ReflectionFactory.get_strategy_info(strategy)
            print(f"Description: {strategy_info.get('description', 'N/A')}")
            print(f"Expected Performance: {strategy_info.get('performance', 'N/A')}")
            print(f"Expected Quality: {strategy_info.get('quality', 'N/A')}")
            print(f"Expected LLM Calls: {strategy_info.get('llm_calls', 'N/A')}")
            
            results[strategy.value] = await self._test_strategy(strategy)
        
        # Display results summary
        print("\n" + "=" * 60)
        print("📊 RESULTS SUMMARY")
        print("=" * 60)
        
        self._display_results_table(results)
        
        # Show optimization impact
        print("\n" + "=" * 60)
        print("💡 OPTIMIZATION IMPACT")
        print("=" * 60)
        
        self._analyze_optimization_impact(results)
    
    async def _test_strategy(self, strategy: ReflectionStrategy) -> Dict[str, Any]:
        """Test a specific reflection strategy."""
        
        # Create agent with the strategy
        agent = ReactAgent(
            verbose=False,  # Keep quiet for demo
            enable_reflection=True,
            reflection_strategy=strategy
        )
        
        strategy_results = {
            "total_queries": 0,
            "total_time": 0,
            "reflection_skipped": 0,
            "avg_quality_score": 0,
            "avg_processing_time": 0,
            "query_results": []
        }
        
        # Test with a subset of queries for demo
        test_queries = [
            ("simple", "What is 2 + 2?"),
            ("moderate", "Explain how photosynthesis works"),
            ("complex", "Compare renewable energy sources")
        ]
        
        total_quality = 0
        quality_count = 0
        
        for query_type, query in test_queries:
            print(f"  Testing {query_type} query: {query[:50]}...")
            
            start_time = time.time()
            
            try:
                # Run the agent
                result = await agent.run(query)
                
                processing_time = time.time() - start_time
                
                # Extract reflection metadata
                reflection_metadata = result.get("metadata", {}).get("reflection", {})
                
                query_result = {
                    "query": query,
                    "query_type": query_type,
                    "processing_time": processing_time,
                    "reflection_skipped": reflection_metadata.get("reflection_skipped", False),
                    "skip_reason": reflection_metadata.get("skip_reason", ""),
                    "final_quality_score": reflection_metadata.get("final_quality_score", 0.0),
                    "reflection_iterations": reflection_metadata.get("reflection_iterations", 0),
                    "optimization_strategy": reflection_metadata.get("optimization_strategy", "unknown")
                }
                
                strategy_results["query_results"].append(query_result)
                strategy_results["total_time"] += processing_time
                
                if query_result["reflection_skipped"]:
                    strategy_results["reflection_skipped"] += 1
                
                if query_result["final_quality_score"] > 0:
                    total_quality += query_result["final_quality_score"]
                    quality_count += 1
                
                print(f"    ✅ Completed in {processing_time:.2f}s")
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                continue
        
        strategy_results["total_queries"] = len(test_queries)
        strategy_results["avg_quality_score"] = total_quality / quality_count if quality_count > 0 else 0.0
        strategy_results["avg_processing_time"] = strategy_results["total_time"] / len(test_queries)
        
        return strategy_results
    
    def _display_results_table(self, results: Dict[str, Dict[str, Any]]):
        """Display results in a formatted table."""
        
        print(f"{'Strategy':<15} {'Avg Time':<10} {'Skipped':<8} {'Quality':<8} {'Notes'}")
        print("-" * 65)
        
        for strategy_name, data in results.items():
            avg_time = f"{data['avg_processing_time']:.2f}s"
            skipped = f"{data['reflection_skipped']}/{data['total_queries']}"
            quality = f"{data['avg_quality_score']:.2f}" if data['avg_quality_score'] > 0 else "N/A"
            
            # Add notes based on performance
            notes = ""
            if data['reflection_skipped'] > 0:
                notes += "Skip-enabled "
            if data['avg_processing_time'] < 2.0:
                notes += "Fast "
            if data['avg_quality_score'] > 0.8:
                notes += "High-quality"
            
            print(f"{strategy_name:<15} {avg_time:<10} {skipped:<8} {quality:<8} {notes}")
    
    def _analyze_optimization_impact(self, results: Dict[str, Dict[str, Any]]):
        """Analyze the impact of optimizations."""
        
        standard_time = results.get("standard", {}).get("avg_processing_time", 0)
        if standard_time == 0:
            print("⚠️ Could not compare - standard strategy results not available")
            return
        
        print(f"Baseline (Standard Strategy): {standard_time:.2f}s average processing time")
        print()
        
        for strategy_name, data in results.items():
            if strategy_name == "standard":
                continue
            
            avg_time = data["avg_processing_time"]
            time_improvement = ((standard_time - avg_time) / standard_time) * 100
            
            skip_rate = (data["reflection_skipped"] / data["total_queries"]) * 100
            
            print(f"{strategy_name.upper()}:")
            print(f"  ⏱️  Time improvement: {time_improvement:+.1f}%")
            print(f"  ⚡ Skip rate: {skip_rate:.0f}%")
            print(f"  🎯 Avg quality: {data['avg_quality_score']:.2f}")
            
            # Calculate estimated LLM call reduction
            if data["reflection_skipped"] > 0:
                estimated_calls_saved = data["reflection_skipped"] * 2  # Assume 2 calls saved per skip
                print(f"  💰 Est. LLM calls saved: {estimated_calls_saved}")
            
            print()
    
    async def run_performance_benchmark(self):
        """Run a focused performance benchmark."""
        
        print("\n🏃‍♂️ Performance Benchmark")
        print("=" * 40)
        
        # Test query that would normally trigger reflection
        test_query = "Explain the process of machine learning in detail"
        
        strategies_to_test = [
            ReflectionStrategy.STANDARD,
            ReflectionStrategy.FAST,
            ReflectionStrategy.BALANCED
        ]
        
        benchmark_results = {}
        
        for strategy in strategies_to_test:
            print(f"\nBenchmarking {strategy.value}...")
            
            agent = ReactAgent(
                verbose=False,
                enable_reflection=True,
                reflection_strategy=strategy
            )
            
            # Run multiple times for average
            times = []
            for i in range(3):
                start_time = time.time()
                try:
                    result = await agent.run(test_query)
                    processing_time = time.time() - start_time
                    times.append(processing_time)
                    print(f"  Run {i+1}: {processing_time:.2f}s")
                except Exception as e:
                    print(f"  Run {i+1}: Error - {str(e)}")
                    continue
            
            if times:
                avg_time = sum(times) / len(times)
                benchmark_results[strategy.value] = avg_time
                print(f"  Average: {avg_time:.2f}s")
        
        # Show improvement
        if "standard" in benchmark_results:
            standard_time = benchmark_results["standard"]
            print(f"\n📈 Performance Improvements vs Standard:")
            for strategy, time_taken in benchmark_results.items():
                if strategy != "standard":
                    improvement = ((standard_time - time_taken) / standard_time) * 100
                    print(f"  {strategy}: {improvement:+.1f}% faster")
    
    def display_strategy_recommendations(self):
        """Display strategy recommendations for different use cases."""
        
        print("\n🎯 Strategy Recommendations")
        print("=" * 50)
        
        use_cases = [
            ("Simple Q&A Bot", "simple", "high", "good"),
            ("Customer Support", "mixed", "balanced", "high"),
            ("Research Assistant", "complex", "low", "critical"),
            ("Real-time Chat", "simple", "high", "good"),
            ("Educational Tool", "moderate", "balanced", "high")
        ]
        
        for use_case, complexity, performance, quality in use_cases:
            recommended = ReflectionFactory.recommend_strategy(
                query_complexity=complexity,
                performance_priority=performance,
                quality_requirements=quality
            )
            
            print(f"{use_case}:")
            print(f"  Complexity: {complexity}, Performance: {performance}, Quality: {quality}")
            print(f"  → Recommended: {recommended.value}")
            print()


async def main():
    """Run the reflection optimization demo."""
    
    demo = ReflectionOptimizationDemo()
    
    print("Starting Reflection Optimization Demo...")
    print("This demo will compare different reflection strategies")
    print("and show performance improvements.\n")
    
    # Run strategy comparison
    await demo.run_strategy_comparison()
    
    # Run performance benchmark
    await demo.run_performance_benchmark()
    
    # Show recommendations
    demo.display_strategy_recommendations()
    
    print("\n✅ Demo completed!")
    print("\nTo use optimized reflection in your agent:")
    print("```python")
    print("from agent.react_agent import ReactAgent")
    print("from agent.reflection_factory import ReflectionStrategy")
    print("")
    print("agent = ReactAgent(")
    print("    enable_reflection=True,")
    print("    reflection_strategy=ReflectionStrategy.BALANCED")
    print(")")
    print("```")


if __name__ == "__main__":
    asyncio.run(main())