"""
Retrieval Performance Monitor

This module implements performance monitoring for retrieval operations,
tracking retrieval times, filtering effects, and providing analysis tools.

Key Features:
- Retrieval time tracking (per query and aggregate)
- Entity type filtering effectiveness metrics
- Quality ranking impact analysis
- Performance logging and reporting
- Real-time performance statistics

Usage:
    from hypergraphrag.retrieval.performance_monitor import PerformanceMonitor
    
    monitor = PerformanceMonitor()
    
    # Track retrieval operation
    with monitor.track_retrieval("query_text"):
        results = await retriever.retrieve(query)
    
    # Get statistics
    stats = monitor.get_statistics()
    print(f"Average retrieval time: {stats['avg_retrieval_time']:.3f}s")
"""

import time
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from contextlib import asynccontextmanager
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetrics:
    """
    Metrics for a single retrieval operation.
    
    Attributes:
        query: Query string
        timestamp: When the retrieval occurred
        retrieval_time: Total retrieval time in seconds
        vector_search_time: Time spent on vector search
        filtering_time: Time spent on entity type filtering
        ranking_time: Time spent on quality ranking
        total_candidates: Number of candidates before filtering
        filtered_candidates: Number of candidates after filtering
        final_results: Number of final results returned
        filter_reduction_rate: Percentage of candidates filtered out
        use_entity_filter: Whether entity filtering was used
        use_quality_ranker: Whether quality ranking was used
        use_lite_mode: Whether lite retriever was used
        use_ann: Whether ANN search was used
        cache_hit: Whether result was from cache
        error: Error message if retrieval failed
    """
    query: str
    timestamp: str
    retrieval_time: float = 0.0
    vector_search_time: float = 0.0
    filtering_time: float = 0.0
    ranking_time: float = 0.0
    total_candidates: int = 0
    filtered_candidates: int = 0
    final_results: int = 0
    filter_reduction_rate: float = 0.0
    use_entity_filter: bool = False
    use_quality_ranker: bool = False
    use_lite_mode: bool = False
    use_ann: bool = False
    cache_hit: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Performance monitor for retrieval operations.
    
    This class tracks and analyzes retrieval performance metrics including
    timing, filtering effectiveness, and resource usage. It provides both
    real-time monitoring and historical analysis capabilities.
    
    Attributes:
        metrics_history: List of all recorded retrieval metrics
        enable_logging: Whether to log metrics to file
        log_file: Path to log file
        log_interval: How often to flush logs (in number of queries)
    """
    
    def __init__(
        self,
        enable_logging: bool = True,
        log_file: Optional[str] = None,
        log_interval: int = 10
    ):
        """
        Initialize PerformanceMonitor.
        
        Args:
            enable_logging: Whether to log metrics to file (default: True)
            log_file: Path to log file (default: logs/retrieval_performance.jsonl)
            log_interval: Flush logs every N queries (default: 10)
        """
        self.metrics_history: List[RetrievalMetrics] = []
        self.enable_logging = enable_logging
        self.log_interval = log_interval
        self._query_count = 0
        
        # Set up log file
        if log_file is None:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            self.log_file = log_dir / "retrieval_performance.jsonl"
        else:
            self.log_file = Path(log_file)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Current operation tracking
        self._current_metrics: Optional[RetrievalMetrics] = None
        self._start_time: Optional[float] = None
        self._phase_start_time: Optional[float] = None
        
        logger.info(
            f"PerformanceMonitor initialized. "
            f"Logging: {enable_logging}, Log file: {self.log_file}"
        )
    
    @asynccontextmanager
    async def track_retrieval(
        self,
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracking a retrieval operation.
        
        Usage:
            async with monitor.track_retrieval("query text") as tracker:
                # Perform retrieval
                results = await retriever.retrieve(query)
                
                # Record metrics
                tracker.set_candidates(total=100, filtered=50, final=10)
                tracker.set_filter_used(True)
        
        Args:
            query: Query string
            metadata: Optional metadata dict
            
        Yields:
            RetrievalTracker instance for recording metrics
        """
        # Initialize metrics
        self._current_metrics = RetrievalMetrics(
            query=query,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        self._start_time = time.time()
        
        # Create tracker
        tracker = RetrievalTracker(self)
        
        try:
            yield tracker
        except Exception as e:
            # Record error
            self._current_metrics.error = str(e)
            logger.error(f"Retrieval failed for query '{query[:50]}...': {e}")
            raise
        finally:
            # Finalize metrics
            if self._start_time is not None:
                self._current_metrics.retrieval_time = time.time() - self._start_time
            
            # Store metrics
            self.metrics_history.append(self._current_metrics)
            self._query_count += 1
            
            # Log metrics
            if self.enable_logging:
                self._log_metrics(self._current_metrics)
                
                # Flush periodically
                if self._query_count % self.log_interval == 0:
                    logger.info(
                        f"Logged {self._query_count} queries. "
                        f"Avg time: {self.get_average_retrieval_time():.3f}s"
                    )
            
            # Log summary
            if self._current_metrics.error is None:
                logger.info(
                    f"[Perf] Query: '{query[:50]}...' | "
                    f"Time: {self._current_metrics.retrieval_time:.3f}s | "
                    f"Candidates: {self._current_metrics.total_candidates} → "
                    f"{self._current_metrics.filtered_candidates} → "
                    f"{self._current_metrics.final_results} | "
                    f"Filter: {self._current_metrics.use_entity_filter} | "
                    f"Ranker: {self._current_metrics.use_quality_ranker} | "
                    f"Lite: {self._current_metrics.use_lite_mode} | "
                    f"ANN: {self._current_metrics.use_ann} | "
                    f"Cache: {self._current_metrics.cache_hit}"
                )
            
            # Reset current tracking
            self._current_metrics = None
            self._start_time = None
    
    def start_phase(self, phase_name: str):
        """
        Start timing a phase of retrieval.
        
        Args:
            phase_name: Name of the phase (e.g., "vector_search", "filtering")
        """
        self._phase_start_time = time.time()
        logger.debug(f"[Perf] Starting phase: {phase_name}")
    
    def end_phase(self, phase_name: str):
        """
        End timing a phase and record the duration.
        
        Args:
            phase_name: Name of the phase
        """
        if self._phase_start_time is None or self._current_metrics is None:
            logger.warning(f"Phase '{phase_name}' ended without start")
            return
        
        duration = time.time() - self._phase_start_time
        
        # Record duration in appropriate field
        if phase_name == "vector_search":
            self._current_metrics.vector_search_time = duration
        elif phase_name == "filtering":
            self._current_metrics.filtering_time = duration
        elif phase_name == "ranking":
            self._current_metrics.ranking_time = duration
        
        logger.debug(f"[Perf] Phase '{phase_name}' took {duration:.3f}s")
        self._phase_start_time = None
    
    def _log_metrics(self, metrics: RetrievalMetrics):
        """
        Log metrics to file.
        
        Args:
            metrics: RetrievalMetrics instance
        """
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                # Write as JSON lines format
                json.dump(asdict(metrics), f, ensure_ascii=False)
                f.write("\n")
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics for all tracked retrievals.
        
        Returns:
            Dict with statistics including:
                - total_queries: Total number of queries
                - successful_queries: Number of successful queries
                - failed_queries: Number of failed queries
                - avg_retrieval_time: Average retrieval time
                - median_retrieval_time: Median retrieval time
                - p95_retrieval_time: 95th percentile retrieval time
                - avg_vector_search_time: Average vector search time
                - avg_filtering_time: Average filtering time
                - avg_ranking_time: Average ranking time
                - avg_filter_reduction: Average filter reduction rate
                - entity_filter_usage: Percentage of queries using entity filter
                - quality_ranker_usage: Percentage of queries using quality ranker
                - lite_mode_usage: Percentage of queries using lite mode
                - ann_usage: Percentage of queries using ANN
                - cache_hit_rate: Percentage of cache hits
        """
        if not self.metrics_history:
            return {
                "total_queries": 0,
                "message": "No metrics recorded yet"
            }
        
        # Filter successful queries
        successful = [m for m in self.metrics_history if m.error is None]
        failed = [m for m in self.metrics_history if m.error is not None]
        
        # Compute statistics
        retrieval_times = [m.retrieval_time for m in successful]
        vector_times = [m.vector_search_time for m in successful if m.vector_search_time > 0]
        filtering_times = [m.filtering_time for m in successful if m.filtering_time > 0]
        ranking_times = [m.ranking_time for m in successful if m.ranking_time > 0]
        filter_reductions = [m.filter_reduction_rate for m in successful if m.use_entity_filter]
        
        stats = {
            "total_queries": len(self.metrics_history),
            "successful_queries": len(successful),
            "failed_queries": len(failed),
            "avg_retrieval_time": sum(retrieval_times) / len(retrieval_times) if retrieval_times else 0.0,
            "median_retrieval_time": sorted(retrieval_times)[len(retrieval_times) // 2] if retrieval_times else 0.0,
            "p95_retrieval_time": sorted(retrieval_times)[int(len(retrieval_times) * 0.95)] if retrieval_times else 0.0,
            "avg_vector_search_time": sum(vector_times) / len(vector_times) if vector_times else 0.0,
            "avg_filtering_time": sum(filtering_times) / len(filtering_times) if filtering_times else 0.0,
            "avg_ranking_time": sum(ranking_times) / len(ranking_times) if ranking_times else 0.0,
            "avg_filter_reduction": sum(filter_reductions) / len(filter_reductions) if filter_reductions else 0.0,
            "entity_filter_usage": sum(1 for m in successful if m.use_entity_filter) / len(successful) * 100 if successful else 0.0,
            "quality_ranker_usage": sum(1 for m in successful if m.use_quality_ranker) / len(successful) * 100 if successful else 0.0,
            "lite_mode_usage": sum(1 for m in successful if m.use_lite_mode) / len(successful) * 100 if successful else 0.0,
            "ann_usage": sum(1 for m in successful if m.use_ann) / len(successful) * 100 if successful else 0.0,
            "cache_hit_rate": sum(1 for m in successful if m.cache_hit) / len(successful) * 100 if successful else 0.0,
        }
        
        return stats
    
    def get_average_retrieval_time(self) -> float:
        """
        Get average retrieval time for successful queries.
        
        Returns:
            Average retrieval time in seconds
        """
        successful = [m for m in self.metrics_history if m.error is None]
        if not successful:
            return 0.0
        
        return sum(m.retrieval_time for m in successful) / len(successful)
    
    def get_recent_metrics(self, n: int = 10) -> List[RetrievalMetrics]:
        """
        Get the N most recent metrics.
        
        Args:
            n: Number of recent metrics to return
            
        Returns:
            List of recent RetrievalMetrics
        """
        return self.metrics_history[-n:]
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate a performance analysis report.
        
        Args:
            output_file: Optional file path to save report
            
        Returns:
            Report string
        """
        stats = self.get_statistics()
        
        report_lines = [
            "=" * 80,
            "RETRIEVAL PERFORMANCE REPORT",
            "=" * 80,
            "",
            f"Generated: {datetime.now().isoformat()}",
            f"Total Queries: {stats['total_queries']}",
            f"Successful: {stats['successful_queries']}",
            f"Failed: {stats['failed_queries']}",
            "",
            "-" * 80,
            "TIMING STATISTICS",
            "-" * 80,
            f"Average Retrieval Time: {stats['avg_retrieval_time']:.3f}s",
            f"Median Retrieval Time: {stats['median_retrieval_time']:.3f}s",
            f"P95 Retrieval Time: {stats['p95_retrieval_time']:.3f}s",
            f"Average Vector Search Time: {stats['avg_vector_search_time']:.3f}s",
            f"Average Filtering Time: {stats['avg_filtering_time']:.3f}s",
            f"Average Ranking Time: {stats['avg_ranking_time']:.3f}s",
            "",
            "-" * 80,
            "FEATURE USAGE",
            "-" * 80,
            f"Entity Filter Usage: {stats['entity_filter_usage']:.1f}%",
            f"Quality Ranker Usage: {stats['quality_ranker_usage']:.1f}%",
            f"Lite Mode Usage: {stats['lite_mode_usage']:.1f}%",
            f"ANN Search Usage: {stats['ann_usage']:.1f}%",
            f"Cache Hit Rate: {stats['cache_hit_rate']:.1f}%",
            "",
            "-" * 80,
            "FILTERING EFFECTIVENESS",
            "-" * 80,
            f"Average Filter Reduction: {stats['avg_filter_reduction']:.1f}%",
            "",
            "=" * 80,
        ]
        
        # Add recent queries section
        recent = self.get_recent_metrics(5)
        if recent:
            report_lines.extend([
                "",
                "-" * 80,
                "RECENT QUERIES (Last 5)",
                "-" * 80,
            ])
            
            for i, m in enumerate(recent, 1):
                report_lines.append(
                    f"{i}. Query: '{m.query[:60]}...' | "
                    f"Time: {m.retrieval_time:.3f}s | "
                    f"Results: {m.final_results} | "
                    f"Error: {m.error or 'None'}"
                )
            
            report_lines.append("=" * 80)
        
        report = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            try:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(report)
                
                logger.info(f"Performance report saved to: {output_path}")
            except Exception as e:
                logger.error(f"Failed to save report: {e}")
        
        return report
    
    def clear_history(self):
        """Clear all metrics history."""
        self.metrics_history.clear()
        self._query_count = 0
        logger.info("Metrics history cleared")
    
    def export_metrics(self, output_file: str, format: str = "json"):
        """
        Export metrics to file.
        
        Args:
            output_file: Output file path
            format: Export format ("json" or "csv")
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(
                        [asdict(m) for m in self.metrics_history],
                        f,
                        indent=2,
                        ensure_ascii=False
                    )
            elif format == "csv":
                import csv
                
                if not self.metrics_history:
                    logger.warning("No metrics to export")
                    return
                
                with open(output_path, "w", newline="", encoding="utf-8") as f:
                    # Get all field names
                    fieldnames = list(asdict(self.metrics_history[0]).keys())
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for metrics in self.metrics_history:
                        row = asdict(metrics)
                        # Convert dict fields to JSON strings
                        row["metadata"] = json.dumps(row["metadata"])
                        writer.writerow(row)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Metrics exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            raise


class RetrievalTracker:
    """
    Helper class for tracking metrics within a retrieval operation.
    
    This class provides a convenient interface for recording metrics
    during a retrieval operation tracked by PerformanceMonitor.
    """
    
    def __init__(self, monitor: PerformanceMonitor):
        """
        Initialize RetrievalTracker.
        
        Args:
            monitor: Parent PerformanceMonitor instance
        """
        self.monitor = monitor
    
    def set_candidates(
        self,
        total: int,
        filtered: Optional[int] = None,
        final: Optional[int] = None
    ):
        """
        Set candidate counts.
        
        Args:
            total: Total candidates before filtering
            filtered: Candidates after filtering (optional)
            final: Final results returned (optional)
        """
        if self.monitor._current_metrics is None:
            return
        
        self.monitor._current_metrics.total_candidates = total
        
        if filtered is not None:
            self.monitor._current_metrics.filtered_candidates = filtered
            
            # Compute reduction rate
            if total > 0:
                reduction = (total - filtered) / total * 100
                self.monitor._current_metrics.filter_reduction_rate = reduction
        
        if final is not None:
            self.monitor._current_metrics.final_results = final
    
    def set_filter_used(self, used: bool):
        """Set whether entity filter was used."""
        if self.monitor._current_metrics:
            self.monitor._current_metrics.use_entity_filter = used
    
    def set_ranker_used(self, used: bool):
        """Set whether quality ranker was used."""
        if self.monitor._current_metrics:
            self.monitor._current_metrics.use_quality_ranker = used
    
    def set_lite_mode(self, used: bool):
        """Set whether lite mode was used."""
        if self.monitor._current_metrics:
            self.monitor._current_metrics.use_lite_mode = used
    
    def set_ann_used(self, used: bool):
        """Set whether ANN search was used."""
        if self.monitor._current_metrics:
            self.monitor._current_metrics.use_ann = used
    
    def set_cache_hit(self, hit: bool):
        """Set whether result was from cache."""
        if self.monitor._current_metrics:
            self.monitor._current_metrics.cache_hit = hit
    
    def start_phase(self, phase_name: str):
        """Start timing a phase."""
        self.monitor.start_phase(phase_name)
    
    def end_phase(self, phase_name: str):
        """End timing a phase."""
        self.monitor.end_phase(phase_name)
    
    def add_metadata(self, key: str, value: Any):
        """
        Add metadata to current metrics.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        if self.monitor._current_metrics:
            self.monitor._current_metrics.metadata[key] = value


# Global monitor instance (optional, for convenience)
_global_monitor: Optional[PerformanceMonitor] = None


def get_global_monitor() -> PerformanceMonitor:
    """
    Get or create the global performance monitor instance.
    
    Returns:
        Global PerformanceMonitor instance
    """
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    
    return _global_monitor


def set_global_monitor(monitor: PerformanceMonitor):
    """
    Set the global performance monitor instance.
    
    Args:
        monitor: PerformanceMonitor instance to use globally
    """
    global _global_monitor
    _global_monitor = monitor
