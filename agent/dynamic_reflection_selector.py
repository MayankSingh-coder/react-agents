"""Dynamic reflection strategy selector that adapts strategy based on query characteristics."""

import re
import time
from typing import Dict, Any, Optional, List
from enum import Enum

from .reflection_factory import ReflectionStrategy


class QueryCharacteristics:
    """Characteristics of a query that influence strategy selection."""
    
    def __init__(self, query: str, context: Optional[Dict[str, Any]] = None):
        self.query = query.lower()
        self.original_query = query
        self.context = context or {}
        self.length = len(query.split())
        self.complexity_score = self._calculate_complexity()
        self.urgency_score = self._calculate_urgency()
        self.quality_requirement = self._determine_quality_requirement()
    
    def _calculate_complexity(self) -> float:
        """Calculate query complexity score (0.0 - 1.0)."""
        score = 0.0
        
        # Length factor
        if self.length > 100:
            score += 0.3
        elif self.length > 50:
            score += 0.2
        elif self.length > 20:
            score += 0.1
        
        # Complexity indicators
        complex_patterns = [
            r'\banalyze\b', r'\bevaluate\b', r'\bassess\b', r'\bcompare.*and\b',
            r'\bcreate.*plan\b', r'\bstrategy\b', r'\bresearch.*and\b',
            r'\bmultiple.*factors\b', r'\bcomprehensive\b', r'\bdetailed\b'
        ]
        
        moderate_patterns = [
            r'\bexplain\b', r'\bhow.*work\b', r'\bsteps\b', r'\bprocess\b',
            r'\blist.*and\b', r'\bcompare\b', r'\bdifferences\b'
        ]
        
        simple_patterns = [
            r'\bwhat is\b', r'\bdefine\b', r'\bcalculate\b', r'\bconvert\b',
            r'^\d+[\+\-\*\/]\d+', r'\bweather\b', r'\btranslate\b'
        ]
        
        # Complex patterns
        complex_matches = sum(1 for pattern in complex_patterns 
                            if re.search(pattern, self.query))
        score += complex_matches * 0.15
        
        # Moderate patterns
        moderate_matches = sum(1 for pattern in moderate_patterns 
                             if re.search(pattern, self.query))
        score += moderate_matches * 0.1
        
        # Simple patterns (negative score)
        simple_matches = sum(1 for pattern in simple_patterns 
                           if re.search(pattern, self.query))
        score -= simple_matches * 0.2
        
        # Multiple questions/tasks
        if self.query.count('?') > 1 or self.query.count(' and ') > 2:
            score += 0.2
        
        # Conditional/logical structures
        if any(word in self.query for word in ['if', 'then', 'because', 'therefore', 'however']):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_urgency(self) -> float:
        """Calculate urgency score based on query indicators (0.0 - 1.0)."""
        urgency_indicators = [
            r'\bquick\b', r'\bfast\b', r'\bimmediately\b', r'\burgent\b',
            r'\bright now\b', r'\basap\b', r'\bshort\b'
        ]
        
        urgency_score = sum(1 for pattern in urgency_indicators 
                          if re.search(pattern, self.query)) * 0.3
        
        # Short queries often need quick responses
        if self.length < 10:
            urgency_score += 0.2
        
        return min(1.0, urgency_score)
    
    def _determine_quality_requirement(self) -> str:
        """Determine quality requirement level."""
        quality_indicators = {
            'critical': [
                r'\bcritical\b', r'\bimportant\b', r'\bessential\b',
                r'\bmust be accurate\b', r'\bprecise\b', r'\bexact\b'
            ],
            'high': [
                r'\bdetailed\b', r'\bcomprehensive\b', r'\bthorough\b',
                r'\bin-depth\b', r'\bresearch\b', r'\banalysis\b'
            ],
            'standard': []  # Default
        }
        
        for level, patterns in quality_indicators.items():
            if any(re.search(pattern, self.query) for pattern in patterns):
                return level
        
        return 'standard'


