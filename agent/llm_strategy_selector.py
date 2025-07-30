"""LLM-based reflection strategy selector that uses AI to analyze queries and select optimal strategies."""

import json
import time
from typing import Dict, Any, Optional, List
from enum import Enum

from .reflection_factory import ReflectionStrategy
from llm_manager import get_llm_manager, safe_llm_invoke
from langchain.schema import HumanMessage, SystemMessage


class LLMStrategySelector:
    """Uses LLM to intelligently select reflection strategies based on query analysis."""
    
    def __init__(self, cache_ttl: int = 3600):
        self.llm_manager = get_llm_manager()
        self.selection_history = []
        self.strategy_cache = {}  # Cache for similar queries
        self.cache_ttl = cache_ttl
        
    async def select_strategy(self, 
                             query: str, 
                             context: Optional[Dict[str, Any]] = None,
                             user_preferences: Optional[Dict[str, Any]] = None) -> ReflectionStrategy:
        """Select optimal reflection strategy using LLM analysis.
        
        Args:
            query: The user query to analyze
            context: Additional context (previous queries, session info, etc.)
            user_preferences: User preferences for speed vs quality
            
        Returns:
            Recommended ReflectionStrategy
        """
        
        # Check cache first
        cache_key = self._get_cache_key(query, user_preferences)
        cached_result = self._get_cached_strategy(cache_key)
        if cached_result:
            return cached_result["strategy"]
        
        try:
            # Get LLM analysis
            analysis_result = await self._analyze_query_with_llm(query, context, user_preferences)
            
            # Parse LLM response and select strategy
            selected_strategy = self._parse_llm_analysis(analysis_result)
            
            # Cache the result
            self._cache_strategy(cache_key, {
                "strategy": selected_strategy,
                "analysis": analysis_result,
                "timestamp": time.time()
            })
            
            # Record selection
            selection_record = {
                "timestamp": time.time(),
                "query": query[:100] + "..." if len(query) > 100 else query,
                "selected_strategy": selected_strategy.value,
                "analysis_method": "llm",
                "llm_reasoning": analysis_result.get("reasoning", ""),
                "confidence": analysis_result.get("confidence", 0.0)
            }
            
            self.selection_history.append(selection_record)
            
            # Keep only recent history
            if len(self.selection_history) > 1000:
                self.selection_history = self.selection_history[-500:]
            
            return selected_strategy
            
        except Exception as e:
            print(f"⚠️ LLM strategy selection failed: {e}")
            # Fallback to heuristic-based selection
            return self._fallback_strategy_selection(query, user_preferences)
    
    async def _analyze_query_with_llm(self, 
                                     query: str, 
                                     context: Optional[Dict[str, Any]] = None,
                                     user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use LLM to analyze query and recommend strategy."""
        
        system_prompt = self._get_strategy_analysis_prompt()
        user_prompt = self._build_analysis_request(query, context, user_preferences)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Get LLM for current session
        llm = self.llm_manager.get_llm_for_session()
        
        # Make LLM call
        response = await safe_llm_invoke(llm, messages)
        
        # Parse JSON response
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback parsing if JSON fails
            return self._parse_text_response(response.content)
    
    def _get_strategy_analysis_prompt(self) -> str:
        """Get the system prompt for strategy analysis."""
        
        return """You are an expert AI assistant that analyzes user queries to recommend the optimal reflection strategy for response generation.

Your task is to analyze queries and recommend one of these reflection strategies:

1. **FAST** - For simple, straightforward queries that don't need deep reflection
   - Basic factual questions
   - Simple calculations
   - Quick lookups
   - Urgent requests

2. **BALANCED** - For moderate complexity queries that benefit from some reflection
   - Explanations of concepts
   - Comparisons between a few items
   - How-to questions
   - General knowledge queries

3. **OPTIMIZED** - For complex queries that need structured reflection
   - Multi-step analysis
   - Complex comparisons
   - Technical explanations
   - Research-style questions

4. **QUALITY_FIRST** - For critical or highly complex queries requiring maximum accuracy
   - Critical decisions
   - Safety-related questions
   - Comprehensive analysis requests
   - Queries explicitly requesting high accuracy

Consider these factors:
- **Complexity**: Semantic complexity, not just length
- **Criticality**: Safety, accuracy, or importance implications
- **Urgency**: Time-sensitive indicators
- **Scope**: Single vs multiple topics
- **Depth**: Surface-level vs deep analysis needed
- **User preferences**: Speed vs quality trade-offs

Respond with a JSON object containing:
{
    "recommended_strategy": "FAST|BALANCED|OPTIMIZED|QUALITY_FIRST",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this strategy was chosen",
    "complexity_score": 0.0-1.0,
    "urgency_score": 0.0-1.0,
    "criticality_score": 0.0-1.0,
    "alternative_strategy": "Second best option",
    "key_factors": ["list", "of", "key", "decision", "factors"]
}"""

    def _build_analysis_request(self, 
                               query: str, 
                               context: Optional[Dict[str, Any]] = None,
                               user_preferences: Optional[Dict[str, Any]] = None) -> str:
        """Build the analysis request for the LLM."""
        
        request = f"Please analyze this query and recommend the optimal reflection strategy:\n\n"
        request += f"**Query:** {query}\n\n"
        
        if context:
            request += f"**Context:**\n"
            if "previous_queries" in context:
                request += f"- Previous queries: {context['previous_queries']}\n"
            if "session_length" in context:
                request += f"- Session length: {context['session_length']} minutes\n"
            if "user_type" in context:
                request += f"- User type: {context['user_type']}\n"
            request += "\n"
        
        if user_preferences:
            request += f"**User Preferences:**\n"
            if "speed_preference" in user_preferences:
                speed_pref = user_preferences["speed_preference"]
                if speed_pref > 0.7:
                    request += "- Prefers fast responses over maximum quality\n"
                elif speed_pref < 0.3:
                    request += "- Prefers high quality over speed\n"
                else:
                    request += "- Balanced preference for speed and quality\n"
            request += "\n"
        
        request += "Analyze the query and provide your recommendation in the specified JSON format."
        
        return request
    
    def _parse_llm_analysis(self, analysis: Dict[str, Any]) -> ReflectionStrategy:
        """Parse LLM analysis result and return strategy."""
        
        strategy_name = analysis.get("recommended_strategy", "BALANCED").upper()
        
        strategy_mapping = {
            "FAST": ReflectionStrategy.FAST,
            "BALANCED": ReflectionStrategy.BALANCED,
            "OPTIMIZED": ReflectionStrategy.OPTIMIZED,
            "QUALITY_FIRST": ReflectionStrategy.QUALITY_FIRST
        }
        
        return strategy_mapping.get(strategy_name, ReflectionStrategy.BALANCED)
    
    def _parse_text_response(self, response_text: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON responses."""
        
        response_lower = response_text.lower()
        
        # Simple keyword-based parsing
        if "fast" in response_lower and ("simple" in response_lower or "quick" in response_lower):
            strategy = "FAST"
            confidence = 0.7
        elif "quality_first" in response_lower or "critical" in response_lower:
            strategy = "QUALITY_FIRST"
            confidence = 0.8
        elif "optimized" in response_lower or "complex" in response_lower:
            strategy = "OPTIMIZED"
            confidence = 0.7
        else:
            strategy = "BALANCED"
            confidence = 0.6
        
        return {
            "recommended_strategy": strategy,
            "confidence": confidence,
            "reasoning": "Parsed from text response",
            "complexity_score": 0.5,
            "urgency_score": 0.5,
            "criticality_score": 0.5
        }
    
    def _fallback_strategy_selection(self, 
                                   query: str, 
                                   user_preferences: Optional[Dict[str, Any]] = None) -> ReflectionStrategy:
        """Fallback strategy selection when LLM fails."""
        
        query_lower = query.lower()
        
        # Simple heuristics as fallback
        if len(query.split()) < 10:
            if any(word in query_lower for word in ["what is", "define", "calculate"]):
                return ReflectionStrategy.FAST
        
        if any(word in query_lower for word in ["critical", "important", "precise", "accurate"]):
            return ReflectionStrategy.QUALITY_FIRST
        
        if any(word in query_lower for word in ["analyze", "compare", "evaluate", "research"]):
            return ReflectionStrategy.OPTIMIZED
        
        # Default to balanced
        return ReflectionStrategy.BALANCED
    
    def _get_cache_key(self, query: str, user_preferences: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for query and preferences."""
        import hashlib
        
        # Create a hash of query + preferences
        content = query + str(user_preferences or {})
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_strategy(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached strategy if available and not expired."""
        
        if cache_key not in self.strategy_cache:
            return None
        
        cached = self.strategy_cache[cache_key]
        if time.time() - cached["timestamp"] > self.cache_ttl:
            del self.strategy_cache[cache_key]
            return None
        
        return cached
    
    def _cache_strategy(self, cache_key: str, result: Dict[str, Any]):
        """Cache strategy selection result."""
        self.strategy_cache[cache_key] = result
        
        # Clean old cache entries
        current_time = time.time()
        expired_keys = [
            key for key, value in self.strategy_cache.items()
            if current_time - value["timestamp"] > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.strategy_cache[key]
    
    async def get_strategy_recommendation_with_reasoning(self, 
                                                        query: str,
                                                        context: Optional[Dict[str, Any]] = None,
                                                        user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get strategy recommendation with detailed LLM reasoning."""
        
        try:
            # Get LLM analysis
            analysis_result = await self._analyze_query_with_llm(query, context, user_preferences)
            selected_strategy = self._parse_llm_analysis(analysis_result)
            
            return {
                "recommended_strategy": selected_strategy,
                "llm_analysis": analysis_result,
                "selection_method": "llm",
                "confidence": analysis_result.get("confidence", 0.0),
                "reasoning": analysis_result.get("reasoning", ""),
                "complexity_score": analysis_result.get("complexity_score", 0.0),
                "urgency_score": analysis_result.get("urgency_score", 0.0),
                "criticality_score": analysis_result.get("criticality_score", 0.0),
                "key_factors": analysis_result.get("key_factors", []),
                "alternative_strategy": analysis_result.get("alternative_strategy", "")
            }
            
        except Exception as e:
            # Fallback analysis
            fallback_strategy = self._fallback_strategy_selection(query, user_preferences)
            
            return {
                "recommended_strategy": fallback_strategy,
                "llm_analysis": None,
                "selection_method": "fallback",
                "confidence": 0.5,
                "reasoning": f"LLM analysis failed ({str(e)}), used fallback heuristics",
                "error": str(e)
            }
    
    def get_selection_analytics(self) -> Dict[str, Any]:
        """Get analytics about LLM-based strategy selections."""
        
        if not self.selection_history:
            return {"message": "No selection history available"}
        
        # Strategy distribution
        strategy_counts = {}
        llm_confidence_scores = []
        
        for record in self.selection_history:
            strategy = record["selected_strategy"]
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            if "confidence" in record:
                llm_confidence_scores.append(record["confidence"])
        
        avg_confidence = sum(llm_confidence_scores) / len(llm_confidence_scores) if llm_confidence_scores else 0.0
        
        return {
            "total_selections": len(self.selection_history),
            "strategy_distribution": strategy_counts,
            "average_llm_confidence": avg_confidence,
            "cache_size": len(self.strategy_cache),
            "selection_method": "llm-based",
            "recent_selections": self.selection_history[-5:] if len(self.selection_history) >= 5 else self.selection_history
        }
    
    def clear_cache(self):
        """Clear the strategy cache."""
        self.strategy_cache.clear()


# Global instance
_global_llm_selector: Optional[LLMStrategySelector] = None


def get_llm_strategy_selector() -> LLMStrategySelector:
    """Get the global LLM strategy selector."""
    global _global_llm_selector
    
    if _global_llm_selector is None:
        _global_llm_selector = LLMStrategySelector()
    
    return _global_llm_selector


async def select_strategy_with_llm(query: str,
                                  context: Optional[Dict[str, Any]] = None,
                                  user_preferences: Optional[Dict[str, Any]] = None) -> ReflectionStrategy:
    """Convenience function to select strategy using LLM analysis."""
    selector = get_llm_strategy_selector()
    return await selector.select_strategy(query, context, user_preferences)


async def get_llm_strategy_recommendation(query: str,
                                         context: Optional[Dict[str, Any]] = None,
                                         user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get detailed LLM-based strategy recommendation."""
    selector = get_llm_strategy_selector()
    return await selector.get_strategy_recommendation_with_reasoning(query, context, user_preferences)