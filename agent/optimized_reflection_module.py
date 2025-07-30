"""Optimized Reflection Module with Performance Enhancements.

This module implements several optimization strategies:
1. Conditional Reflection: Skip reflection for simple queries
2. Early Stopping: Stop reflection if initial quality > threshold
3. Async Reflection: Run reflection in background, return initial response  
4. Quality Prediction: Pre-predict if reflection is needed
"""

import asyncio
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import hashlib

from langchain.schema import HumanMessage, SystemMessage
from llm_manager import get_llm_manager, safe_llm_invoke
from .agent_state import AgentState
from .reflection_module import (
    ReflectionType, ReflectionSeverity, ReflectionIssue, 
    CritiqueResult, RefinementResult, ReflectionModule
)
from .reflection_analytics import record_reflection_operation
from .reflection_config import ReflectionConfig


class QueryComplexity(Enum):
    """Query complexity levels for conditional reflection."""
    SIMPLE = "simple"           # Single fact lookup, basic calculation
    MODERATE = "moderate"       # Multi-step but straightforward
    COMPLEX = "complex"         # Multi-domain, requires reasoning
    VERY_COMPLEX = "very_complex"  # Long chains, multiple tools


@dataclass
class QualityPrediction:
    """Prediction of response quality before reflection."""
    predicted_quality: float
    confidence: float
    should_reflect: bool
    reasoning: str
    metadata: Dict[str, Any]


# ReflectionConfig is now imported from .reflection_config


