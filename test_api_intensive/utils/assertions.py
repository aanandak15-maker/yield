"""
Custom Assertions for Crop Yield API Testing

This module provides domain-specific assertion functions for validating
API responses, performance metrics, and data integrity.
"""

from typing import Any, Dict, List, Optional
from .api_client import APIResponse


class AssertionError(Exception):
    """Custom assertion error with detailed messages"""
    pass


def assert_valid_prediction_response(
    response: APIResponse,
    check_variety_metadata: bool = False
) -> None:
    """
    Assert response has valid prediction structure
    
    Args:
        response: API response object
        check_variety_metadata: Whether to check for variety selection metadata
    
    Raises:
        AssertionError: If response is invalid
    """
    # Check status code
    if not response.is_success():
        raise AssertionError(
            f"Expected successful response (2xx), got {response.status_code}. "
            f"Error: {response.get_error_message()}"
        )
    
    # Check JSON data exists
    if not response.json_data:
        raise AssertionError("Response has no JSON data")
    
    # Check required top-level fields
    required_fields = ['prediction', 'metadata', 'status']
    for field in required_fields:
        if field not in response.json_data:
            raise AssertionError(f"Response missing required field: {field}")
    
    # Check prediction fields
    prediction = response.json_data.get('prediction', {})
    required_prediction_fields = [
        'yield_tons_per_hectare',
        'confidence_score',
        'variety_name'
    ]
    
    for field in required_prediction_fields:
        if field not in prediction:
            raise AssertionError(f"Prediction missing required field: {field}")
    
    # Validate data types
    yield_value = prediction.get('yield_tons_per_hectare')
    if not isinstance(yield_value, (int, float)):
        raise AssertionError(
            f"yield_tons_per_hectare must be numeric, got {type(yield_value)}"
        )
    
    confidence = prediction.get('confidence_score')
    if not isinstance(confidence, (int, float)):
        raise AssertionError(
            f"confidence_score must be numeric, got {type(confidence)}"
        )
    
    # Check confidence score range
    if not (0 <= confidence <= 1):
        raise AssertionError(
            f"confidence_score must be between 0 and 1, got {confidence}"
        )
    
    # Check variety metadata if requested
    if check_variety_metadata:
        if 'variety_assumed' not in prediction:
            raise AssertionError("Prediction missing variety_assumed field")


def assert_variety_selection_metadata(
    response: APIResponse,
    expected_assumed: bool,
    check_metadata_fields: bool = True
) -> None:
    """
    Assert variety selection metadata is correct
    
    Args:
        response: API response object
        expected_assumed: Expected value of variety_assumed flag
        check_metadata_fields: Whether to check metadata fields
    
    Raises:
        AssertionError: If metadata is invalid
    """
    if not response.is_success():
        raise AssertionError(
            f"Expected successful response, got {response.status_code}"
        )
    
    prediction = response.get_field('prediction', {})
    
    # Check variety_assumed flag
    variety_assumed = prediction.get('variety_assumed')
    if variety_assumed is None:
        raise AssertionError("Response missing variety_assumed field")
    
    if variety_assumed != expected_assumed:
        raise AssertionError(
            f"Expected variety_assumed={expected_assumed}, got {variety_assumed}"
        )
    
    # If variety was assumed, check for metadata
    if expected_assumed and check_metadata_fields:
        metadata = prediction.get('default_variety_selection')
        
        if not metadata:
            raise AssertionError(
                "Expected default_variety_selection metadata when variety_assumed=true"
            )
        
        # Check required metadata fields
        required_metadata_fields = ['selected_variety', 'region', 'reason']
        for field in required_metadata_fields:
            if field not in metadata:
                raise AssertionError(
                    f"default_variety_selection missing required field: {field}"
                )
        
        # Check alternatives field exists (can be empty list)
        if 'alternatives' not in metadata:
            raise AssertionError(
                "default_variety_selection missing alternatives field"
            )
    
    # If variety was not assumed, metadata should not be present
    if not expected_assumed:
        metadata = prediction.get('default_variety_selection')
        if metadata is not None:
            raise AssertionError(
                "default_variety_selection should not be present when variety_assumed=false"
            )


def assert_response_time_within(
    response: APIResponse,
    max_ms: float,
    message: Optional[str] = None
) -> None:
    """
    Assert response time is within acceptable range
    
    Args:
        response: API response object
        max_ms: Maximum acceptable response time in milliseconds
        message: Custom error message
    
    Raises:
        AssertionError: If response time exceeds limit
    """
    if response.response_time_ms > max_ms:
        error_msg = message or (
            f"Response time {response.response_time_ms:.2f}ms exceeds "
            f"maximum {max_ms}ms"
        )
        raise AssertionError(error_msg)


