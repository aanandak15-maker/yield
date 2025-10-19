"""
Verification tests for core test utilities

This module tests that the core utilities (API client, test data generator,
assertions, and performance metrics) are working correctly.
"""

import pytest
from utils import (
    CropYieldAPIClient,
    APIResponse,
    TestDataGenerator,
    PerformanceMetrics,
    assert_valid_prediction_response,
    assert_variety_selection_metadata,
    assert_response_time_within,
    assert_yield_in_range,
    assert_error_response,
    assert_field_exists,
    assert_field_equals
)


class TestAPIResponse:
    """Test APIResponse wrapper functionality"""
    
    def test_api_response_success(self):
        """Test successful response detection"""
        response = APIResponse(
            status_code=200,
            json_data={'status': 'success'},
            headers={},
            response_time_ms=100.0
        )
        
        assert response.is_success()
        assert not response.is_client_error()
        assert not response.is_server_error()
    
    def test_api_response_has_field(self):
        """Test field existence checking"""
        response = APIResponse(
            status_code=200,
            json_data={
                'prediction': {
                    'yield_tons_per_hectare': 5.5,
                    'confidence_score': 0.85
                }
            },
            headers={},
            response_time_ms=100.0
        )
        
        assert response.has_field('prediction')
        assert response.has_field('prediction.yield_tons_per_hectare')
        assert response.has_field('prediction.confidence_score')
        assert not response.has_field('prediction.nonexistent')
    
    def test_api_response_get_field(self):
        """Test field value retrieval"""
        response = APIResponse(
            status_code=200,
            json_data={
                'prediction': {
                    'yield_tons_per_hectare': 5.5
                }
            },
            headers={},
            response_time_ms=100.0
        )
        
        assert response.get_field('prediction.yield_tons_per_hectare') == 5.5
        assert response.get_field('nonexistent', 'default') == 'default'


class TestTestDataGenerator:
    """Test TestDataGenerator functionality"""
    
    def test_generate_valid_request(self):
        """Test valid request generation"""
        generator = TestDataGenerator(seed=42)
        request = generator.generate_valid_request()
        
        assert 'crop_type' in request
        assert 'latitude' in request
        assert 'longitude' in request
        assert 'sowing_date' in request
        assert request['crop_type'] in ['Rice', 'Wheat', 'Maize']
    
    def test_generate_valid_request_without_variety(self):
        """Test valid request generation without variety"""
        generator = TestDataGenerator(seed=42)
        request = generator.generate_valid_request(include_variety=False)
        
        assert 'variety_name' not in request
    
    def test_generate_invalid_request(self):
        """Test invalid request generation"""
        generator = TestDataGenerator(seed=42)
        
        # Test invalid crop
        request = generator.generate_invalid_request('invalid_crop')
        assert request['crop_type'] not in ['Rice', 'Wheat', 'Maize']
        
        # Test missing required field
        request = generator.generate_invalid_request('missing_required')
        required_fields = ['crop_type', 'latitude', 'longitude', 'sowing_date']
        assert not all(field in request for field in required_fields)
    
    def test_generate_edge_case_request(self):
        """Test edge case request generation"""
        generator = TestDataGenerator(seed=42)
        
        # Test null variety
        request = generator.generate_edge_case_request('null_variety')
        assert 'variety_name' in request
        assert request['variety_name'] is None
        
        # Test empty variety
        request = generator.generate_edge_case_request('empty_variety')
        assert request['variety_name'] == ""
    
    def test_get_test_locations(self):
        """Test getting test locations"""
        generator = TestDataGenerator()
        locations = generator.get_test_locations()
        
        assert len(locations) > 0
        assert all('name' in loc for loc in locations)
        assert all('latitude' in loc for loc in locations)
        assert all('longitude' in loc for loc in locations)
    
    def test_get_test_varieties(self):
        """Test getting test varieties"""
        generator = TestDataGenerator()
        
        rice_varieties = generator.get_test_varieties('Rice')
        assert len(rice_varieties) > 0
        assert 'IR-64' in rice_varieties
        
        wheat_varieties = generator.get_test_varieties('Wheat')
        assert len(wheat_varieties) > 0
        assert 'HD 3086' in wheat_varieties
    
    def test_generate_load_test_requests(self):
        """Test load test request generation"""
        generator = TestDataGenerator(seed=42)
        requests = generator.generate_load_test_requests(10)
        
        assert len(requests) == 10
        assert all('crop_type' in req for req in requests)


