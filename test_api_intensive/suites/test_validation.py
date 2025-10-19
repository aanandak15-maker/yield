"""
Validation Test Suite for Crop Yield API

This module contains tests for input validation, including invalid inputs
and edge cases to ensure the API properly validates and rejects bad data.
"""

import pytest
from utils.api_client import CropYieldAPIClient, APIResponse
from utils.test_data_generator import TestDataGenerator
from utils.assertions import (
    assert_error_response,
    assert_no_sensitive_data_in_error
)


@pytest.fixture(scope="module")
def api_client(api_base_url, api_timeout):
    """Create API client for validation tests"""
    client = CropYieldAPIClient(api_base_url, timeout=api_timeout)
    yield client
    client.close()


@pytest.fixture(scope="module")
def data_generator():
    """Create test data generator"""
    return TestDataGenerator(seed=42)


# ============================================================================
# Task 6.1: Invalid Input Tests
# ============================================================================

@pytest.mark.validation
@pytest.mark.critical
class TestInvalidCropTypes:
    """Test invalid crop type handling"""
    
    def test_lowercase_crop_type(self, api_client, data_generator):
        """Test that lowercase crop type is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['crop_type'] = 'rice'  # Should be 'Rice'
        
        response = api_client.predict_yield(**request)
        
        # Should return 400 or 422 error
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for lowercase crop, got {response.status_code}"
        
        # Should have error message
        error_msg = response.get_error_message()
        assert error_msg is not None, "Error response should have error message"
        assert 'crop' in error_msg.lower() or 'invalid' in error_msg.lower()
    
    def test_uppercase_crop_type(self, api_client, data_generator):
        """Test that all-uppercase crop type is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['crop_type'] = 'RICE'  # Should be 'Rice'
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for uppercase crop, got {response.status_code}"
    
    def test_typo_in_crop_type(self, api_client, data_generator):
        """Test that typo in crop type is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['crop_type'] = 'Ric'  # Typo
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for typo in crop, got {response.status_code}"
    
    def test_unsupported_crop_type(self, api_client, data_generator):
        """Test that unsupported crop type is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['crop_type'] = 'Barley'  # Not supported
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for unsupported crop, got {response.status_code}"
    
    def test_corn_instead_of_maize(self, api_client, data_generator):
        """Test that 'Corn' is rejected (should be 'Maize')"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['crop_type'] = 'Corn'
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for 'Corn', got {response.status_code}"


@pytest.mark.validation
@pytest.mark.critical
class TestInvalidCoordinates:
    """Test invalid coordinate handling"""
    
    def test_latitude_out_of_range_positive(self, api_client, data_generator):
        """Test that latitude > 90 is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['latitude'] = 91.0
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for lat > 90, got {response.status_code}"
        
        error_msg = response.get_error_message()
        assert error_msg is not None
        assert 'latitude' in error_msg.lower() or 'coordinate' in error_msg.lower()
    
    def test_latitude_out_of_range_negative(self, api_client, data_generator):
        """Test that latitude < -90 is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['latitude'] = -91.0
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for lat < -90, got {response.status_code}"
    
    def test_longitude_out_of_range_positive(self, api_client, data_generator):
        """Test that longitude > 180 is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['longitude'] = 181.0
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for lon > 180, got {response.status_code}"
        
        error_msg = response.get_error_message()
        assert error_msg is not None
        assert 'longitude' in error_msg.lower() or 'coordinate' in error_msg.lower()
    
    def test_longitude_out_of_range_negative(self, api_client, data_generator):
        """Test that longitude < -180 is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['longitude'] = -181.0
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for lon < -180, got {response.status_code}"
    
    def test_non_numeric_latitude(self, api_client, data_generator):
        """Test that non-numeric latitude is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        
        # Make raw request with invalid data type
        payload = {
            "crop_type": request['crop_type'],
            "latitude": "invalid",  # String instead of number
            "longitude": request['longitude'],
            "sowing_date": request['sowing_date'],
            "location_name": request['location_name']
        }
        
        response = api_client._make_request("POST", "/predict/yield", json_data=payload)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for non-numeric lat, got {response.status_code}"
    
    def test_non_numeric_longitude(self, api_client, data_generator):
        """Test that non-numeric longitude is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        
        payload = {
            "crop_type": request['crop_type'],
            "latitude": request['latitude'],
            "longitude": "invalid",  # String instead of number
            "sowing_date": request['sowing_date'],
            "location_name": request['location_name']
        }
        
        response = api_client._make_request("POST", "/predict/yield", json_data=payload)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for non-numeric lon, got {response.status_code}"
    
    def test_extremely_large_coordinates(self, api_client, data_generator):
        """Test that extremely large coordinate values are rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['latitude'] = 999.0
        request['longitude'] = 999.0
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for extreme coordinates, got {response.status_code}"


