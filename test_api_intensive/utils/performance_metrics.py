"""
Performance Metrics Collector for API Testing

This module provides utilities for collecting, analyzing, and exporting
performance metrics during API testing.
"""

import time
import json
import csv
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import statistics


@dataclass
class RequestMetric:
    """Individual request metric"""
    timestamp: float
    endpoint: str
    response_time_ms: float
    status_code: int
    request_size_bytes: int
    response_size_bytes: int
    success: bool
    error_message: Optional[str] = None


class PerformanceMetrics:
    """
    Collect and analyze performance metrics
    
    Tracks request metrics including response times, throughput,
    error rates, and provides statistical analysis.
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self.metrics: List[RequestMetric] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
    def start_collection(self):
        """Start metrics collection"""
        self.start_time = time.time()
        self.metrics = []
        
    def stop_collection(self):
        """Stop metrics collection"""
        self.end_time = time.time()
    
    def record_request(
        self,
        endpoint: str,
        response_time_ms: float,
        status_code: int,
        request_size: int = 0,
        response_size: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Record individual request metrics
        
        Args:
            endpoint: API endpoint path
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
            request_size: Request size in bytes
            response_size: Response size in bytes
            error_message: Optional error message
        """
        metric = RequestMetric(
            timestamp=time.time(),
            endpoint=endpoint,
            response_time_ms=response_time_ms,
            status_code=status_code,
            request_size_bytes=request_size,
            response_size_bytes=response_size,
            success=200 <= status_code < 300,
            error_message=error_message
        )
        
        self.metrics.append(metric)
    
    def get_statistics(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistical summary
        
        Args:
            endpoint: Optional endpoint to filter by (None for all)
        
        Returns:
            Dictionary with statistical metrics including:
            - min, max, avg, median response times
            - p50, p95, p99 percentiles
            - total requests, success/error counts
            - error rate
        """
        # Filter metrics by endpoint if specified
        filtered_metrics = self.metrics
        if endpoint:
            filtered_metrics = [m for m in self.metrics if m.endpoint == endpoint]
        
        if not filtered_metrics:
            return {
                'total_requests': 0,
                'error': 'No metrics available'
            }
        
        # Extract response times
        response_times = [m.response_time_ms for m in filtered_metrics]
        
        # Calculate statistics
        stats = {
            'total_requests': len(filtered_metrics),
            'successful_requests': sum(1 for m in filtered_metrics if m.success),
            'failed_requests': sum(1 for m in filtered_metrics if not m.success),
            'error_rate_percent': self.get_error_rate(endpoint) * 100,
            'response_time': {
                'min_ms': min(response_times),
                'max_ms': max(response_times),
                'avg_ms': statistics.mean(response_times),
                'median_ms': statistics.median(response_times),
                'stdev_ms': statistics.stdev(response_times) if len(response_times) > 1 else 0,
                'p50_ms': self._percentile(response_times, 50),
                'p75_ms': self._percentile(response_times, 75),
                'p90_ms': self._percentile(response_times, 90),
                'p95_ms': self._percentile(response_times, 95),
                'p99_ms': self._percentile(response_times, 99)
            },
            'data_transfer': {
                'total_request_bytes': sum(m.request_size_bytes for m in filtered_metrics),
                'total_response_bytes': sum(m.response_size_bytes for m in filtered_metrics),
                'avg_request_bytes': statistics.mean([m.request_size_bytes for m in filtered_metrics]),
                'avg_response_bytes': statistics.mean([m.response_size_bytes for m in filtered_metrics])
            }
        }
        
        # Add endpoint-specific breakdown if not filtered
        if not endpoint:
            stats['by_endpoint'] = self._get_endpoint_breakdown()
        
        # Add status code breakdown
        stats['status_codes'] = self._get_status_code_breakdown(filtered_metrics)
        
        return stats
    
    def get_throughput(self, time_window_seconds: Optional[float] = None) -> float:
        """
        Calculate requests per second
        
        Args:
            time_window_seconds: Time window to calculate over (None for entire collection)
        
        Returns:
            Requests per second
        """
        if not self.metrics:
            return 0.0
        
        if time_window_seconds is None:
            # Use entire collection period
            if self.start_time and self.end_time:
                duration = self.end_time - self.start_time
            else:
                # Calculate from first to last metric
                duration = self.metrics[-1].timestamp - self.metrics[0].timestamp
        else:
            duration = time_window_seconds
        
        if duration <= 0:
            return 0.0
        
        return len(self.metrics) / duration
    
    def get_error_rate(self, endpoint: Optional[str] = None) -> float:
        """
        Calculate error rate percentage
        
        Args:
            endpoint: Optional endpoint to filter by
        
        Returns:
            Error rate as decimal (0.0 to 1.0)
        """
        filtered_metrics = self.metrics
        if endpoint:
            filtered_metrics = [m for m in self.metrics if m.endpoint == endpoint]
        
        if not filtered_metrics:
            return 0.0
        
        failed = sum(1 for m in filtered_metrics if not m.success)
        return failed / len(filtered_metrics)
    
    def get_response_time_distribution(
        self,
        endpoint: Optional[str] = None,
        bucket_size_ms: float = 100
    ) -> Dict[str, int]:
        """
        Get response time distribution in buckets
        
        Args:
            endpoint: Optional endpoint to filter by
            bucket_size_ms: Size of each bucket in milliseconds
        
        Returns:
            Dictionary mapping bucket ranges to counts
        """
        filtered_metrics = self.metrics
        if endpoint:
            filtered_metrics = [m for m in self.metrics if m.endpoint == endpoint]
        
        if not filtered_metrics:
            return {}
        
        distribution = defaultdict(int)
        
        for metric in filtered_metrics:
            bucket = int(metric.response_time_ms / bucket_size_ms) * bucket_size_ms
            bucket_label = f"{bucket}-{bucket + bucket_size_ms}ms"
            distribution[bucket_label] += 1
        
        return dict(sorted(distribution.items()))
    
    def get_errors(self, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of all errors
        
        Args:
            endpoint: Optional endpoint to filter by
        
        Returns:
            List of error dictionaries
        """
        filtered_metrics = self.metrics
        if endpoint:
            filtered_metrics = [m for m in self.metrics if m.endpoint == endpoint]
        
        errors = []
        for metric in filtered_metrics:
            if not metric.success:
                errors.append({
                    'timestamp': datetime.fromtimestamp(metric.timestamp).isoformat(),
                    'endpoint': metric.endpoint,
                    'status_code': metric.status_code,
                    'response_time_ms': metric.response_time_ms,
                    'error_message': metric.error_message
                })
        
        return errors
    
    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics in specified format
        
        Args:
            format: Export format ('json' or 'csv')
        
        Returns:
            Formatted metrics string
        """
        if format.lower() == "json":
            return self._export_json()
        elif format.lower() == "csv":
            return self._export_csv()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_to_file(self, filepath: str, format: str = "json"):
        """
        Export metrics to file
        
        Args:
            filepath: Path to output file
            format: Export format ('json' or 'csv')
        """
        content = self.export_metrics(format)
        
        with open(filepath, 'w') as f:
            f.write(content)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get high-level summary of metrics
        
        Returns:
            Summary dictionary
        """
        if not self.metrics:
            return {'error': 'No metrics collected'}
        
        stats = self.get_statistics()
        
        duration = 0
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
        elif self.metrics:
            duration = self.metrics[-1].timestamp - self.metrics[0].timestamp
        
        return {
            'collection_period': {
                'start': datetime.fromtimestamp(self.metrics[0].timestamp).isoformat() if self.metrics else None,
                'end': datetime.fromtimestamp(self.metrics[-1].timestamp).isoformat() if self.metrics else None,
                'duration_seconds': duration
            },
            'total_requests': stats['total_requests'],
            'successful_requests': stats['successful_requests'],
            'failed_requests': stats['failed_requests'],
            'error_rate_percent': stats['error_rate_percent'],
            'throughput_rps': self.get_throughput(),
            'response_time_summary': {
                'avg_ms': stats['response_time']['avg_ms'],
                'median_ms': stats['response_time']['median_ms'],
                'p95_ms': stats['response_time']['p95_ms'],
                'p99_ms': stats['response_time']['p99_ms']
            },
            'endpoints_tested': len(set(m.endpoint for m in self.metrics))
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _get_endpoint_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics breakdown by endpoint"""
        endpoints = set(m.endpoint for m in self.metrics)
        breakdown = {}
        
        for endpoint in endpoints:
            breakdown[endpoint] = self.get_statistics(endpoint)
        
        return breakdown
    
    def _get_status_code_breakdown(self, metrics: List[RequestMetric]) -> Dict[int, int]:
        """Get count of each status code"""
        status_codes = defaultdict(int)
        
        for metric in metrics:
            status_codes[metric.status_code] += 1
        
        return dict(sorted(status_codes.items()))
    
    def _export_json(self) -> str:
        """Export metrics as JSON"""
        export_data = {
            'summary': self.get_summary(),
            'statistics': self.get_statistics(),
            'errors': self.get_errors(),
            'response_time_distribution': self.get_response_time_distribution(),
            'raw_metrics': [
                {
                    'timestamp': datetime.fromtimestamp(m.timestamp).isoformat(),
                    'endpoint': m.endpoint,
                    'response_time_ms': m.response_time_ms,
                    'status_code': m.status_code,
                    'success': m.success,
                    'request_size_bytes': m.request_size_bytes,
                    'response_size_bytes': m.response_size_bytes,
                    'error_message': m.error_message
                }
                for m in self.metrics
            ]
        }
        
        return json.dumps(export_data, indent=2)
    
    def _export_csv(self) -> str:
        """Export metrics as CSV"""
        if not self.metrics:
            return ""
        
        # Create CSV in memory
        import io
        output = io.StringIO()
        
        fieldnames = [
            'timestamp',
            'endpoint',
            'response_time_ms',
            'status_code',
            'success',
            'request_size_bytes',
            'response_size_bytes',
            'error_message'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for metric in self.metrics:
            writer.writerow({
                'timestamp': datetime.fromtimestamp(metric.timestamp).isoformat(),
                'endpoint': metric.endpoint,
                'response_time_ms': metric.response_time_ms,
                'status_code': metric.status_code,
                'success': metric.success,
                'request_size_bytes': metric.request_size_bytes,
                'response_size_bytes': metric.response_size_bytes,
                'error_message': metric.error_message or ''
            })
        
        return output.getvalue()
    
    def reset(self):
        """Reset all metrics"""
        self.metrics = []
        self.start_time = None
        self.end_time = None
    
    def __len__(self) -> int:
        """Return number of recorded metrics"""
        return len(self.metrics)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"PerformanceMetrics(requests={len(self.metrics)}, throughput={self.get_throughput():.2f} rps)"
