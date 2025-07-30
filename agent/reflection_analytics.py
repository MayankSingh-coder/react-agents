"""Analytics and monitoring for reflection optimization performance."""

import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import statistics
import threading


class MetricType(Enum):
    """Types of metrics to track."""
    PROCESSING_TIME = "processing_time"
    QUALITY_SCORE = "quality_score"
    REFLECTION_SKIPPED = "reflection_skipped"
    SKIP_REASON = "skip_reason"
    LLM_CALLS = "llm_calls"
    CACHE_HIT_RATE = "cache_hit_rate"
    IMPROVEMENT_GAINED = "improvement_gained"


@dataclass
class ReflectionMetrics:
    """Metrics for a single reflection operation."""
    
    # Basic info
    timestamp: float
    session_id: str
    query: str
    query_complexity: str
    strategy_used: str
    
    # Performance metrics
    processing_time: float
    total_time: float
    reflection_skipped: bool
    skip_reason: Optional[str]
    
    # Quality metrics
    initial_quality: Optional[float]
    final_quality: Optional[float]
    quality_improvement: float
    reflection_iterations: int
    
    # Resource usage
    llm_calls_made: int
    cache_hits: int
    cache_misses: int
    
    # Optimization impact
    estimated_time_saved: float
    estimated_calls_saved: int
    
    # Metadata
    metadata: Dict[str, Any]