@pytest.mark.validation
@pytest.mark.critical
class TestInvalidDates:
    """Test invalid date handling"""
    
    def test_future_sowing_date(self, api_client, data_generator):
        """Test that future sowing date is rejected"""
        request = data_generator.generate_invalid_request('future_date')
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for future date, got {response.status_code}"
        
        error_msg = response.get_error_message()
        assert error_msg is not None
        assert 'date' in error_msg.lower() or 'future' in error_msg.lower()
    
    def test_wrong_date_format_slash(self, api_client, data_generator):
        """Test that date with slashes is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['sowing_date'] = '2024/06/15'  # Should be YYYY-MM-DD
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for wrong date format, got {response.status_code}"
    
    def test_wrong_date_format_dmy(self, api_client, data_generator):
        """Test that DD-MM-YYYY format is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['sowing_date'] = '15-06-2024'  # Should be YYYY-MM-DD
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for DD-MM-YYYY format, got {response.status_code}"
    
    def test_invalid_month(self, api_client, data_generator):
        """Test that invalid month (13) is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['sowing_date'] = '2024-13-01'
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for invalid month, got {response.status_code}"
    
    def test_invalid_day(self, api_client, data_generator):
        """Test that invalid day (32) is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['sowing_date'] = '2024-06-32'
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for invalid day, got {response.status_code}"
    
    def test_non_date_string(self, api_client, data_generator):
        """Test that non-date string is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['sowing_date'] = 'invalid-date'
        
        response = api_client.predict_yield(**request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for non-date string, got {response.status_code}"
    
    def test_very_old_date(self, api_client, data_generator):
        """Test that very old sowing date (> 2 years) is rejected or handled"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['sowing_date'] = '2020-06-15'  # More than 2 years old
        
        response = api_client.predict_yield(**request)
        
        # API might reject or handle with warning
        # Accept either error or success with low confidence
        if not response.is_success():
            assert response.status_code in [400, 422], \
                f"Expected 400 or 422 for very old date, got {response.status_code}"