class DynamicReflectionSelector:
    """Dynamically selects reflection strategy based on query characteristics."""
    
    def __init__(self, default_strategy: ReflectionStrategy = ReflectionStrategy.BALANCED):
        self.default_strategy = default_strategy
        self.selection_history = []
        self.performance_cache = {}
    
    def select_strategy(self, 
                       query: str, 
                       context: Optional[Dict[str, Any]] = None,
                       user_preferences: Optional[Dict[str, Any]] = None) -> ReflectionStrategy:
        """Select optimal reflection strategy for the given query.
        
        Args:
            query: The user query
            context: Additional context (previous queries, user info, etc.)
            user_preferences: User preferences for speed vs quality
            
        Returns:
            Recommended ReflectionStrategy
        """
        
        characteristics = QueryCharacteristics(query, context)
        
        # Record selection attempt
        selection_record = {
            'timestamp': time.time(),
            'query': query[:100] + '...' if len(query) > 100 else query,
            'complexity': characteristics.complexity_score,
            'urgency': characteristics.urgency_score,
            'quality_requirement': characteristics.quality_requirement
        }
        
        # Strategy selection logic
        strategy = self._determine_strategy(characteristics, user_preferences)
        
        selection_record['selected_strategy'] = strategy.value
        selection_record['selection_reason'] = self._get_selection_reason(
            characteristics, strategy
        )
        
        self.selection_history.append(selection_record)
        
        # Keep only recent history
        if len(self.selection_history) > 1000:
            self.selection_history = self.selection_history[-500:]
        
        return strategy
    
    def _determine_strategy(self, 
                           characteristics: QueryCharacteristics,
                           user_preferences: Optional[Dict[str, Any]] = None) -> ReflectionStrategy:
        """Core strategy selection logic."""
        
        complexity = characteristics.complexity_score
        urgency = characteristics.urgency_score
        quality_req = characteristics.quality_requirement
        
        # Get user preference weights (default to balanced)
        prefs = user_preferences or {}
        speed_weight = prefs.get('speed_preference', 0.5)  # 0.0 = quality first, 1.0 = speed first
        quality_weight = 1.0 - speed_weight
        
        # Critical quality requirements override everything
        if quality_req == 'critical':
            return ReflectionStrategy.QUALITY_FIRST
        
        # Very high urgency with low complexity -> FAST
        if urgency > 0.7 and complexity < 0.3:
            return ReflectionStrategy.FAST
        
        # High urgency generally favors speed
        if urgency > 0.5:
            if complexity < 0.5:
                return ReflectionStrategy.FAST
            else:
                return ReflectionStrategy.BALANCED
        
        # Complex queries with high quality requirements
        if complexity > 0.7:
            if quality_req == 'high' or quality_weight > 0.7:
                return ReflectionStrategy.QUALITY_FIRST
            else:
                return ReflectionStrategy.BALANCED
        
        # Simple queries
        if complexity < 0.3:
            if speed_weight > 0.7:
                return ReflectionStrategy.FAST
            else:
                return ReflectionStrategy.BALANCED
        
        # Moderate complexity - use user preference to decide
        if speed_weight > 0.7:
            return ReflectionStrategy.FAST
        elif quality_weight > 0.7:
            return ReflectionStrategy.QUALITY_FIRST
        else:
            return ReflectionStrategy.BALANCED
    
    def _get_selection_reason(self, 
                             characteristics: QueryCharacteristics,
                             strategy: ReflectionStrategy) -> str:
        """Generate human-readable reason for strategy selection."""
        
        complexity = characteristics.complexity_score
        urgency = characteristics.urgency_score
        quality_req = characteristics.quality_requirement
        
        if strategy == ReflectionStrategy.FAST:
            if urgency > 0.7:
                return f"High urgency ({urgency:.1f}) with manageable complexity ({complexity:.1f})"
            elif complexity < 0.3:
                return f"Simple query (complexity: {complexity:.1f}) - optimizing for speed"
            else:
                return "User preference for speed over quality"
        
        elif strategy == ReflectionStrategy.QUALITY_FIRST:
            if quality_req == 'critical':
                return "Critical quality requirement detected"
            elif complexity > 0.7:
                return f"High complexity ({complexity:.1f}) requires thorough reflection"
            else:
                return "User preference for quality over speed"
        
        else:  # BALANCED
            return f"Balanced approach for moderate complexity ({complexity:.1f}) and urgency ({urgency:.1f})"
    
    def get_strategy_recommendation_with_reasoning(self, 
                                                  query: str,
                                                  context: Optional[Dict[str, Any]] = None,
                                                  user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get strategy recommendation with detailed reasoning."""
        
        characteristics = QueryCharacteristics(query, context)
        strategy = self.select_strategy(query, context, user_preferences)
        
        return {
            'recommended_strategy': strategy,
            'query_characteristics': {
                'complexity_score': characteristics.complexity_score,
                'urgency_score': characteristics.urgency_score,
                'quality_requirement': characteristics.quality_requirement,
                'query_length': characteristics.length
            },
            'selection_reason': self._get_selection_reason(characteristics, strategy),
            'alternative_strategies': self._get_alternative_strategies(characteristics),
            'expected_performance': self._estimate_performance(strategy, characteristics)
        }
    
    def _get_alternative_strategies(self, characteristics: QueryCharacteristics) -> List[Dict[str, Any]]:
        """Get alternative strategy options with trade-offs."""
        
        alternatives = []
        all_strategies = [ReflectionStrategy.FAST, ReflectionStrategy.BALANCED, ReflectionStrategy.QUALITY_FIRST]
        
        for strategy in all_strategies:
            perf = self._estimate_performance(strategy, characteristics)
            alternatives.append({
                'strategy': strategy,
                'estimated_speed': perf['speed_score'],
                'estimated_quality': perf['quality_score'],
                'estimated_calls': perf['llm_calls'],
                'trade_off': perf['trade_off']
            })
        
        return sorted(alternatives, key=lambda x: x['estimated_speed'] + x['estimated_quality'], reverse=True)
    
    def _estimate_performance(self, 
                             strategy: ReflectionStrategy,
                             characteristics: QueryCharacteristics) -> Dict[str, Any]:
        """Estimate performance metrics for a strategy."""
        
        complexity = characteristics.complexity_score
        
        if strategy == ReflectionStrategy.FAST:
            speed_score = 0.9 - (complexity * 0.1)  # Slight slowdown for complex queries
            quality_score = 0.7 + (complexity * 0.1)  # Better quality for complex queries
            llm_calls = 1 + int(complexity > 0.5)  # 1-2 calls
            trade_off = "Prioritizes speed, may sacrifice some quality"
            
        elif strategy == ReflectionStrategy.QUALITY_FIRST:
            speed_score = 0.5 - (complexity * 0.2)  # Slower for complex queries
            quality_score = 0.9 + (complexity * 0.05)  # Excellent quality
            llm_calls = 3 + int(complexity > 0.7)  # 3-4 calls
            trade_off = "Prioritizes quality, takes longer"
            
        else:  # BALANCED
            speed_score = 0.7 - (complexity * 0.15)
            quality_score = 0.8 + (complexity * 0.05)
            llm_calls = 2 + int(complexity > 0.6)  # 2-3 calls
            trade_off = "Good balance of speed and quality"
        
        return {
            'speed_score': max(0.1, min(1.0, speed_score)),
            'quality_score': max(0.1, min(1.0, quality_score)),
            'llm_calls': llm_calls,
            'trade_off': trade_off
        }
    
    def get_selection_analytics(self) -> Dict[str, Any]:
        """Get analytics on strategy selections."""
        
        if not self.selection_history:
            return {'message': 'No selection history available'}
        
        # Strategy distribution
        strategy_counts = {}
        complexity_by_strategy = {}
        
        for record in self.selection_history:
            strategy = record['selected_strategy']
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            if strategy not in complexity_by_strategy:
                complexity_by_strategy[strategy] = []
            complexity_by_strategy[strategy].append(record['complexity'])
        
        # Average complexity by strategy
        avg_complexity = {}
        for strategy, complexities in complexity_by_strategy.items():
            avg_complexity[strategy] = sum(complexities) / len(complexities)
        
        return {
            'total_selections': len(self.selection_history),
            'strategy_distribution': strategy_counts,
            'average_complexity_by_strategy': avg_complexity,
            'recent_selections': self.selection_history[-10:] if len(self.selection_history) >= 10 else self.selection_history
        }


# Global selector instance
_global_selector: Optional[DynamicReflectionSelector] = None


def get_dynamic_selector() -> DynamicReflectionSelector:
    """Get the global dynamic reflection selector."""
    global _global_selector
    
    if _global_selector is None:
        _global_selector = DynamicReflectionSelector()
    
    return _global_selector


def select_strategy_for_query(query: str,
                             context: Optional[Dict[str, Any]] = None,
                             user_preferences: Optional[Dict[str, Any]] = None) -> ReflectionStrategy:
    """Convenience function to select strategy for a query."""
    selector = get_dynamic_selector()
    return selector.select_strategy(query, context, user_preferences)


def get_strategy_recommendation(query: str,
                               context: Optional[Dict[str, Any]] = None,
                               user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get detailed strategy recommendation for a query."""
    selector = get_dynamic_selector()
    return selector.get_strategy_recommendation_with_reasoning(query, context, user_preferences)