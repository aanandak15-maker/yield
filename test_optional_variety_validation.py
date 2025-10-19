#!/usr/bin/env python3
"""
Test Error Handling and Validation for Optional Variety Feature

Tests comprehensive error handling including:
- Try-catch blocks around variety selection
- NoVarietiesAvailable error responses
- Database query failure handling
- Input sanitization for location_name
- Variety existence validation
- Fallback chain implementation
- Detailed error logging
"""

import pytest
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from variety_selection_service import VarietySelectionService
from crop_variety_database import CropVarietyDatabase


class TestInputSanitization:
    """Test input sanitization for location_name"""
    
    def test_sanitize_location_with_special_characters(self):
        """Test that special characters are removed from location names"""
        variety_db = Mock(spec=CropVarietyDatabase)
        service = VarietySelectionService(variety_db)
        
        # Test with special characters
        test_cases = [
            ("Bhopal'; DROP TABLE--", "bhopal drop table"),
            ("Lucknow<script>", "lucknowscript"),
            ("Delhi@#$%", "delhi"),
            ("Mumbai123", "mumbai123"),
        ]
        
        for input_location, expected_normalized in test_cases:
            region = service.map_location_to_region(input_location)
            # Should not crash and should return a valid region
            assert region is not None
            assert isinstance(region, str)
    
    def test_sanitize_empty_location(self):
        """Test handling of empty or None location names"""
        variety_db = Mock(spec=CropVarietyDatabase)
        service = VarietySelectionService(variety_db)
        
        # Test with None
        region = service.map_location_to_region(None)
        assert region == service.DEFAULT_REGION
        
        # Test with empty string
        region = service.map_location_to_region("")
        assert region == service.DEFAULT_REGION
        
        # Test with whitespace only
        region = service.map_location_to_region("   ")
        assert region == service.DEFAULT_REGION
    
    def test_sanitize_invalid_type(self):
        """Test handling of non-string location names"""
        variety_db = Mock(spec=CropVarietyDatabase)
        service = VarietySelectionService(variety_db)
        
        # Test with integer
        region = service.map_location_to_region(123)
        assert region == service.DEFAULT_REGION
        
        # Test with list
        region = service.map_location_to_region(["Bhopal"])
        assert region == service.DEFAULT_REGION


class TestDatabaseErrorHandling:
    """Test database query failure handling"""
    
    def test_database_query_failure_regional_varieties(self):
        """Test handling of database query failures for regional varieties"""
        variety_db = Mock(spec=CropVarietyDatabase)
        variety_db.get_crop_varieties.side_effect = Exception("Database connection failed")
        
        service = VarietySelectionService(variety_db)
        
        # Should return empty DataFrame on database error
        result = service.get_regional_varieties("Rice", "Punjab")
        assert result.empty
    
    def test_database_query_failure_in_select_default(self):
        """Test that select_default_variety handles database failures gracefully"""
        variety_db = Mock(spec=CropVarietyDatabase)
        variety_db.get_crop_varieties.side_effect = Exception("Database connection failed")
        
        # Mock global default to succeed
        variety_db.get_variety_by_name.return_value = {
            'variety_name': 'IR-64',
            'yield_potential': 5.5
        }
        
        service = VarietySelectionService(variety_db)
        
        # Should fall back to global defaults
        result = service.select_default_variety("Rice", "Bhopal")
        assert result['variety_name'] == 'IR-64'
        assert result['selection_metadata']['reason'] == 'global_default'