class TestPerformanceMetrics:
    """Test PerformanceMetrics functionality"""
    
    def test_record_request(self):
        """Test recording request metrics"""
        metrics = PerformanceMetrics()
        
        metrics.record_request(
            endpoint='/predict/yield',
            response_time_ms=150.0,
            status_code=200,
            request_size=500,
            response_size=1000
        )
        
        assert len(metrics) == 1
    
    def test_get_statistics(self):
        """Test statistics calculation"""
        metrics = PerformanceMetrics()
        
        # Record multiple requests
        for i in range(10):
            metrics.record_request(
                endpoint='/predict/yield',
                response_time_ms=100.0 + i * 10,
                status_code=200,
                request_size=500,
                response_size=1000
            )
        
        stats = metrics.get_statistics()
        
        assert stats['total_requests'] == 10
        assert stats['successful_requests'] == 10
        assert stats['failed_requests'] == 0
        assert 'response_time' in stats
        assert stats['response_time']['min_ms'] == 100.0
        assert stats['response_time']['max_ms'] == 190.0
    
    def test_get_error_rate(self):
        """Test error rate calculation"""
        metrics = PerformanceMetrics()
        
        # Record 8 successful and 2 failed requests
        for i in range(8):
            metrics.record_request('/predict/yield', 100.0, 200, 500, 1000)
        
        for i in range(2):
            metrics.record_request('/predict/yield', 100.0, 500, 500, 1000)
        
        error_rate = metrics.get_error_rate()
        assert error_rate == 0.2  # 20% error rate
    
    def test_get_throughput(self):
        """Test throughput calculation"""
        metrics = PerformanceMetrics()
        metrics.start_collection()
        
        # Record 10 requests
        for i in range(10):
            metrics.record_request('/predict/yield', 100.0, 200, 500, 1000)
        
        metrics.stop_collection()
        
        throughput = metrics.get_throughput()
        assert throughput > 0
    
    def test_export_json(self):
        """Test JSON export"""
        metrics = PerformanceMetrics()
        
        metrics.record_request('/predict/yield', 100.0, 200, 500, 1000)
        
        json_export = metrics.export_metrics('json')
        assert isinstance(json_export, str)
        assert 'summary' in json_export
        assert 'statistics' in json_export
    
    def test_get_summary(self):
        """Test summary generation"""
        metrics = PerformanceMetrics()
        
        metrics.record_request('/predict/yield', 100.0, 200, 500, 1000)
        metrics.record_request('/health', 50.0, 200, 100, 200)
        
        summary = metrics.get_summary()
        
        assert summary['total_requests'] == 2
        assert summary['successful_requests'] == 2
        assert summary['endpoints_tested'] == 2


class TestAssertions:
    """Test custom assertion functions"""
    
    def test_assert_field_exists(self):
        """Test field existence assertion"""
        response = APIResponse(
            status_code=200,
            json_data={'prediction': {'yield_tons_per_hectare': 5.5}},
            headers={},
            response_time_ms=100.0
        )
        
        # Should not raise
        assert_field_exists(response, 'prediction')
        assert_field_exists(response, 'prediction.yield_tons_per_hectare')
        
        # Should raise
        with pytest.raises(Exception):
            assert_field_exists(response, 'nonexistent')
    
    def test_assert_field_equals(self):
        """Test field value assertion"""
        response = APIResponse(
            status_code=200,
            json_data={'status': 'success'},
            headers={},
            response_time_ms=100.0
        )
        
        # Should not raise
        assert_field_equals(response, 'status', 'success')
        
        # Should raise
        with pytest.raises(Exception):
            assert_field_equals(response, 'status', 'failure')
    
    def test_assert_response_time_within(self):
        """Test response time assertion"""
        response = APIResponse(
            status_code=200,
            json_data={},
            headers={},
            response_time_ms=100.0
        )
        
        # Should not raise
        assert_response_time_within(response, 200.0)
        
        # Should raise
        with pytest.raises(Exception):
            assert_response_time_within(response, 50.0)
    
    def test_assert_yield_in_range(self):
        """Test yield range assertion"""
        response = APIResponse(
            status_code=200,
            json_data={'prediction': {'yield_tons_per_hectare': 5.5}},
            headers={},
            response_time_ms=100.0
        )
        
        # Should not raise
        assert_yield_in_range(response, 1.0, 10.0)
        
        # Should raise
        with pytest.raises(Exception):
            assert_yield_in_range(response, 6.0, 10.0)
    
    def test_assert_error_response(self):
        """Test error response assertion"""
        response = APIResponse(
            status_code=400,
            json_data={'error': 'Invalid input'},
            headers={},
            response_time_ms=100.0
        )
        
        # Should not raise
        assert_error_response(response, 400)
        
        # Should raise
        with pytest.raises(Exception):
            assert_error_response(response, 500)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
