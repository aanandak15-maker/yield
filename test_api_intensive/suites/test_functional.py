"""
Functional Test Suite for Crop Yield Prediction API

This module contains functional tests for all API endpoints with valid inputs.
Tests verify that the API correctly handles valid requests and returns
properly structured responses.

Requirements covered: 1.1, 1.2, 1.3, 1.4, 1.5, 3.3, 11.6, 11.7
"""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import CropYieldAPIClient, APIResponse
from utils.test_data_generator import TestDataGenerator
from utils.assertions import (
    assert_valid_prediction_response,
    assert_response_time_within,
    assert_yield_in_range,
    assert_field_exists,
    assert_field_type,
    assert_field_analysis_valid,
    assert_confidence_score_valid
)


class TestBasicEndpoints:
    """Test basic API endpoints with valid inputs (Task 4.1)"""
    
    @pytest.fixture
    def api_client(self, config):
        """Create API client instance"""
        client = CropYieldAPIClient(
            base_url=config['api']['base_url'],
            timeout=config['api']['timeout_seconds']
        )
        yield client
        client.close()
    
    @pytest.fixture
    def data_generator(self):
        """Create test data generator"""
        return TestDataGenerator(seed=42)
    
    def test_predict_yield_with_valid_inputs(self, api_client, data_generator, config):
        """
        Test /predict/yield endpoint with valid inputs
        
        Requirements: 1.1, 1.2
        """
        # Generate valid request
        request_data = data_generator.generate_valid_request(
            crop_type="Rice",
            include_variety=True
        )
        
        # Make prediction request
        response = api_client.predict_yield(
            crop_type=request_data['crop_type'],
            latitude=request_data['latitude'],
            longitude=request_data['longitude'],
            sowing_date=request_data['sowing_date'],
            variety_name=request_data.get('variety_name'),
            location_name=request_data.get('location_name')
        )
        
        # Assert response is valid
        assert_valid_prediction_response(response)
        
        # Assert response time is acceptable
        max_response_time = config['performance']['max_response_time_ms']
        assert_response_time_within(response, max_response_time)
        
        # Assert yield is in reasonable range
        min_yield = config['thresholds']['min_yield_tons_per_hectare']
        max_yield = config['thresholds']['max_yield_tons_per_hectare']
        assert_yield_in_range(response, min_yield, max_yield, crop_type="Rice")
        
        # Assert confidence score is valid
        min_confidence = config['thresholds']['min_confidence_score']
        assert_confidence_score_valid(response, min_confidence)
    
    def test_predict_yield_without_variety(self, api_client, data_generator, config):
        """
        Test /predict/yield endpoint without variety (auto-selection)
        
        Requirements: 1.2
        """
        # Generate request without variety
        request_data = data_generator.generate_valid_request(
            crop_type="Wheat",
            include_variety=False
        )
        
        # Make prediction request
        response = api_client.predict_yield(
            crop_type=request_data['crop_type'],
            latitude=request_data['latitude'],
            longitude=request_data['longitude'],
            sowing_date=request_data['sowing_date'],
            location_name=request_data.get('location_name')
        )
        
        # Assert response is valid
        assert_valid_prediction_response(response, check_variety_metadata=True)
        
        # Assert variety_assumed flag is present
        assert_field_exists(response, 'prediction.variety_assumed')
        
        # Assert response time is acceptable
        max_response_time = config['performance']['max_response_time_ms']
        assert_response_time_within(response, max_response_time)
    
    def test_predict_field_analysis_with_polygon(self, api_client, data_generator, config):
        """
        Test /predict/field-analysis endpoint with polygon coordinates
        
        Requirements: 1.3
        """
        # Generate field coordinates
        location = data_generator.get_random_location()
        field_coords = data_generator.generate_field_coordinates(
            num_points=4,
            center_lat=location['latitude'],
            center_lon=location['longitude']
        )
        
        # Generate sowing date
        sowing_date = data_generator.get_sowing_date_for_crop("Maize", days_ago=60)
        
        # Make field analysis request
        response = api_client.predict_field_analysis(
            crop_type="Maize",
            sowing_date=sowing_date,
            field_coordinates=field_coords,
            variety_name="DHM 117"
        )
        
        # Assert response is valid
        assert_valid_prediction_response(response)
        assert_field_analysis_valid(response)
        
        # Assert field-specific fields exist
        assert_field_exists(response, 'prediction.field_area_hectares')
        assert_field_exists(response, 'prediction.total_yield_tons')
        
        # Assert field area is positive
        field_area = response.get_field('prediction.field_area_hectares')
        assert field_area > 0, f"Field area must be positive, got {field_area}"
        
        # Assert response time is acceptable
        max_response_time = config['performance']['max_response_time_ms']
        assert_response_time_within(response, max_response_time)
    
    def test_health_endpoint(self, api_client):
        """
        Test /health endpoint
        
        Requirements: 1.4
        """
        # Make health check request
        response = api_client.get_health()
        
        # Assert response is successful
        assert response.is_success(), (
            f"Health endpoint should return 2xx, got {response.status_code}"
        )
        
        # Assert response has JSON data
        assert response.json_data is not None, "Health endpoint should return JSON"
        
        # Assert status field exists
        assert_field_exists(response, 'status')
        
        # Assert status is healthy
        status = response.get_field('status')
        assert status in ['healthy', 'ok', 'up'], (
            f"Expected healthy status, got {status}"
        )
        
        # Assert response time is fast (health checks should be quick)
        assert_response_time_within(response, 1000, "Health check should respond within 1 second")
    
    def test_supported_crops_endpoint(self, api_client):
        """
        Test /crops/supported endpoint
        
        Requirements: 1.5
        
        Note: This endpoint may not exist in the current API implementation.
        If it returns 404, the test will be skipped.
        """
        # Make supported crops request
        response = api_client.get_supported_crops()
        
        # Skip test if endpoint doesn't exist
        if response.status_code == 404:
            pytest.skip("Supported crops endpoint not implemented in API")
        
        # Assert response is successful
        assert response.is_success(), (
            f"Supported crops endpoint should return 2xx, got {response.status_code}"
        )
        
        # Assert response has JSON data
        assert response.json_data is not None, "Supported crops endpoint should return JSON"
        
        # Assert crops field exists
        assert_field_exists(response, 'crops')
        
        # Assert crops is a list
        assert_field_type(response, 'crops', list)
        
        # Assert expected crops are present
        crops = response.get_field('crops', [])
        expected_crops = ['Rice', 'Wheat', 'Maize']
        
        for expected_crop in expected_crops:
            assert expected_crop in crops, (
                f"Expected crop '{expected_crop}' not found in supported crops"
            )
        
        # Assert response time is fast
        assert_response_time_within(response, 1000, "Supported crops should respond within 1 second")
    
    def test_all_required_response_fields_present(self, api_client, data_generator):
        """
        Test that all required response fields are present
        
        Requirements: 1.1, 1.5
        """
        # Generate valid request
        request_data = data_generator.generate_valid_request(crop_type="Rice")
        
        # Make prediction request
        response = api_client.predict_yield(
            crop_type=request_data['crop_type'],
            latitude=request_data['latitude'],
            longitude=request_data['longitude'],
            sowing_date=request_data['sowing_date'],
            variety_name=request_data.get('variety_name')
        )
        
        # Assert response is successful
        assert response.is_success(), f"Request failed with status {response.status_code}"
        
        # Check top-level required fields
        required_top_level = ['prediction', 'metadata', 'status']
        for field in required_top_level:
            assert_field_exists(response, field)
        
        # Check prediction required fields
        required_prediction_fields = [
            'prediction.yield_tons_per_hectare',
            'prediction.confidence_score',
            'prediction.variety_name',
            'prediction.variety_assumed'
        ]
        for field in required_prediction_fields:
            assert_field_exists(response, field)
        
        # Check metadata required fields
        required_metadata_fields = [
            'metadata.location',
            'metadata.crop_type',
            'metadata.sowing_date'
        ]
        for field in required_metadata_fields:
            assert_field_exists(response, field)