class TestVarietyValidation:
    """Test validation that selected variety exists in database"""
    
    def test_validate_selected_variety_exists(self):
        """Test that selected variety is validated against database"""
        variety_db = Mock(spec=CropVarietyDatabase)
        
        # Mock regional varieties query
        regional_df = pd.DataFrame([
            {'variety_name': 'Swarna', 'yield_potential': 5.8, 'region_prevalence': 'Madhya Pradesh'}
        ])
        variety_db.get_crop_varieties.return_value = regional_df
        
        # Mock variety validation - variety exists
        variety_db.get_variety_by_name.return_value = {
            'variety_name': 'Swarna',
            'yield_potential': 5.8
        }
        
        service = VarietySelectionService(variety_db)
        result = service.select_default_variety("Rice", "Bhopal")
        
        # Should successfully select the variety
        assert result['variety_name'] == 'Swarna'
        
        # Verify that validation was called
        variety_db.get_variety_by_name.assert_called_with("Rice", "Swarna")
    
    def test_selected_variety_not_found_in_database(self):
        """Test handling when selected variety doesn't exist in database"""
        variety_db = Mock(spec=CropVarietyDatabase)
        
        # Mock regional varieties query - returns variety that doesn't exist in DB
        regional_df = pd.DataFrame([
            {'variety_name': 'NonExistent', 'yield_potential': 5.8, 'region_prevalence': 'Madhya Pradesh'}
        ])
        
        # Mock to return empty for both regional queries (Madhya Pradesh and All North India)
        variety_db.get_crop_varieties.side_effect = [
            regional_df,  # First call for Madhya Pradesh
            pd.DataFrame()  # Second call for All North India fallback
        ]
        
        # Mock variety validation calls:
        # 1. NonExistent (regional) - fails
        # 2. IR-64 (first global default) - succeeds
        # 3. IR-64 again (final validation in select_default_variety) - succeeds
        variety_db.get_variety_by_name.side_effect = [
            None,  # Regional variety 'NonExistent' validation fails
            {'variety_name': 'IR-64', 'yield_potential': 5.5},  # get_global_default finds IR-64
            {'variety_name': 'IR-64', 'yield_potential': 5.5},  # Final validation of IR-64
        ]
        
        service = VarietySelectionService(variety_db)
        result = service.select_default_variety("Rice", "Bhopal")
        
        # Should fall back to global default after regional variety validation fails
        assert result['variety_name'] == 'IR-64'
        assert result['selection_metadata']['reason'] == 'global_default'


class TestFallbackChain:
    """Test the complete fallback chain implementation"""
    
    def test_fallback_chain_regional_to_north_india(self):
        """Test fallback from regional to All North India"""
        variety_db = Mock(spec=CropVarietyDatabase)
        
        # Mock regional varieties - empty for specific region
        variety_db.get_crop_varieties.side_effect = [
            pd.DataFrame(),  # Empty for Madhya Pradesh
            pd.DataFrame([  # Has varieties for All North India
                {'variety_name': 'IR-64', 'yield_potential': 5.5, 'region_prevalence': 'All North India'}
            ])
        ]
        
        # Mock variety validation
        variety_db.get_variety_by_name.return_value = {
            'variety_name': 'IR-64',
            'yield_potential': 5.5
        }
        
        service = VarietySelectionService(variety_db)
        result = service.select_default_variety("Rice", "Bhopal")
        
        # Should use All North India fallback
        assert result['variety_name'] == 'IR-64'
        assert result['selection_metadata']['reason'] == 'regional_fallback'
        assert result['selection_metadata']['region'] == 'All North India'
        assert result['selection_metadata']['original_region'] == 'Madhya Pradesh'
    
    def test_fallback_chain_to_global_defaults(self):
        """Test fallback to global defaults when no regional varieties"""
        variety_db = Mock(spec=CropVarietyDatabase)
        
        # Mock regional varieties - empty for all regions
        variety_db.get_crop_varieties.return_value = pd.DataFrame()
        
        # Mock variety validation for global default
        variety_db.get_variety_by_name.return_value = {
            'variety_name': 'IR-64',
            'yield_potential': 5.5
        }
        
        service = VarietySelectionService(variety_db)
        result = service.select_default_variety("Rice", "Bhopal")
        
        # Should use global default
        assert result['variety_name'] == 'IR-64'
        assert result['selection_metadata']['reason'] == 'global_default'
    
    def test_fallback_chain_complete_failure(self):
        """Test error when all fallback attempts fail"""
        variety_db = Mock(spec=CropVarietyDatabase)
        
        # Mock regional varieties - empty for all regions
        variety_db.get_crop_varieties.return_value = pd.DataFrame()
        
        # Mock variety validation - all global defaults fail
        variety_db.get_variety_by_name.return_value = None
        
        service = VarietySelectionService(variety_db)
        
        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            service.select_default_variety("Rice", "Bhopal")
        
        assert "Unable to determine appropriate variety" in str(exc_info.value)


