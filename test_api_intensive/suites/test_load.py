"""
Load and Stress Test Suite for Crop Yield Prediction API

This module implements comprehensive load and stress testing including:
- Gradual ramp-up tests (1 to 100 users)
- Sustained high load tests (100 users for 5 minutes)
- Spike tests (sudden load increase)
- Stress tests (beyond capacity)
- System recovery measurement
- Memory and CPU usage monitoring

Requirements tested: 4.4, 4.5, 4.6
"""

import pytest
import time
import threading
import psutil
import os
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from utils.api_client import CropYieldAPIClient, APIResponse
from utils.test_data_generator import TestDataGenerator
from utils.performance_metrics import PerformanceMetrics


class ResourceMonitor:
    """Monitor system resource usage during load tests"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.monitoring = False
        self.samples = []
        self.monitor_thread = None
        
    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start monitoring resource usage"""
        self.monitoring = True
        self.samples = []
        
        def monitor():
            while self.monitoring:
                try:
                    cpu_percent = self.process.cpu_percent(interval=0.1)
                    memory_info = self.process.memory_info()
                    
                    self.samples.append({
                        'timestamp': time.time(),
                        'cpu_percent': cpu_percent,
                        'memory_mb': memory_info.rss / (1024 * 1024),
                        'memory_percent': self.process.memory_percent()
                    })
                    
                    time.sleep(interval_seconds)
                except Exception as e:
                    print(f"Error monitoring resources: {e}")
                    break
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring and return collected samples"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        return self.samples
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get resource usage statistics"""
        if not self.samples:
            return {}
        
        cpu_values = [s['cpu_percent'] for s in self.samples]
        memory_values = [s['memory_mb'] for s in self.samples]
        
        return {
            'cpu': {
                'min_percent': min(cpu_values),
                'max_percent': max(cpu_values),
                'avg_percent': sum(cpu_values) / len(cpu_values),
                'samples': len(cpu_values)
            },
            'memory': {
                'min_mb': min(memory_values),
                'max_mb': max(memory_values),
                'avg_mb': sum(memory_values) / len(memory_values),
                'samples': len(memory_values)
            },
            'duration_seconds': self.samples[-1]['timestamp'] - self.samples[0]['timestamp'] if len(self.samples) > 1 else 0
        }


class LoadTestRunner:
    """Runner for executing load tests with various patterns"""
    
    def __init__(self, api_client: CropYieldAPIClient, data_generator: TestDataGenerator):
        self.api_client = api_client
        self.data_generator = data_generator
        self.metrics = PerformanceMetrics()
        self.resource_monitor = ResourceMonitor()
    
    def execute_single_request(self) -> APIResponse:
        """Execute a single prediction request"""
        request_data = self.data_generator.generate_valid_request(include_variety=False)
        
        response = self.api_client.predict_yield(
            crop_type=request_data['crop_type'],
            latitude=request_data['latitude'],
            longitude=request_data['longitude'],
            sowing_date=request_data['sowing_date'],
            variety_name=request_data.get('variety_name'),
            location_name=request_data.get('location_name')
        )
        
        # Record metrics
        self.metrics.record_request(
            endpoint='/predict/yield',
            response_time_ms=response.response_time_ms,
            status_code=response.status_code,
            error_message=response.error
        )
        
        return response
    
    def ramp_up_test(
        self,
        start_users: int = 1,
        end_users: int = 100,
        ramp_time_seconds: int = 60,
        requests_per_user: int = 5
    ) -> Dict[str, Any]:
        """
        Gradual ramp-up test: increase load from start_users to end_users
        
        Args:
            start_users: Starting number of concurrent users
            end_users: Ending number of concurrent users
            ramp_time_seconds: Time to ramp up from start to end
            requests_per_user: Number of requests each user makes
        
        Returns:
            Test results dictionary
        """
        print(f"\n🚀 Starting ramp-up test: {start_users} → {end_users} users over {ramp_time_seconds}s")
        
        self.metrics.reset()
        self.resource_monitor.start_monitoring()
        
        start_time = time.time()
        user_increment = (end_users - start_users) / ramp_time_seconds
        current_users = start_users
        
        results = {
            'test_type': 'ramp_up',
            'start_users': start_users,
            'end_users': end_users,
            'ramp_time_seconds': ramp_time_seconds,
            'requests_per_user': requests_per_user,
            'start_time': datetime.now().isoformat(),
            'phases': []
        }
        
        # Execute ramp-up in phases
        phase_duration = 10  # seconds per phase
        num_phases = ramp_time_seconds // phase_duration
        
        for phase in range(num_phases):
            phase_start = time.time()
            users_in_phase = int(start_users + (user_increment * phase * phase_duration))
            
            print(f"  Phase {phase + 1}/{num_phases}: {users_in_phase} concurrent users")
            
            # Execute requests for this phase
            with ThreadPoolExecutor(max_workers=users_in_phase) as executor:
                futures = []
                for _ in range(users_in_phase * requests_per_user):
                    futures.append(executor.submit(self.execute_single_request))
                
                # Wait for phase to complete
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"    Error in request: {e}")
            
            phase_duration_actual = time.time() - phase_start
            phase_stats = self.metrics.get_statistics()
            
            results['phases'].append({
                'phase': phase + 1,
                'users': users_in_phase,
                'duration_seconds': phase_duration_actual,
                'total_requests': phase_stats.get('total_requests', 0),
                'error_rate_percent': phase_stats.get('error_rate_percent', 0),
                'avg_response_time_ms': phase_stats.get('response_time', {}).get('avg_ms', 0)
            })
        
        # Stop monitoring and collect results
        resource_stats = self.resource_monitor.get_statistics()
        self.resource_monitor.stop_monitoring()
        
        total_duration = time.time() - start_time
        final_stats = self.metrics.get_statistics()
        
        results.update({
            'end_time': datetime.now().isoformat(),
            'total_duration_seconds': total_duration,
            'total_requests': final_stats.get('total_requests', 0),
            'successful_requests': final_stats.get('successful_requests', 0),
            'failed_requests': final_stats.get('failed_requests', 0),
            'error_rate_percent': final_stats.get('error_rate_percent', 0),
            'throughput_rps': self.metrics.get_throughput(),
            'response_time_stats': final_stats.get('response_time', {}),
            'resource_usage': resource_stats
        })
        
        return results
    
    def sustained_load_test(
        self,
        num_users: int = 100,
        duration_seconds: int = 300,
        requests_per_second: int = 10
    ) -> Dict[str, Any]:
        """
        Sustained high load test: maintain constant load for duration
        
        Args:
            num_users: Number of concurrent users
            duration_seconds: Test duration in seconds
            requests_per_second: Target requests per second
        
        Returns:
            Test results dictionary
        """
        print(f"\n⚡ Starting sustained load test: {num_users} users for {duration_seconds}s")
        
        self.metrics.reset()
        self.resource_monitor.start_monitoring()
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        results = {
            'test_type': 'sustained_load',
            'num_users': num_users,
            'duration_seconds': duration_seconds,
            'target_rps': requests_per_second,
            'start_time': datetime.now().isoformat(),
            'intervals': []
        }
        
        interval_duration = 10  # Report every 10 seconds
        next_report_time = start_time + interval_duration
        interval_num = 1
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = []
            
            while time.time() < end_time:
                # Submit request
                futures.append(executor.submit(self.execute_single_request))
                
                # Control request rate
                time.sleep(1.0 / requests_per_second)
                
                # Report interval stats
                if time.time() >= next_report_time:
                    interval_stats = self.metrics.get_statistics()
                    current_rps = self.metrics.get_throughput()
                    
                    print(f"  Interval {interval_num}: {current_rps:.2f} RPS, "
                          f"{interval_stats.get('error_rate_percent', 0):.2f}% errors")
                    
                    results['intervals'].append({
                        'interval': interval_num,
                        'elapsed_seconds': time.time() - start_time,
                        'throughput_rps': current_rps,
                        'error_rate_percent': interval_stats.get('error_rate_percent', 0),
                        'avg_response_time_ms': interval_stats.get('response_time', {}).get('avg_ms', 0)
                    })
                    
                    next_report_time += interval_duration
                    interval_num += 1
            
            # Wait for all requests to complete
            print("  Waiting for remaining requests to complete...")
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"    Error in request: {e}")
        
        # Stop monitoring and collect results
        resource_stats = self.resource_monitor.get_statistics()
        self.resource_monitor.stop_monitoring()
        
        total_duration = time.time() - start_time
        final_stats = self.metrics.get_statistics()
        
        results.update({
            'end_time': datetime.now().isoformat(),
            'actual_duration_seconds': total_duration,
            'total_requests': final_stats.get('total_requests', 0),
            'successful_requests': final_stats.get('successful_requests', 0),
            'failed_requests': final_stats.get('failed_requests', 0),
            'error_rate_percent': final_stats.get('error_rate_percent', 0),
            'actual_throughput_rps': self.metrics.get_throughput(),
            'response_time_stats': final_stats.get('response_time', {}),
            'resource_usage': resource_stats
        })
        
        return results

    
    def spike_test(
        self,
        baseline_users: int = 10,
        spike_users: int = 150,
        spike_duration_seconds: int = 10,
        baseline_duration_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Spike test: sudden increase in load
        
        Args:
            baseline_users: Normal load level
            spike_users: Spike load level
            spike_duration_seconds: Duration of spike
            baseline_duration_seconds: Duration before and after spike
        
        Returns:
            Test results dictionary
        """
        print(f"\n📈 Starting spike test: {baseline_users} → {spike_users} users for {spike_duration_seconds}s")
        
        self.metrics.reset()
        self.resource_monitor.start_monitoring()
        
        start_time = time.time()
        
        results = {
            'test_type': 'spike',
            'baseline_users': baseline_users,
            'spike_users': spike_users,
            'spike_duration_seconds': spike_duration_seconds,
            'baseline_duration_seconds': baseline_duration_seconds,
            'start_time': datetime.now().isoformat(),
            'phases': []
        }
        
        # Phase 1: Baseline load
        print(f"  Phase 1: Baseline load ({baseline_users} users)")
        phase1_start = time.time()
        
        with ThreadPoolExecutor(max_workers=baseline_users) as executor:
            futures = []
            phase1_end = phase1_start + baseline_duration_seconds
            
            while time.time() < phase1_end:
                futures.append(executor.submit(self.execute_single_request))
                time.sleep(0.1)
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"    Error in baseline: {e}")
        
        phase1_stats = self.metrics.get_statistics()
        results['phases'].append({
            'phase': 'baseline_before',
            'users': baseline_users,
            'duration_seconds': time.time() - phase1_start,
            'total_requests': phase1_stats.get('total_requests', 0),
            'error_rate_percent': phase1_stats.get('error_rate_percent', 0),
            'avg_response_time_ms': phase1_stats.get('response_time', {}).get('avg_ms', 0)
        })
        
        # Phase 2: Spike load
        print(f"  Phase 2: SPIKE! ({spike_users} users)")
        phase2_start = time.time()
        
        with ThreadPoolExecutor(max_workers=spike_users) as executor:
            futures = []
            phase2_end = phase2_start + spike_duration_seconds
            
            while time.time() < phase2_end:
                futures.append(executor.submit(self.execute_single_request))
                time.sleep(0.05)  # Higher request rate
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"    Error in spike: {e}")
        
        phase2_stats = self.metrics.get_statistics()
        results['phases'].append({
            'phase': 'spike',
            'users': spike_users,
            'duration_seconds': time.time() - phase2_start,
            'total_requests': phase2_stats.get('total_requests', 0),
            'error_rate_percent': phase2_stats.get('error_rate_percent', 0),
            'avg_response_time_ms': phase2_stats.get('response_time', {}).get('avg_ms', 0)
        })
        
        # Phase 3: Recovery to baseline
        print(f"  Phase 3: Recovery ({baseline_users} users)")
        phase3_start = time.time()
        
        with ThreadPoolExecutor(max_workers=baseline_users) as executor:
            futures = []
            phase3_end = phase3_start + baseline_duration_seconds
            
            while time.time() < phase3_end:
                futures.append(executor.submit(self.execute_single_request))
                time.sleep(0.1)
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"    Error in recovery: {e}")
        
        phase3_stats = self.metrics.get_statistics()
        results['phases'].append({
            'phase': 'baseline_after',
            'users': baseline_users,
            'duration_seconds': time.time() - phase3_start,
            'total_requests': phase3_stats.get('total_requests', 0),
            'error_rate_percent': phase3_stats.get('error_rate_percent', 0),
            'avg_response_time_ms': phase3_stats.get('response_time', {}).get('avg_ms', 0)
        })
        
        # Stop monitoring and collect results
        resource_stats = self.resource_monitor.get_statistics()
        self.resource_monitor.stop_monitoring()
        
        total_duration = time.time() - start_time
        final_stats = self.metrics.get_statistics()
        
        results.update({
            'end_time': datetime.now().isoformat(),
            'total_duration_seconds': total_duration,
            'total_requests': final_stats.get('total_requests', 0),
            'successful_requests': final_stats.get('successful_requests', 0),
            'failed_requests': final_stats.get('failed_requests', 0),
            'error_rate_percent': final_stats.get('error_rate_percent', 0),
            'throughput_rps': self.metrics.get_throughput(),
            'response_time_stats': final_stats.get('response_time', {}),
            'resource_usage': resource_stats
        })
        
        return results
    
    def stress_test(
        self,
        max_users: int = 200,
        duration_seconds: int = 60,
        aggressive_rate: bool = True
    ) -> Dict[str, Any]:
        """
        Stress test: push system beyond normal capacity
        
        Args:
            max_users: Maximum concurrent users (beyond capacity)
            duration_seconds: Test duration
            aggressive_rate: Use aggressive request rate
        
        Returns:
            Test results dictionary
        """
        print(f"\n💥 Starting stress test: {max_users} users for {duration_seconds}s")
        
        self.metrics.reset()
        self.resource_monitor.start_monitoring()
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        results = {
            'test_type': 'stress',
            'max_users': max_users,
            'duration_seconds': duration_seconds,
            'aggressive_rate': aggressive_rate,
            'start_time': datetime.now().isoformat(),
            'intervals': []
        }
        
        interval_duration = 10
        next_report_time = start_time + interval_duration
        interval_num = 1
        
        request_delay = 0.01 if aggressive_rate else 0.05
        
        with ThreadPoolExecutor(max_workers=max_users) as executor:
            futures = []
            
            while time.time() < end_time:
                # Submit request
                futures.append(executor.submit(self.execute_single_request))
                
                # Aggressive or moderate rate
                time.sleep(request_delay)
                
                # Report interval stats
                if time.time() >= next_report_time:
                    interval_stats = self.metrics.get_statistics()
                    current_rps = self.metrics.get_throughput()
                    
                    print(f"  Interval {interval_num}: {current_rps:.2f} RPS, "
                          f"{interval_stats.get('error_rate_percent', 0):.2f}% errors, "
                          f"{interval_stats.get('response_time', {}).get('p95_ms', 0):.0f}ms p95")
                    
                    results['intervals'].append({
                        'interval': interval_num,
                        'elapsed_seconds': time.time() - start_time,
                        'throughput_rps': current_rps,
                        'error_rate_percent': interval_stats.get('error_rate_percent', 0),
                        'avg_response_time_ms': interval_stats.get('response_time', {}).get('avg_ms', 0),
                        'p95_response_time_ms': interval_stats.get('response_time', {}).get('p95_ms', 0)
                    })
                    
                    next_report_time += interval_duration
                    interval_num += 1
            
            # Wait for all requests to complete
            print("  Waiting for remaining requests to complete...")
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    pass  # Expected to have errors under stress
        
        # Stop monitoring and collect results
        resource_stats = self.resource_monitor.get_statistics()
        self.resource_monitor.stop_monitoring()
        
        total_duration = time.time() - start_time
        final_stats = self.metrics.get_statistics()
        
        results.update({
            'end_time': datetime.now().isoformat(),
            'actual_duration_seconds': total_duration,
            'total_requests': final_stats.get('total_requests', 0),
            'successful_requests': final_stats.get('successful_requests', 0),
            'failed_requests': final_stats.get('failed_requests', 0),
            'error_rate_percent': final_stats.get('error_rate_percent', 0),
            'throughput_rps': self.metrics.get_throughput(),
            'response_time_stats': final_stats.get('response_time', {}),
            'resource_usage': resource_stats
        })
        
        return results
    
    def recovery_test(
        self,
        stress_users: int = 150,
        stress_duration_seconds: int = 30,
        recovery_duration_seconds: int = 60,
        normal_users: int = 10
    ) -> Dict[str, Any]:
        """
        Recovery test: measure system recovery after stress
        
        Args:
            stress_users: Users during stress phase
            stress_duration_seconds: Duration of stress
            recovery_duration_seconds: Duration to monitor recovery
            normal_users: Normal load during recovery
        
        Returns:
            Test results dictionary
        """
        print(f"\n🔄 Starting recovery test: {stress_users} users stress → {normal_users} users recovery")
        
        self.metrics.reset()
        self.resource_monitor.start_monitoring()
        
        start_time = time.time()
        
        results = {
            'test_type': 'recovery',
            'stress_users': stress_users,
            'stress_duration_seconds': stress_duration_seconds,
            'recovery_duration_seconds': recovery_duration_seconds,
            'normal_users': normal_users,
            'start_time': datetime.now().isoformat(),
            'phases': []
        }
        
        # Phase 1: Stress
        print(f"  Phase 1: Applying stress ({stress_users} users)")
        phase1_start = time.time()
        
        with ThreadPoolExecutor(max_workers=stress_users) as executor:
            futures = []
            phase1_end = phase1_start + stress_duration_seconds
            
            while time.time() < phase1_end:
                futures.append(executor.submit(self.execute_single_request))
                time.sleep(0.01)
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass
        
        phase1_stats = self.metrics.get_statistics()
        results['phases'].append({
            'phase': 'stress',
            'users': stress_users,
            'duration_seconds': time.time() - phase1_start,
            'total_requests': phase1_stats.get('total_requests', 0),
            'error_rate_percent': phase1_stats.get('error_rate_percent', 0),
            'avg_response_time_ms': phase1_stats.get('response_time', {}).get('avg_ms', 0)
        })
        
        # Phase 2: Recovery monitoring
        print(f"  Phase 2: Monitoring recovery ({normal_users} users)")
        phase2_start = time.time()
        
        recovery_intervals = []
        interval_duration = 10
        num_intervals = recovery_duration_seconds // interval_duration
        
        for interval in range(num_intervals):
            interval_start = time.time()
            
            with ThreadPoolExecutor(max_workers=normal_users) as executor:
                futures = []
                interval_end = interval_start + interval_duration
                
                while time.time() < interval_end:
                    futures.append(executor.submit(self.execute_single_request))
                    time.sleep(0.1)
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception:
                        pass
            
            interval_stats = self.metrics.get_statistics()
            recovery_intervals.append({
                'interval': interval + 1,
                'elapsed_seconds': time.time() - phase2_start,
                'error_rate_percent': interval_stats.get('error_rate_percent', 0),
                'avg_response_time_ms': interval_stats.get('response_time', {}).get('avg_ms', 0),
                'p95_response_time_ms': interval_stats.get('response_time', {}).get('p95_ms', 0)
            })
            
            print(f"    Recovery interval {interval + 1}/{num_intervals}: "
                  f"{interval_stats.get('error_rate_percent', 0):.2f}% errors, "
                  f"{interval_stats.get('response_time', {}).get('avg_ms', 0):.0f}ms avg")
        
        results['phases'].append({
            'phase': 'recovery',
            'users': normal_users,
            'duration_seconds': time.time() - phase2_start,
            'intervals': recovery_intervals
        })
        
        # Stop monitoring and collect results
        resource_stats = self.resource_monitor.get_statistics()
        self.resource_monitor.stop_monitoring()
        
        total_duration = time.time() - start_time
        final_stats = self.metrics.get_statistics()
        
        # Analyze recovery
        recovery_complete = all(
            interval['error_rate_percent'] < 5.0 
            for interval in recovery_intervals[-3:]  # Last 3 intervals
        )
        
        results.update({
            'end_time': datetime.now().isoformat(),
            'total_duration_seconds': total_duration,
            'recovery_complete': recovery_complete,
            'total_requests': final_stats.get('total_requests', 0),
            'successful_requests': final_stats.get('successful_requests', 0),
            'failed_requests': final_stats.get('failed_requests', 0),
            'error_rate_percent': final_stats.get('error_rate_percent', 0),
            'throughput_rps': self.metrics.get_throughput(),
            'response_time_stats': final_stats.get('response_time', {}),
            'resource_usage': resource_stats
        })
        
        return results


