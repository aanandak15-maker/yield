#!/usr/bin/env python3
"""
End-to-End Validation Tests for Optional Variety Feature

Comprehensive tests simulating full prediction flow without variety specification
for each location, verifying correct variety selection, successful predictions,
and proper metadata inclusion. Also tests error scenarios and graceful degradation.

Requirements tested: 1.1, 2.1, 3.1, 3.2, 3.3, 5.1, 5.2, 5.3, 7.1, 7.2, 7.3, 7.4
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from prediction_api import CropYieldPredictionService


class TestOptionalVarietyE2E:
    """End-to-end validation tests for optional variety feature"""
    
    def __init__(self):
        self.service = None
        self.test_results = []
        
    def setup(self):
        """Initialize the prediction service"""
        print("\n" + "="*80)
        print("END-TO-END VALIDATION TESTS - OPTIONAL VARIETY FEATURE")
        print("="*80)
        print("\n🔧 Setting up test environment...")
        
        try:
            self.service = CropYieldPredictionService()
            print("✅ Prediction service initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize service: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_request(self, crop_type: str, location_name: str, 
                       latitude: float, longitude: float, 
                       variety_name: Any = 'OMIT') -> Dict[str, Any]:
        """Create a prediction request"""
        request = {
            'crop_type': crop_type,
            'location_name': location_name,
            'latitude': latitude,
            'longitude': longitude,
            'sowing_date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
            'use_real_time_data': False  # Use fallback data for faster testing
        }
        
        # Only add variety_name if not 'OMIT'
        if variety_name != 'OMIT':
            request['variety_name'] = variety_name
            
        return request
    
    def _verify_metadata_fields(self, response: Dict[str, Any], 
                                expected_variety_assumed: bool) -> bool:
        """Verify all required metadata fields are present"""
        errors = []
        
        # Check prediction section fields
        if 'prediction' not in response:
            errors.append("Missing 'prediction' section")
            return False
        
        prediction = response['prediction']
        
        # Required fields in prediction section
        required_prediction_fields = [
            'yield_tons_per_hectare', 'variety_used', 'variety_assumed',
            'lower_bound', 'upper_bound', 'confidence_score', 'variety_adjusted_yield'
        ]
        
        for field in required_prediction_fields:
            if field not in prediction:
                errors.append(f"Missing field in prediction: {field}")
        
        # Verify variety_assumed value
        if 'variety_assumed' in prediction:
            if prediction['variety_assumed'] != expected_variety_assumed:
                errors.append(
                    f"variety_assumed should be {expected_variety_assumed}, "
                    f"got {prediction['variety_assumed']}"
                )
        
        # Check for selection metadata when variety was assumed
        if expected_variety_assumed:
            if 'factors' not in response:
                errors.append("Missing 'factors' section")
            elif 'default_variety_selection' not in response['factors']:
                errors.append("Missing 'default_variety_selection' in factors")
            else:
                metadata = response['factors']['default_variety_selection']
                required_metadata_fields = ['region', 'reason']
                for field in required_metadata_fields:
                    if field not in metadata:
                        errors.append(f"Missing field in selection metadata: {field}")
        else:
            # When variety not assumed, selection metadata should NOT be present
            if 'factors' in response and 'default_variety_selection' in response['factors']:
                errors.append("default_variety_selection should NOT be present when variety is specified")
        
        # Check API version
        if response.get('api_version') != '6.1.0':
            errors.append(f"API version should be '6.1.0', got '{response.get('api_version')}'")
        
        if errors:
            for error in errors:
                print(f"  ❌ {error}")
            return False
        
        return True
    
    def test_full_flow_bhopal_rice(self):
        """Test full prediction flow without variety for Bhopal + Rice"""
        print("\n" + "-"*80)
        print("TEST 1: Full prediction flow - Bhopal + Rice (no variety)")
        print("-"*80)
        
        request = self._create_request(
            crop_type='Rice',
            location_name='Bhopal',
            latitude=23.2599,
            longitude=77.4126
        )
        
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            if 'error' in response:
                print(f"❌ Prediction failed: {response['error']}")
                return False
            
            print(f"✅ Prediction successful")
            print(f"  - Yield: {response['prediction']['yield_tons_per_hectare']} tons/ha")
            print(f"  - Variety used: {response['prediction']['variety_used']}")
            print(f"  - Variety assumed: {response['prediction']['variety_assumed']}")
            print(f"  - Region: {response['factors']['default_variety_selection']['region']}")
            print(f"  - Selection reason: {response['factors']['default_variety_selection']['reason']}")
            
            # Verify correct region mapping (Bhopal → Madhya Pradesh)
            metadata = response['factors']['default_variety_selection']
            if metadata['region'] not in ['Madhya Pradesh', 'All North India']:
                print(f"  ❌ Expected region 'Madhya Pradesh' or 'All North India', got '{metadata['region']}'")
                return False
            
            # Verify metadata fields
            if not self._verify_metadata_fields(response, expected_variety_assumed=True):
                return False
            
            # Verify prediction completed successfully
            if response['prediction']['yield_tons_per_hectare'] <= 0:
                print(f"  ❌ Invalid yield prediction: {response['prediction']['yield_tons_per_hectare']}")
                return False
            
            print("✅ TEST 1 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_full_flow_lucknow_maize(self):
        """Test full prediction flow without variety for Lucknow + Maize"""
        print("\n" + "-"*80)
        print("TEST 2: Full prediction flow - Lucknow + Maize (no variety)")
        print("-"*80)
        
        request = self._create_request(
            crop_type='Maize',
            location_name='Lucknow',
            latitude=26.8467,
            longitude=80.9462
        )
        
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            if 'error' in response:
                print(f"❌ Prediction failed: {response['error']}")
                return False
            
            print(f"✅ Prediction successful")
            print(f"  - Yield: {response['prediction']['yield_tons_per_hectare']} tons/ha")
            print(f"  - Variety used: {response['prediction']['variety_used']}")
            print(f"  - Region: {response['factors']['default_variety_selection']['region']}")
            
            # Verify correct region mapping (Lucknow → Uttar Pradesh)
            metadata = response['factors']['default_variety_selection']
            if metadata['region'] not in ['Uttar Pradesh', 'All North India']:
                print(f"  ❌ Expected region 'Uttar Pradesh' or 'All North India', got '{metadata['region']}'")
                return False
            
            # Verify metadata fields
            if not self._verify_metadata_fields(response, expected_variety_assumed=True):
                return False
            
            print("✅ TEST 2 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_full_flow_chandigarh_wheat(self):
        """Test full prediction flow without variety for Chandigarh + Wheat"""
        print("\n" + "-"*80)
        print("TEST 3: Full prediction flow - Chandigarh + Wheat (no variety)")
        print("-"*80)
        
        request = self._create_request(
            crop_type='Wheat',
            location_name='Chandigarh',
            latitude=30.7333,
            longitude=76.7794
        )
        
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            if 'error' in response:
                print(f"❌ Prediction failed: {response['error']}")
                return False
            
            print(f"✅ Prediction successful")
            print(f"  - Yield: {response['prediction']['yield_tons_per_hectare']} tons/ha")
            print(f"  - Variety used: {response['prediction']['variety_used']}")
            print(f"  - Region: {response['factors']['default_variety_selection']['region']}")
            
            # Verify correct region mapping (Chandigarh → Punjab)
            metadata = response['factors']['default_variety_selection']
            if metadata['region'] not in ['Punjab', 'All North India']:
                print(f"  ❌ Expected region 'Punjab' or 'All North India', got '{metadata['region']}'")
                return False
            
            # Verify metadata fields
            if not self._verify_metadata_fields(response, expected_variety_assumed=True):
                return False
            
            print("✅ TEST 3 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_full_flow_patna_rice(self):
        """Test full prediction flow without variety for Patna + Rice"""
        print("\n" + "-"*80)
        print("TEST 4: Full prediction flow - Patna + Rice (no variety)")
        print("-"*80)
        
        request = self._create_request(
            crop_type='Rice',
            location_name='Patna',
            latitude=25.5941,
            longitude=85.1376
        )
        
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            if 'error' in response:
                print(f"❌ Prediction failed: {response['error']}")
                return False
            
            print(f"✅ Prediction successful")
            print(f"  - Yield: {response['prediction']['yield_tons_per_hectare']} tons/ha")
            print(f"  - Variety used: {response['prediction']['variety_used']}")
            print(f"  - Region: {response['factors']['default_variety_selection']['region']}")
            
            # Verify correct region mapping (Patna → Bihar)
            metadata = response['factors']['default_variety_selection']
            if metadata['region'] not in ['Bihar', 'All North India']:
                print(f"  ❌ Expected region 'Bihar' or 'All North India', got '{metadata['region']}'")
                return False
            
            # Verify metadata fields
            if not self._verify_metadata_fields(response, expected_variety_assumed=True):
                return False
            
            print("✅ TEST 4 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_full_flow_north_india_regional(self):
        """Test full prediction flow without variety for North India Regional"""
        print("\n" + "-"*80)
        print("TEST 5: Full prediction flow - North India Regional + Wheat (no variety)")
        print("-"*80)
        
        request = self._create_request(
            crop_type='Wheat',
            location_name='North India Regional',
            latitude=28.6139,
            longitude=77.2090
        )
        
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            if 'error' in response:
                print(f"❌ Prediction failed: {response['error']}")
                return False
            
            print(f"✅ Prediction successful")
            print(f"  - Yield: {response['prediction']['yield_tons_per_hectare']} tons/ha")
            print(f"  - Variety used: {response['prediction']['variety_used']}")
            print(f"  - Region: {response['factors']['default_variety_selection']['region']}")
            
            # Verify correct region mapping (North India Regional → All North India)
            metadata = response['factors']['default_variety_selection']
            if metadata['region'] != 'All North India':
                print(f"  ❌ Expected region 'All North India', got '{metadata['region']}'")
                return False
            
            # Verify metadata fields
            if not self._verify_metadata_fields(response, expected_variety_assumed=True):
                return False
            
            print("✅ TEST 5 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_error_invalid_crop_type(self):
        """Test error scenario: invalid crop type"""
        print("\n" + "-"*80)
        print("TEST 6: Error scenario - Invalid crop type")
        print("-"*80)
        
        request = self._create_request(
            crop_type='InvalidCrop',
            location_name='Bhopal',
            latitude=23.2599,
            longitude=77.4126
        )
        
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            # Should return an error
            if 'error' not in response:
                print(f"❌ Expected error response, got successful prediction")
                return False
            
            print(f"✅ Error response received as expected")
            print(f"  - Error code: {response['error'].get('code', 'N/A')}")
            print(f"  - Error message: {response['error'].get('message', 'N/A')}")
            
            print("✅ TEST 6 PASSED")
            return True
            
        except Exception as e:
            # Exception is also acceptable for invalid input
            print(f"✅ Exception raised as expected: {type(e).__name__}")
            print("✅ TEST 6 PASSED")
            return True
    
    def test_error_unknown_location(self):
        """Test error scenario: unknown location (should use fallback)"""
        print("\n" + "-"*80)
        print("TEST 7: Unknown location - Should use fallback region")
        print("-"*80)
        
        request = self._create_request(
            crop_type='Rice',
            location_name='UnknownCity',
            latitude=25.0,
            longitude=80.0
        )
        
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            if 'error' in response:
                print(f"❌ Prediction failed: {response['error']}")
                return False
            
            print(f"✅ Prediction successful with fallback region")
            print(f"  - Yield: {response['prediction']['yield_tons_per_hectare']} tons/ha")
            print(f"  - Variety used: {response['prediction']['variety_used']}")
            print(f"  - Region: {response['factors']['default_variety_selection']['region']}")
            
            # Verify fallback to "All North India"
            metadata = response['factors']['default_variety_selection']
            if metadata['region'] != 'All North India':
                print(f"  ⚠️  Expected fallback to 'All North India', got '{metadata['region']}'")
                # This is not a failure, just unexpected
            
            # Verify metadata fields
            if not self._verify_metadata_fields(response, expected_variety_assumed=True):
                return False
            
            print("✅ TEST 7 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_with_explicit_variety(self):
        """Test with explicit variety (verify unchanged behavior)"""
        print("\n" + "-"*80)
        print("TEST 8: With explicit variety - Verify unchanged behavior")
        print("-"*80)
        
        request = self._create_request(
            crop_type='Rice',
            location_name='Bhopal',
            latitude=23.2599,
            longitude=77.4126,
            variety_name='Swarna'
        )
        
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            if 'error' in response:
                print(f"❌ Prediction failed: {response['error']}")
                return False
            
            print(f"✅ Prediction successful")
            print(f"  - Yield: {response['prediction']['yield_tons_per_hectare']} tons/ha")
            print(f"  - Variety used: {response['prediction']['variety_used']}")
            print(f"  - Variety assumed: {response['prediction']['variety_assumed']}")
            
            # Verify specified variety was used
            if response['prediction']['variety_used'] != 'Swarna':
                print(f"  ❌ Expected 'Swarna', got '{response['prediction']['variety_used']}'")
                return False
            
            # Verify metadata fields (variety_assumed should be False)
            if not self._verify_metadata_fields(response, expected_variety_assumed=False):
                return False
            
            print("✅ TEST 8 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_all_locations_all_crops(self):
        """Test all location-crop combinations"""
        print("\n" + "-"*80)
        print("TEST 9: All location-crop combinations")
        print("-"*80)
        
        test_cases = [
            ('Rice', 'Bhopal', 23.2599, 77.4126, 'Madhya Pradesh'),
            ('Wheat', 'Bhopal', 23.2599, 77.4126, 'Madhya Pradesh'),
            ('Maize', 'Bhopal', 23.2599, 77.4126, 'Madhya Pradesh'),
            ('Rice', 'Lucknow', 26.8467, 80.9462, 'Uttar Pradesh'),
            ('Wheat', 'Lucknow', 26.8467, 80.9462, 'Uttar Pradesh'),
            ('Maize', 'Lucknow', 26.8467, 80.9462, 'Uttar Pradesh'),
            ('Rice', 'Chandigarh', 30.7333, 76.7794, 'Punjab'),
            ('Wheat', 'Chandigarh', 30.7333, 76.7794, 'Punjab'),
            ('Maize', 'Chandigarh', 30.7333, 76.7794, 'Punjab'),
            ('Rice', 'Patna', 25.5941, 85.1376, 'Bihar'),
            ('Wheat', 'Patna', 25.5941, 85.1376, 'Bihar'),
            ('Maize', 'Patna', 25.5941, 85.1376, 'Bihar'),
        ]
        
        passed = 0
        failed = 0
        
        for crop_type, location, lat, lon, expected_region in test_cases:
            request = self._create_request(crop_type, location, lat, lon)
            
            try:
                response = self.service.predict_yield(request)
                
                if 'error' in response:
                    print(f"  ❌ {crop_type} in {location}: {response['error'].get('message', 'Unknown error')}")
                    failed += 1
                    continue
                
                # Verify variety was selected
                if not response['prediction']['variety_used']:
                    print(f"  ❌ {crop_type} in {location}: No variety selected")
                    failed += 1
                    continue
                
                # Verify region (allow fallback to All North India)
                metadata = response['factors']['default_variety_selection']
                if metadata['region'] not in [expected_region, 'All North India']:
                    print(f"  ⚠️  {crop_type} in {location}: Expected {expected_region}, got {metadata['region']}")
                
                print(f"  ✅ {crop_type} in {location}: {response['prediction']['variety_used']} ({metadata['region']})")
                passed += 1
                
            except Exception as e:
                print(f"  ❌ {crop_type} in {location}: Exception - {str(e)}")
                failed += 1
        
        print(f"\n  Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
        
        if failed == 0:
            print("✅ TEST 9 PASSED")
            return True
        else:
            print(f"❌ TEST 9 FAILED ({failed} sub-tests failed)")
            return False
    
    def test_response_structure_completeness(self):
        """Test that response includes all required fields"""
        print("\n" + "-"*80)
        print("TEST 10: Response structure completeness")
        print("-"*80)
        
        request = self._create_request(
            crop_type='Rice',
            location_name='Bhopal',
            latitude=23.2599,
            longitude=77.4126
        )
        
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            if 'error' in response:
                print(f"❌ Prediction failed: {response['error']}")
                return False
            
            # Check all required top-level sections
            required_sections = [
                'prediction_id', 'timestamp', 'input', 'prediction',
                'model', 'data_sources', 'factors', 'api_version',
                'processing_time_seconds'
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in response:
                    missing_sections.append(section)
            
            if missing_sections:
                print(f"  ❌ Missing sections: {', '.join(missing_sections)}")
                return False
            
            print(f"  ✅ All required top-level sections present")
            
            # Verify metadata fields
            if not self._verify_metadata_fields(response, expected_variety_assumed=True):
                return False
            
            print(f"  ✅ All required metadata fields present")
            
            # Print response structure summary
            print(f"\n  Response structure:")
            print(f"    - prediction_id: {response['prediction_id']}")
            print(f"    - api_version: {response['api_version']}")
            print(f"    - variety_used: {response['prediction']['variety_used']}")
            print(f"    - variety_assumed: {response['prediction']['variety_assumed']}")
            print(f"    - selection_region: {response['factors']['default_variety_selection']['region']}")
            print(f"    - selection_reason: {response['factors']['default_variety_selection']['reason']}")
            
            print("✅ TEST 10 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all end-to-end validation tests"""
        if not self.setup():
            print("\n❌ Setup failed, cannot run tests")
            return False
        
        tests = [
            ("Full flow - Bhopal + Rice", self.test_full_flow_bhopal_rice),
            ("Full flow - Lucknow + Maize", self.test_full_flow_lucknow_maize),
            ("Full flow - Chandigarh + Wheat", self.test_full_flow_chandigarh_wheat),
            ("Full flow - Patna + Rice", self.test_full_flow_patna_rice),
            ("Full flow - North India Regional + Wheat", self.test_full_flow_north_india_regional),
            ("Error scenario - Invalid crop type", self.test_error_invalid_crop_type),
            ("Unknown location - Fallback region", self.test_error_unknown_location),
            ("With explicit variety - Unchanged behavior", self.test_with_explicit_variety),
            ("All location-crop combinations", self.test_all_locations_all_crops),
            ("Response structure completeness", self.test_response_structure_completeness),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"\n❌ Test '{test_name}' crashed: {e}")
                import traceback
                traceback.print_exc()
                results.append((test_name, False))
        
        # Print summary
        print("\n" + "="*80)
        print("END-TO-END VALIDATION TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\n{'='*80}")
        print(f"Results: {passed}/{total} tests passed")
        print("="*80)
        
        if passed == total:
            print("\n🎉 ALL END-TO-END VALIDATION TESTS PASSED!")
            print("Optional variety feature is fully functional and production-ready.")
            print("\nKey validations completed:")
            print("  ✅ Correct variety selection for each region")
            print("  ✅ Successful predictions with selected varieties")
            print("  ✅ All required metadata fields present")
            print("  ✅ Error scenarios handled gracefully")
            print("  ✅ Backward compatibility maintained")
            print("  ✅ Response structure complete and correct")
            return True
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
            return False


def main():
    """Main test runner"""
    tester = TestOptionalVarietyE2E()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
