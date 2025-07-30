"""Configuration settings for reflection optimization."""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# ReflectionStrategy will be imported when needed to avoid circular imports


@dataclass
class ReflectionConfig:
    """Configuration for reflection optimization settings."""
    
    # Strategy selection
    default_strategy: str = "balanced"  # Will be converted to ReflectionStrategy when needed
    
    # Performance thresholds
    high_quality_threshold: float = 0.9
    quality_threshold: float = 0.7
    simple_query_threshold: float = 0.3
    
    # Optimization toggles
    skip_simple_queries: bool = True
    enable_async_reflection: bool = True
    enable_quality_prediction: bool = True
    enable_early_stopping: bool = True
    cache_predictions: bool = True
    
    # Performance limits
    max_refinement_iterations: int = 2
    async_timeout: float = 30.0
    cache_ttl: int = 3600  # 1 hour
    early_stop_improvement_threshold: float = 0.05
    prediction_confidence_threshold: float = 0.8
    
    # Environment-based overrides
    @classmethod
    def from_environment(cls) -> 'ReflectionConfig':
        """Create configuration from environment variables."""
        
        # Map environment variables to config attributes
        env_mappings = {
            'REFLECTION_STRATEGY': 'default_strategy',
            'REFLECTION_HIGH_QUALITY_THRESHOLD': 'high_quality_threshold',
            'REFLECTION_QUALITY_THRESHOLD': 'quality_threshold',
            'REFLECTION_SKIP_SIMPLE': 'skip_simple_queries',
            'REFLECTION_ENABLE_ASYNC': 'enable_async_reflection',
            'REFLECTION_ENABLE_PREDICTION': 'enable_quality_prediction',
            'REFLECTION_ENABLE_EARLY_STOP': 'enable_early_stopping',
            'REFLECTION_CACHE_ENABLED': 'cache_predictions',
            'REFLECTION_MAX_ITERATIONS': 'max_refinement_iterations',
            'REFLECTION_ASYNC_TIMEOUT': 'async_timeout',
            'REFLECTION_CACHE_TTL': 'cache_ttl'
        }
        
        config_kwargs = {}
        
        for env_var, config_attr in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert environment string to appropriate type
                if config_attr == 'default_strategy':
                    # Store as string, will be converted to enum when needed
                    config_kwargs[config_attr] = env_value.lower()
                elif config_attr in ['high_quality_threshold', 'quality_threshold', 
                                   'simple_query_threshold', 'async_timeout',
                                   'early_stop_improvement_threshold', 'prediction_confidence_threshold']:
                    try:
                        config_kwargs[config_attr] = float(env_value)
                    except ValueError:
                        pass
                elif config_attr in ['max_refinement_iterations', 'cache_ttl']:
                    try:
                        config_kwargs[config_attr] = int(env_value)
                    except ValueError:
                        pass
                elif config_attr in ['skip_simple_queries', 'enable_async_reflection',
                                   'enable_quality_prediction', 'enable_early_stopping',
                                   'cache_predictions']:
                    config_kwargs[config_attr] = env_value.lower() in ('true', '1', 'yes', 'on')
        
        return cls(**config_kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        config_dict = asdict(self)
        # default_strategy is already a string
        return config_dict
    
    def get_strategy_config(self, strategy: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific strategy."""
        target_strategy = strategy or self.default_strategy
        
        if target_strategy == "fast":
            return {
                'high_quality_threshold': 0.8,
                'quality_threshold': self.quality_threshold,
                'skip_simple_queries': True,
                'simple_query_threshold': 0.4,
                'enable_async_reflection': True,
                'async_timeout': 15.0,
                'enable_quality_prediction': True,
                'prediction_confidence_threshold': 0.7,
                'max_refinement_iterations': 1,
                'cache_predictions': True,
                'cache_ttl': 7200,
                'enable_early_stopping': True,
                'early_stop_improvement_threshold': 0.1
            }
        
        elif target_strategy == "balanced":
            return {
                'high_quality_threshold': self.high_quality_threshold,
                'quality_threshold': self.quality_threshold,
                'skip_simple_queries': self.skip_simple_queries,
                'simple_query_threshold': self.simple_query_threshold,
                'enable_async_reflection': self.enable_async_reflection,
                'async_timeout': self.async_timeout,
                'enable_quality_prediction': self.enable_quality_prediction,
                'prediction_confidence_threshold': self.prediction_confidence_threshold,
                'max_refinement_iterations': self.max_refinement_iterations,
                'cache_predictions': self.cache_predictions,
                'cache_ttl': self.cache_ttl,
                'enable_early_stopping': self.enable_early_stopping,
                'early_stop_improvement_threshold': self.early_stop_improvement_threshold
            }
        
        elif target_strategy == "quality_first":
            return {
                'high_quality_threshold': 0.95,
                'quality_threshold': self.quality_threshold,
                'skip_simple_queries': False,
                'enable_async_reflection': False,
                'enable_quality_prediction': False,
                'max_refinement_iterations': 3,
                'cache_predictions': False,
                'enable_early_stopping': False,
                'early_stop_improvement_threshold': 0.01
            }
        
        else:
            # Default configuration
            return self.to_dict()


# Global configuration instance
_global_config: Optional[ReflectionConfig] = None


def get_reflection_config() -> ReflectionConfig:
    """Get the global reflection configuration."""
    global _global_config
    
    if _global_config is None:
        _global_config = ReflectionConfig.from_environment()
    
    return _global_config


def set_reflection_config(config: ReflectionConfig):
    """Set the global reflection configuration."""
    global _global_config
    _global_config = config


def reset_reflection_config():
    """Reset to default configuration."""
    global _global_config
    _global_config = ReflectionConfig()


# Preset configurations for common scenarios
PRESET_CONFIGS = {
    'development': ReflectionConfig(
        default_strategy="fast",
        skip_simple_queries=True,
        enable_async_reflection=True,
        cache_predictions=True,
        max_refinement_iterations=1
    ),
    
    'production': ReflectionConfig(
        default_strategy="balanced",
        skip_simple_queries=True,
        enable_async_reflection=True,
        enable_quality_prediction=True,
        enable_early_stopping=True,
        cache_predictions=True,
        max_refinement_iterations=2
    ),
    
    'high_quality': ReflectionConfig(
        default_strategy="quality_first",
        skip_simple_queries=False,
        enable_async_reflection=False,
        enable_quality_prediction=False,
        cache_predictions=False,
        max_refinement_iterations=3
    ),
    
    'high_performance': ReflectionConfig(
        default_strategy="fast",
        skip_simple_queries=True,
        simple_query_threshold=0.4,
        enable_async_reflection=True,
        async_timeout=15.0,
        enable_quality_prediction=True,
        prediction_confidence_threshold=0.7,
        max_refinement_iterations=1,
        cache_predictions=True,
        cache_ttl=7200
    )
}


def load_preset_config(preset_name: str) -> ReflectionConfig:
    """Load a preset configuration."""
    if preset_name not in PRESET_CONFIGS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(PRESET_CONFIGS.keys())}")
    
    return PRESET_CONFIGS[preset_name]


def apply_preset_config(preset_name: str):
    """Apply a preset configuration globally."""
    config = load_preset_config(preset_name)
    set_reflection_config(config)


# Environment variable documentation
ENV_VAR_DOCS = """
Environment Variables for Reflection Configuration:

Performance Settings:
- REFLECTION_STRATEGY: fast|balanced|optimized|quality_first (default: balanced)
- REFLECTION_HIGH_QUALITY_THRESHOLD: 0.0-1.0 (default: 0.9)
- REFLECTION_QUALITY_THRESHOLD: 0.0-1.0 (default: 0.7)

Optimization Toggles:
- REFLECTION_SKIP_SIMPLE: true|false (default: true)
- REFLECTION_ENABLE_ASYNC: true|false (default: true)
- REFLECTION_ENABLE_PREDICTION: true|false (default: true)
- REFLECTION_ENABLE_EARLY_STOP: true|false (default: true)
- REFLECTION_CACHE_ENABLED: true|false (default: true)

Performance Limits:
- REFLECTION_MAX_ITERATIONS: integer (default: 2)
- REFLECTION_ASYNC_TIMEOUT: seconds (default: 30.0)
- REFLECTION_CACHE_TTL: seconds (default: 3600)

Example .env file:
REFLECTION_STRATEGY=balanced
REFLECTION_SKIP_SIMPLE=true
REFLECTION_ENABLE_ASYNC=true
REFLECTION_MAX_ITERATIONS=2
"""