class OptimizedReflectionModule:
    """Enhanced reflection module with performance optimizations."""
    
    def __init__(self, config: Optional[ReflectionConfig] = None, verbose: bool = False):
        """Initialize the optimized reflection module.
        
        Args:
            config: Configuration for reflection behavior
            verbose: Whether to print detailed reflection process
        """
        self.config = config or ReflectionConfig()
        self.verbose = verbose
        self.llm_manager = get_llm_manager()
        
        # Expose commonly accessed attributes for compatibility
        self.quality_threshold = self.config.quality_threshold
        self.max_refinement_iterations = self.config.max_refinement_iterations
        
        # Caches for performance
        self._complexity_cache = {}
        self._quality_prediction_cache = {}
        
        # Fallback to original reflection module for complex cases
        self._fallback_module = ReflectionModule(
            quality_threshold=self.config.quality_threshold,
            max_refinement_iterations=self.config.max_refinement_iterations,
            verbose=verbose
        )
    
    async def reflect_and_refine(self, 
                                state: AgentState,
                                response: str,
                                reasoning_steps: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """Main optimized reflection and refinement process.
        
        Args:
            state: Current agent state
            response: Initial response to reflect on
            reasoning_steps: Steps taken to reach the response
            
        Returns:
            Tuple of (refined_response, reflection_metadata)
        """
        start_time = time.time()
        
        if self.verbose:
            print(f"\n🚀 Starting optimized reflection process...")
        
        # Step 1: Analyze query complexity
        complexity = await self._analyze_query_complexity(state)
        
        # Initialize metrics tracking
        session_id = state.get("session_id", "unknown")
        query = state.get("input", "")
        llm_calls_made = 0
        cache_hits = 0
        cache_misses = 0
        
        # Step 2: Skip reflection for simple queries if configured
        if self.config.skip_simple_queries and complexity == QueryComplexity.SIMPLE:
            if self.verbose:
                print(f"⚡ Skipping reflection for simple query")
            
            processing_time = time.time() - start_time
            
            # Record analytics
            record_reflection_operation(
                session_id=session_id,
                query=query,
                query_complexity=complexity.value,
                strategy_used=f"optimized_{self.config.default_strategy.value}",
                processing_time=processing_time,
                total_time=processing_time,
                reflection_skipped=True,
                skip_reason="simple_query",
                llm_calls_made=llm_calls_made,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                estimated_time_saved=2.0,  # Estimated time saved by skipping
                estimated_calls_saved=2    # Estimated LLM calls saved
            )
            
            return response, {
                "reflection_skipped": True,
                "skip_reason": "simple_query",
                "query_complexity": complexity.value,
                "processing_time": processing_time
            }
        
        # Step 3: Quality prediction (if enabled)
        quality_prediction = None
        if self.config.enable_quality_prediction:
            quality_prediction = await self._predict_quality(state, response, reasoning_steps)
            
            # Skip reflection if predicted quality is high and we're confident
            if (quality_prediction.confidence >= self.config.prediction_confidence_threshold and 
                not quality_prediction.should_reflect):
                
                if self.verbose:
                    print(f"🎯 Skipping reflection - predicted quality: {quality_prediction.predicted_quality:.2f}")
                
                return response, {
                    "reflection_skipped": True,
                    "skip_reason": "high_predicted_quality",
                    "predicted_quality": quality_prediction.predicted_quality,
                    "prediction_confidence": quality_prediction.confidence,
                    "processing_time": time.time() - start_time
                }
        
        # Step 4: Perform initial quality assessment
        initial_critique = await self._quick_quality_assessment(state, response, reasoning_steps)
        
        # Step 5: Early stopping if quality is already high
        if (self.config.enable_early_stopping and 
            initial_critique.overall_quality >= self.config.high_quality_threshold):
            
            if self.verbose:
                print(f"🎯 Early stopping - quality already high: {initial_critique.overall_quality:.2f}")
            
            return response, {
                "reflection_skipped": True,
                "skip_reason": "early_stopping_high_quality",
                "initial_quality": initial_critique.overall_quality,
                "processing_time": time.time() - start_time
            }
        
        # Step 6: Decide on reflection strategy
        if self.config.enable_async_reflection and complexity in [QueryComplexity.SIMPLE, QueryComplexity.MODERATE]:
            # Async reflection - return original response, refine in background
            return await self._async_reflection(state, response, reasoning_steps, initial_critique, start_time)
        else:
            # Synchronous reflection for complex queries
            return await self._sync_reflection(state, response, reasoning_steps, initial_critique, start_time)
    
    async def _analyze_query_complexity(self, state: AgentState) -> QueryComplexity:
        """Analyze query complexity to determine reflection strategy."""
        query = state.get("input", "")
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # Check cache first
        if self.config.cache_predictions and query_hash in self._complexity_cache:
            cached_result = self._complexity_cache[query_hash]
            if time.time() - cached_result["timestamp"] < self.config.cache_ttl:
                return cached_result["complexity"]
        
        # Simple heuristics for complexity analysis
        complexity_indicators = {
            QueryComplexity.SIMPLE: [
                r'\bwhat is\b', r'\bdefine\b', r'\bcalculate\b', r'\bconvert\b',
                r'\btranslate\b', r'^\d+[\+\-\*\/]\d+', r'\bweather\b'
            ],
            QueryComplexity.MODERATE: [
                r'\bcompare\b', r'\blist\b', r'\bexplain\b', r'\bhow to\b',
                r'\bsteps\b', r'\bprocess\b', r'\bfind.*and\b'
            ],
            QueryComplexity.COMPLEX: [
                r'\banalyze\b', r'\bevaluate\b', r'\bplan\b', r'\bstrategy\b',
                r'\bmultiple\b', r'\bthen\b', r'\bafter.*do\b', r'\bfirst.*then\b'
            ],
            QueryComplexity.VERY_COMPLEX: [
                r'\bcomplex\b', r'\bcomprehensive\b', r'\bdetailed analysis\b',
                r'\bresearch.*write\b', r'\bcreate.*plan.*implement\b'
            ]
        }
        
        # Count indicators for each complexity level
        scores = {}
        for complexity, patterns in complexity_indicators.items():
            score = sum(1 for pattern in patterns if re.search(pattern, query, re.IGNORECASE))
            scores[complexity] = score
        
        # Additional factors
        query_length = len(query.split())
        if query_length > 50:
            scores[QueryComplexity.COMPLEX] += 1
        if query_length > 100:
            scores[QueryComplexity.VERY_COMPLEX] += 1
        
        # Tool usage complexity
        num_tools_used = len(state.get("actions", []))
        if num_tools_used > 3:
            scores[QueryComplexity.COMPLEX] += 1
        if num_tools_used > 5:
            scores[QueryComplexity.VERY_COMPLEX] += 1
        
        # Determine final complexity
        max_score = max(scores.values())
        if max_score == 0:
            complexity = QueryComplexity.SIMPLE
        else:
            complexity = max(scores.keys(), key=lambda k: scores[k])
        
        # Cache result
        if self.config.cache_predictions:
            self._complexity_cache[query_hash] = {
                "complexity": complexity,
                "timestamp": time.time()
            }
        
        if self.verbose:
            print(f"📊 Query complexity: {complexity.value} (score: {max_score})")
        
        return complexity
    
    async def _predict_quality(self, 
                              state: AgentState,
                              response: str,
                              reasoning_steps: List[Dict[str, Any]]) -> QualityPrediction:
        """Predict response quality without full reflection."""
        query = state.get("input", "")
        query_hash = hashlib.md5((query + response).encode()).hexdigest()
        
        # Check cache first
        if self.config.cache_predictions and query_hash in self._quality_prediction_cache:
            cached_result = self._quality_prediction_cache[query_hash]
            if time.time() - cached_result["timestamp"] < self.config.cache_ttl:
                return cached_result["prediction"]
        
        # Quick heuristic-based quality prediction
        quality_score = 0.7  # Base score
        confidence = 0.6     # Base confidence
        
        # Response length indicators
        response_words = len(response.split())
        if response_words < 10:
            quality_score -= 0.2
        elif response_words > 100:
            quality_score += 0.1
        
        # Structure indicators
        if any(marker in response.lower() for marker in ['because', 'therefore', 'however', 'first', 'second']):
            quality_score += 0.1
            
        if response.count('.') > 2:  # Multiple sentences
            quality_score += 0.05
            
        # Tool usage correlation
        num_tools = len(state.get("actions", []))
        if num_tools > 0:
            quality_score += min(0.1 * num_tools, 0.3)
            confidence += 0.1
        
        # Error indicators
        error_indicators = ['error', 'failed', 'unable', 'cannot', 'unclear']
        if any(error in response.lower() for error in error_indicators):
            quality_score -= 0.3
            
        # Confidence in answer indicators
        confidence_indicators = ['according to', 'based on', 'research shows', 'data indicates']
        if any(indicator in response.lower() for indicator in confidence_indicators):
            quality_score += 0.15
            confidence += 0.1
        
        # Normalize scores
        quality_score = max(0.0, min(1.0, quality_score))
        confidence = max(0.0, min(1.0, confidence))
        
        should_reflect = quality_score < self.config.high_quality_threshold
        
        prediction = QualityPrediction(
            predicted_quality=quality_score,
            confidence=confidence,
            should_reflect=should_reflect,
            reasoning=f"Heuristic prediction based on structure and content analysis",
            metadata={
                "response_length": response_words,
                "tools_used": num_tools,
                "structure_score": quality_score
            }
        )
        
        # Cache result
        if self.config.cache_predictions:
            self._quality_prediction_cache[query_hash] = {
                "prediction": prediction,
                "timestamp": time.time()
            }
        
        if self.verbose:
            print(f"🔮 Quality prediction: {quality_score:.2f} (confidence: {confidence:.2f})")
        
        return prediction
    
    async def _quick_quality_assessment(self, 
                                       state: AgentState,
                                       response: str,
                                       reasoning_steps: List[Dict[str, Any]]) -> CritiqueResult:
        """Perform a lightweight quality assessment."""
        # Use a simplified prompt for faster assessment
        assessment_prompt = f"""Quickly assess the quality of this response on a scale of 0.0 to 1.0:

Question: {state.get('input', '')}
Response: {response}

Consider:
- Accuracy and relevance
- Completeness 
- Clarity

Respond with just a JSON object:
{{"overall_quality": 0.0-1.0, "needs_refinement": true/false, "reasoning": "brief explanation"}}"""
        
        messages = [
            SystemMessage(content="You are a quality assessor. Provide quick, accurate quality scores."),
            HumanMessage(content=assessment_prompt)
        ]
        
        try:
            llm = self.llm_manager.get_llm_for_session(state.get("session_id"))
            llm_response = await safe_llm_invoke(llm, messages, state.get("session_id"))
            assessment_text = llm_response.content
            
            # Parse the assessment
            json_match = re.search(r'\{.*\}', assessment_text, re.DOTALL)
            if json_match:
                assessment_data = json.loads(json_match.group())
                
                return CritiqueResult(
                    overall_quality=assessment_data.get("overall_quality", 0.5),
                    confidence=0.8,  # High confidence in quick assessment
                    issues=[],
                    strengths=[],
                    needs_refinement=assessment_data.get("needs_refinement", True),
                    reasoning=assessment_data.get("reasoning", "Quick assessment"),
                    metadata={"assessment_type": "quick"}
                )
        
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Quick assessment failed: {e}")
        
        # Fallback assessment
        return CritiqueResult(
            overall_quality=0.6,
            confidence=0.3,
            issues=[],
            strengths=[],
            needs_refinement=True,
            reasoning="Fallback assessment due to error",
            metadata={"assessment_type": "fallback"}
        )
    
    async def _async_reflection(self, 
                               state: AgentState,
                               response: str,
                               reasoning_steps: List[Dict[str, Any]],
                               initial_critique: CritiqueResult,
                               start_time: float) -> Tuple[str, Dict[str, Any]]:
        """Perform asynchronous reflection - return response immediately, refine in background."""
        
        if self.verbose:
            print(f"🔄 Starting async reflection...")
        
        # Create background task for reflection
        async def background_reflection():
            try:
                if self.verbose:
                    print(f"🌟 Background reflection started...")
                
                # Use fallback module for actual reflection
                refined_response, metadata = await self._fallback_module.reflect_and_refine(
                    state, response, reasoning_steps
                )
                
                # Store result in context or cache for future use
                # This could be used for learning/improvement
                if self.verbose:
                    print(f"✨ Background reflection completed")
                
                return refined_response, metadata
                
            except Exception as e:
                if self.verbose:
                    print(f"❌ Background reflection failed: {e}")
                return response, {"background_error": str(e)}
        
        # Start background task but don't wait for it
        background_task = asyncio.create_task(background_reflection())
        
        # Return original response immediately with metadata
        return response, {
            "reflection_mode": "async",
            "initial_quality": initial_critique.overall_quality,
            "background_task_started": True,
            "processing_time": time.time() - start_time,
            "optimization_strategy": "async_reflection"
        }
    
    async def _sync_reflection(self, 
                              state: AgentState,
                              response: str,
                              reasoning_steps: List[Dict[str, Any]],
                              initial_critique: CritiqueResult,
                              start_time: float) -> Tuple[str, Dict[str, Any]]:
        """Perform synchronous reflection with optimizations."""
        
        if self.verbose:
            print(f"🔄 Starting optimized sync reflection...")
        
        current_response = response
        reflection_history = []
        total_improvements = []
        
        for iteration in range(self.config.max_refinement_iterations):
            if self.verbose:
                print(f"📝 Reflection iteration {iteration + 1}/{self.config.max_refinement_iterations}")
            
            # Use cached critique for first iteration
            if iteration == 0:
                critique = initial_critique
            else:
                critique = await self._fallback_module.self_critique(state, current_response, reasoning_steps)
            
            reflection_history.append({
                "iteration": iteration + 1,
                "critique": critique,
                "response_at_iteration": current_response
            })
            
            if self.verbose:
                print(f"🎯 Quality Score: {critique.overall_quality:.2f}")
            
            # Early stopping if quality is sufficient
            if critique.overall_quality >= self.config.quality_threshold:
                if self.verbose:
                    print(f"✅ Quality threshold met! Stopping refinement.")
                break
            
            # Early stopping if improvement is minimal
            if (iteration > 0 and 
                self.config.enable_early_stopping and 
                len(reflection_history) > 1):
                
                prev_quality = reflection_history[-2]["critique"].overall_quality
                current_quality = critique.overall_quality
                improvement = current_quality - prev_quality
                
                if improvement < self.config.early_stop_improvement_threshold:
                    if self.verbose:
                        print(f"🛑 Early stopping - minimal improvement: {improvement:.3f}")
                    break
            
            # Refine if needed
            if critique.needs_refinement:
                refinement = await self._fallback_module.refine_response(
                    state, current_response, critique, reasoning_steps
                )
                
                current_response = refinement.refined_response
                total_improvements.extend(refinement.improvements_made)
                
                if self.verbose:
                    print(f"🔧 Refinement completed")
        
        # Prepare metadata
        metadata = {
            "reflection_mode": "sync_optimized",
            "reflection_iterations": len(reflection_history),
            "final_quality_score": reflection_history[-1]["critique"].overall_quality if reflection_history else 0.0,
            "total_improvements": total_improvements,
            "reflection_history": reflection_history,
            "quality_threshold": self.config.quality_threshold,
            "threshold_met": reflection_history[-1]["critique"].overall_quality >= self.config.quality_threshold if reflection_history else False,
            "processing_time": time.time() - start_time,
            "optimization_strategy": "sync_optimized"
        }
        
        if self.verbose:
            print(f"🎉 Optimized reflection complete!")
            print(f"📊 Final quality: {metadata['final_quality_score']:.2f}")
            print(f"⏱️ Time: {metadata['processing_time']:.2f}s")
        
        return current_response, metadata
    
    def clear_cache(self):
        """Clear prediction caches."""
        self._complexity_cache.clear()
        self._quality_prediction_cache.clear()
        
        if self.verbose:
            print("🧹 Reflection caches cleared")