#!/usr/bin/env python3
"""
Unit Tests for VarietySelectionService

Tests the variety selection logic including location-to-region mapping,
regional variety selection, global defaults, and caching behavior.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from variety_selection_service import VarietySelectionService


class TestVarietySelectionService(unittest.TestCase):
    """Test suite for VarietySelectionService"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mock variety database
        self.mock_variety_db = Mock()
        
        # Create service instance with mock database
        self.service = VarietySelectionService(self.mock_variety_db)

    def test_location_to_region_mapping_known_cities(self):
        """Test location-to-region mapping with known cities"""
        # Test various known cities
        test_cases = [
            ('Bhopal', 'Madhya Pradesh'),
            ('Lucknow', 'Uttar Pradesh'),
            ('Chandigarh', 'Punjab'),
            ('Patna', 'Bihar'),
            ('Delhi', 'Delhi'),
            ('Jaipur', 'Rajasthan'),
            ('Amritsar', 'Punjab'),
            ('Kanpur', 'Uttar Pradesh'),
            ('Indore', 'Madhya Pradesh'),
        ]
        
        for location, expected_region in test_cases:
            with self.subTest(location=location):
                region = self.service.map_location_to_region(location)
                self.assertEqual(region, expected_region,
                               f"Expected {location} to map to {expected_region}, got {region}")

    def test_location_to_region_mapping_unknown_location(self):
        """Test location-to-region mapping with unknown locations (fallback)"""
        # Test unknown locations should fallback to "All North India"
        unknown_locations = ['Unknown City', 'Random Place', 'XYZ Town', 'Nowhere']
        
        for location in unknown_locations:
            with self.subTest(location=location):
                region = self.service.map_location_to_region(location)
                self.assertEqual(region, 'All North India',
                               f"Expected unknown location '{location}' to fallback to 'All North India'")

    def test_location_to_region_mapping_case_insensitive(self):
        """Test case-insensitive location mapping"""
        # Test various case combinations
        test_cases = [
            ('bhopal', 'Madhya Pradesh'),
            ('BHOPAL', 'Madhya Pradesh'),
            ('BhOpAl', 'Madhya Pradesh'),
            ('lucknow', 'Uttar Pradesh'),
            ('LUCKNOW', 'Uttar Pradesh'),
            ('LuCkNoW', 'Uttar Pradesh'),
            ('chandigarh', 'Punjab'),
            ('CHANDIGARH', 'Punjab'),
            ('ChAnDiGaRh', 'Punjab'),
        ]
        
        for location, expected_region in test_cases:
            with self.subTest(location=location):
                region = self.service.map_location_to_region(location)
                self.assertEqual(region, expected_region,
                               f"Case-insensitive mapping failed for '{location}'")

    def test_location_to_region_mapping_with_whitespace(self):
        """Test location mapping handles whitespace correctly"""
        test_cases = [
            ('  Bhopal  ', 'Madhya Pradesh'),
            (' Lucknow ', 'Uttar Pradesh'),
            ('Chandigarh  ', 'Punjab'),
        ]
        
        for location, expected_region in test_cases:
            with self.subTest(location=location):
                region = self.service.map_location_to_region(location)
                self.assertEqual(region, expected_region,
                               f"Whitespace handling failed for '{location}'")

    def test_get_regional_varieties_with_matches(self):
        """Test get_regional_varieties with matching varieties"""
        # Mock database response with varieties
        mock_varieties = pd.DataFrame({
            'variety_name': ['Swarna', 'IR-64', 'Basmati 370'],
            'yield_potential': [5.8, 5.5, 4.2],
            'maturity_days': [140, 135, 130],
            'region_prevalence': ['Madhya Pradesh', 'Madhya Pradesh', 'Punjab,Haryana']
        })
        
        self.mock_variety_db.get_crop_varieties.return_value = mock_varieties
        
        # Call method
        result = self.service.get_regional_varieties('Rice', 'Madhya Pradesh')
        
        # Verify database was called correctly
        self.mock_variety_db.get_crop_varieties.assert_called_once_with(
            crop_type='Rice',
            region='Madhya Pradesh'
        )
        
        # Verify results are sorted by yield_potential (descending)
        self.assertFalse(result.empty)
        self.assertEqual(len(result), 3)
        self.assertEqual(result.iloc[0]['variety_name'], 'Swarna')
        self.assertEqual(result.iloc[0]['yield_potential'], 5.8)
        
        # Verify sorting
        yield_potentials = result['yield_potential'].tolist()
        self.assertEqual(yield_potentials, sorted(yield_potentials, reverse=True))

    def test_get_regional_varieties_no_matches(self):
        """Test get_regional_varieties with no matches"""
        # Mock database response with empty DataFrame
        self.mock_variety_db.get_crop_varieties.return_value = pd.DataFrame()
        
        # Call method
        result = self.service.get_regional_varieties('Rice', 'Unknown Region')
        
        # Verify empty DataFrame returned
        self.assertTrue(result.empty)
        self.assertEqual(len(result), 0)

    def test_get_regional_varieties_database_error(self):
        """Test get_regional_varieties handles database errors gracefully"""
        # Mock database to raise exception
        self.mock_variety_db.get_crop_varieties.side_effect = Exception("Database error")
        
        # Call method - should return empty DataFrame, not raise exception
        result = self.service.get_regional_varieties('Rice', 'Punjab')
        
        # Verify empty DataFrame returned
        self.assertTrue(result.empty)

    def test_select_default_variety_regional_success(self):
        """Test select_default_variety with regional success"""
        # Mock regional varieties
        mock_varieties = pd.DataFrame({
            'variety_name': ['Swarna', 'IR-64', 'Basmati 370'],
            'yield_potential': [5.8, 5.5, 4.2],
            'maturity_days': [140, 135, 130]
        })
        
        self.mock_variety_db.get_crop_varieties.return_value = mock_varieties
        
        # Call method
        result = self.service.select_default_variety('Rice', 'Bhopal')
        
        # Verify result structure
        self.assertIn('variety_name', result)
        self.assertIn('variety_assumed', result)
        self.assertIn('selection_metadata', result)
        
        # Verify selected variety (highest yield potential)
        self.assertEqual(result['variety_name'], 'Swarna')
        self.assertTrue(result['variety_assumed'])
        
        # Verify metadata
        metadata = result['selection_metadata']
        self.assertEqual(metadata['region'], 'Madhya Pradesh')
        self.assertEqual(metadata['reason'], 'regional_highest_yield')
        self.assertEqual(metadata['yield_potential'], 5.8)
        self.assertIn('alternatives', metadata)
        self.assertEqual(metadata['alternatives'], ['IR-64', 'Basmati 370'])

    def test_select_default_variety_fallback_to_north_india(self):
        """Test select_default_variety with fallback to 'All North India'"""
        # Mock: no varieties for specific region, but varieties for "All North India"
        def mock_get_varieties(crop_type, region):
            if region == 'Madhya Pradesh':
                return pd.DataFrame()  # No varieties for MP
            elif region == 'All North India':
                return pd.DataFrame({
                    'variety_name': ['IR-64', 'Swarna'],
                    'yield_potential': [5.5, 5.3],
                    'maturity_days': [135, 140]
                })
            return pd.DataFrame()
        
        self.mock_variety_db.get_crop_varieties.side_effect = mock_get_varieties
        
        # Call method
        result = self.service.select_default_variety('Rice', 'Bhopal')
        
        # Verify fallback was used
        self.assertEqual(result['variety_name'], 'IR-64')
        self.assertTrue(result['variety_assumed'])
        
        # Verify metadata indicates fallback
        metadata = result['selection_metadata']
        self.assertEqual(metadata['region'], 'All North India')
        self.assertEqual(metadata['reason'], 'regional_fallback')
        self.assertEqual(metadata['original_region'], 'Madhya Pradesh')
        self.assertEqual(metadata['yield_potential'], 5.5)

    def test_select_default_variety_using_global_defaults(self):
        """Test select_default_variety using global defaults"""
        # Mock: no regional varieties at all
        self.mock_variety_db.get_crop_varieties.return_value = pd.DataFrame()
        
        # Mock: global default variety exists in database
        self.mock_variety_db.get_variety_by_name.return_value = {
            'variety_name': 'IR-64',
            'yield_potential': 5.5
        }
        
        # Call method
        result = self.service.select_default_variety('Rice', 'Bhopal')
        
        # Verify global default was used
        self.assertEqual(result['variety_name'], 'IR-64')
        self.assertTrue(result['variety_assumed'])
        
        # Verify metadata indicates global default
        metadata = result['selection_metadata']
        self.assertEqual(metadata['reason'], 'global_default')
        self.assertIn('note', metadata)

    def test_get_global_default_valid_crop_types(self):
        """Test get_global_default with valid crop types"""
        # Mock database to return varieties
        def mock_get_variety(crop_type, variety_name):
            # Return the first variety in the priority list
            return {'variety_name': variety_name, 'yield_potential': 5.0}
        
        self.mock_variety_db.get_variety_by_name.side_effect = mock_get_variety
        
        # Test each crop type
        test_cases = [
            ('Rice', 'IR-64'),
            ('Wheat', 'HD 3086'),
            ('Maize', 'DHM 117')
        ]
        
        for crop_type, expected_variety in test_cases:
            with self.subTest(crop_type=crop_type):
                result = self.service.get_global_default(crop_type)
                self.assertEqual(result, expected_variety)

    def test_get_global_default_invalid_crop_type(self):
        """Test get_global_default with invalid crop type (error case)"""
        # Test invalid crop types
        invalid_crop_types = ['Barley', 'Sorghum', 'InvalidCrop', '']
        
        for crop_type in invalid_crop_types:
            with self.subTest(crop_type=crop_type):
                with self.assertRaises(ValueError) as context:
                    self.service.get_global_default(crop_type)
                
                self.assertIn('Invalid crop type', str(context.exception))

    def test_get_global_default_no_varieties_in_database(self):
        """Test get_global_default when no default varieties exist in database"""
        # Mock database to return None for all varieties
        self.mock_variety_db.get_variety_by_name.return_value = None
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.service.get_global_default('Rice')
        
        self.assertIn('No default varieties found in database', str(context.exception))

    def test_get_global_default_fallback_to_second_priority(self):
        """Test get_global_default falls back to second priority if first not found"""
        # Mock database: first variety not found, second variety found
        def mock_get_variety(crop_type, variety_name):
            if variety_name == 'IR-64':
                return None  # First priority not found
            elif variety_name == 'Basmati 370':
                return {'variety_name': variety_name, 'yield_potential': 4.2}
            return None
        
        self.mock_variety_db.get_variety_by_name.side_effect = mock_get_variety
        
        # Should return second priority
        result = self.service.get_global_default('Rice')
        self.assertEqual(result, 'Basmati 370')

    def test_location_mapping_caching_behavior(self):
        """Test location mapping caching behavior"""
        # The cache should be pre-populated during initialization
        # Verify cache contains expected mappings
        self.assertIn('bhopal', self.service._location_region_cache)
        self.assertIn('lucknow', self.service._location_region_cache)
        self.assertIn('chandigarh', self.service._location_region_cache)
        
        # Verify cache values
        self.assertEqual(self.service._location_region_cache['bhopal'], 'Madhya Pradesh')
        self.assertEqual(self.service._location_region_cache['lucknow'], 'Uttar Pradesh')
        self.assertEqual(self.service._location_region_cache['chandigarh'], 'Punjab')
        
        # Verify cache is used (no additional processing for known locations)
        region1 = self.service.map_location_to_region('Bhopal')
        region2 = self.service.map_location_to_region('Bhopal')
        self.assertEqual(region1, region2)
        self.assertEqual(region1, 'Madhya Pradesh')

    def test_location_mapping_cache_size(self):
        """Test that cache is properly initialized with all mappings"""
        # Verify cache contains all expected locations
        expected_locations = [
            'bhopal', 'lucknow', 'chandigarh', 'patna', 'delhi',
            'jaipur', 'amritsar', 'ludhiana', 'kanpur', 'agra',
            'varanasi', 'allahabad', 'prayagraj', 'gwalior', 'indore',
            'jabalpur', 'north india regional', 'north india',
            'punjab', 'haryana', 'uttar pradesh', 'up',
            'madhya pradesh', 'mp', 'bihar', 'rajasthan'
        ]
        
        for location in expected_locations:
            with self.subTest(location=location):
                self.assertIn(location, self.service._location_region_cache,
                            f"Cache missing location: {location}")

    def test_select_default_variety_with_single_alternative(self):
        """Test select_default_variety when only one variety exists (no alternatives)"""
        # Mock single variety
        mock_varieties = pd.DataFrame({
            'variety_name': ['Swarna'],
            'yield_potential': [5.8],
            'maturity_days': [140]
        })
        
        self.mock_variety_db.get_crop_varieties.return_value = mock_varieties
        
        # Call method
        result = self.service.select_default_variety('Rice', 'Bhopal')
        
        # Verify alternatives is empty list
        metadata = result['selection_metadata']
        self.assertEqual(metadata['alternatives'], [])

    def test_select_default_variety_error_handling(self):
        """Test select_default_variety error handling"""
        # Mock database to raise exception
        self.mock_variety_db.get_crop_varieties.side_effect = Exception("Database connection failed")
        self.mock_variety_db.get_variety_by_name.return_value = None
        
        # Should raise ValueError with descriptive message
        with self.assertRaises(ValueError) as context:
            self.service.select_default_variety('Rice', 'Bhopal')
        
        # Check for the actual error message
        self.assertIn('Unable to determine appropriate variety', str(context.exception))

    def test_select_default_variety_for_all_crop_types(self):
        """Test select_default_variety works for all supported crop types"""
        # Mock varieties for each crop type
        def mock_get_varieties(crop_type, region):
            varieties = {
                'Rice': pd.DataFrame({
                    'variety_name': ['Swarna', 'IR-64'],
                    'yield_potential': [5.8, 5.5]
                }),
                'Wheat': pd.DataFrame({
                    'variety_name': ['HD 3086', 'PBW 725'],
                    'yield_potential': [5.2, 5.0]
                }),
                'Maize': pd.DataFrame({
                    'variety_name': ['DHM 117', 'HQPM 1'],
                    'yield_potential': [6.5, 6.2]
                })
            }
            return varieties.get(crop_type, pd.DataFrame())
        
        self.mock_variety_db.get_crop_varieties.side_effect = mock_get_varieties
        
        # Test each crop type
        test_cases = [
            ('Rice', 'Bhopal', 'Swarna'),
            ('Wheat', 'Chandigarh', 'HD 3086'),
            ('Maize', 'Lucknow', 'DHM 117')
        ]
        
        for crop_type, location, expected_variety in test_cases:
            with self.subTest(crop_type=crop_type):
                result = self.service.select_default_variety(crop_type, location)
                self.assertEqual(result['variety_name'], expected_variety)

    def test_state_name_passthrough(self):
        """Test that state names are passed through directly"""
        # Test state names (should map to themselves)
        test_cases = [
            ('Punjab', 'Punjab'),
            ('Haryana', 'Haryana'),
            ('Uttar Pradesh', 'Uttar Pradesh'),
            ('UP', 'Uttar Pradesh'),
            ('Madhya Pradesh', 'Madhya Pradesh'),
            ('MP', 'Madhya Pradesh'),
            ('Bihar', 'Bihar'),
            ('Rajasthan', 'Rajasthan'),
        ]
        
        for location, expected_region in test_cases:
            with self.subTest(location=location):
                region = self.service.map_location_to_region(location)
                self.assertEqual(region, expected_region)

    def test_regional_identifier_mapping(self):
        """Test regional identifier mapping"""
        test_cases = [
            ('North India Regional', 'All North India'),
            ('North India', 'All North India'),
            ('north india regional', 'All North India'),
            ('NORTH INDIA', 'All North India'),
        ]
        
        for location, expected_region in test_cases:
            with self.subTest(location=location):
                region = self.service.map_location_to_region(location)
                self.assertEqual(region, expected_region)


class TestVarietySelectionServiceIntegration(unittest.TestCase):
    """Integration tests with real database (if available)"""

    def setUp(self):
        """Set up test fixtures"""
        try:
            from crop_variety_database import CropVarietyDatabase
            self.variety_db = CropVarietyDatabase()
            self.service = VarietySelectionService(self.variety_db)
            self.db_available = True
        except Exception as e:
            self.db_available = False
            self.skipTest(f"Database not available: {e}")

    def test_real_database_variety_selection(self):
        """Test variety selection with real database"""
        if not self.db_available:
            self.skipTest("Database not available")
        
        # Test real variety selection
        try:
            result = self.service.select_default_variety('Rice', 'Bhopal')
            
            # Verify result structure
            self.assertIn('variety_name', result)
            self.assertIn('variety_assumed', result)
            self.assertIn('selection_metadata', result)
            self.assertTrue(result['variety_assumed'])
            
            # Verify variety name is not empty
            self.assertIsNotNone(result['variety_name'])
            self.assertNotEqual(result['variety_name'], '')
            
        except Exception as e:
            self.fail(f"Real database variety selection failed: {e}")


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestVarietySelectionService))
    suite.addTests(loader.loadTestsFromTestCase(TestVarietySelectionServiceIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
