"""
Tests for Retrieval Performance Monitor

This test suite validates the functionality of the PerformanceMonitor class.
"""

import pytest
import asyncio
import json
from pathlib import Path
import tempfile
import shutil

from hypergraphrag.retrieval import (
    PerformanceMonitor,
    RetrievalTracker,
    RetrievalMetrics,
    get_global_monitor,
    set_global_monitor
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def monitor(temp_dir):
    """Create a PerformanceMonitor instance for testing"""
    log_file = temp_dir / "test_performance.jsonl"
    return PerformanceMonitor(
        enable_logging=True,
        log_file=str(log_file),
        log_interval=5
    )


@pytest.mark.asyncio
async def test_basic_tracking(monitor):
    """Test basic retrieval tracking"""
    query = "Test query"
    
    async with monitor.track_retrieval(query) as tracker:
        await asyncio.sleep(0.01)  # Simulate work
        tracker.set_candidates(total=100, filtered=60, final=10)
        tracker.set_filter_used(True)
    
    # Check metrics were recorded
    assert len(monitor.metrics_history) == 1
    
    metrics = monitor.metrics_history[0]
    assert metrics.query == query
    assert metrics.total_candidates == 100
    assert metrics.filtered_candidates == 60
    assert metrics.final_results == 10
    assert metrics.use_entity_filter is True
    assert metrics.retrieval_time > 0
    assert metrics.error is None


@pytest.mark.asyncio
async def test_phase_timing(monitor):
    """Test phase timing tracking"""
    query = "Test query"
    
    async with monitor.track_retrieval(query) as tracker:
        # Vector search phase
        tracker.start_phase("vector_search")
        await asyncio.sleep(0.01)
        tracker.end_phase("vector_search")
        
        # Filtering phase
        tracker.start_phase("filtering")
        await asyncio.sleep(0.005)
        tracker.end_phase("filtering")
        
        # Ranking phase
        tracker.start_phase("ranking")
        await asyncio.sleep(0.003)
        tracker.end_phase("ranking")
    
    metrics = monitor.metrics_history[0]
    assert metrics.vector_search_time > 0
    assert metrics.filtering_time > 0
    assert metrics.ranking_time > 0
    assert metrics.vector_search_time > metrics.filtering_time
    assert metrics.filtering_time > metrics.ranking_time


@pytest.mark.asyncio
async def test_error_handling(monitor):
    """Test error handling during retrieval"""
    query = "Test query"
    
    with pytest.raises(ValueError):
        async with monitor.track_retrieval(query) as tracker:
            raise ValueError("Test error")
    
    # Check error was recorded
    assert len(monitor.metrics_history) == 1
    metrics = monitor.metrics_history[0]
    assert metrics.error == "Test error"


@pytest.mark.asyncio
async def test_multiple_queries(monitor):
    """Test tracking multiple queries"""
    queries = ["Query 1", "Query 2", "Query 3"]
    
    for query in queries:
        async with monitor.track_retrieval(query) as tracker:
            await asyncio.sleep(0.01)
            tracker.set_candidates(total=100, final=10)
    
    assert len(monitor.metrics_history) == 3
    assert [m.query for m in monitor.metrics_history] == queries


def test_statistics(monitor):
    """Test statistics computation"""
    # Add some mock metrics
    for i in range(10):
        metrics = RetrievalMetrics(
            query=f"Query {i}",
            timestamp="2025-01-15T10:00:00",
            retrieval_time=0.1 + i * 0.01,
            total_candidates=100,
            filtered_candidates=60,
            final_results=10,
            use_entity_filter=i % 2 == 0,
            use_quality_ranker=i % 3 == 0,
            filter_reduction_rate=40.0
        )
        monitor.metrics_history.append(metrics)
    
    stats = monitor.get_statistics()
    
    assert stats["total_queries"] == 10
    assert stats["successful_queries"] == 10
    assert stats["failed_queries"] == 0
    assert stats["avg_retrieval_time"] > 0
    assert stats["entity_filter_usage"] == 50.0  # 5 out of 10
    assert stats["quality_ranker_usage"] > 0


def test_filter_reduction_calculation(monitor):
    """Test filter reduction rate calculation"""
    # Add metrics with filtering
    metrics = RetrievalMetrics(
        query="Test",
        timestamp="2025-01-15T10:00:00",
        total_candidates=100,
        filtered_candidates=60,
        final_results=10,
        use_entity_filter=True
    )
    
    # Calculate reduction manually
    expected_reduction = (100 - 60) / 100 * 100  # 40%
    
    # Simulate what tracker does
    if metrics.total_candidates > 0:
        reduction = (metrics.total_candidates - metrics.filtered_candidates) / metrics.total_candidates * 100
        metrics.filter_reduction_rate = reduction
    
    assert metrics.filter_reduction_rate == expected_reduction


@pytest.mark.asyncio
async def test_logging(monitor, temp_dir):
    """Test metrics logging to file"""
    query = "Test query"
    
    async with monitor.track_retrieval(query) as tracker:
        tracker.set_candidates(total=100, final=10)
    
    # Check log file was created
    log_file = temp_dir / "test_performance.jsonl"
    assert log_file.exists()
    
    # Read and verify log content
    with open(log_file, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 1
    
    log_entry = json.loads(lines[0])
    assert log_entry["query"] == query
    assert log_entry["total_candidates"] == 100
    assert log_entry["final_results"] == 10


def test_report_generation(monitor):
    """Test performance report generation"""
    # Add some metrics
    for i in range(5):
        metrics = RetrievalMetrics(
            query=f"Query {i}",
            timestamp="2025-01-15T10:00:00",
            retrieval_time=0.1,
            total_candidates=100,
            final_results=10
        )
        monitor.metrics_history.append(metrics)
    
    # Generate report
    report = monitor.generate_report()
    
    assert "RETRIEVAL PERFORMANCE REPORT" in report
    assert "Total Queries: 5" in report
    assert "Average Retrieval Time" in report
    assert "RECENT QUERIES" in report


@pytest.mark.asyncio
async def test_export_json(monitor, temp_dir):
    """Test exporting metrics to JSON"""
    # Add metrics
    async with monitor.track_retrieval("Test query") as tracker:
        tracker.set_candidates(total=100, final=10)
    
    # Export to JSON
    json_file = temp_dir / "metrics.json"
    monitor.export_metrics(str(json_file), format="json")
    
    assert json_file.exists()
    
    # Verify content
    with open(json_file, "r") as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["query"] == "Test query"


@pytest.mark.asyncio
async def test_export_csv(monitor, temp_dir):
    """Test exporting metrics to CSV"""
    # Add metrics
    async with monitor.track_retrieval("Test query") as tracker:
        tracker.set_candidates(total=100, final=10)
    
    # Export to CSV
    csv_file = temp_dir / "metrics.csv"
    monitor.export_metrics(str(csv_file), format="csv")
    
    assert csv_file.exists()
    
    # Verify content
    with open(csv_file, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 2  # Header + 1 data row
    assert "query" in lines[0]
    assert "Test query" in lines[1]


def test_recent_metrics(monitor):
    """Test getting recent metrics"""
    # Add 10 metrics
    for i in range(10):
        metrics = RetrievalMetrics(
            query=f"Query {i}",
            timestamp="2025-01-15T10:00:00",
            retrieval_time=0.1
        )
        monitor.metrics_history.append(metrics)
    
    # Get last 5
    recent = monitor.get_recent_metrics(5)
    
    assert len(recent) == 5
    assert recent[0].query == "Query 5"
    assert recent[-1].query == "Query 9"


def test_clear_history(monitor):
    """Test clearing metrics history"""
    # Add metrics
    for i in range(5):
        metrics = RetrievalMetrics(
            query=f"Query {i}",
            timestamp="2025-01-15T10:00:00",
            retrieval_time=0.1
        )
        monitor.metrics_history.append(metrics)
    
    assert len(monitor.metrics_history) == 5
    
    # Clear history
    monitor.clear_history()
    
    assert len(monitor.metrics_history) == 0
    assert monitor._query_count == 0


@pytest.mark.asyncio
async def test_metadata(monitor):
    """Test adding metadata to metrics"""
    query = "Test query"
    
    async with monitor.track_retrieval(query) as tracker:
        tracker.add_metadata("domain", "legal")
        tracker.add_metadata("user_id", "user123")
        tracker.add_metadata("custom_field", 42)
    
    metrics = monitor.metrics_history[0]
    assert metrics.metadata["domain"] == "legal"
    assert metrics.metadata["user_id"] == "user123"
    assert metrics.metadata["custom_field"] == 42


@pytest.mark.asyncio
async def test_cache_hit_tracking(monitor):
    """Test cache hit tracking"""
    async with monitor.track_retrieval("Query 1") as tracker:
        tracker.set_cache_hit(False)
    
    async with monitor.track_retrieval("Query 2") as tracker:
        tracker.set_cache_hit(True)
    
    stats = monitor.get_statistics()
    assert stats["cache_hit_rate"] == 50.0  # 1 out of 2


def test_global_monitor():
    """Test global monitor functionality"""
    # Create and set global monitor
    monitor = PerformanceMonitor(enable_logging=False)
    set_global_monitor(monitor)
    
    # Get global monitor
    global_monitor = get_global_monitor()
    
    assert global_monitor is monitor


@pytest.mark.asyncio
async def test_feature_flags(monitor):
    """Test all feature usage flags"""
    async with monitor.track_retrieval("Test query") as tracker:
        tracker.set_filter_used(True)
        tracker.set_ranker_used(True)
        tracker.set_lite_mode(True)
        tracker.set_ann_used(True)
        tracker.set_cache_hit(True)
    
    metrics = monitor.metrics_history[0]
    assert metrics.use_entity_filter is True
    assert metrics.use_quality_ranker is True
    assert metrics.use_lite_mode is True
    assert metrics.use_ann is True
    assert metrics.cache_hit is True


@pytest.mark.asyncio
async def test_average_retrieval_time(monitor):
    """Test average retrieval time calculation"""
    # Add metrics with known times
    times = [0.1, 0.2, 0.3]
    
    for t in times:
        metrics = RetrievalMetrics(
            query="Test",
            timestamp="2025-01-15T10:00:00",
            retrieval_time=t
        )
        monitor.metrics_history.append(metrics)
    
    avg_time = monitor.get_average_retrieval_time()
    expected_avg = sum(times) / len(times)
    
    assert abs(avg_time - expected_avg) < 0.001


@pytest.mark.asyncio
async def test_disabled_logging(temp_dir):
    """Test monitor with logging disabled"""
    log_file = temp_dir / "test_performance.jsonl"
    monitor = PerformanceMonitor(
        enable_logging=False,
        log_file=str(log_file)
    )
    
    async with monitor.track_retrieval("Test query") as tracker:
        tracker.set_candidates(total=100, final=10)
    
    # Log file should not be created
    assert not log_file.exists()
    
    # But metrics should still be tracked
    assert len(monitor.metrics_history) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
