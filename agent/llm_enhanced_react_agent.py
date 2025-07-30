"""LLM-Enhanced ReactAgent with intelligent reflection strategy selection."""

import json
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from .react_agent import ReactAgent
from .reflection_factory import ReflectionFactory, ReflectionStrategy
from .llm_strategy_selector import get_llm_strategy_selector, select_strategy_with_llm


class LLMEnhancedReactAgent(ReactAgent):
    """ReactAgent that uses LLM to intelligently select reflection strategies per query."""
    
    def __init__(self, verbose: bool = True, mode: str = "hybrid", use_mysql: bool = True, 
                 enable_reflection: bool = True, reflection_quality_threshold: float = 0.7,
                 reflection_strategy: ReflectionStrategy = ReflectionStrategy.BALANCED,
                 enable_llm_strategy_selection: bool = True, user_preferences: dict = None,
                 use_hybrid_selection: bool = True, cache_strategies: bool = True):
        """Initialize LLM-Enhanced ReactAgent.
        
        Args:
            enable_llm_strategy_selection: Use LLM for strategy selection
            use_hybrid_selection: Use fast regex for obvious cases, LLM for nuanced ones
            cache_strategies: Cache reflection modules for different strategies
        """
        
        # Initialize parent with reflection disabled initially
        super().__init__(
            verbose=verbose,
            mode=mode,
            use_mysql=use_mysql,
            enable_reflection=enable_reflection,
            reflection_quality_threshold=reflection_quality_threshold,
            reflection_strategy=reflection_strategy,
            enable_dynamic_strategy=False,  # We'll handle this ourselves
            user_preferences=user_preferences
        )
        
        # LLM-based strategy selection settings
        self.enable_llm_strategy_selection = enable_llm_strategy_selection and enable_reflection
        self.use_hybrid_selection = use_hybrid_selection
        self.cache_strategies = cache_strategies
        self.default_reflection_strategy = reflection_strategy
        self.reflection_quality_threshold = reflection_quality_threshold
        
        # Initialize LLM strategy selector
        if self.enable_llm_strategy_selection:
            self.llm_strategy_selector = get_llm_strategy_selector()
            self.strategy_selection_stats = {
                "total_selections": 0,
                "llm_selections": 0,
                "regex_fallback_selections": 0,
                "cache_hits": 0,
                "selection_times": []
            }
        else:
            self.llm_strategy_selector = None
            self.strategy_selection_stats = {}
        
        # Strategy module cache
        if self.cache_strategies:
            self.reflection_module_cache = {}
            self.max_cache_size = 4  # Cache for FAST, BALANCED, OPTIMIZED, QUALITY_FIRST
        else:
            self.reflection_module_cache = {}
    
    def _is_obviously_simple(self, query: str) -> bool:
        """Quick check for obviously simple queries using regex."""
        
        query_lower = query.lower().strip()
        
        # Very short queries
        if len(query.split()) <= 5:
            simple_patterns = [
                r'^what is \d+[\+\-\*\/]\d+',  # "what is 2+2"
                r'^\d+[\+\-\*\/]\d+$',         # "2+2"
                r'^what is .{1,20}\?$',        # "what is X?" (short)
                r'^define .{1,20}$',           # "define X" (short)
                r'weather',                     # weather queries
                r'time',                       # time queries
                r'translate .{1,30}'           # short translations
            ]
            
            for pattern in simple_patterns:
                if re.search(pattern, query_lower):
                    return True
        
        return False
    
    def _is_obviously_critical(self, query: str) -> bool:
        """Quick check for obviously critical queries using regex."""
        
        query_lower = query.lower()
        
        critical_indicators = [
            r'\bcritical\b',
            r'\bimportant\b', 
            r'\burgent\b',
            r'\bemergency\b',
            r'\blife.*death\b',
            r'\bsafety\b',
            r'\bmedical\b.*\b(advice|help|emergency)\b',
            r'\bmust be (accurate|precise|exact)\b'
        ]
        
        for pattern in critical_indicators:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    async def _select_reflection_strategy_for_query(self, query: str, state: dict) -> Tuple[ReflectionStrategy, Dict[str, Any]]:
        """Select optimal reflection strategy using LLM analysis."""
        
        if not self.enable_llm_strategy_selection:
            return self.default_reflection_strategy, {"method": "fixed", "reasoning": "LLM selection disabled"}
        
        start_time = time.time()
        selection_metadata = {}
        
        try:
            # Prepare context from agent state
            context = {
                "current_step": state.get("current_step", 0),
                "thoughts": state.get("thoughts", []),
                "actions": state.get("actions", []),
                "session_id": state.get("session_id"),
                "mode": state.get("mode", self.mode)
            }
            
            # Add query history if available
            if hasattr(self, '_query_history'):
                context["previous_queries"] = self._query_history[-3:]
            
            # Hybrid approach: Quick regex checks first
            if self.use_hybrid_selection:
                if self._is_obviously_simple(query):
                    selection_time = time.time() - start_time
                    self.strategy_selection_stats["regex_fallback_selections"] += 1
                    self.strategy_selection_stats["selection_times"].append(selection_time)
                    
                    return ReflectionStrategy.FAST, {
                        "method": "regex_simple",
                        "reasoning": "Obviously simple query detected by regex",
                        "selection_time": selection_time,
                        "confidence": 0.9
                    }
                
                if self._is_obviously_critical(query):
                    selection_time = time.time() - start_time
                    self.strategy_selection_stats["regex_fallback_selections"] += 1
                    self.strategy_selection_stats["selection_times"].append(selection_time)
                    
                    return ReflectionStrategy.QUALITY_FIRST, {
                        "method": "regex_critical",
                        "reasoning": "Obviously critical query detected by regex", 
                        "selection_time": selection_time,
                        "confidence": 0.9
                    }
            
            # Use LLM for nuanced analysis
            recommendation = await self.llm_strategy_selector.get_strategy_recommendation_with_reasoning(
                query=query,
                context=context,
                user_preferences=self.user_preferences
            )
            
            selected_strategy = recommendation["recommended_strategy"]
            selection_time = time.time() - start_time
            
            # Update stats
            self.strategy_selection_stats["llm_selections"] += 1
            self.strategy_selection_stats["selection_times"].append(selection_time)
            
            selection_metadata = {
                "method": "llm",
                "reasoning": recommendation.get("reasoning", ""),
                "confidence": recommendation.get("confidence", 0.0),
                "complexity_score": recommendation.get("complexity_score", 0.0),
                "urgency_score": recommendation.get("urgency_score", 0.0),
                "criticality_score": recommendation.get("criticality_score", 0.0),
                "key_factors": recommendation.get("key_factors", []),
                "selection_time": selection_time,
                "llm_analysis": recommendation.get("llm_analysis", {})
            }
            
            if self.verbose:
                print(f"\n🧠 LLM Strategy Selection:")
                print(f"   Strategy: {selected_strategy.value}")
                print(f"   Confidence: {recommendation.get('confidence', 0.0):.2f}")
                print(f"   Reasoning: {recommendation.get('reasoning', '')}")
                print(f"   Selection Time: {selection_time:.3f}s")
            
            return selected_strategy, selection_metadata
            
        except Exception as e:
            # Fallback to simple heuristics
            selection_time = time.time() - start_time
            self.strategy_selection_stats["regex_fallback_selections"] += 1
            self.strategy_selection_stats["selection_times"].append(selection_time)
            
            if self.verbose:
                print(f"⚠️ LLM strategy selection failed: {e}")
                print(f"   Falling back to heuristic selection")
            
            # Simple fallback logic
            if len(query.split()) < 10 and any(word in query.lower() for word in ["what is", "define", "calculate"]):
                fallback_strategy = ReflectionStrategy.FAST
            elif any(word in query.lower() for word in ["critical", "important", "emergency"]):
                fallback_strategy = ReflectionStrategy.QUALITY_FIRST
            elif any(word in query.lower() for word in ["analyze", "research", "comprehensive"]):
                fallback_strategy = ReflectionStrategy.OPTIMIZED
            else:
                fallback_strategy = ReflectionStrategy.BALANCED
            
            return fallback_strategy, {
                "method": "fallback",
                "reasoning": f"LLM failed ({str(e)}), used heuristic fallback",
                "selection_time": selection_time,
                "error": str(e)
            }
        
        finally:
            self.strategy_selection_stats["total_selections"] += 1
    
    def _get_reflection_module_for_strategy(self, strategy: ReflectionStrategy):
        """Get or create a reflection module for the given strategy."""
        
        if not self.cache_strategies:
            # Create new module each time if caching disabled
            return ReflectionFactory.create_reflection_module(
                strategy=strategy,
                quality_threshold=self.reflection_quality_threshold,
                verbose=self.verbose
            )
        
        if strategy not in self.reflection_module_cache:
            # Create and cache new module
            module = ReflectionFactory.create_reflection_module(
                strategy=strategy,
                quality_threshold=self.reflection_quality_threshold,
                verbose=self.verbose
            )
            
            self.reflection_module_cache[strategy] = module
            
            if self.verbose:
                print(f"🆕 Created and cached reflection module for {strategy.value}")
        else:
            self.strategy_selection_stats["cache_hits"] += 1
        
        return self.reflection_module_cache[strategy]
    
    async def _reflect_node(self, state):
        """Enhanced reflection node with LLM-based strategy selection."""
        
        if not self.enable_reflection:
            if self.verbose:
                print("🔍 Reflection disabled, skipping...")
            return state
        
        # Get the original query for strategy selection
        original_query = state.get("input", "")
        if not original_query:
            if self.verbose:
                print("⚠️ No original query found for strategy selection")
            return await super()._reflect_node(state)
        
        # Select strategy using LLM analysis
        selected_strategy, selection_metadata = await self._select_reflection_strategy_for_query(
            original_query, state
        )
        
        # Get reflection module for selected strategy
        reflection_module = self._get_reflection_module_for_strategy(selected_strategy)
        
        # Store strategy selection info in state metadata
        if "metadata" not in state:
            state["metadata"] = {}
        
        state["metadata"]["llm_strategy_selection"] = {
            "selected_strategy": selected_strategy.value,
            "selection_metadata": selection_metadata,
            "llm_enhanced": True
        }
        
        if self.verbose:
            print(f"\n🔍 Starting reflection with {selected_strategy.value} strategy...")
            if selection_metadata.get("method") == "llm":
                print(f"   LLM Confidence: {selection_metadata.get('confidence', 0.0):.2f}")
        
        try:
            # Set reflection enabled flag
            state["reflection_enabled"] = True
            
            # Store original response for comparison
            original_response = state.get("output", "")
            state["original_response"] = original_response
            
            if not original_response:
                if self.verbose:
                    print("⚠️ No output to reflect on, skipping reflection")
                return state
            
            # Prepare reasoning steps (same as parent implementation)
            reasoning_steps = []
            
            # Add thoughts as reasoning steps
            for i, thought in enumerate(state.get("thoughts", [])):
                reasoning_steps.append({
                    "step": i + 1,
                    "thought": thought,
                    "action": None,
                    "observation": None
                })
            
            # Add actions and observations
            actions = state.get("actions", [])
            observations = state.get("observations", [])
            
            for i, action in enumerate(actions):
                step_data = {
                    "step": action.get("step", i + 1),
                    "thought": None,
                    "action": action.get("name"),
                    "action_input": action.get("input"),
                    "observation": observations[i] if i < len(observations) else None
                }
                
                # Find corresponding reasoning step or create new one
                step_found = False
                for rs in reasoning_steps:
                    if rs["step"] == step_data["step"]:
                        rs.update({k: v for k, v in step_data.items() if v is not None})
                        step_found = True
                        break
                
                if not step_found:
                    reasoning_steps.append(step_data)
            
            # Sort reasoning steps by step number
            reasoning_steps.sort(key=lambda x: x["step"])
            
            # Perform reflection using the selected module
            refined_response, reflection_metadata = await reflection_module.reflect_and_refine(
                state, original_response, reasoning_steps
            )
            
            # Add strategy selection info to reflection metadata
            reflection_metadata["strategy_selection"] = selection_metadata
            reflection_metadata["selected_strategy"] = selected_strategy.value
            reflection_metadata["llm_enhanced_selection"] = True
            
            # Update state with reflection results
            state["output"] = refined_response
            state["reflection_iterations"] = reflection_metadata["reflection_iterations"]
            state["reflection_history"] = reflection_metadata["reflection_history"]
            state["final_quality_score"] = reflection_metadata["final_quality_score"]
            state["reflection_improvements"] = reflection_metadata["total_improvements"]
            
            # Update metadata
            state["metadata"]["reflection"] = reflection_metadata
            
            if self.verbose:
                print(f"🎉 Reflection completed with {selected_strategy.value}!")
                print(f"📊 Quality Score: {reflection_metadata['final_quality_score']:.2f}")
                print(f"🔧 Improvements: {len(reflection_metadata['total_improvements'])}")
                if selection_metadata.get("method") == "llm":
                    print(f"⚡ Selection Method: LLM (confidence: {selection_metadata.get('confidence', 0.0):.2f})")
                else:
                    print(f"⚡ Selection Method: {selection_metadata.get('method', 'unknown')}")
            
            return state
            
        except Exception as e:
            if self.verbose:
                print(f"❌ LLM-enhanced reflection failed: {str(e)}")
            
            # Add error to metadata
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["reflection_error"] = str(e)
            state["metadata"]["failed_strategy"] = selected_strategy.value
            
            return state
    
    async def run(self, query: str, max_steps: int = None) -> Dict[str, Any]:
        """Enhanced run method that tracks query history."""
        
        # Track query history for context
        if not hasattr(self, '_query_history'):
            self._query_history = []
        
        self._query_history.append(query)
        if len(self._query_history) > 10:
            self._query_history = self._query_history[-5:]
        
        # Call parent run method
        result = await super().run(query, max_steps)
        
        # Add LLM strategy selection info to result metadata
        if self.enable_llm_strategy_selection and "metadata" in result:
            result["metadata"]["llm_strategy_selection_enabled"] = True
            result["metadata"]["strategy_selection_stats"] = self.get_strategy_selection_stats()
        
        return result
    
    def get_strategy_selection_stats(self) -> Dict[str, Any]:
        """Get statistics about strategy selection performance."""
        
        if not self.strategy_selection_stats:
            return {"error": "LLM strategy selection not enabled"}
        
        stats = self.strategy_selection_stats.copy()
        
        # Calculate averages
        if stats["selection_times"]:
            stats["average_selection_time"] = sum(stats["selection_times"]) / len(stats["selection_times"])
            stats["max_selection_time"] = max(stats["selection_times"])
            stats["min_selection_time"] = min(stats["selection_times"])
        
        # Calculate percentages
        if stats["total_selections"] > 0:
            stats["llm_selection_rate"] = stats["llm_selections"] / stats["total_selections"]
            stats["fallback_rate"] = stats["regex_fallback_selections"] / stats["total_selections"]
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_selections"]
        
        return stats
    
    def get_llm_selector_analytics(self) -> Dict[str, Any]:
        """Get analytics from the LLM strategy selector."""
        
        if not self.llm_strategy_selector:
            return {"error": "LLM strategy selector not available"}
        
        return self.llm_strategy_selector.get_selection_analytics()
    
    def clear_strategy_cache(self):
        """Clear the reflection module cache."""
        if self.cache_strategies:
            self.reflection_module_cache.clear()
            if self.verbose:
                print("🗑️ Cleared reflection module cache")
    
    def get_cached_strategies(self) -> List[str]:
        """Get list of currently cached strategies."""
        return [strategy.value for strategy in self.reflection_module_cache.keys()]