# ============================================================================
# PYTEST TEST CASES
# ============================================================================

@pytest.fixture(scope="module")
def api_client(config):
    """Create API client for load tests"""
    client = CropYieldAPIClient(
        base_url=config["api"]["base_url"],
        timeout=config["api"]["timeout_seconds"]
    )
    yield client
    client.close()


@pytest.fixture(scope="module")
def data_generator(config):
    """Create test data generator"""
    return TestDataGenerator(config)


@pytest.fixture(scope="module")
def load_runner(api_client, data_generator):
    """Create load test runner"""
    return LoadTestRunner(api_client, data_generator)


@pytest.fixture(scope="module")
def reports_dir(config):
    """Get reports directory"""
    reports_path = Path(config.get("reporting", {}).get("output_directory", "test_api_intensive/reports"))
    reports_path.mkdir(parents=True, exist_ok=True)
    return reports_path


@pytest.mark.load
@pytest.mark.slow
class TestLoadAndStress:
    """Load and stress test suite"""
    
    def test_gradual_ramp_up(self, load_runner, reports_dir, config):
        """
        Test gradual load increase from 1 to 100 users
        
        Requirements: 4.4, 4.5
        """
        print("\n" + "="*80)
        print("TEST: Gradual Ramp-Up (1 → 100 users)")
        print("="*80)
        
        # Get configuration
        perf_config = config.get("performance", {})
        ramp_time = perf_config.get("ramp_up_time_seconds", 60)
        
        # Run ramp-up test
        results = load_runner.ramp_up_test(
            start_users=1,
            end_users=100,
            ramp_time_seconds=ramp_time,
            requests_per_user=3
        )
        
        # Save results
        import json
        results_file = reports_dir / f"load_test_ramp_up_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Ramp-up test completed:")
        print(f"   Total requests: {results['total_requests']}")
        print(f"   Success rate: {100 - results['error_rate_percent']:.2f}%")
        print(f"   Throughput: {results['throughput_rps']:.2f} RPS")
        print(f"   Avg response time: {results['response_time_stats'].get('avg_ms', 0):.2f}ms")
        print(f"   P95 response time: {results['response_time_stats'].get('p95_ms', 0):.2f}ms")
        print(f"   CPU usage: {results['resource_usage']['cpu']['avg_percent']:.1f}% avg, "
              f"{results['resource_usage']['cpu']['max_percent']:.1f}% max")
        print(f"   Memory usage: {results['resource_usage']['memory']['avg_mb']:.1f}MB avg, "
              f"{results['resource_usage']['memory']['max_mb']:.1f}MB max")
        print(f"\n📊 Results saved to: {results_file}")
        
        # Assertions
        assert results['error_rate_percent'] < 10.0, \
            f"Error rate too high during ramp-up: {results['error_rate_percent']:.2f}%"
        
        assert results['response_time_stats'].get('p95_ms', 0) < 15000, \
            f"P95 response time too high: {results['response_time_stats'].get('p95_ms', 0):.2f}ms"

    
    def test_sustained_high_load(self, load_runner, reports_dir, config):
        """
        Test sustained load with 100 users for 5 minutes
        
        Requirements: 4.5, 4.6
        """
        print("\n" + "="*80)
        print("TEST: Sustained High Load (100 users for 5 minutes)")
        print("="*80)
        
        # Get configuration
        perf_config = config.get("performance", {})
        duration = perf_config.get("load_test_duration_seconds", 300)
        
        # Run sustained load test
        results = load_runner.sustained_load_test(
            num_users=100,
            duration_seconds=duration,
            requests_per_second=10
        )
        
        # Save results
        import json
        results_file = reports_dir / f"load_test_sustained_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Sustained load test completed:")
        print(f"   Duration: {results['actual_duration_seconds']:.1f}s")
        print(f"   Total requests: {results['total_requests']}")
        print(f"   Success rate: {100 - results['error_rate_percent']:.2f}%")
        print(f"   Throughput: {results['actual_throughput_rps']:.2f} RPS")
        print(f"   Avg response time: {results['response_time_stats'].get('avg_ms', 0):.2f}ms")
        print(f"   P95 response time: {results['response_time_stats'].get('p95_ms', 0):.2f}ms")
        print(f"   P99 response time: {results['response_time_stats'].get('p99_ms', 0):.2f}ms")
        print(f"   CPU usage: {results['resource_usage']['cpu']['avg_percent']:.1f}% avg, "
              f"{results['resource_usage']['cpu']['max_percent']:.1f}% max")
        print(f"   Memory usage: {results['resource_usage']['memory']['avg_mb']:.1f}MB avg, "
              f"{results['resource_usage']['memory']['max_mb']:.1f}MB max")
        print(f"\n📊 Results saved to: {results_file}")
        
        # Assertions
        thresholds = config.get("thresholds", {})
        max_error_rate = thresholds.get("max_error_rate_percent", 5.0)
        max_p95_time = thresholds.get("max_p95_response_time_ms", 10000)
        
        assert results['error_rate_percent'] < max_error_rate, \
            f"Error rate too high: {results['error_rate_percent']:.2f}% (max: {max_error_rate}%)"
        
        assert results['response_time_stats'].get('p95_ms', 0) < max_p95_time, \
            f"P95 response time too high: {results['response_time_stats'].get('p95_ms', 0):.2f}ms (max: {max_p95_time}ms)"
        
        # Check system stability (error rate should not increase significantly over time)
        if len(results['intervals']) > 2:
            first_half_errors = sum(i['error_rate_percent'] for i in results['intervals'][:len(results['intervals'])//2])
            second_half_errors = sum(i['error_rate_percent'] for i in results['intervals'][len(results['intervals'])//2:])
            
            first_half_avg = first_half_errors / (len(results['intervals']) // 2)
            second_half_avg = second_half_errors / (len(results['intervals']) - len(results['intervals']) // 2)
            
            print(f"\n   Stability check:")
            print(f"   First half error rate: {first_half_avg:.2f}%")
            print(f"   Second half error rate: {second_half_avg:.2f}%")
            
            # Allow up to 50% increase in error rate
            assert second_half_avg <= first_half_avg * 1.5, \
                "System stability degraded significantly over time"
    
    def test_spike_load(self, load_runner, reports_dir, config):
        """
        Test sudden spike in load
        
        Requirements: 4.4, 4.5
        """
        print("\n" + "="*80)
        print("TEST: Spike Load (10 → 150 users)")
        print("="*80)
        
        # Get configuration
        perf_config = config.get("performance", {})
        spike_users = perf_config.get("spike_test_users", 150)
        spike_duration = perf_config.get("spike_duration_seconds", 10)
        
        # Run spike test
        results = load_runner.spike_test(
            baseline_users=10,
            spike_users=spike_users,
            spike_duration_seconds=spike_duration,
            baseline_duration_seconds=30
        )
        
        # Save results
        import json
        results_file = reports_dir / f"load_test_spike_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Spike test completed:")
        print(f"   Total requests: {results['total_requests']}")
        print(f"   Success rate: {100 - results['error_rate_percent']:.2f}%")
        print(f"   Throughput: {results['throughput_rps']:.2f} RPS")
        
        # Print phase-by-phase results
        for phase in results['phases']:
            phase_name = phase['phase']
            print(f"\n   {phase_name.upper()}:")
            print(f"     Users: {phase['users']}")
            print(f"     Requests: {phase['total_requests']}")
            print(f"     Error rate: {phase['error_rate_percent']:.2f}%")
            print(f"     Avg response time: {phase['avg_response_time_ms']:.2f}ms")
        
        print(f"\n   Resource usage:")
        print(f"     CPU: {results['resource_usage']['cpu']['avg_percent']:.1f}% avg, "
              f"{results['resource_usage']['cpu']['max_percent']:.1f}% max")
        print(f"     Memory: {results['resource_usage']['memory']['avg_mb']:.1f}MB avg, "
              f"{results['resource_usage']['memory']['max_mb']:.1f}MB max")
        print(f"\n📊 Results saved to: {results_file}")
        
        # Assertions
        # System should handle spike without crashing
        assert results['total_requests'] > 0, "No requests completed"
        
        # Error rate during spike should be reasonable (< 20%)
        spike_phase = next((p for p in results['phases'] if p['phase'] == 'spike'), None)
        if spike_phase:
            assert spike_phase['error_rate_percent'] < 20.0, \
                f"Error rate during spike too high: {spike_phase['error_rate_percent']:.2f}%"
        
        # System should recover after spike
        recovery_phase = next((p for p in results['phases'] if p['phase'] == 'baseline_after'), None)
        baseline_phase = next((p for p in results['phases'] if p['phase'] == 'baseline_before'), None)
        
        if recovery_phase and baseline_phase:
            print(f"\n   Recovery analysis:")
            print(f"     Baseline error rate: {baseline_phase['error_rate_percent']:.2f}%")
            print(f"     Recovery error rate: {recovery_phase['error_rate_percent']:.2f}%")
            
            # Recovery error rate should be similar to baseline (within 2x)
            assert recovery_phase['error_rate_percent'] <= baseline_phase['error_rate_percent'] * 2 + 5.0, \
                "System did not recover properly after spike"
    
    def test_stress_beyond_capacity(self, load_runner, reports_dir, config):
        """
        Test system under stress beyond normal capacity
        
        Requirements: 4.4, 4.5, 4.6
        """
        print("\n" + "="*80)
        print("TEST: Stress Beyond Capacity (200 users)")
        print("="*80)
        
        # Get configuration
        perf_config = config.get("performance", {})
        max_users = perf_config.get("stress_test_max_users", 200)
        
        # Run stress test
        results = load_runner.stress_test(
            max_users=max_users,
            duration_seconds=60,
            aggressive_rate=True
        )
        
        # Save results
        import json
        results_file = reports_dir / f"load_test_stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Stress test completed:")
        print(f"   Duration: {results['actual_duration_seconds']:.1f}s")
        print(f"   Total requests: {results['total_requests']}")
        print(f"   Successful: {results['successful_requests']}")
        print(f"   Failed: {results['failed_requests']}")
        print(f"   Error rate: {results['error_rate_percent']:.2f}%")
        print(f"   Throughput: {results['throughput_rps']:.2f} RPS")
        print(f"   Avg response time: {results['response_time_stats'].get('avg_ms', 0):.2f}ms")
        print(f"   P95 response time: {results['response_time_stats'].get('p95_ms', 0):.2f}ms")
        print(f"   P99 response time: {results['response_time_stats'].get('p99_ms', 0):.2f}ms")
        print(f"\n   Resource usage:")
        print(f"     CPU: {results['resource_usage']['cpu']['avg_percent']:.1f}% avg, "
              f"{results['resource_usage']['cpu']['max_percent']:.1f}% max")
        print(f"     Memory: {results['resource_usage']['memory']['avg_mb']:.1f}MB avg, "
              f"{results['resource_usage']['memory']['max_mb']:.1f}MB max")
        print(f"\n📊 Results saved to: {results_file}")
        
        # Assertions
        # System should not crash (should complete some requests)
        assert results['successful_requests'] > 0, "System crashed - no successful requests"
        
        # System should maintain some level of service (> 50% success rate)
        success_rate = (results['successful_requests'] / results['total_requests']) * 100
        print(f"\n   Success rate under stress: {success_rate:.2f}%")
        
        assert success_rate > 50.0, \
            f"Success rate too low under stress: {success_rate:.2f}%"
        
        # Memory should not grow unbounded (< 2GB)
        max_memory_mb = results['resource_usage']['memory']['max_mb']
        assert max_memory_mb < 2048, \
            f"Memory usage too high: {max_memory_mb:.1f}MB"
    
    def test_system_recovery(self, load_runner, reports_dir, config):
        """
        Test system recovery after stress
        
        Requirements: 4.5, 4.6
        """
        print("\n" + "="*80)
        print("TEST: System Recovery After Stress")
        print("="*80)
        
        # Run recovery test
        results = load_runner.recovery_test(
            stress_users=150,
            stress_duration_seconds=30,
            recovery_duration_seconds=60,
            normal_users=10
        )
        
        # Save results
        import json
        results_file = reports_dir / f"load_test_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Recovery test completed:")
        print(f"   Total duration: {results['total_duration_seconds']:.1f}s")
        print(f"   Total requests: {results['total_requests']}")
        print(f"   Overall error rate: {results['error_rate_percent']:.2f}%")
        print(f"   Recovery complete: {'YES' if results['recovery_complete'] else 'NO'}")
        
        # Print phase results
        for phase in results['phases']:
            phase_name = phase['phase']
            print(f"\n   {phase_name.upper()}:")
            print(f"     Users: {phase['users']}")
            print(f"     Duration: {phase['duration_seconds']:.1f}s")
            
            if 'intervals' in phase:
                print(f"     Recovery intervals:")
                for interval in phase['intervals']:
                    print(f"       Interval {interval['interval']}: "
                          f"{interval['error_rate_percent']:.2f}% errors, "
                          f"{interval['avg_response_time_ms']:.0f}ms avg")
            else:
                print(f"     Requests: {phase['total_requests']}")
                print(f"     Error rate: {phase['error_rate_percent']:.2f}%")
        
        print(f"\n   Resource usage:")
        print(f"     CPU: {results['resource_usage']['cpu']['avg_percent']:.1f}% avg, "
              f"{results['resource_usage']['cpu']['max_percent']:.1f}% max")
        print(f"     Memory: {results['resource_usage']['memory']['avg_mb']:.1f}MB avg, "
              f"{results['resource_usage']['memory']['max_mb']:.1f}MB max")
        print(f"\n📊 Results saved to: {results_file}")
        
        # Assertions
        # System should eventually recover (last 3 intervals should have low error rate)
        recovery_phase = next((p for p in results['phases'] if p['phase'] == 'recovery'), None)
        
        if recovery_phase and 'intervals' in recovery_phase:
            last_intervals = recovery_phase['intervals'][-3:]
            avg_error_rate = sum(i['error_rate_percent'] for i in last_intervals) / len(last_intervals)
            
            print(f"\n   Final recovery error rate: {avg_error_rate:.2f}%")
            
            assert avg_error_rate < 10.0, \
                f"System did not recover properly: {avg_error_rate:.2f}% error rate"
        
        assert results['recovery_complete'], "System recovery incomplete"


# ============================================================================
# LOCUST LOAD TEST DEFINITIONS
# ============================================================================

"""
Locust-based load tests for more advanced scenarios.

To run these tests:
    locust -f test_api_intensive/suites/test_load.py --host=http://localhost:8000
"""

try:
    from locust import HttpUser, task, between, events
    from locust.env import Environment
    
    class CropYieldUser(HttpUser):
        """Locust user for Crop Yield API load testing"""
        
        wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
        
        def on_start(self):
            """Initialize user session"""
            self.data_generator = TestDataGenerator({
                "test_data": {
                    "locations": [
                        {"name": "Bhopal", "latitude": 23.2599, "longitude": 77.4126},
                        {"name": "Lucknow", "latitude": 26.8467, "longitude": 80.9462},
                    ],
                    "crops": ["Rice", "Wheat", "Maize"],
                    "sowing_dates": {
                        "Rice": {"kharif": ["2024-06-15", "2024-07-01"]},
                        "Wheat": {"rabi": ["2024-11-01", "2024-11-15"]},
                        "Maize": {"kharif": ["2024-06-01", "2024-06-15"]}
                    }
                }
            })
        
        @task(3)
        def predict_yield_auto_variety(self):
            """Make prediction request without variety (auto-selection)"""
            request_data = self.data_generator.generate_valid_request(include_variety=False)
            
            with self.client.post(
                "/predict/yield",
                json=request_data,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")
        
        @task(2)
        def predict_yield_with_variety(self):
            """Make prediction request with specified variety"""
            request_data = self.data_generator.generate_valid_request(include_variety=True)
            
            with self.client.post(
                "/predict/yield",
                json=request_data,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")
        
        @task(1)
        def health_check(self):
            """Check API health"""
            with self.client.get("/health", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")

except ImportError:
    # Locust not available, skip locust tests
    print("Locust not available, skipping locust test definitions")