def assert_yield_in_range(
    response: APIResponse,
    min_yield: float,
    max_yield: float,
    crop_type: Optional[str] = None
) -> None:
    """
    Assert predicted yield is within reasonable range
    
    Args:
        response: API response object
        min_yield: Minimum acceptable yield (tons/hectare)
        max_yield: Maximum acceptable yield (tons/hectare)
        crop_type: Optional crop type for context
    
    Raises:
        AssertionError: If yield is out of range
    """
    if not response.is_success():
        raise AssertionError(
            f"Cannot check yield on failed response: {response.status_code}"
        )
    
    yield_value = response.get_field('prediction.yield_tons_per_hectare')
    
    if yield_value is None:
        raise AssertionError("Response missing yield_tons_per_hectare field")
    
    if not (min_yield <= yield_value <= max_yield):
        crop_msg = f" for {crop_type}" if crop_type else ""
        raise AssertionError(
            f"Yield {yield_value:.2f} t/ha{crop_msg} is outside acceptable range "
            f"[{min_yield}, {max_yield}]"
        )


def assert_error_response(
    response: APIResponse,
    expected_status_code: int,
    expected_error_field: Optional[str] = None
) -> None:
    """
    Assert error response has expected structure and code
    
    Args:
        response: API response object
        expected_status_code: Expected HTTP status code
        expected_error_field: Optional expected error field name
    
    Raises:
        AssertionError: If error response is invalid
    """
    if response.status_code != expected_status_code:
        raise AssertionError(
            f"Expected status code {expected_status_code}, got {response.status_code}"
        )
    
    # Check that response has error information
    error_message = response.get_error_message()
    if not error_message:
        raise AssertionError(
            f"Error response (status {expected_status_code}) missing error message"
        )
    
    # Check for specific error field if provided
    if expected_error_field and response.json_data:
        if expected_error_field not in response.json_data:
            raise AssertionError(
                f"Error response missing expected field: {expected_error_field}"
            )


def assert_backward_compatible(
    v6_response: APIResponse,
    v61_response: APIResponse,
    ignore_fields: Optional[List[str]] = None
) -> None:
    """
    Assert v6.1 response is backward compatible with v6.0
    
    Args:
        v6_response: Response from v6.0 API (or v6.1 with variety specified)
        v61_response: Response from v6.1 API
        ignore_fields: Fields to ignore in comparison (e.g., new fields)
    
    Raises:
        AssertionError: If responses are not compatible
    """
    if not v6_response.is_success() or not v61_response.is_success():
        raise AssertionError("Cannot compare failed responses")
    
    ignore_fields = ignore_fields or ['variety_assumed', 'default_variety_selection']
    
    # Check that all v6.0 fields exist in v6.1
    def check_fields_recursive(v6_data: Any, v61_data: Any, path: str = ""):
        if isinstance(v6_data, dict):
            for key, value in v6_data.items():
                field_path = f"{path}.{key}" if path else key
                
                # Skip ignored fields
                if any(ignored in field_path for ignored in ignore_fields):
                    continue
                
                if key not in v61_data:
                    raise AssertionError(
                        f"v6.1 response missing v6.0 field: {field_path}"
                    )
                
                # Recursively check nested structures
                check_fields_recursive(value, v61_data[key], field_path)
        
        elif isinstance(v6_data, list):
            if not isinstance(v61_data, list):
                raise AssertionError(
                    f"Field type mismatch at {path}: v6.0 is list, v6.1 is {type(v61_data)}"
                )
    
    check_fields_recursive(v6_response.json_data, v61_response.json_data)


def assert_field_exists(
    response: APIResponse,
    field_path: str,
    message: Optional[str] = None
) -> None:
    """
    Assert that a field exists in the response
    
    Args:
        response: API response object
        field_path: Dot-separated field path
        message: Custom error message
    
    Raises:
        AssertionError: If field doesn't exist
    """
    if not response.has_field(field_path):
        error_msg = message or f"Response missing field: {field_path}"
        raise Exception(error_msg)


def assert_field_equals(
    response: APIResponse,
    field_path: str,
    expected_value: Any,
    message: Optional[str] = None
) -> None:
    """
    Assert that a field has expected value
    
    Args:
        response: API response object
        field_path: Dot-separated field path
        expected_value: Expected field value
        message: Custom error message
    
    Raises:
        AssertionError: If field value doesn't match
    """
    actual_value = response.get_field(field_path)
    
    if actual_value != expected_value:
        error_msg = message or (
            f"Field {field_path}: expected {expected_value}, got {actual_value}"
        )
        raise AssertionError(error_msg)