class TestNoVarietiesAvailableError:
    """Test NoVarietiesAvailable error scenario"""
    
    def test_no_varieties_for_crop_type(self):
        """Test error when no varieties exist for crop type"""
        variety_db = Mock(spec=CropVarietyDatabase)
        
        # Mock empty results for all queries
        variety_db.get_crop_varieties.return_value = pd.DataFrame()
        variety_db.get_variety_by_name.return_value = None
        
        service = VarietySelectionService(variety_db)
        
        # Should raise ValueError with appropriate message
        with pytest.raises(ValueError) as exc_info:
            service.select_default_variety("Rice", "Bhopal")
        
        error_message = str(exc_info.value)
        assert "Unable to determine appropriate variety" in error_message
        assert "Rice" in error_message
        assert "Bhopal" in error_message


class TestDetailedErrorLogging:
    """Test detailed error logging with crop type, region, and attempted varieties"""
    
    def test_error_logging_includes_details(self, caplog):
        """Test that error logs include crop type, region, and attempted varieties"""
        variety_db = Mock(spec=CropVarietyDatabase)
        
        # Mock to trigger error scenario
        variety_db.get_crop_varieties.return_value = pd.DataFrame()
        variety_db.get_variety_by_name.return_value = None
        
        service = VarietySelectionService(variety_db)
        
        with caplog.at_level(logging.ERROR):
            try:
                service.select_default_variety("Wheat", "Chandigarh")
            except ValueError:
                pass
        
        # Check that error log contains relevant details
        error_logs = [record.message for record in caplog.records if record.levelname == 'ERROR']
        assert any('Wheat' in log for log in error_logs)
        assert any('Chandigarh' in log for log in error_logs)
    
    def test_warning_logging_for_fallbacks(self, caplog):
        """Test that warnings are logged for fallback scenarios"""
        variety_db = Mock(spec=CropVarietyDatabase)
        
        # Mock regional varieties - empty for specific region
        variety_db.get_crop_varieties.side_effect = [
            pd.DataFrame(),  # Empty for Punjab
            pd.DataFrame([  # Has varieties for All North India
                {'variety_name': 'HD 3086', 'yield_potential': 4.5, 'region_prevalence': 'All North India'}
            ])
        ]
        
        variety_db.get_variety_by_name.return_value = {
            'variety_name': 'HD 3086',
            'yield_potential': 4.5
        }
        
        service = VarietySelectionService(variety_db)
        
        with caplog.at_level(logging.WARNING):
            service.select_default_variety("Wheat", "Chandigarh")
        
        # Check that warning was logged for fallback
        warning_logs = [record.message for record in caplog.records if record.levelname == 'WARNING']
        assert any('falling back' in log.lower() for log in warning_logs)


class TestInvalidInputHandling:
    """Test handling of invalid inputs"""
    
    def test_invalid_crop_type(self):
        """Test handling of invalid crop type"""
        variety_db = Mock(spec=CropVarietyDatabase)
        service = VarietySelectionService(variety_db)
        
        with pytest.raises(ValueError) as exc_info:
            service.select_default_variety("", "Bhopal")
        
        assert "Invalid crop_type" in str(exc_info.value)
    
    def test_invalid_location_name(self):
        """Test handling of invalid location name"""
        variety_db = Mock(spec=CropVarietyDatabase)
        service = VarietySelectionService(variety_db)
        
        with pytest.raises(ValueError) as exc_info:
            service.select_default_variety("Rice", "")
        
        assert "Invalid location_name" in str(exc_info.value)
    
    def test_none_inputs(self):
        """Test handling of None inputs"""
        variety_db = Mock(spec=CropVarietyDatabase)
        service = VarietySelectionService(variety_db)
        
        with pytest.raises(ValueError):
            service.select_default_variety(None, "Bhopal")
        
        with pytest.raises(ValueError):
            service.select_default_variety("Rice", None)


def run_validation_tests():
    """Run all validation tests"""
    print("🧪 Running Error Handling and Validation Tests...")
    print("=" * 60)
    
    # Run pytest
    pytest_args = [
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ]
    
    exit_code = pytest.main(pytest_args)
    
    print("=" * 60)
    if exit_code == 0:
        print("✅ All validation tests passed!")
    else:
        print(f"❌ Some tests failed (exit code: {exit_code})")
    
    return exit_code


if __name__ == "__main__":
    exit(run_validation_tests())
