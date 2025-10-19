"""
Test utilities for Crop Yield API intensive testing

This package provides core utilities for API testing including:
- API client wrapper with retry logic and timing
- Test data generators for valid, invalid, and edge cases
- Custom assertions for domain-specific validation
- Performance metrics collection and analysis
"""

from .api_client import CropYieldAPIClient, APIResponse
from .test_data_generator import TestDataGenerator
from .assertions import (
    assert_valid_prediction_response,
    assert_variety_selection_metadata,
    assert_response_time_within,
    assert_yield_in_range,
    assert_error_response,
    assert_backward_compatible,
    assert_field_exists,
    assert_field_equals,
    assert_field_type,
    assert_satellite_data_valid,
    assert_weather_data_valid,
    assert_confidence_score_valid,
    assert_no_sensitive_data_in_error,
    assert_field_analysis_valid
)
from .performance_metrics import PerformanceMetrics, RequestMetric

__all__ = [
    # API Client
    'CropYieldAPIClient',
    'APIResponse',
    
    # Test Data Generator
    'TestDataGenerator',
    
    # Assertions
    'assert_valid_prediction_response',
    'assert_variety_selection_metadata',
    'assert_response_time_within',
    'assert_yield_in_range',
    'assert_error_response',
    'assert_backward_compatible',
    'assert_field_exists',
    'assert_field_equals',
    'assert_field_type',
    'assert_satellite_data_valid',
    'assert_weather_data_valid',
    'assert_confidence_score_valid',
    'assert_no_sensitive_data_in_error',
    'assert_field_analysis_valid',
    
    # Performance Metrics
    'PerformanceMetrics',
    'RequestMetric'
]