def assert_field_type(
    response: APIResponse,
    field_path: str,
    expected_type: type,
    message: Optional[str] = None
) -> None:
    """
    Assert that a field has expected type
    
    Args:
        response: API response object
        field_path: Dot-separated field path
        expected_type: Expected Python type
        message: Custom error message
    
    Raises:
        AssertionError: If field type doesn't match
    """
    value = response.get_field(field_path)
    
    if value is None:
        raise AssertionError(f"Field {field_path} not found")
    
    if not isinstance(value, expected_type):
        error_msg = message or (
            f"Field {field_path}: expected type {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )
        raise AssertionError(error_msg)


def assert_satellite_data_valid(response: APIResponse) -> None:
    """
    Assert satellite data is within expected ranges
    
    Args:
        response: API response object
    
    Raises:
        AssertionError: If satellite data is invalid
    """
    if not response.is_success():
        raise AssertionError("Cannot validate satellite data on failed response")
    
    # Check if satellite data exists in metadata
    satellite_data = response.get_field('metadata.satellite_data')
    
    if not satellite_data:
        # Satellite data might be optional, so just return
        return
    
    # Validate NDVI (0-1 range)
    ndvi = satellite_data.get('ndvi')
    if ndvi is not None and not (0 <= ndvi <= 1):
        raise AssertionError(f"NDVI {ndvi} is outside valid range [0, 1]")
    
    # Validate FPAR (0-1 range)
    fpar = satellite_data.get('fpar')
    if fpar is not None and not (0 <= fpar <= 1):
        raise AssertionError(f"FPAR {fpar} is outside valid range [0, 1]")
    
    # Validate LAI (0-8 range typically)
    lai = satellite_data.get('lai')
    if lai is not None and not (0 <= lai <= 8):
        raise AssertionError(f"LAI {lai} is outside valid range [0, 8]")


def assert_weather_data_valid(response: APIResponse) -> None:
    """
    Assert weather data is within realistic ranges
    
    Args:
        response: API response object
    
    Raises:
        AssertionError: If weather data is invalid
    """
    if not response.is_success():
        raise AssertionError("Cannot validate weather data on failed response")
    
    # Check if weather data exists in metadata
    weather_data = response.get_field('metadata.weather_data')
    
    if not weather_data:
        # Weather data might be optional, so just return
        return
    
    # Validate temperature (-10 to 50°C)
    temp = weather_data.get('temperature')
    if temp is not None and not (-10 <= temp <= 50):
        raise AssertionError(
            f"Temperature {temp}°C is outside realistic range [-10, 50]"
        )
    
    # Validate rainfall (0-500mm)
    rainfall = weather_data.get('rainfall')
    if rainfall is not None and not (0 <= rainfall <= 500):
        raise AssertionError(
            f"Rainfall {rainfall}mm is outside realistic range [0, 500]"
        )


def assert_confidence_score_valid(response: APIResponse, min_confidence: float = 0.0) -> None:
    """
    Assert confidence score is valid and above minimum threshold
    
    Args:
        response: API response object
        min_confidence: Minimum acceptable confidence score
    
    Raises:
        AssertionError: If confidence score is invalid
    """
    confidence = response.get_field('prediction.confidence_score')
    
    if confidence is None:
        raise AssertionError("Response missing confidence_score")
    
    if not (0 <= confidence <= 1):
        raise AssertionError(
            f"Confidence score {confidence} is outside valid range [0, 1]"
        )
    
    if confidence < min_confidence:
        raise AssertionError(
            f"Confidence score {confidence} is below minimum threshold {min_confidence}"
        )


def assert_no_sensitive_data_in_error(response: APIResponse) -> None:
    """
    Assert error response doesn't expose sensitive information
    
    Args:
        response: API response object
    
    Raises:
        AssertionError: If sensitive data is exposed
    """
    if response.is_success():
        return  # Only check error responses
    
    response_text = response.raw_text.lower()
    
    # Check for common sensitive data patterns
    sensitive_patterns = [
        'api_key',
        'api key',
        'password',
        'secret',
        'token',
        '/home/',
        '/usr/',
        'traceback',
        'stack trace',
        '.py", line'
    ]
    
    for pattern in sensitive_patterns:
        if pattern in response_text:
            raise AssertionError(
                f"Error response may expose sensitive information: contains '{pattern}'"
            )


def assert_field_analysis_valid(response: APIResponse) -> None:
    """
    Assert field analysis response has valid structure
    
    Args:
        response: API response object
    
    Raises:
        AssertionError: If field analysis response is invalid
    """
    if not response.is_success():
        raise AssertionError(
            f"Expected successful response, got {response.status_code}"
        )
    
    # Check for field-specific fields
    field_area = response.get_field('prediction.field_area_hectares')
    if field_area is None:
        raise AssertionError("Field analysis missing field_area_hectares")
    
    if not isinstance(field_area, (int, float)) or field_area <= 0:
        raise AssertionError(
            f"field_area_hectares must be positive number, got {field_area}"
        )
    
    # Check for total yield
    total_yield = response.get_field('prediction.total_yield_tons')
    if total_yield is None:
        raise AssertionError("Field analysis missing total_yield_tons")
    
    if not isinstance(total_yield, (int, float)) or total_yield <= 0:
        raise AssertionError(
            f"total_yield_tons must be positive number, got {total_yield}"
        )
