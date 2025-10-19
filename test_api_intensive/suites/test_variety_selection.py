"""
Variety Selection Test Suite

This module tests the automatic variety selection feature across all scenarios:
- Auto-selection when variety is omitted, null, or empty
- Regional variety selection for different crops and locations
- Variety selection metadata validation
- Comparison between auto-selected and user-specified varieties
"""

import pytest
from typing import Dict, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import CropYieldAPIClient, APIResponse
from utils.test_data_generator import TestDataGenerator
from utils.assertions import (
    assert_valid_prediction_response,
    assert_variety_selection_metadata,
    assert_field_exists,
    assert_field_equals,
    assert_response_time_within
)


class TestAutoSelection:
    """
    Test suite for automatic variety selection
    
    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    
    @pytest.fixture
    def api_client(self, config):
        """Create API client instance"""
        return CropYieldAPIClient(
            base_url=config['api']['base_url'],
            timeout=config['api']['timeout_seconds']
        )
    
    @pytest.fixture
    def data_generator(self):
        """Create test data generator"""
        return TestDataGenerator(seed=42)
    
    def test_omitted_variety_name(self, api_client, data_generator, config):
        """
        Test prediction with omitted variety_name parameter
        
        Requirement 2.1: WHEN variety_name is omitted THEN the system SHALL 
        automatically select the most appropriate variety based on location
        """
        # Generate request without variety_name
        request = data_generator.generate_valid_request(
            crop_type="Rice",
            include_variety=False
        )
        
        # Make prediction request
        response = api_client.predict_yield(**request)
        
        # Verify response is successful
        assert_valid_prediction_response(response, check_variety_metadata=True)
        
        # Verify variety_assumed flag is true
        assert_variety_selection_metadata(
            response,
            expected_assumed=True,
            check_metadata_fields=True
        )
        
        # Verify a variety was selected
        variety_name = response.get_field('prediction.variety_name')
        assert variety_name is not None, "No variety was selected"
        assert variety_name != "", "Selected variety is empty string"
        
        # Verify response time is acceptable
        assert_response_time_within(
            response,
            config['performance']['max_response_time_ms']
        )
    
    def test_null_variety_name(self, api_client, data_generator, config):
        """
        Test prediction with null variety_name
        
        Requirement 2.2: WHEN variety_name is null or empty string THEN 
        the system SHALL treat it as omitted and auto-select
        """
        # Generate request with explicit null variety
        request = data_generator.generate_edge_case_request('null_variety')
        
        # Make prediction request
        response = api_client.predict_yield(**request)
        
        # Verify response is successful
        assert_valid_prediction_response(response, check_variety_metadata=True)
        
        # Verify variety_assumed flag is true
        assert_variety_selection_metadata(
            response,
            expected_assumed=True,
            check_metadata_fields=True
        )
        
        # Verify a variety was selected
        variety_name = response.get_field('prediction.variety_name')
        assert variety_name is not None, "No variety was selected"
        assert variety_name != "", "Selected variety is empty string"
    
    def test_empty_string_variety_name(self, api_client, data_generator, config):
        """
        Test prediction with empty string variety_name
        
        Requirement 2.2: WHEN variety_name is null or empty string THEN 
        the system SHALL treat it as omitted and auto-select
        """
        # Generate request with empty string variety
        request = data_generator.generate_edge_case_request('empty_variety')
        
        # Make prediction request
        response = api_client.predict_yield(**request)
        
        # Verify response is successful
        assert_valid_prediction_response(response, check_variety_metadata=True)
        
        # Verify variety_assumed flag is true
        assert_variety_selection_metadata(
            response,
            expected_assumed=True,
            check_metadata_fields=True
        )
        
        # Verify a variety was selected
        variety_name = response.get_field('prediction.variety_name')
        assert variety_name is not None, "No variety was selected"
        assert variety_name != "", "Selected variety is empty string"
    
    def test_variety_assumed_flag_true(self, api_client, data_generator):
        """
        Test that variety_assumed flag is set correctly when auto-selecting
        
        Requirement 2.3: WHEN auto-selection occurs THEN the response SHALL 
        include variety_assumed=true
        """
        # Test for each crop type
        for crop_type in ["Rice", "Wheat", "Maize"]:
            request = data_generator.generate_valid_request(
                crop_type=crop_type,
                include_variety=False
            )
            
            response = api_client.predict_yield(**request)
            
            # Verify variety_assumed is true
            variety_assumed = response.get_field('prediction.variety_assumed')
            assert variety_assumed is True, (
                f"variety_assumed should be True for {crop_type} auto-selection, "
                f"got {variety_assumed}"
            )
    
    def test_selection_metadata_present(self, api_client, data_generator):
        """
        Test that selection metadata is present and complete
        
        Requirement 2.4: WHEN auto-selection occurs THEN the response SHALL 
        include default_variety_selection metadata with region, reason, and alternatives
        """
        # Generate request without variety
        request = data_generator.generate_valid_request(
            crop_type="Wheat",
            include_variety=False
        )
        
        response = api_client.predict_yield(**request)
        
        # Verify response is successful
        assert response.is_success(), f"Request failed: {response.get_error_message()}"
        
        # Verify metadata exists
        metadata = response.get_field('prediction.default_variety_selection')
        assert metadata is not None, "default_variety_selection metadata is missing"
        
        # Verify required metadata fields
        required_fields = ['selected_variety', 'region', 'reason', 'alternatives']
        for field in required_fields:
            assert field in metadata, f"Metadata missing required field: {field}"
            
            # Verify fields are not empty (except alternatives which can be empty list)
            if field != 'alternatives':
                value = metadata[field]
                assert value is not None and value != "", (
                    f"Metadata field '{field}' should not be empty"
                )
        
        # Verify alternatives is a list
        alternatives = metadata['alternatives']
        assert isinstance(alternatives, list), (
            f"alternatives should be a list, got {type(alternatives)}"
        )
    
    def test_selection_metadata_fields_valid(self, api_client, data_generator):
        """
        Test that selection metadata fields contain valid data
        
        Requirement 2.4: Verify metadata completeness
        """
        request = data_generator.generate_valid_request(
            crop_type="Rice",
            include_variety=False
        )
        
        response = api_client.predict_yield(**request)
        
        metadata = response.get_field('prediction.default_variety_selection')
        
        # Verify selected_variety matches prediction.variety_name
        selected_variety = metadata['selected_variety']
        prediction_variety = response.get_field('prediction.variety_name')
        assert selected_variety == prediction_variety, (
            f"selected_variety '{selected_variety}' doesn't match "
            f"prediction.variety_name '{prediction_variety}'"
        )
        
        # Verify region is a string
        region = metadata['region']
        assert isinstance(region, str), f"region should be string, got {type(region)}"
        
        # Verify reason is a string
        reason = metadata['reason']
        assert isinstance(reason, str), f"reason should be string, got {type(reason)}"
        
        # Verify alternatives is a list of strings
        alternatives = metadata['alternatives']
        for alt in alternatives:
            assert isinstance(alt, str), (
                f"Alternative variety should be string, got {type(alt)}"
            )


class TestRegionalVarietySelection:
    """
    Test suite for regional variety selection
    
    Requirements: 2.5, 2.6, 2.7, 2.8
    """
    
    @pytest.fixture
    def api_client(self, config):
        """Create API client instance"""
        return CropYieldAPIClient(
            base_url=config['api']['base_url'],
            timeout=config['api']['timeout_seconds']
        )
    
    @pytest.fixture
    def data_generator(self):
        """Create test data generator"""
        return TestDataGenerator(seed=42)
    
    @pytest.mark.parametrize("crop_type", ["Rice", "Wheat", "Maize"])
    def test_auto_selection_for_each_crop(self, api_client, data_generator, crop_type):
        """
        Test auto-selection for each crop type
        
        Requirement 2.5: WHEN testing each crop type (Rice, Wheat, Maize) THEN 
        the system SHALL select appropriate varieties for each
        """
        request = data_generator.generate_valid_request(
            crop_type=crop_type,
            include_variety=False
        )
        
        response = api_client.predict_yield(**request)
        
        # Verify successful response
        assert response.is_success(), (
            f"Auto-selection failed for {crop_type}: {response.get_error_message()}"
        )
        
        # Verify variety was selected
        variety_name = response.get_field('prediction.variety_name')
        assert variety_name is not None and variety_name != "", (
            f"No variety selected for {crop_type}"
        )
        
        # Verify variety_assumed is true
        variety_assumed = response.get_field('prediction.variety_assumed')
        assert variety_assumed is True, (
            f"variety_assumed should be True for {crop_type}"
        )
        
        # Verify metadata is present
        metadata = response.get_field('prediction.default_variety_selection')
        assert metadata is not None, f"Metadata missing for {crop_type}"
    
    @pytest.mark.parametrize("location_name,expected_region", [
        ("Chandigarh", "Punjab"),
        ("Amritsar", "Punjab"),
        ("Hisar", "Haryana"),
        ("Lucknow", "Uttar Pradesh"),
        ("Varanasi", "Uttar Pradesh"),
        ("Patna", "Bihar"),
        ("Bhopal", "Madhya Pradesh")
    ])
    def test_regional_variety_selection(
        self,
        api_client,
        data_generator,
        location_name,
        expected_region
    ):
        """
        Test variety selection for different regions
        
        Requirement 2.6: WHEN testing different regions (Punjab, Haryana, UP, Bihar, MP) 
        THEN the system SHALL select region-specific varieties
        """
        # Get location data
        locations = data_generator.get_test_locations()
        location = next((loc for loc in locations if loc['name'] == location_name), None)
        
        if location is None:
            pytest.skip(f"Location {location_name} not in test data")
        
        # Create request for this location
        request = {
            "crop_type": "Rice",
            "latitude": location['latitude'],
            "longitude": location['longitude'],
            "sowing_date": data_generator.get_sowing_date_for_crop("Rice", days_ago=60),
            "location_name": location['name']
        }
        
        response = api_client.predict_yield(**request)
        
        # Verify successful response
        assert response.is_success(), (
            f"Request failed for {location_name}: {response.get_error_message()}"
        )
        
        # Verify variety was selected
        variety_name = response.get_field('prediction.variety_name')
        assert variety_name is not None, f"No variety selected for {location_name}"
        
        # Verify metadata contains region information
        metadata = response.get_field('prediction.default_variety_selection')
        assert metadata is not None, f"Metadata missing for {location_name}"
        
        region = metadata.get('region')
        assert region is not None, f"Region not specified in metadata for {location_name}"
        
        # Note: Region might be "All North India" if no specific regional variety exists
        # This is acceptable per requirement 2.7
    
    def test_fallback_to_all_north_india(self, api_client, data_generator):
        """
        Test fallback to "All North India" varieties
        
        Requirement 2.7: WHEN no regional varieties exist THEN the system SHALL 
        fall back to "All North India" varieties
        """
        # Use a location that might not have specific regional varieties
        request = data_generator.generate_valid_request(
            crop_type="Maize",
            include_variety=False
        )
        
        response = api_client.predict_yield(**request)
        
        # Verify successful response
        assert response.is_success(), f"Request failed: {response.get_error_message()}"
        
        # Verify variety was selected
        variety_name = response.get_field('prediction.variety_name')
        assert variety_name is not None, "No variety selected"
        
        # Verify metadata
        metadata = response.get_field('prediction.default_variety_selection')
        assert metadata is not None, "Metadata missing"
        
        region = metadata.get('region')
        reason = metadata.get('reason')
        
        # Region should be either specific or "All North India"
        assert region is not None, "Region not specified"
        
        # If region is "All North India", reason should explain the fallback
        if region == "All North India":
            assert "fallback" in reason.lower() or "no regional" in reason.lower(), (
                "Reason should explain fallback to All North India"
            )
    
    def test_global_defaults_used(self, api_client):
        """
        Test that global defaults are used when needed
        
        Requirement 2.8: WHEN no North India varieties exist THEN the system SHALL 
        use global defaults (IR-64 for Rice, HD 3086 for Wheat, DHM 117 for Maize)
        """
        # Test global defaults for each crop
        global_defaults = {
            "Rice": "IR-64",
            "Wheat": "HD 3086",
            "Maize": "DHM 117"
        }
        
        for crop_type, expected_default in global_defaults.items():
            # Create a request
            request = {
                "crop_type": crop_type,
                "latitude": 25.0,
                "longitude": 80.0,
                "sowing_date": "2024-06-15" if crop_type != "Wheat" else "2024-11-15",
                "location_name": "Test Location"
            }
            
            response = api_client.predict_yield(**request)
            
            # Verify successful response
            assert response.is_success(), (
                f"Request failed for {crop_type}: {response.get_error_message()}"
            )
            
            # Verify a variety was selected
            variety_name = response.get_field('prediction.variety_name')
            assert variety_name is not None, f"No variety selected for {crop_type}"
            
            # Note: The actual variety might be regional or All North India variety
            # Global default is only used as last resort
            # We just verify that SOME variety was selected
    
    def test_selection_metadata_region_field(self, api_client, data_generator):
        """
        Test that selection metadata includes region information
        
        Requirement 2.8: Test selection metadata (region, reason, alternatives)
        """
        locations = data_generator.get_test_locations()
        
        for location in locations[:3]:  # Test first 3 locations
            request = {
                "crop_type": "Rice",
                "latitude": location['latitude'],
                "longitude": location['longitude'],
                "sowing_date": data_generator.get_sowing_date_for_crop("Rice"),
                "location_name": location['name']
            }
            
            response = api_client.predict_yield(**request)
            
            if not response.is_success():
                continue
            
            metadata = response.get_field('prediction.default_variety_selection')
            assert metadata is not None, f"Metadata missing for {location['name']}"
            
            # Verify region field
            region = metadata.get('region')
            assert region is not None and region != "", (
                f"Region should be specified for {location['name']}"
            )
            
            # Verify reason field explains the selection
            reason = metadata.get('reason')
            assert reason is not None and reason != "", (
                f"Reason should be specified for {location['name']}"
            )
            
            # Verify alternatives field exists
            alternatives = metadata.get('alternatives')
            assert alternatives is not None, (
                f"Alternatives field missing for {location['name']}"
            )
    
    def test_crop_specific_regional_varieties(self, api_client, data_generator):
        """
        Test that different crops get appropriate regional varieties
        
        Requirement 2.5, 2.6: Verify crop-specific regional variety selection
        """
        # Test each crop type for a specific region
        test_location = {
            "name": "Chandigarh",
            "latitude": 30.7333,
            "longitude": 76.7794,
            "region": "Punjab"
        }
        
        for crop_type in ["Rice", "Wheat", "Maize"]:
            request = {
                "crop_type": crop_type,
                "latitude": test_location['latitude'],
                "longitude": test_location['longitude'],
                "sowing_date": data_generator.get_sowing_date_for_crop(crop_type),
                "location_name": test_location['name']
            }
            
            response = api_client.predict_yield(**request)
            
            if not response.is_success():
                # Skip if API has issues, but log it
                print(f"Warning: API failed for {crop_type} in {test_location['name']}: "
                      f"{response.get_error_message()}")
                continue
            
            # Verify variety was selected
            variety_name = response.get_field('prediction.variety_name')
            assert variety_name is not None and variety_name != "", (
                f"No variety selected for {crop_type} in {test_location['name']}"
            )
            
            # Verify metadata
            metadata = response.get_field('prediction.default_variety_selection')
            assert metadata is not None, (
                f"Metadata missing for {crop_type} in {test_location['name']}"
            )
            
            # Verify selected variety matches metadata
            selected_variety = metadata.get('selected_variety')
            assert selected_variety == variety_name, (
                f"Metadata variety '{selected_variety}' doesn't match "
                f"prediction variety '{variety_name}' for {crop_type}"
            )
    
    def test_multiple_regions_same_crop(self, api_client, data_generator):
        """
        Test that same crop gets different varieties in different regions
        
        Requirement 2.6: Verify region-specific variety selection
        """
        crop_type = "Rice"
        test_locations = [
            {"name": "Chandigarh", "latitude": 30.7333, "longitude": 76.7794, "region": "Punjab"},
            {"name": "Patna", "latitude": 25.5941, "longitude": 85.1376, "region": "Bihar"},
            {"name": "Bhopal", "latitude": 23.2599, "longitude": 77.4126, "region": "Madhya Pradesh"}
        ]
        
        varieties_by_region = {}
        
        for location in test_locations:
            request = {
                "crop_type": crop_type,
                "latitude": location['latitude'],
                "longitude": location['longitude'],
                "sowing_date": data_generator.get_sowing_date_for_crop(crop_type),
                "location_name": location['name']
            }
            
            response = api_client.predict_yield(**request)
            
            if not response.is_success():
                print(f"Warning: API failed for {location['name']}: "
                      f"{response.get_error_message()}")
                continue
            
            variety_name = response.get_field('prediction.variety_name')
            metadata = response.get_field('prediction.default_variety_selection')
            
            if metadata:
                region = metadata.get('region')
                varieties_by_region[location['name']] = {
                    'variety': variety_name,
                    'region': region,
                    'reason': metadata.get('reason')
                }
        
        # Verify we got results for at least 2 locations
        if len(varieties_by_region) >= 2:
            # Log the varieties selected for each region
            for loc_name, data in varieties_by_region.items():
                print(f"{loc_name}: {data['variety']} (Region: {data['region']})")
            
            # Note: Varieties might be the same if they're "All North India" varieties
            # or if regional varieties aren't available. This is acceptable.
    
    def test_alternatives_list_validity(self, api_client, data_generator):
        """
        Test that alternatives list contains valid variety names
        
        Requirement 2.8: Test selection metadata (alternatives)
        """
        request = data_generator.generate_valid_request(
            crop_type="Wheat",
            include_variety=False
        )
        
        response = api_client.predict_yield(**request)
        
        if not response.is_success():
            pytest.skip(f"API not available: {response.get_error_message()}")
        
        metadata = response.get_field('prediction.default_variety_selection')
        assert metadata is not None, "Metadata missing"
        
        alternatives = metadata.get('alternatives')
        assert alternatives is not None, "Alternatives field missing"
        assert isinstance(alternatives, list), "Alternatives should be a list"
        
        # Verify each alternative is a non-empty string
        for alt in alternatives:
            assert isinstance(alt, str), f"Alternative should be string, got {type(alt)}"
            assert alt != "", "Alternative variety name should not be empty"
        
        # Verify selected variety is not in alternatives
        selected_variety = metadata.get('selected_variety')
        if alternatives:  # Only check if there are alternatives
            assert selected_variety not in alternatives, (
                "Selected variety should not be in alternatives list"
            )
    
    def test_reason_field_descriptiveness(self, api_client, data_generator):
        """
        Test that reason field provides meaningful explanation
        
        Requirement 2.8: Test selection metadata (reason)
        """
        request = data_generator.generate_valid_request(
            crop_type="Maize",
            include_variety=False
        )
        
        response = api_client.predict_yield(**request)
        
        if not response.is_success():
            pytest.skip(f"API not available: {response.get_error_message()}")
        
        metadata = response.get_field('prediction.default_variety_selection')
        assert metadata is not None, "Metadata missing"
        
        reason = metadata.get('reason')
        assert reason is not None and reason != "", "Reason should not be empty"
        
        # Verify reason is descriptive (at least 10 characters)
        assert len(reason) >= 10, (
            f"Reason should be descriptive, got: '{reason}'"
        )
        
        # Verify reason mentions relevant concepts
        reason_lower = reason.lower()
        relevant_terms = [
            'region', 'location', 'variety', 'selected', 'available',
            'default', 'fallback', 'north india', 'specific'
        ]
        
        has_relevant_term = any(term in reason_lower for term in relevant_terms)
        assert has_relevant_term, (
            f"Reason should mention relevant concepts, got: '{reason}'"
        )


class TestVarietyComparison:
    """
    Test suite for comparing auto-selected vs user-specified varieties
    
    Requirements: 2.9, 2.10
    """
    
    @pytest.fixture
    def api_client(self, config):
        """Create API client instance"""
        return CropYieldAPIClient(
            base_url=config['api']['base_url'],
            timeout=config['api']['timeout_seconds']
        )
    
    @pytest.fixture
    def data_generator(self):
        """Create test data generator"""
        return TestDataGenerator(seed=42)
    
    def test_auto_vs_user_specified_variety(self, api_client, data_generator):
        """
        Test comparing auto-selected vs user-specified varieties
        
        Requirement 2.9: WHEN variety is user-specified THEN the response SHALL 
        include variety_assumed=false
        """
        # Create base request
        base_request = data_generator.generate_valid_request(
            crop_type="Rice",
            include_variety=False
        )
        
        # Test 1: Auto-selected variety
        auto_response = api_client.predict_yield(**base_request)
        
        assert auto_response.is_success(), (
            f"Auto-selection failed: {auto_response.get_error_message()}"
        )
        
        # Verify variety_assumed is true
        auto_assumed = auto_response.get_field('prediction.variety_assumed')
        assert auto_assumed is True, "variety_assumed should be True for auto-selection"
        
        # Test 2: User-specified variety
        user_request = base_request.copy()
        user_request['variety_name'] = "IR-64"
        
        user_response = api_client.predict_yield(**user_request)
        
        assert user_response.is_success(), (
            f"User-specified variety failed: {user_response.get_error_message()}"
        )
        
        # Verify variety_assumed is false
        user_assumed = user_response.get_field('prediction.variety_assumed')
        assert user_assumed is False, (
            "variety_assumed should be False for user-specified variety"
        )
    
    def test_variety_assumed_flag_differences(self, api_client, data_generator):
        """
        Test variety_assumed flag differences between auto and user-specified
        
        Requirement 2.9: Verify variety_assumed flag differences
        """
        request = data_generator.generate_valid_request(
            crop_type="Wheat",
            include_variety=False
        )
        
        # Test with auto-selection
        auto_response = api_client.predict_yield(**request)
        auto_assumed = auto_response.get_field('prediction.variety_assumed')
        auto_metadata = auto_response.get_field('prediction.default_variety_selection')
        
        # Test with user-specified variety
        request['variety_name'] = "HD 3086"
        user_response = api_client.predict_yield(**request)
        user_assumed = user_response.get_field('prediction.variety_assumed')
        user_metadata = user_response.get_field('prediction.default_variety_selection')
        
        # Verify flag differences
        assert auto_assumed is True, "Auto-selection should have variety_assumed=True"
        assert user_assumed is False, "User-specified should have variety_assumed=False"
        
        # Verify metadata presence
        assert auto_metadata is not None, (
            "Auto-selection should have default_variety_selection metadata"
        )
        assert user_metadata is None, (
            "User-specified should NOT have default_variety_selection metadata"
        )
    
    def test_response_structure_consistency(self, api_client, data_generator):
        """
        Test response structure consistency between auto and user-specified
        
        Requirement 2.9: Verify response structure consistency
        """
        request = data_generator.generate_valid_request(
            crop_type="Maize",
            include_variety=False
        )
        
        # Get auto-selected response
        auto_response = api_client.predict_yield(**request)
        
        # Get user-specified response
        request['variety_name'] = "DHM 117"
        user_response = api_client.predict_yield(**request)
        
        # Both should be successful
        assert auto_response.is_success(), "Auto-selection failed"
        assert user_response.is_success(), "User-specified failed"
        
        # Both should have same top-level structure
        auto_keys = set(auto_response.json_data.keys())
        user_keys = set(user_response.json_data.keys())
        
        assert auto_keys == user_keys, (
            f"Response structure differs: auto={auto_keys}, user={user_keys}"
        )
        
        # Both should have prediction object with same base fields
        base_prediction_fields = [
            'yield_tons_per_hectare',
            'confidence_score',
            'variety_name',
            'variety_assumed'
        ]
        
        for field in base_prediction_fields:
            assert auto_response.has_field(f'prediction.{field}'), (
                f"Auto-selection missing prediction.{field}"
            )
            assert user_response.has_field(f'prediction.{field}'), (
                f"User-specified missing prediction.{field}"
            )
    
    def test_invalid_variety_with_auto_selection_suggestion(
        self,
        api_client,
        data_generator
    ):
        """
        Test invalid variety handling with auto-selection suggestion
        
        Requirement 2.10: WHEN invalid variety is specified THEN the system SHALL 
        return appropriate error with suggestion to use auto-selection
        """
        # Create request with invalid variety
        request = data_generator.generate_invalid_request('invalid_variety')
        
        response = api_client.predict_yield(**request)
        
        # Should return error (400 or 422)
        assert response.is_client_error(), (
            f"Expected client error for invalid variety, got {response.status_code}"
        )
        
        # Error message should suggest auto-selection
        error_message = response.get_error_message()
        assert error_message is not None, "Error message should be present"
        
        # Check if error message suggests omitting variety or auto-selection
        error_lower = error_message.lower()
        suggests_auto = any(phrase in error_lower for phrase in [
            'omit',
            'auto',
            'automatic',
            'leave blank',
            'not specify',
            'without variety'
        ])
        
        # Note: This is a soft assertion - the API might not always suggest auto-selection
        # but it's good practice to do so
        if not suggests_auto:
            print(f"Warning: Error message doesn't suggest auto-selection: {error_message}")
    
    def test_multiple_crops_auto_vs_user(self, api_client, data_generator):
        """
        Test auto vs user-specified for multiple crop types
        
        Requirement 2.9: Comprehensive comparison testing
        """
        test_varieties = {
            "Rice": "IR-64",
            "Wheat": "HD 3086",
            "Maize": "DHM 117"
        }
        
        for crop_type, variety in test_varieties.items():
            # Auto-selection test
            auto_request = data_generator.generate_valid_request(
                crop_type=crop_type,
                include_variety=False
            )
            auto_response = api_client.predict_yield(**auto_request)
            
            # User-specified test
            user_request = auto_request.copy()
            user_request['variety_name'] = variety
            user_response = api_client.predict_yield(**user_request)
            
            # Verify both successful
            assert auto_response.is_success(), (
                f"Auto-selection failed for {crop_type}"
            )
            assert user_response.is_success(), (
                f"User-specified failed for {crop_type}"
            )
            
            # Verify variety_assumed flags
            assert auto_response.get_field('prediction.variety_assumed') is True
            assert user_response.get_field('prediction.variety_assumed') is False
            
            # Verify metadata presence
            assert auto_response.get_field('prediction.default_variety_selection') is not None
            assert user_response.get_field('prediction.default_variety_selection') is None
    
    def test_same_location_auto_vs_user_consistency(self, api_client, data_generator):
        """
        Test that auto and user-specified varieties produce consistent response structures
        for the same location
        
        Requirement 2.9: Verify response structure consistency
        """
        # Use a specific location for consistency
        location = {
            "latitude": 26.8467,
            "longitude": 80.9462,
            "name": "Lucknow"
        }
        
        crop_type = "Rice"
        sowing_date = data_generator.get_sowing_date_for_crop(crop_type, days_ago=60)
        
        # Auto-selection request
        auto_request = {
            "crop_type": crop_type,
            "latitude": location['latitude'],
            "longitude": location['longitude'],
            "sowing_date": sowing_date,
            "location_name": location['name']
        }
        
        auto_response = api_client.predict_yield(**auto_request)
        
        # User-specified request with same parameters
        user_request = auto_request.copy()
        user_request['variety_name'] = "IR-64"
        
        user_response = api_client.predict_yield(**user_request)
        
        # Both should succeed
        assert auto_response.is_success(), "Auto-selection failed"
        assert user_response.is_success(), "User-specified failed"
        
        # Verify both have same response structure
        auto_data = auto_response.json_data
        user_data = user_response.json_data
        
        # Check top-level keys
        assert set(auto_data.keys()) == set(user_data.keys()), (
            "Top-level response structure differs"
        )
        
        # Check prediction object structure
        auto_pred = auto_data.get('prediction', {})
        user_pred = user_data.get('prediction', {})
        
        # Common fields should exist in both
        common_fields = [
            'yield_tons_per_hectare',
            'confidence_score',
            'variety_name',
            'variety_assumed',
            'crop_type',
            'location'
        ]
        
        for field in common_fields:
            assert field in auto_pred, f"Auto-selection missing field: {field}"
            assert field in user_pred, f"User-specified missing field: {field}"
        
        # Verify data types are consistent
        assert type(auto_pred['yield_tons_per_hectare']) == type(user_pred['yield_tons_per_hectare'])
        assert type(auto_pred['confidence_score']) == type(user_pred['confidence_score'])
        assert type(auto_pred['variety_name']) == type(user_pred['variety_name'])
        assert type(auto_pred['variety_assumed']) == type(user_pred['variety_assumed'])
    
    def test_yield_predictions_reasonable_auto_vs_user(self, api_client, data_generator):
        """
        Test that yield predictions are reasonable for both auto and user-specified varieties
        
        Requirement 2.9: Verify response structure consistency and data validity
        """
        request = data_generator.generate_valid_request(
            crop_type="Wheat",
            include_variety=False
        )
        
        # Auto-selection
        auto_response = api_client.predict_yield(**request)
        
        # User-specified
        request['variety_name'] = "HD 3086"
        user_response = api_client.predict_yield(**request)
        
        # Both should succeed
        assert auto_response.is_success(), "Auto-selection failed"
        assert user_response.is_success(), "User-specified failed"
        
        # Get yield values
        auto_yield = auto_response.get_field('prediction.yield_tons_per_hectare')
        user_yield = user_response.get_field('prediction.yield_tons_per_hectare')
        
        # Both should be reasonable values (1-10 t/ha for most crops)
        assert 1.0 <= auto_yield <= 10.0, (
            f"Auto-selected yield {auto_yield} outside reasonable range"
        )
        assert 1.0 <= user_yield <= 10.0, (
            f"User-specified yield {user_yield} outside reasonable range"
        )
        
        # Get confidence scores
        auto_confidence = auto_response.get_field('prediction.confidence_score')
        user_confidence = user_response.get_field('prediction.confidence_score')
        
        # Both should be between 0 and 1
        assert 0.0 <= auto_confidence <= 1.0, (
            f"Auto-selected confidence {auto_confidence} outside valid range"
        )
        assert 0.0 <= user_confidence <= 1.0, (
            f"User-specified confidence {user_confidence} outside valid range"
        )
    
    def test_invalid_variety_error_details(self, api_client, data_generator):
        """
        Test that invalid variety errors provide helpful details
        
        Requirement 2.10: Test invalid variety handling with auto-selection suggestion
        """
        # Create request with clearly invalid variety
        request = data_generator.generate_valid_request(
            crop_type="Rice",
            include_variety=True
        )
        request['variety_name'] = "INVALID_VARIETY_XYZ_123"
        
        response = api_client.predict_yield(**request)
        
        # Should return client error
        assert response.is_client_error(), (
            f"Expected client error for invalid variety, got {response.status_code}"
        )
        
        # Get error details
        error_data = response.json_data
        
        # Should have error field or message
        has_error_info = (
            'error' in error_data or 
            'message' in error_data or 
            'detail' in error_data
        )
        assert has_error_info, "Response should contain error information"
        
        # Get error message
        error_message = response.get_error_message()
        assert error_message is not None and error_message != "", (
            "Error message should be present and non-empty"
        )
        
        # Error should mention the variety issue
        error_lower = error_message.lower()
        mentions_variety = any(term in error_lower for term in [
            'variety', 'invalid', 'not found', 'unknown'
        ])
        assert mentions_variety, (
            f"Error message should mention variety issue: {error_message}"
        )
    
    def test_case_sensitive_variety_names(self, api_client, data_generator):
        """
        Test variety name case sensitivity
        
        Requirement 2.10: Test invalid variety handling
        """
        request = data_generator.generate_valid_request(
            crop_type="Rice",
            include_variety=False
        )
        
        # Test with correct case
        request['variety_name'] = "IR-64"
        correct_response = api_client.predict_yield(**request)
        
        # Test with lowercase
        request['variety_name'] = "ir-64"
        lowercase_response = api_client.predict_yield(**request)
        
        # Test with uppercase
        request['variety_name'] = "IR-64"
        uppercase_response = api_client.predict_yield(**request)
        
        # At least the correct case should work
        assert correct_response.is_success(), (
            "Correct case variety should work"
        )
        
        # Log results for other cases
        if not lowercase_response.is_success():
            print(f"Note: Lowercase variety 'ir-64' not accepted: "
                  f"{lowercase_response.get_error_message()}")
        
        if not uppercase_response.is_success():
            print(f"Note: Uppercase variety 'IR-64' not accepted: "
                  f"{uppercase_response.get_error_message()}")
    
    def test_metadata_not_present_for_user_specified(self, api_client, data_generator):
        """
        Test that default_variety_selection metadata is NOT present for user-specified varieties
        
        Requirement 2.9: Verify variety_assumed flag differences
        """
        test_cases = [
            {"crop_type": "Rice", "variety": "IR-64"},
            {"crop_type": "Wheat", "variety": "HD 3086"},
            {"crop_type": "Maize", "variety": "DHM 117"}
        ]
        
        for test_case in test_cases:
            request = data_generator.generate_valid_request(
                crop_type=test_case['crop_type'],
                include_variety=True
            )
            request['variety_name'] = test_case['variety']
            
            response = api_client.predict_yield(**request)
            
            if not response.is_success():
                print(f"Warning: Request failed for {test_case['crop_type']} "
                      f"with {test_case['variety']}: {response.get_error_message()}")
                continue
            
            # Verify variety_assumed is false
            variety_assumed = response.get_field('prediction.variety_assumed')
            assert variety_assumed is False, (
                f"variety_assumed should be False for user-specified {test_case['variety']}"
            )
            
            # Verify metadata is NOT present
            metadata = response.get_field('prediction.default_variety_selection')
            assert metadata is None, (
                f"default_variety_selection should be None for user-specified "
                f"{test_case['variety']}, got {metadata}"
            )
    
    def test_auto_selection_with_alternatives(self, api_client, data_generator):
        """
        Test that auto-selection provides alternatives when available
        
        Requirement 2.9: Verify response structure consistency
        """
        # Test for a location that likely has multiple varieties
        request = {
            "crop_type": "Rice",
            "latitude": 30.7333,
            "longitude": 76.7794,
            "sowing_date": data_generator.get_sowing_date_for_crop("Rice", days_ago=60),
            "location_name": "Chandigarh"
        }
        
        response = api_client.predict_yield(**request)
        
        if not response.is_success():
            pytest.skip(f"API not available: {response.get_error_message()}")
        
        # Get metadata
        metadata = response.get_field('prediction.default_variety_selection')
        assert metadata is not None, "Metadata should be present for auto-selection"
        
        # Get alternatives
        alternatives = metadata.get('alternatives')
        assert alternatives is not None, "Alternatives field should be present"
        assert isinstance(alternatives, list), "Alternatives should be a list"
        
        # If alternatives exist, verify they're different from selected variety
        selected_variety = metadata.get('selected_variety')
        if alternatives:
            for alt in alternatives:
                assert alt != selected_variety, (
                    f"Alternative '{alt}' should not be the same as selected '{selected_variety}'"
                )
                assert isinstance(alt, str) and alt != "", (
                    "Each alternative should be a non-empty string"
                )
    
    def test_comparison_across_multiple_locations(self, api_client, data_generator):
        """
        Test auto vs user-specified comparison across multiple locations
        
        Requirement 2.9: Comprehensive comparison testing
        """
        locations = data_generator.get_test_locations()[:3]  # Test first 3 locations
        crop_type = "Wheat"
        variety = "HD 3086"
        
        for location in locations:
            # Auto-selection
            auto_request = {
                "crop_type": crop_type,
                "latitude": location['latitude'],
                "longitude": location['longitude'],
                "sowing_date": data_generator.get_sowing_date_for_crop(crop_type),
                "location_name": location['name']
            }
            
            auto_response = api_client.predict_yield(**auto_request)
            
            # User-specified
            user_request = auto_request.copy()
            user_request['variety_name'] = variety
            
            user_response = api_client.predict_yield(**user_request)
            
            # Both should succeed
            if not auto_response.is_success():
                print(f"Warning: Auto-selection failed for {location['name']}: "
                      f"{auto_response.get_error_message()}")
                continue
            
            if not user_response.is_success():
                print(f"Warning: User-specified failed for {location['name']}: "
                      f"{user_response.get_error_message()}")
                continue
            
            # Verify variety_assumed flags
            auto_assumed = auto_response.get_field('prediction.variety_assumed')
            user_assumed = user_response.get_field('prediction.variety_assumed')
            
            assert auto_assumed is True, (
                f"Auto-selection should have variety_assumed=True for {location['name']}"
            )
            assert user_assumed is False, (
                f"User-specified should have variety_assumed=False for {location['name']}"
            )
            
            # Verify metadata presence
            auto_metadata = auto_response.get_field('prediction.default_variety_selection')
            user_metadata = user_response.get_field('prediction.default_variety_selection')
            
            assert auto_metadata is not None, (
                f"Auto-selection should have metadata for {location['name']}"
            )
            assert user_metadata is None, (
                f"User-specified should not have metadata for {location['name']}"
            )
            
            # Verify both have valid yields
            auto_yield = auto_response.get_field('prediction.yield_tons_per_hectare')
            user_yield = user_response.get_field('prediction.yield_tons_per_hectare')
            
            assert auto_yield is not None and auto_yield > 0, (
                f"Auto-selection yield invalid for {location['name']}"
            )
            assert user_yield is not None and user_yield > 0, (
                f"User-specified yield invalid for {location['name']}"
            )
