"""Factory for creating reflection modules with different optimization strategies."""

from typing import Optional, Dict, Any
from enum import Enum

from .reflection_module import ReflectionModule
from .optimized_reflection_module import OptimizedReflectionModule
from .reflection_config import ReflectionConfig


class ReflectionStrategy(Enum):
    """Available reflection strategies."""
    STANDARD = "standard"           # Original reflection module
    OPTIMIZED = "optimized"         # Optimized reflection with all enhancements
    FAST = "fast"                   # Maximum performance, minimal quality loss
    BALANCED = "balanced"           # Balance between performance and quality
    QUALITY_FIRST = "quality_first" # Prioritize quality over performance


class ReflectionFactory:
    """Factory for creating reflection modules with different strategies."""
    
    @staticmethod
    def create_reflection_module(
        strategy: ReflectionStrategy = ReflectionStrategy.BALANCED,
        quality_threshold: float = 0.7,
        verbose: bool = False,
        custom_config: Optional[Dict[str, Any]] = None
    ):
        """Create a reflection module based on the specified strategy.
        
        Args:
            strategy: The reflection strategy to use
            quality_threshold: Minimum quality threshold
            verbose: Whether to enable verbose output
            custom_config: Custom configuration to override defaults
            
        Returns:
            Configured reflection module instance
        """
        
        if strategy == ReflectionStrategy.STANDARD:
            return ReflectionModule(
                quality_threshold=quality_threshold,
                max_refinement_iterations=3,
                verbose=verbose
            )
        
        elif strategy == ReflectionStrategy.FAST:
            config = ReflectionConfig(
                high_quality_threshold=0.8,
                quality_threshold=quality_threshold,
                skip_simple_queries=True,
                simple_query_threshold=0.4,
                enable_async_reflection=True,
                async_timeout=15.0,  # Shorter timeout
                enable_quality_prediction=True,
                prediction_confidence_threshold=0.7,  # Lower threshold
                max_refinement_iterations=1,  # Minimal refinement
                cache_predictions=True,
                cache_ttl=7200,  # 2 hours
                enable_early_stopping=True,
                early_stop_improvement_threshold=0.1  # Higher threshold for stopping
            )
            
        elif strategy == ReflectionStrategy.BALANCED:
            config = ReflectionConfig(
                high_quality_threshold=0.9,
                quality_threshold=quality_threshold,
                skip_simple_queries=True,
                simple_query_threshold=0.3,
                enable_async_reflection=True,
                async_timeout=30.0,
                enable_quality_prediction=True,
                prediction_confidence_threshold=0.8,
                max_refinement_iterations=2,
                cache_predictions=True,
                cache_ttl=3600,  # 1 hour
                enable_early_stopping=True,
                early_stop_improvement_threshold=0.05
            )
            
        elif strategy == ReflectionStrategy.OPTIMIZED:
            config = ReflectionConfig(
                high_quality_threshold=0.9,
                quality_threshold=quality_threshold,
                skip_simple_queries=True,
                simple_query_threshold=0.3,
                enable_async_reflection=True,
                async_timeout=30.0,
                enable_quality_prediction=True,
                prediction_confidence_threshold=0.8,
                max_refinement_iterations=2,
                cache_predictions=True,
                cache_ttl=3600,
                enable_early_stopping=True,
                early_stop_improvement_threshold=0.05
            )
            
        elif strategy == ReflectionStrategy.QUALITY_FIRST:
            config = ReflectionConfig(
                high_quality_threshold=0.95,  # Very high threshold
                quality_threshold=quality_threshold,
                skip_simple_queries=False,  # Reflect on everything
                enable_async_reflection=False,  # Always synchronous
                enable_quality_prediction=False,  # No shortcuts
                max_refinement_iterations=3,  # More iterations
                cache_predictions=False,  # No caching
                enable_early_stopping=False,  # No early stopping
                early_stop_improvement_threshold=0.01  # Very low threshold
            )
        
        else:
            # Default to balanced
            config = ReflectionConfig()
        
        # Apply custom configuration overrides
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        return OptimizedReflectionModule(config=config, verbose=verbose)
    
    @staticmethod
    def get_strategy_info(strategy: ReflectionStrategy) -> Dict[str, Any]:
        """Get information about a reflection strategy.
        
        Args:
            strategy: The strategy to get info for
            
        Returns:
            Dictionary with strategy information
        """
        strategy_info = {
            ReflectionStrategy.STANDARD: {
                "description": "Original reflection module with standard behavior",
                "performance": "Moderate",
                "quality": "High",
                "llm_calls": "3-4 per query",
                "use_cases": ["High-quality responses required", "Simple implementation"]
            },
            
            ReflectionStrategy.FAST: {
                "description": "Maximum performance optimization with minimal quality impact",
                "performance": "Very High",
                "quality": "Good", 
                "llm_calls": "0-2 per query",
                "use_cases": ["High-throughput applications", "Simple queries", "Real-time responses"]
            },
            
            ReflectionStrategy.BALANCED: {
                "description": "Optimal balance between performance and quality",
                "performance": "High",
                "quality": "High",
                "llm_calls": "1-3 per query",
                "use_cases": ["General purpose", "Production systems", "Mixed query complexity"]
            },
            
            ReflectionStrategy.OPTIMIZED: {
                "description": "Full optimization suite with all enhancements enabled",
                "performance": "High",
                "quality": "High",
                "llm_calls": "1-3 per query",
                "use_cases": ["Advanced applications", "Complex queries", "Resource optimization"]
            },
            
            ReflectionStrategy.QUALITY_FIRST: {
                "description": "Prioritizes maximum quality over performance",
                "performance": "Moderate",
                "quality": "Very High",
                "llm_calls": "3-4 per query",
                "use_cases": ["Critical applications", "Complex analysis", "Research queries"]
            }
        }
        
        return strategy_info.get(strategy, {})
    
    @staticmethod
    def recommend_strategy(
        query_complexity: str = "mixed",
        performance_priority: str = "balanced",
        quality_requirements: str = "high"
    ) -> ReflectionStrategy:
        """Recommend a reflection strategy based on requirements.
        
        Args:
            query_complexity: "simple", "moderate", "complex", or "mixed"
            performance_priority: "low", "balanced", or "high"
            quality_requirements: "good", "high", or "critical"
            
        Returns:
            Recommended reflection strategy
        """
        
        # Quality-first scenarios
        if quality_requirements == "critical":
            return ReflectionStrategy.QUALITY_FIRST
        
        # Performance-first scenarios
        if performance_priority == "high":
            if query_complexity == "simple":
                return ReflectionStrategy.FAST
            else:
                return ReflectionStrategy.BALANCED
        
        # Complex query scenarios
        if query_complexity == "complex":
            if performance_priority == "low":
                return ReflectionStrategy.QUALITY_FIRST
            else:
                return ReflectionStrategy.OPTIMIZED
        
        # Simple query scenarios
        if query_complexity == "simple":
            return ReflectionStrategy.FAST
        
        # Default balanced approach
        return ReflectionStrategy.BALANCED


# Convenience functions for common configurations
def create_fast_reflection(quality_threshold: float = 0.7, verbose: bool = False):
    """Create a fast reflection module optimized for performance."""
    return ReflectionFactory.create_reflection_module(
        ReflectionStrategy.FAST, quality_threshold, verbose
    )

def create_balanced_reflection(quality_threshold: float = 0.7, verbose: bool = False):
    """Create a balanced reflection module for general use."""
    return ReflectionFactory.create_reflection_module(
        ReflectionStrategy.BALANCED, quality_threshold, verbose
    )

def create_quality_reflection(quality_threshold: float = 0.8, verbose: bool = False):
    """Create a quality-first reflection module."""
    return ReflectionFactory.create_reflection_module(
        ReflectionStrategy.QUALITY_FIRST, quality_threshold, verbose
    )