@pytest.mark.validation
@pytest.mark.critical
class TestMissingRequiredFields:
    """Test missing required field handling"""
    
    def test_missing_crop_type(self, api_client, data_generator):
        """Test that missing crop_type is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        del request['crop_type']
        
        # Use _make_request to send incomplete payload
        response = api_client._make_request("POST", "/predict/yield", json_data=request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for missing crop_type, got {response.status_code}"
        
        error_msg = response.get_error_message()
        assert error_msg is not None
        assert 'crop' in error_msg.lower() or 'required' in error_msg.lower()
    
    def test_missing_latitude(self, api_client, data_generator):
        """Test that missing latitude is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        del request['latitude']
        
        # Use _make_request to send incomplete payload
        response = api_client._make_request("POST", "/predict/yield", json_data=request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for missing latitude, got {response.status_code}"
        
        error_msg = response.get_error_message()
        assert error_msg is not None
        assert 'latitude' in error_msg.lower() or 'required' in error_msg.lower()
    
    def test_missing_longitude(self, api_client, data_generator):
        """Test that missing longitude is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        del request['longitude']
        
        # Use _make_request to send incomplete payload
        response = api_client._make_request("POST", "/predict/yield", json_data=request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for missing longitude, got {response.status_code}"
        
        error_msg = response.get_error_message()
        assert error_msg is not None
        assert 'longitude' in error_msg.lower() or 'required' in error_msg.lower()
    
    def test_missing_sowing_date(self, api_client, data_generator):
        """Test that missing sowing_date is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        del request['sowing_date']
        
        # Use _make_request to send incomplete payload
        response = api_client._make_request("POST", "/predict/yield", json_data=request)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for missing sowing_date, got {response.status_code}"
        
        error_msg = response.get_error_message()
        assert error_msg is not None
        assert 'date' in error_msg.lower() or 'required' in error_msg.lower()
    
    def test_empty_request_body(self, api_client):
        """Test that empty request body is rejected"""
        response = api_client._make_request("POST", "/predict/yield", json_data={})
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for empty request, got {response.status_code}"
    
    def test_null_values_in_required_fields(self, api_client, data_generator):
        """Test that null values in required fields are rejected"""
        payload = {
            "crop_type": None,
            "latitude": 25.0,
            "longitude": 80.0,
            "sowing_date": "2024-06-15",
            "location_name": "Test"
        }
        
        response = api_client._make_request("POST", "/predict/yield", json_data=payload)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for null crop_type, got {response.status_code}"


@pytest.mark.validation
class TestErrorResponseQuality:
    """Test that error responses are helpful and secure"""
    
    def test_error_has_message(self, api_client, data_generator):
        """Test that error responses include helpful messages"""
        request = data_generator.generate_invalid_request('invalid_crop')
        
        response = api_client.predict_yield(**request)
        
        assert not response.is_success()
        error_msg = response.get_error_message()
        assert error_msg is not None, "Error response should have error message"
        assert len(error_msg) > 0, "Error message should not be empty"
    
    def test_error_no_sensitive_data(self, api_client, data_generator):
        """Test that error responses don't expose sensitive information"""
        request = data_generator.generate_invalid_request('invalid_crop')
        
        response = api_client.predict_yield(**request)
        
        assert not response.is_success()
        assert_no_sensitive_data_in_error(response)
    
    def test_multiple_validation_errors(self, api_client):
        """Test handling of multiple validation errors"""
        payload = {
            "crop_type": "invalid",
            "latitude": 999.0,
            "longitude": 999.0,
            "sowing_date": "invalid-date",
            "location_name": "Test"
        }
        
        response = api_client._make_request("POST", "/predict/yield", json_data=payload)
        
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for multiple errors, got {response.status_code}"
        
        # Should have error message
        error_msg = response.get_error_message()
        assert error_msg is not None



# ============================================================================
# Task 6.2: Edge Case Tests
# ============================================================================

@pytest.mark.validation
@pytest.mark.edge_case
class TestBoundaryCoordinates:
    """Test boundary coordinate values"""
    
    def test_minimum_valid_latitude(self, api_client, data_generator):
        """Test minimum valid latitude for India region"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['latitude'] = 8.0  # Southern tip of India
        request['longitude'] = 77.0
        
        response = api_client.predict_yield(**request)
        
        # Should either succeed or fail gracefully with clear message
        if not response.is_success():
            assert response.status_code in [400, 422]
            error_msg = response.get_error_message()
            assert error_msg is not None
    
    def test_maximum_valid_latitude(self, api_client, data_generator):
        """Test maximum valid latitude for India region"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['latitude'] = 37.0  # Northern tip of India
        request['longitude'] = 77.0
        
        response = api_client.predict_yield(**request)
        
        # Should either succeed or fail gracefully
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_minimum_valid_longitude(self, api_client, data_generator):
        """Test minimum valid longitude for India region"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['latitude'] = 25.0
        request['longitude'] = 68.0  # Western edge of India
        
        response = api_client.predict_yield(**request)
        
        # Should either succeed or fail gracefully
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_maximum_valid_longitude(self, api_client, data_generator):
        """Test maximum valid longitude for India region"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['latitude'] = 25.0
        request['longitude'] = 97.0  # Eastern edge of India
        
        response = api_client.predict_yield(**request)
        
        # Should either succeed or fail gracefully
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_exact_boundary_lat_90(self, api_client, data_generator):
        """Test exact boundary latitude value (90.0)"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['latitude'] = 90.0
        
        response = api_client.predict_yield(**request)
        
        # 90.0 is technically valid but likely outside service area
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_exact_boundary_lat_minus_90(self, api_client, data_generator):
        """Test exact boundary latitude value (-90.0)"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['latitude'] = -90.0
        
        response = api_client.predict_yield(**request)
        
        # -90.0 is technically valid but outside service area
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_exact_boundary_lon_180(self, api_client, data_generator):
        """Test exact boundary longitude value (180.0)"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['longitude'] = 180.0
        
        response = api_client.predict_yield(**request)
        
        # 180.0 is technically valid but outside service area
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_exact_boundary_lon_minus_180(self, api_client, data_generator):
        """Test exact boundary longitude value (-180.0)"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['longitude'] = -180.0
        
        response = api_client.predict_yield(**request)
        
        # -180.0 is technically valid but outside service area
        if not response.is_success():
            assert response.status_code in [400, 422]


@pytest.mark.validation
@pytest.mark.edge_case
class TestBoundaryDates:
    """Test boundary date values"""
    
    def test_very_recent_sowing_date(self, api_client, data_generator):
        """Test very recent sowing date (15 days ago)"""
        request = data_generator.generate_edge_case_request('recent_sowing')
        
        response = api_client.predict_yield(**request)
        
        # Should either succeed with low confidence or fail gracefully
        if response.is_success():
            # Check if confidence is appropriately low for recent sowing
            confidence = response.get_field('prediction.confidence_score')
            assert confidence is not None
        else:
            assert response.status_code in [400, 422]
            error_msg = response.get_error_message()
            assert error_msg is not None
    
    def test_sowing_date_2_years_ago(self, api_client, data_generator):
        """Test sowing date from 2 years ago"""
        request = data_generator.generate_edge_case_request('old_sowing')
        
        response = api_client.predict_yield(**request)
        
        # Should either reject or handle with appropriate warning
        if not response.is_success():
            assert response.status_code in [400, 422]
            error_msg = response.get_error_message()
            assert error_msg is not None
            assert 'date' in error_msg.lower() or 'old' in error_msg.lower()
    
    def test_sowing_date_yesterday(self, api_client, data_generator):
        """Test sowing date from yesterday"""
        from datetime import datetime, timedelta
        
        request = data_generator.generate_valid_request(include_variety=False)
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        request['sowing_date'] = yesterday
        
        response = api_client.predict_yield(**request)
        
        # Very recent sowing - should either reject or return with low confidence
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_sowing_date_today(self, api_client, data_generator):
        """Test sowing date as today"""
        from datetime import datetime
        
        request = data_generator.generate_valid_request(include_variety=False)
        today = datetime.now().strftime("%Y-%m-%d")
        request['sowing_date'] = today
        
        response = api_client.predict_yield(**request)
        
        # Same day sowing - should likely be rejected
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_sowing_date_30_days_ago(self, api_client, data_generator):
        """Test sowing date 30 days ago (minimum reasonable growth period)"""
        from datetime import datetime, timedelta
        
        request = data_generator.generate_valid_request(include_variety=False)
        date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        request['sowing_date'] = date_30_days_ago
        
        response = api_client.predict_yield(**request)
        
        # 30 days should be acceptable for most crops
        # If it fails, should be graceful
        if not response.is_success():
            assert response.status_code in [400, 422]


@pytest.mark.validation
@pytest.mark.edge_case
class TestFieldPolygonEdgeCases:
    """Test edge cases for field polygon coordinates"""
    
    def test_minimum_polygon_3_points(self, api_client, data_generator):
        """Test minimum valid polygon with 3 points"""
        request = data_generator.generate_valid_request(include_variety=False)
        
        # Generate triangle (3 points)
        field_coords = data_generator.generate_field_coordinates(
            num_points=3,
            center_lat=request['latitude'],
            center_lon=request['longitude']
        )
        
        # Remove point-specific fields and use field analysis endpoint
        payload = {
            "crop_type": request['crop_type'],
            "sowing_date": request['sowing_date'],
            "field_coordinates": field_coords
        }
        
        response = api_client.predict_field_analysis(**payload)
        
        # Should accept 3-point polygon
        if not response.is_success():
            # If it fails, should be for other reasons, not point count
            error_msg = response.get_error_message()
            assert error_msg is not None
    
    def test_polygon_with_2_points_rejected(self, api_client, data_generator):
        """Test that polygon with only 2 points is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        
        # Create invalid polygon with only 2 points
        lat = request['latitude']
        lon = request['longitude']
        field_coords = f"{lon},{lat};{lon+0.01},{lat+0.01}"
        
        payload = {
            "crop_type": request['crop_type'],
            "sowing_date": request['sowing_date'],
            "field_coordinates": field_coords
        }
        
        response = api_client.predict_field_analysis(**payload)
        
        # Should reject polygon with < 3 points
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for 2-point polygon, got {response.status_code}"
    
    def test_polygon_with_1_point_rejected(self, api_client, data_generator):
        """Test that polygon with only 1 point is rejected"""
        request = data_generator.generate_valid_request(include_variety=False)
        
        lat = request['latitude']
        lon = request['longitude']
        field_coords = f"{lon},{lat}"
        
        payload = {
            "crop_type": request['crop_type'],
            "sowing_date": request['sowing_date'],
            "field_coordinates": field_coords
        }
        
        response = api_client.predict_field_analysis(**payload)
        
        # Should reject single point
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for 1-point polygon, got {response.status_code}"
    
    def test_large_polygon_many_points(self, api_client, data_generator):
        """Test polygon with many points (100)"""
        request = data_generator.generate_valid_request(include_variety=False)
        
        # Generate polygon with 100 points
        field_coords = data_generator.generate_field_coordinates(
            num_points=100,
            center_lat=request['latitude'],
            center_lon=request['longitude']
        )
        
        payload = {
            "crop_type": request['crop_type'],
            "sowing_date": request['sowing_date'],
            "field_coordinates": field_coords
        }
        
        response = api_client.predict_field_analysis(**payload)
        
        # Should handle large polygon or reject gracefully
        if not response.is_success():
            assert response.status_code in [400, 422]


@pytest.mark.validation
@pytest.mark.edge_case
class TestSpecialCharacters:
    """Test special characters in string fields"""
    
    def test_sql_injection_in_location_name(self, api_client, data_generator):
        """Test SQL injection attempt in location_name"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['location_name'] = "Test'; DROP TABLE varieties;--"
        
        response = api_client.predict_yield(**request)
        
        # Should either sanitize and succeed, or reject
        # Should NOT cause server error
        assert response.status_code != 500, \
            "SQL injection attempt should not cause server error"
        
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_xss_attempt_in_location_name(self, api_client, data_generator):
        """Test XSS attempt in location_name"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['location_name'] = "<script>alert('xss')</script>"
        
        response = api_client.predict_yield(**request)
        
        # Should sanitize or reject, not cause server error
        assert response.status_code != 500
        
        if response.is_success():
            # If accepted, should be sanitized in response
            location = response.get_field('metadata.location_name')
            if location:
                assert '<script>' not in location
    
    def test_unicode_characters_in_location_name(self, api_client, data_generator):
        """Test Unicode characters in location_name"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['location_name'] = "भोपाल"  # Bhopal in Hindi
        
        response = api_client.predict_yield(**request)
        
        # Should handle Unicode gracefully
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_special_characters_in_variety_name(self, api_client, data_generator):
        """Test special characters in variety_name"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['variety_name'] = "Test@#$%^&*()"
        
        response = api_client.predict_yield(**request)
        
        # Should reject invalid variety or handle gracefully
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_newline_characters_in_strings(self, api_client, data_generator):
        """Test newline characters in string fields"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['location_name'] = "Test\nLocation\nName"
        
        response = api_client.predict_yield(**request)
        
        # Should handle or reject gracefully
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_null_bytes_in_strings(self, api_client, data_generator):
        """Test null bytes in string fields"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['location_name'] = "Test\x00Location"
        
        response = api_client.predict_yield(**request)
        
        # Should reject or sanitize
        if not response.is_success():
            assert response.status_code in [400, 422]


@pytest.mark.validation
@pytest.mark.edge_case
@pytest.mark.slow
class TestExtremelyLongStrings:
    """Test extremely long string inputs"""
    
    def test_very_long_location_name(self, api_client, data_generator):
        """Test very long location_name (10000 characters)"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['location_name'] = "A" * 10000
        
        response = api_client.predict_yield(**request)
        
        # Should reject with appropriate error
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for very long string, got {response.status_code}"
        
        error_msg = response.get_error_message()
        assert error_msg is not None
    
    def test_very_long_variety_name(self, api_client, data_generator):
        """Test very long variety_name (10000 characters)"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['variety_name'] = "B" * 10000
        
        response = api_client.predict_yield(**request)
        
        # Should reject with appropriate error
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for very long variety name, got {response.status_code}"
    
    def test_moderately_long_location_name(self, api_client, data_generator):
        """Test moderately long location_name (500 characters)"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['location_name'] = "A" * 500
        
        response = api_client.predict_yield(**request)
        
        # Should either accept or reject gracefully
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_empty_string_location_name(self, api_client, data_generator):
        """Test empty string for location_name"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['location_name'] = ""
        
        response = api_client.predict_yield(**request)
        
        # Should either accept empty string or reject
        if not response.is_success():
            assert response.status_code in [400, 422]


@pytest.mark.validation
@pytest.mark.edge_case
class TestNullAndEmptyValues:
    """Test null and empty value handling"""
    
    def test_explicit_null_variety(self, api_client, data_generator):
        """Test explicit null for variety_name (should trigger auto-selection)"""
        request = data_generator.generate_edge_case_request('null_variety')
        
        response = api_client.predict_yield(**request)
        
        # Should succeed with auto-selection
        if response.is_success():
            variety_assumed = response.get_field('prediction.variety_assumed')
            assert variety_assumed == True, \
                "Null variety should trigger auto-selection (variety_assumed=true)"
    
    def test_empty_string_variety(self, api_client, data_generator):
        """Test empty string for variety_name (should trigger auto-selection)"""
        request = data_generator.generate_edge_case_request('empty_variety')
        
        response = api_client.predict_yield(**request)
        
        # Should succeed with auto-selection
        if response.is_success():
            variety_assumed = response.get_field('prediction.variety_assumed')
            assert variety_assumed == True, \
                "Empty variety should trigger auto-selection (variety_assumed=true)"
    
    def test_whitespace_only_variety(self, api_client, data_generator):
        """Test whitespace-only variety_name"""
        request = data_generator.generate_valid_request(include_variety=False)
        request['variety_name'] = "   "
        
        response = api_client.predict_yield(**request)
        
        # Should either treat as empty (auto-select) or reject
        if response.is_success():
            variety_assumed = response.get_field('prediction.variety_assumed')
            # Could be treated as empty and auto-selected
            assert variety_assumed is not None
        else:
            assert response.status_code in [400, 422]


@pytest.mark.validation
@pytest.mark.edge_case
class TestCombinedEdgeCases:
    """Test combinations of edge cases"""
    
    def test_boundary_coordinates_with_recent_date(self, api_client, data_generator):
        """Test boundary coordinates with very recent sowing date"""
        from datetime import datetime, timedelta
        
        request = data_generator.generate_valid_request(include_variety=False)
        request['latitude'] = 8.0  # Boundary
        request['longitude'] = 68.0  # Boundary
        request['sowing_date'] = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
        
        response = api_client.predict_yield(**request)
        
        # Should handle gracefully
        if not response.is_success():
            assert response.status_code in [400, 422]
    
    def test_all_optional_fields_omitted(self, api_client, data_generator):
        """Test request with only required fields"""
        request = data_generator.generate_valid_request(include_variety=False)
        
        # Remove all optional fields except location_name (which might be required)
        minimal_request = {
            "crop_type": request['crop_type'],
            "latitude": request['latitude'],
            "longitude": request['longitude'],
            "sowing_date": request['sowing_date'],
            "location_name": request['location_name']
        }
        
        response = api_client.predict_yield(**minimal_request)
        
        # Should succeed with auto-selection
        if response.is_success():
            variety_assumed = response.get_field('prediction.variety_assumed')
            assert variety_assumed == True