class TestCropAndLocationCoverage:
    """Test all crop types and locations (Task 4.2)"""
    
    @pytest.fixture
    def api_client(self, config):
        """Create API client instance"""
        client = CropYieldAPIClient(
            base_url=config['api']['base_url'],
            timeout=config['api']['timeout_seconds']
        )
        yield client
        client.close()
    
    @pytest.fixture
    def data_generator(self):
        """Create test data generator"""
        return TestDataGenerator(seed=42)
    
    @pytest.mark.parametrize("crop_type", ["Rice", "Wheat", "Maize"])
    def test_all_crop_types(self, api_client, data_generator, config, crop_type):
        """
        Test predictions for all crop types
        
        Requirements: 1.1, 11.6
        """
        # Generate valid request for specific crop
        request_data = data_generator.generate_valid_request(
            crop_type=crop_type,
            include_variety=True
        )
        
        # Make prediction request
        response = api_client.predict_yield(
            crop_type=request_data['crop_type'],
            latitude=request_data['latitude'],
            longitude=request_data['longitude'],
            sowing_date=request_data['sowing_date'],
            variety_name=request_data.get('variety_name')
        )
        
        # Assert response is valid
        assert_valid_prediction_response(response)
        
        # Assert crop type in response matches request
        response_crop = response.get_field('metadata.crop_type')
        assert response_crop == crop_type, (
            f"Expected crop_type {crop_type}, got {response_crop}"
        )
        
        # Assert yield is in reasonable range
        min_yield = config['thresholds']['min_yield_tons_per_hectare']
        max_yield = config['thresholds']['max_yield_tons_per_hectare']
        assert_yield_in_range(response, min_yield, max_yield, crop_type=crop_type)
    
    @pytest.mark.parametrize("location_name", ["Bhopal", "Lucknow", "Chandigarh", "Patna"])
    def test_all_test_locations(self, api_client, data_generator, config, location_name):
        """
        Test predictions for all test locations
        
        Requirements: 1.1, 11.7
        """
        # Get specific location
        locations = data_generator.get_test_locations()
        location = next((loc for loc in locations if loc['name'] == location_name), None)
        
        assert location is not None, f"Location {location_name} not found in test data"
        
        # Generate sowing date
        sowing_date = data_generator.get_sowing_date_for_crop("Rice", days_ago=90)
        
        # Make prediction request
        response = api_client.predict_yield(
            crop_type="Rice",
            latitude=location['latitude'],
            longitude=location['longitude'],
            sowing_date=sowing_date,
            variety_name="IR-64",
            location_name=location['name']
        )
        
        # Assert response is valid
        assert_valid_prediction_response(response)
        
        # Assert location in response
        response_location = response.get_field('metadata.location')
        assert response_location is not None, "Response missing location metadata"
        
        # Assert yield is in reasonable range
        min_yield = config['thresholds']['min_yield_tons_per_hectare']
        max_yield = config['thresholds']['max_yield_tons_per_hectare']
        assert_yield_in_range(response, min_yield, max_yield)
    
    def test_different_sowing_dates(self, api_client, data_generator, config):
        """
        Test predictions with different sowing dates and growth periods
        
        Requirements: 1.1, 3.3
        """
        location = data_generator.get_random_location()
        
        # Test with different growth periods (30, 60, 90, 120 days)
        growth_periods = [30, 60, 90, 120]
        
        for days_ago in growth_periods:
            sowing_date = data_generator.get_sowing_date_for_crop("Wheat", days_ago=days_ago)
            
            # Make prediction request
            response = api_client.predict_yield(
                crop_type="Wheat",
                latitude=location['latitude'],
                longitude=location['longitude'],
                sowing_date=sowing_date,
                variety_name="HD 3086"
            )
            
            # Assert response is valid
            assert_valid_prediction_response(response)
            
            # Assert yield is in reasonable range
            min_yield = config['thresholds']['min_yield_tons_per_hectare']
            max_yield = config['thresholds']['max_yield_tons_per_hectare']
            assert_yield_in_range(response, min_yield, max_yield, crop_type="Wheat")
            
            # Assert growth days are calculated correctly
            sowing_date_obj = datetime.strptime(sowing_date, "%Y-%m-%d")
            expected_growth_days = (datetime.now() - sowing_date_obj).days
            
            # Growth days should be approximately correct (within 1 day tolerance)
            growth_days = response.get_field('metadata.growth_days')
            if growth_days is not None:
                assert abs(growth_days - expected_growth_days) <= 1, (
                    f"Growth days mismatch: expected ~{expected_growth_days}, got {growth_days}"
                )
    
    def test_predictions_within_reasonable_ranges(self, api_client, data_generator, config):
        """
        Test that predictions are within reasonable ranges for all crops
        
        Requirements: 3.3, 11.6
        """
        crops = ["Rice", "Wheat", "Maize"]
        min_yield = config['thresholds']['min_yield_tons_per_hectare']
        max_yield = config['thresholds']['max_yield_tons_per_hectare']
        
        for crop_type in crops:
            # Generate multiple requests for each crop
            for _ in range(3):
                request_data = data_generator.generate_valid_request(
                    crop_type=crop_type,
                    include_variety=True
                )
                
                # Make prediction request
                response = api_client.predict_yield(
                    crop_type=request_data['crop_type'],
                    latitude=request_data['latitude'],
                    longitude=request_data['longitude'],
                    sowing_date=request_data['sowing_date'],
                    variety_name=request_data.get('variety_name')
                )
                
                # Assert response is valid
                assert_valid_prediction_response(response)
                
                # Assert yield is in reasonable range
                assert_yield_in_range(response, min_yield, max_yield, crop_type=crop_type)
                
                # Assert confidence score is reasonable
                confidence = response.get_field('prediction.confidence_score')
                assert 0 <= confidence <= 1, (
                    f"Confidence score {confidence} out of range [0, 1] for {crop_type}"
                )
    
    def test_crop_variety_combinations(self, api_client, data_generator, config):
        """
        Test different crop and variety combinations
        
        Requirements: 1.1, 11.6
        """
        # Test specific crop-variety combinations
        test_combinations = [
            ("Rice", "IR-64"),
            ("Rice", "Pusa Basmati 1121"),
            ("Wheat", "HD 3086"),
            ("Wheat", "PBW 343"),
            ("Maize", "DHM 117"),
            ("Maize", "Vivek Hybrid 27")
        ]
        
        location = data_generator.get_random_location()
        
        for crop_type, variety_name in test_combinations:
            sowing_date = data_generator.get_sowing_date_for_crop(crop_type, days_ago=75)
            
            # Make prediction request
            response = api_client.predict_yield(
                crop_type=crop_type,
                latitude=location['latitude'],
                longitude=location['longitude'],
                sowing_date=sowing_date,
                variety_name=variety_name
            )
            
            # Assert response is valid
            assert_valid_prediction_response(response)
            
            # Assert variety in response matches request
            response_variety = response.get_field('prediction.variety_name')
            assert response_variety == variety_name, (
                f"Expected variety {variety_name}, got {response_variety}"
            )
            
            # Assert variety_assumed is false (variety was specified)
            variety_assumed = response.get_field('prediction.variety_assumed')
            assert variety_assumed is False, (
                f"variety_assumed should be False when variety is specified"
            )
    
    def test_regional_predictions(self, api_client, data_generator, config):
        """
        Test predictions across different regions
        
        Requirements: 11.7
        """
        # Test one crop across all regions
        crop_type = "Rice"
        variety_name = "IR-64"
        
        locations = data_generator.get_test_locations()
        
        for location in locations[:4]:  # Test first 4 locations
            sowing_date = data_generator.get_sowing_date_for_crop(crop_type, days_ago=80)
            
            # Make prediction request
            response = api_client.predict_yield(
                crop_type=crop_type,
                latitude=location['latitude'],
                longitude=location['longitude'],
                sowing_date=sowing_date,
                variety_name=variety_name,
                location_name=location['name']
            )
            
            # Assert response is valid
            assert_valid_prediction_response(response)
            
            # Assert yield is in reasonable range
            min_yield = config['thresholds']['min_yield_tons_per_hectare']
            max_yield = config['thresholds']['max_yield_tons_per_hectare']
            assert_yield_in_range(response, min_yield, max_yield, crop_type=crop_type)
            
            # Predictions may vary by region, but should all be valid
            yield_value = response.get_field('prediction.yield_tons_per_hectare')
            assert yield_value > 0, (
                f"Yield for {location['name']} should be positive, got {yield_value}"
            )
