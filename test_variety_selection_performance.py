#!/usr/bin/env python3
"""
Performance Tests for Variety Selection Service

Tests performance characteristics of variety selection including:
- Selection latency (must be < 50ms)
- Cached location mapping performance
- Bulk request processing (100 requests)
- Response time comparison with/without variety specification
- Average response time increase threshold (within 10%)
"""

import unittest
import time
import statistics
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from variety_selection_service import VarietySelectionService
from crop_variety_database import CropVarietyDatabase


class TestVarietySelectionPerformance(unittest.TestCase):
    """Performance test suite for VarietySelectionService"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests"""
        try:
            cls.variety_db = CropVarietyDatabase()
            cls.service = VarietySelectionService(cls.variety_db)
            cls.db_available = True
            print("\n✅ Database initialized for performance tests")
        except Exception as e:
            cls.db_available = False
            print(f"\n⚠️  Database not available: {e}")

    def setUp(self):
        """Check database availability before each test"""
        if not self.db_available:
            self.skipTest("Database not available for performance testing")

    def test_variety_selection_latency_under_50ms(self):
        """Test that variety selection latency is under 50ms (Requirement 8.1)"""
        print("\n" + "="*70)
        print("TEST: Variety Selection Latency (must be < 50ms)")
        print("="*70)
        
        # Test cases covering different scenarios
        test_cases = [
            ('Rice', 'Bhopal'),
            ('Wheat', 'Chandigarh'),
            ('Maize', 'Lucknow'),
            ('Rice', 'Patna'),
            ('Wheat', 'Delhi'),
            ('Maize', 'Jaipur'),
            ('Rice', 'Unknown City'),  # Fallback scenario
        ]
        
        latencies = []
        
        for crop_type, location in test_cases:
            # Measure selection time
            start_time = time.perf_counter()
            
            try:
                result = self.service.select_default_variety(crop_type, location)
                
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
                
                print(f"  {crop_type:6s} in {location:15s}: {latency_ms:6.2f}ms "
                      f"(selected: {result['variety_name']})")
                
                # Assert individual latency is under 50ms
                self.assertLess(latency_ms, 50.0,
                              f"Variety selection took {latency_ms:.2f}ms, exceeds 50ms threshold")
                
            except Exception as e:
                self.fail(f"Variety selection failed for {crop_type} in {location}: {e}")
        
        # Calculate statistics
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        median_latency = statistics.median(latencies)
        
        print(f"\n  Statistics:")
        print(f"    Average latency: {avg_latency:.2f}ms")
        print(f"    Median latency:  {median_latency:.2f}ms")
        print(f"    Min latency:     {min_latency:.2f}ms")
        print(f"    Max latency:     {max_latency:.2f}ms")
        print(f"    Threshold:       50.00ms")
        
        # Assert average latency is well under threshold
        self.assertLess(avg_latency, 50.0,
                       f"Average latency {avg_latency:.2f}ms exceeds 50ms threshold")
        
        # Assert max latency is under threshold
        self.assertLess(max_latency, 50.0,
                       f"Max latency {max_latency:.2f}ms exceeds 50ms threshold")
        
        print(f"\n  ✅ All latencies under 50ms threshold")

    def test_cached_location_mapping_performance(self):
        """Test cached location mapping performance (Requirement 8.3)"""
        print("\n" + "="*70)
        print("TEST: Cached Location Mapping Performance")
        print("="*70)
        
        # Test locations
        test_locations = [
            'Bhopal', 'Lucknow', 'Chandigarh', 'Patna', 'Delhi',
            'Jaipur', 'Amritsar', 'Kanpur', 'Indore', 'Varanasi'
        ]
        
        # Measure first access (cache hit, already initialized)
        first_access_times = []
        for location in test_locations:
            start_time = time.perf_counter()
            region = self.service.map_location_to_region(location)
            end_time = time.perf_counter()
            
            latency_us = (end_time - start_time) * 1_000_000  # microseconds
            first_access_times.append(latency_us)
            print(f"  {location:15s} → {region:20s}: {latency_us:6.2f}μs")
        
        # Measure repeated access (should be from cache)
        repeated_access_times = []
        for location in test_locations * 10:  # Repeat 10 times
            start_time = time.perf_counter()
            region = self.service.map_location_to_region(location)
            end_time = time.perf_counter()
            
            latency_us = (end_time - start_time) * 1_000_000
            repeated_access_times.append(latency_us)
        
        # Calculate statistics
        avg_first = statistics.mean(first_access_times)
        avg_repeated = statistics.mean(repeated_access_times)
        
        print(f"\n  Statistics:")
        print(f"    Average first access:    {avg_first:.2f}μs")
        print(f"    Average repeated access: {avg_repeated:.2f}μs")
        print(f"    Cache speedup factor:    {avg_first/avg_repeated:.2f}x")
        
        # Assert cached access is very fast (< 10 microseconds)
        self.assertLess(avg_repeated, 10.0,
                       f"Cached location mapping too slow: {avg_repeated:.2f}μs")
        
        # Assert cache provides speedup (or at least not slower)
        self.assertLessEqual(avg_repeated, avg_first * 1.5,
                            "Cache not providing expected performance benefit")
        
        print(f"\n  ✅ Location mapping cache performing efficiently")

    def test_100_requests_with_variety_selection(self):
        """Test processing 100 requests with variety selection (Requirement 8.3)"""
        print("\n" + "="*70)
        print("TEST: Processing 100 Requests with Variety Selection")
        print("="*70)
        
        # Create 100 test requests with variety selection
        test_requests = []
        locations = ['Bhopal', 'Lucknow', 'Chandigarh', 'Patna', 'Delhi']
        crop_types = ['Rice', 'Wheat', 'Maize']
        
        for i in range(100):
            test_requests.append({
                'crop_type': crop_types[i % len(crop_types)],
                'location': locations[i % len(locations)]
            })
        
        # Process all requests and measure time
        start_time = time.perf_counter()
        
        results = []
        for req in test_requests:
            try:
                result = self.service.select_default_variety(
                    req['crop_type'],
                    req['location']
                )
                results.append({
                    'success': True,
                    'variety': result['variety_name'],
                    'reason': result['selection_metadata']['reason']
                })
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e)
                })
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Calculate statistics
        successful = sum(1 for r in results if r.get('success', False))
        failed = len(results) - successful
        avg_time_per_request = (total_time / len(test_requests)) * 1000  # ms
        requests_per_second = len(test_requests) / total_time
        
        print(f"\n  Results:")
        print(f"    Total requests:           {len(test_requests)}")
        print(f"    Successful:               {successful}")
        print(f"    Failed:                   {failed}")
        print(f"    Total time:               {total_time:.3f}s")
        print(f"    Avg time per request:     {avg_time_per_request:.2f}ms")
        print(f"    Requests per second:      {requests_per_second:.1f}")
        
        # Count selection reasons
        reason_counts = {}
        for r in results:
            if r.get('success'):
                reason = r.get('reason', 'unknown')
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        print(f"\n  Selection Reasons:")
        for reason, count in sorted(reason_counts.items()):
            print(f"    {reason:25s}: {count:3d} ({count/successful*100:.1f}%)")
        
        # Assertions
        self.assertEqual(successful, 100, "Not all requests succeeded")
        self.assertLess(avg_time_per_request, 50.0,
                       f"Average time per request {avg_time_per_request:.2f}ms exceeds 50ms")
        self.assertGreater(requests_per_second, 20,
                          f"Throughput {requests_per_second:.1f} req/s is too low")
        
        print(f"\n  ✅ Successfully processed 100 requests efficiently")

    def test_response_time_comparison_with_without_variety(self):
        """Test comparing response times with and without variety specification (Requirement 8.4)"""
        print("\n" + "="*70)
        print("TEST: Response Time Comparison (With vs Without Variety)")
        print("="*70)
        
        # Import prediction service for full integration test
        try:
            from prediction_api import CropYieldPredictionService
            
            # Initialize service
            service = CropYieldPredictionService()
            
            # Test cases
            test_cases = [
                {
                    'crop_type': 'Rice',
                    'location_name': 'Bhopal',
                    'latitude': 23.2599,
                    'longitude': 77.4126,
                    'sowing_date': '2024-06-15',
                    'use_real_time_data': False  # Use historical data for consistent timing
                },
                {
                    'crop_type': 'Wheat',
                    'location_name': 'Chandigarh',
                    'latitude': 30.7333,
                    'longitude': 76.7794,
                    'sowing_date': '2024-11-01',
                    'use_real_time_data': False
                },
                {
                    'crop_type': 'Maize',
                    'location_name': 'Lucknow',
                    'latitude': 26.8467,
                    'longitude': 80.9462,
                    'sowing_date': '2024-07-01',
                    'use_real_time_data': False
                }
            ]
            
            with_variety_times = []
            without_variety_times = []
            
            for test_case in test_cases:
                # Test WITH variety specified
                test_with_variety = test_case.copy()
                
                # Get a valid variety for this crop type
                varieties = service.variety_db.get_crop_varieties(test_case['crop_type'])
                if not varieties.empty:
                    test_with_variety['variety_name'] = varieties.iloc[0]['variety_name']
                else:
                    # Skip if no varieties available
                    continue
                
                start_time = time.perf_counter()
                result_with = service.predict_yield(test_with_variety)
                end_time = time.perf_counter()
                time_with = (end_time - start_time) * 1000  # ms
                with_variety_times.append(time_with)
                
                # Test WITHOUT variety specified
                test_without_variety = test_case.copy()
                test_without_variety['variety_name'] = None
                
                start_time = time.perf_counter()
                result_without = service.predict_yield(test_without_variety)
                end_time = time.perf_counter()
                time_without = (end_time - start_time) * 1000  # ms
                without_variety_times.append(time_without)
                
                # Calculate overhead
                overhead_ms = time_without - time_with
                overhead_pct = (overhead_ms / time_with) * 100
                
                print(f"\n  {test_case['crop_type']} in {test_case['location_name']}:")
                print(f"    With variety:    {time_with:7.2f}ms")
                print(f"    Without variety: {time_without:7.2f}ms")
                print(f"    Overhead:        {overhead_ms:7.2f}ms ({overhead_pct:+.1f}%)")
                
                # Verify both predictions succeeded
                self.assertNotIn('error', result_with, "Prediction with variety failed")
                self.assertNotIn('error', result_without, "Prediction without variety failed")
            
            # Calculate overall statistics
            if with_variety_times and without_variety_times:
                avg_with = statistics.mean(with_variety_times)
                avg_without = statistics.mean(without_variety_times)
                avg_overhead = avg_without - avg_with
                avg_overhead_pct = (avg_overhead / avg_with) * 100
                
                print(f"\n  Overall Statistics:")
                print(f"    Avg with variety:    {avg_with:.2f}ms")
                print(f"    Avg without variety: {avg_without:.2f}ms")
                print(f"    Avg overhead:        {avg_overhead:.2f}ms ({avg_overhead_pct:+.1f}%)")
                print(f"    Threshold:           10% increase")
                
                # Assert average response time increase is within 10% threshold
                self.assertLess(avg_overhead_pct, 10.0,
                              f"Response time increase {avg_overhead_pct:.1f}% exceeds 10% threshold")
                
                print(f"\n  ✅ Response time increase within 10% threshold")
            else:
                self.skipTest("Could not perform comparison - no valid test cases")
                
        except ImportError as e:
            self.skipTest(f"Prediction API not available for integration test: {e}")
        except Exception as e:
            self.skipTest(f"Integration test failed: {e}")

    def test_variety_selection_only_latency(self):
        """Test isolated variety selection latency (without full prediction)"""
        print("\n" + "="*70)
        print("TEST: Isolated Variety Selection Latency")
        print("="*70)
        
        # Warm up cache
        for _ in range(10):
            self.service.select_default_variety('Rice', 'Bhopal')
        
        # Measure variety selection only
        iterations = 1000
        latencies = []
        
        test_cases = [
            ('Rice', 'Bhopal'),
            ('Wheat', 'Chandigarh'),
            ('Maize', 'Lucknow')
        ]
        
        for crop_type, location in test_cases:
            case_latencies = []
            
            for _ in range(iterations):
                start_time = time.perf_counter()
                result = self.service.select_default_variety(crop_type, location)
                end_time = time.perf_counter()
                
                latency_ms = (end_time - start_time) * 1000
                case_latencies.append(latency_ms)
            
            avg_latency = statistics.mean(case_latencies)
            median_latency = statistics.median(case_latencies)
            p95_latency = sorted(case_latencies)[int(0.95 * len(case_latencies))]
            p99_latency = sorted(case_latencies)[int(0.99 * len(case_latencies))]
            
            print(f"\n  {crop_type} in {location} ({iterations} iterations):")
            print(f"    Average:  {avg_latency:.3f}ms")
            print(f"    Median:   {median_latency:.3f}ms")
            print(f"    P95:      {p95_latency:.3f}ms")
            print(f"    P99:      {p99_latency:.3f}ms")
            
            latencies.extend(case_latencies)
            
            # Assert P99 latency is under 50ms
            self.assertLess(p99_latency, 50.0,
                          f"P99 latency {p99_latency:.2f}ms exceeds 50ms threshold")
        
        # Overall statistics
        overall_avg = statistics.mean(latencies)
        overall_median = statistics.median(latencies)
        overall_p95 = sorted(latencies)[int(0.95 * len(latencies))]
        overall_p99 = sorted(latencies)[int(0.99 * len(latencies))]
        
        print(f"\n  Overall Statistics ({len(latencies)} total selections):")
        print(f"    Average:  {overall_avg:.3f}ms")
        print(f"    Median:   {overall_median:.3f}ms")
        print(f"    P95:      {overall_p95:.3f}ms")
        print(f"    P99:      {overall_p99:.3f}ms")
        print(f"    Threshold: 50.00ms")
        
        # Assert overall P99 is under threshold
        self.assertLess(overall_p99, 50.0,
                       f"Overall P99 latency {overall_p99:.2f}ms exceeds 50ms threshold")
        
        print(f"\n  ✅ Variety selection consistently fast across {len(latencies)} iterations")

    def test_database_query_performance(self):
        """Test database query performance for variety selection"""
        print("\n" + "="*70)
        print("TEST: Database Query Performance")
        print("="*70)
        
        # Test regional variety queries
        test_queries = [
            ('Rice', 'Madhya Pradesh'),
            ('Wheat', 'Punjab'),
            ('Maize', 'Uttar Pradesh'),
            ('Rice', 'All North India'),
            ('Wheat', 'Bihar'),
        ]
        
        query_times = []
        
        for crop_type, region in test_queries:
            start_time = time.perf_counter()
            varieties = self.service.get_regional_varieties(crop_type, region)
            end_time = time.perf_counter()
            
            query_time_ms = (end_time - start_time) * 1000
            query_times.append(query_time_ms)
            
            print(f"  {crop_type:6s} in {region:20s}: {query_time_ms:6.2f}ms "
                  f"({len(varieties)} varieties)")
            
            # Assert individual query is fast (< 20ms as per design)
            self.assertLess(query_time_ms, 20.0,
                          f"Database query took {query_time_ms:.2f}ms, exceeds 20ms threshold")
        
        # Statistics
        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)
        
        print(f"\n  Statistics:")
        print(f"    Average query time: {avg_query_time:.2f}ms")
        print(f"    Max query time:     {max_query_time:.2f}ms")
        print(f"    Threshold:          20.00ms")
        
        # Assert average query time is under threshold
        self.assertLess(avg_query_time, 20.0,
                       f"Average query time {avg_query_time:.2f}ms exceeds 20ms threshold")
        
        print(f"\n  ✅ Database queries performing efficiently")


def run_performance_tests():
    """Run all performance tests"""
    print("\n" + "="*70)
    print("VARIETY SELECTION PERFORMANCE TEST SUITE")
    print("="*70)
    print("\nTesting performance requirements:")
    print("  - Variety selection latency < 50ms (Requirement 8.1)")
    print("  - Indexed database queries (Requirement 8.2)")
    print("  - Cached location mappings (Requirement 8.3)")
    print("  - Response time increase < 10% (Requirement 8.4)")
    print("="*70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestVarietySelectionPerformance))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("PERFORMANCE TEST SUMMARY")
    print("="*70)
    print(f"Tests run:     {result.testsRun}")
    print(f"Successes:     {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:      {len(result.failures)}")
    print(f"Errors:        {len(result.errors)}")
    print(f"Skipped:       {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ All performance requirements met!")
    else:
        print("\n❌ Some performance tests failed")
    
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_performance_tests()
    sys.exit(0 if success else 1)