class ReflectionAnalytics:
    """Analytics system for tracking reflection performance and optimization impact."""
    
    def __init__(self, max_history: int = 10000):
        """Initialize analytics system.
        
        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history
        self._metrics_history = deque(maxlen=max_history)
        self._session_metrics = defaultdict(list)
        self._strategy_metrics = defaultdict(list)
        self._lock = threading.Lock()
        
        # Running statistics
        self._running_stats = {
            MetricType.PROCESSING_TIME: [],
            MetricType.QUALITY_SCORE: [],
            MetricType.LLM_CALLS: [],
            MetricType.CACHE_HIT_RATE: []
        }
    
    def record_reflection_metrics(self, metrics: ReflectionMetrics):
        """Record metrics from a reflection operation."""
        with self._lock:
            # Add to history
            self._metrics_history.append(metrics)
            
            # Update session metrics
            self._session_metrics[metrics.session_id].append(metrics)
            
            # Update strategy metrics
            self._strategy_metrics[metrics.strategy_used].append(metrics)
            
            # Update running statistics
            self._update_running_stats(metrics)
    
    def _update_running_stats(self, metrics: ReflectionMetrics):
        """Update running statistics with new metrics."""
        # Keep only recent metrics for running stats (last 1000)
        max_running_stats = 1000
        
        # Processing time
        self._running_stats[MetricType.PROCESSING_TIME].append(metrics.processing_time)
        if len(self._running_stats[MetricType.PROCESSING_TIME]) > max_running_stats:
            self._running_stats[MetricType.PROCESSING_TIME].pop(0)
        
        # Quality score (if available)
        if metrics.final_quality is not None:
            self._running_stats[MetricType.QUALITY_SCORE].append(metrics.final_quality)
            if len(self._running_stats[MetricType.QUALITY_SCORE]) > max_running_stats:
                self._running_stats[MetricType.QUALITY_SCORE].pop(0)
        
        # LLM calls
        self._running_stats[MetricType.LLM_CALLS].append(metrics.llm_calls_made)
        if len(self._running_stats[MetricType.LLM_CALLS]) > max_running_stats:
            self._running_stats[MetricType.LLM_CALLS].pop(0)
        
        # Cache hit rate
        total_cache_ops = metrics.cache_hits + metrics.cache_misses
        if total_cache_ops > 0:
            hit_rate = metrics.cache_hits / total_cache_ops
            self._running_stats[MetricType.CACHE_HIT_RATE].append(hit_rate)
            if len(self._running_stats[MetricType.CACHE_HIT_RATE]) > max_running_stats:
                self._running_stats[MetricType.CACHE_HIT_RATE].pop(0)
    
    def get_performance_summary(self, 
                               time_window_hours: Optional[float] = None,
                               strategy: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary statistics.
        
        Args:
            time_window_hours: Only include metrics from last N hours
            strategy: Filter by specific strategy
            
        Returns:
            Dictionary with performance statistics
        """
        with self._lock:
            # Filter metrics based on criteria
            filtered_metrics = self._filter_metrics(time_window_hours, strategy)
            
            if not filtered_metrics:
                return {"message": "No metrics available for the specified criteria"}
            
            # Calculate statistics
            processing_times = [m.processing_time for m in filtered_metrics]
            quality_scores = [m.final_quality for m in filtered_metrics if m.final_quality is not None]
            llm_calls = [m.llm_calls_made for m in filtered_metrics]
            skipped_count = sum(1 for m in filtered_metrics if m.reflection_skipped)
            
            # Skip reasons breakdown
            skip_reasons = defaultdict(int)
            for m in filtered_metrics:
                if m.reflection_skipped and m.skip_reason:
                    skip_reasons[m.skip_reason] += 1
            
            # Strategy breakdown
            strategy_breakdown = defaultdict(int)
            for m in filtered_metrics:
                strategy_breakdown[m.strategy_used] += 1
            
            return {
                "total_operations": len(filtered_metrics),
                "time_period": f"Last {time_window_hours}h" if time_window_hours else "All time",
                
                # Performance metrics
                "processing_time": {
                    "mean": statistics.mean(processing_times),
                    "median": statistics.median(processing_times),
                    "min": min(processing_times),
                    "max": max(processing_times),
                    "std_dev": statistics.stdev(processing_times) if len(processing_times) > 1 else 0
                },
                
                # Quality metrics
                "quality_scores": {
                    "mean": statistics.mean(quality_scores) if quality_scores else None,
                    "median": statistics.median(quality_scores) if quality_scores else None,
                    "min": min(quality_scores) if quality_scores else None,
                    "max": max(quality_scores) if quality_scores else None,
                    "count": len(quality_scores)
                } if quality_scores else None,
                
                # Resource usage
                "llm_calls": {
                    "mean": statistics.mean(llm_calls),
                    "total": sum(llm_calls),
                    "saved_estimate": sum(m.estimated_calls_saved for m in filtered_metrics)
                },
                
                # Optimization impact
                "optimization": {
                    "skip_rate": skipped_count / len(filtered_metrics),
                    "skip_reasons": dict(skip_reasons),
                    "total_time_saved": sum(m.estimated_time_saved for m in filtered_metrics),
                    "avg_time_saved_per_op": statistics.mean([m.estimated_time_saved for m in filtered_metrics])
                },
                
                # Strategy breakdown
                "strategies": dict(strategy_breakdown)
            }
    
    def _filter_metrics(self, 
                       time_window_hours: Optional[float] = None,
                       strategy: Optional[str] = None) -> List[ReflectionMetrics]:
        """Filter metrics based on criteria."""
        
        metrics = list(self._metrics_history)
        
        # Filter by time window
        if time_window_hours is not None:
            cutoff_time = time.time() - (time_window_hours * 3600)
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        # Filter by strategy
        if strategy is not None:
            metrics = [m for m in metrics if m.strategy_used == strategy]
        
        return metrics
    
    def get_strategy_comparison(self) -> Dict[str, Any]:
        """Compare performance across different reflection strategies."""
        
        with self._lock:
            comparison = {}
            
            for strategy, metrics_list in self._strategy_metrics.items():
                if not metrics_list:
                    continue
                
                processing_times = [m.processing_time for m in metrics_list]
                quality_scores = [m.final_quality for m in metrics_list if m.final_quality is not None]
                skipped_count = sum(1 for m in metrics_list if m.reflection_skipped)
                
                comparison[strategy] = {
                    "total_operations": len(metrics_list),
                    "avg_processing_time": statistics.mean(processing_times),
                    "avg_quality_score": statistics.mean(quality_scores) if quality_scores else None,
                    "skip_rate": skipped_count / len(metrics_list),
                    "avg_llm_calls": statistics.mean([m.llm_calls_made for m in metrics_list]),
                    "total_time_saved": sum(m.estimated_time_saved for m in metrics_list),
                    "total_calls_saved": sum(m.estimated_calls_saved for m in metrics_list)
                }
            
            return comparison
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization impact report."""
        
        with self._lock:
            if not self._metrics_history:
                return {"message": "No metrics available"}
            
            total_operations = len(self._metrics_history)
            total_skipped = sum(1 for m in self._metrics_history if m.reflection_skipped)
            
            # Calculate savings
            total_time_saved = sum(m.estimated_time_saved for m in self._metrics_history)
            total_calls_saved = sum(m.estimated_calls_saved for m in self._metrics_history)
            
            # Quality impact
            quality_metrics = [m for m in self._metrics_history if m.initial_quality is not None and m.final_quality is not None]
            avg_quality_improvement = statistics.mean([m.quality_improvement for m in quality_metrics]) if quality_metrics else 0
            
            # Skip reason analysis
            skip_reasons = defaultdict(int)
            for m in self._metrics_history:
                if m.reflection_skipped and m.skip_reason:
                    skip_reasons[m.skip_reason] += 1
            
            return {
                "summary": {
                    "total_operations": total_operations,
                    "optimizations_applied": total_skipped,
                    "optimization_rate": total_skipped / total_operations if total_operations > 0 else 0
                },
                
                "performance_gains": {
                    "total_time_saved_seconds": total_time_saved,
                    "avg_time_saved_per_operation": total_time_saved / total_operations if total_operations > 0 else 0,
                    "total_llm_calls_saved": total_calls_saved,
                    "avg_calls_saved_per_operation": total_calls_saved / total_operations if total_operations > 0 else 0
                },
                
                "quality_impact": {
                    "avg_quality_improvement": avg_quality_improvement,
                    "operations_with_quality_data": len(quality_metrics)
                },
                
                "optimization_breakdown": {
                    "skip_reasons": dict(skip_reasons),
                    "most_common_optimization": max(skip_reasons.items(), key=lambda x: x[1])[0] if skip_reasons else None
                }
            }
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics data for external analysis.
        
        Args:
            format: Export format ("json" or "csv")
            
        Returns:
            Serialized metrics data
        """
        with self._lock:
            if format.lower() == "json":
                metrics_data = [asdict(m) for m in self._metrics_history]
                return json.dumps(metrics_data, indent=2)
            
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                if self._metrics_history:
                    fieldnames = asdict(self._metrics_history[0]).keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for metrics in self._metrics_history:
                        writer.writerow(asdict(metrics))
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def clear_history(self):
        """Clear all metrics history."""
        with self._lock:
            self._metrics_history.clear()
            self._session_metrics.clear()
            self._strategy_metrics.clear()
            self._running_stats = {metric: [] for metric in MetricType}
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time performance statistics."""
        with self._lock:
            if not self._running_stats[MetricType.PROCESSING_TIME]:
                return {"message": "No recent data available"}
            
            recent_times = self._running_stats[MetricType.PROCESSING_TIME][-100:]  # Last 100 operations
            recent_quality = self._running_stats[MetricType.QUALITY_SCORE][-100:] if self._running_stats[MetricType.QUALITY_SCORE] else []
            recent_llm_calls = self._running_stats[MetricType.LLM_CALLS][-100:]
            
            return {
                "recent_operations": len(recent_times),
                "avg_processing_time": statistics.mean(recent_times),
                "avg_quality_score": statistics.mean(recent_quality) if recent_quality else None,
                "avg_llm_calls": statistics.mean(recent_llm_calls),
                "cache_hit_rate": statistics.mean(self._running_stats[MetricType.CACHE_HIT_RATE][-100:]) if self._running_stats[MetricType.CACHE_HIT_RATE] else None
            }


# Global analytics instance
_global_analytics: Optional[ReflectionAnalytics] = None


def get_reflection_analytics() -> ReflectionAnalytics:
    """Get the global reflection analytics instance."""
    global _global_analytics
    
    if _global_analytics is None:
        _global_analytics = ReflectionAnalytics()
    
    return _global_analytics


def record_reflection_operation(
    session_id: str,
    query: str,
    query_complexity: str,
    strategy_used: str,
    processing_time: float,
    total_time: float,
    reflection_skipped: bool,
    skip_reason: Optional[str] = None,
    initial_quality: Optional[float] = None,
    final_quality: Optional[float] = None,
    quality_improvement: float = 0.0,
    reflection_iterations: int = 0,
    llm_calls_made: int = 0,
    cache_hits: int = 0,
    cache_misses: int = 0,
    estimated_time_saved: float = 0.0,
    estimated_calls_saved: int = 0,
    **metadata
):
    """Convenience function to record reflection metrics."""
    
    metrics = ReflectionMetrics(
        timestamp=time.time(),
        session_id=session_id,
        query=query,
        query_complexity=query_complexity,
        strategy_used=strategy_used,
        processing_time=processing_time,
        total_time=total_time,
        reflection_skipped=reflection_skipped,
        skip_reason=skip_reason,
        initial_quality=initial_quality,
        final_quality=final_quality,
        quality_improvement=quality_improvement,
        reflection_iterations=reflection_iterations,
        llm_calls_made=llm_calls_made,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        estimated_time_saved=estimated_time_saved,
        estimated_calls_saved=estimated_calls_saved,
        metadata=metadata
    )
    
    analytics = get_reflection_analytics()
    analytics.record_reflection_metrics(metrics)