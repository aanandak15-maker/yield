#!/usr/bin/env python3
"""
Integration Tests for Optional Variety Feature

Tests the complete integration of optional variety selection in the prediction API.
Verifies that the system correctly handles requests with and without variety_name,
and that responses include appropriate metadata.

Requirements tested: 1.1, 1.2, 1.3, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from prediction_api import CropYieldPredictionService


class TestOptionalVarietyIntegration:
    """Integration tests for optional variety feature"""
    
    def __init__(self):
        self.service = None
        self.test_results = []
        
    def setup(self):
        """Initialize the prediction service"""
        print("\n" + "="*80)
        print("OPTIONAL VARIETY INTEGRATION TESTS")
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
    
    def _create_base_request(self, crop_type: str, location_name: str, 
                            latitude: float, longitude: float, 
                            variety_name: Any = None) -> Dict[str, Any]:
        """Create a base prediction request"""
        request = {
            'crop_type': crop_type,
            'location_name': location_name,
            'latitude': latitude,
            'longitude': longitude,
            'sowing_date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
            'use_real_time_data': False  # Use fallback data for faster testing
        }
        
        # Only add variety_name if explicitly provided (including None)
        if variety_name is not None or 'variety_name' in locals():
            request['variety_name'] = variety_name
            
        return request
    
    def _verify_response_structure(self, response: Dict[str, Any], 
                                   test_name: str) -> bool:
        """Verify basic response structure"""
        required_sections = ['prediction_id', 'timestamp', 'input', 'prediction', 
                           'model', 'data_sources', 'factors', 'api_version']
        
        for section in required_sections:
            if section not in response:
                print(f"  ❌ Missing section: {section}")
                return False
        
        # Check API version
        if response.get('api_version') != '6.1.0':
            print(f"  ❌ API version should be '6.1.0', got '{response.get('api_version')}'")
            return False
        
        return True
    
    def test_prediction_without_variety_bhopal_rice(self):
        """Test prediction without variety for Bhopal + Rice"""
        print("\n" + "-"*80)
        print("TEST 1: Prediction without variety for Bhopal + Rice")
        print("-"*80)
        
        request = self._create_base_request(
            crop_type='Rice',
            location_name='Bhopal',
            latitude=23.2599,
            longitude=77.4126
        )
        # Don't include variety_name at all
        
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
            
            # Verify response structure
            if not self._verify_response_structure(response, "Bhopal Rice"):
                return False
            
            # Verify variety was selected
            if not response['prediction']['variety_used']:
                print("  ❌ No variety was selected")
                return False
            
            # Verify variety_assumed is True
            if response['prediction']['variety_assumed'] != True:
                print(f"  ❌ variety_assumed should be True, got {response['prediction']['variety_assumed']}")
                return False
            
            # Verify selection metadata exists
            if 'default_variety_selection' not in response['factors']:
                print("  ❌ default_variety_selection metadata missing")
                return False
            
            metadata = response['factors']['default_variety_selection']
            print(f"  - Selection region: {metadata.get('region')}")
            print(f"  - Selection reason: {metadata.get('reason')}")
            
            print("✅ TEST 1 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_prediction_without_variety_chandigarh_wheat(self):
        """Test prediction without variety for Chandigarh + Wheat"""
        print("\n" + "-"*80)
        print("TEST 2: Prediction without variety for Chandigarh + Wheat")
        print("-"*80)
        
        request = self._create_base_request(
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
            print(f"  - Variety assumed: {response['prediction']['variety_assumed']}")
            
            # Verify variety was selected
            if not response['prediction']['variety_used']:
                print("  ❌ No variety was selected")
                return False
            
            # Verify variety_assumed is True
            if response['prediction']['variety_assumed'] != True:
                print(f"  ❌ variety_assumed should be True, got {response['prediction']['variety_assumed']}")
                return False
            
            # Verify selection metadata exists
            if 'default_variety_selection' not in response['factors']:
                print("  ❌ default_variety_selection metadata missing")
                return False
            
            print("✅ TEST 2 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_prediction_without_variety_lucknow_maize(self):
        """Test prediction without variety for Lucknow + Maize"""
        print("\n" + "-"*80)
        print("TEST 3: Prediction without variety for Lucknow + Maize")
        print("-"*80)
        
        request = self._create_base_request(
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
            print(f"  - Variety assumed: {response['prediction']['variety_assumed']}")
            
            # Verify variety was selected
            if not response['prediction']['variety_used']:
                print("  ❌ No variety was selected")
                return False
            
            # Verify variety_assumed is True
            if response['prediction']['variety_assumed'] != True:
                print(f"  ❌ variety_assumed should be True, got {response['prediction']['variety_assumed']}")
                return False
            
            # Verify selection metadata exists
            if 'default_variety_selection' not in response['factors']:
                print("  ❌ default_variety_selection metadata missing")
                return False
            
            print("✅ TEST 3 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_prediction_with_variety_unchanged_behavior(self):
        """Test prediction with variety (verify unchanged behavior)"""
        print("\n" + "-"*80)
        print("TEST 4: Prediction with variety (verify unchanged behavior)")
        print("-"*80)
        
        request = self._create_base_request(
            crop_type='Rice',
            location_name='Bhopal',
            latitude=23.2599,
            longitude=77.4126,
            variety_name='Basmati 370'
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
            if response['prediction']['variety_used'] != 'Basmati 370':
                print(f"  ❌ Expected 'Basmati 370', got '{response['prediction']['variety_used']}'")
                return False
            
            # Verify variety_assumed is False
            if response['prediction']['variety_assumed'] != False:
                print(f"  ❌ variety_assumed should be False, got {response['prediction']['variety_assumed']}")
                return False
            
            # Verify selection metadata does NOT exist
            if 'default_variety_selection' in response['factors']:
                print("  ❌ default_variety_selection should NOT be present when variety is specified")
                return False
            
            print("✅ TEST 4 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_prediction_with_null_variety(self):
        """Test prediction with variety_name=null (treated as missing)"""
        print("\n" + "-"*80)
        print("TEST 5: Prediction with variety_name=null (treated as missing)")
        print("-"*80)
        
        request = self._create_base_request(
            crop_type='Wheat',
            location_name='Chandigarh',
            latitude=30.7333,
            longitude=76.7794,
            variety_name=None
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
            
            # Verify variety was selected (null should trigger selection)
            if not response['prediction']['variety_used']:
                print("  ❌ No variety was selected for null variety_name")
                return False
            
            # Verify variety_assumed is True
            if response['prediction']['variety_assumed'] != True:
                print(f"  ❌ variety_assumed should be True for null, got {response['prediction']['variety_assumed']}")
                return False
            
            # Verify selection metadata exists
            if 'default_variety_selection' not in response['factors']:
                print("  ❌ default_variety_selection metadata missing for null variety")
                return False
            
            print("✅ TEST 5 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_prediction_with_empty_string_variety(self):
        """Test prediction with variety_name="" (treated as missing)"""
        print("\n" + "-"*80)
        print("TEST 6: Prediction with variety_name=\"\" (treated as missing)")
        print("-"*80)
        
        request = self._create_base_request(
            crop_type='Maize',
            location_name='Lucknow',
            latitude=26.8467,
            longitude=80.9462,
            variety_name=''
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
            
            # Verify variety was selected (empty string should trigger selection)
            if not response['prediction']['variety_used']:
                print("  ❌ No variety was selected for empty string variety_name")
                return False
            
            # Verify variety_assumed is True
            if response['prediction']['variety_assumed'] != True:
                print(f"  ❌ variety_assumed should be True for empty string, got {response['prediction']['variety_assumed']}")
                return False
            
            # Verify selection metadata exists
            if 'default_variety_selection' not in response['factors']:
                print("  ❌ default_variety_selection metadata missing for empty string variety")
                return False
            
            print("✅ TEST 6 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_response_includes_variety_assumed_true(self):
        """Test verifying response includes variety_assumed=true when variety selected"""
        print("\n" + "-"*80)
        print("TEST 7: Response includes variety_assumed=true when variety selected")
        print("-"*80)
        
        request = self._create_base_request(
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
            
            # Check prediction section has variety_assumed field
            if 'variety_assumed' not in response['prediction']:
                print("  ❌ variety_assumed field missing from prediction section")
                return False
            
            # Verify it's True
            if response['prediction']['variety_assumed'] != True:
                print(f"  ❌ variety_assumed should be True, got {response['prediction']['variety_assumed']}")
                return False
            
            print(f"  ✅ variety_assumed = {response['prediction']['variety_assumed']}")
            print(f"  ✅ variety_used = {response['prediction']['variety_used']}")
            
            print("✅ TEST 7 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_response_includes_variety_assumed_false(self):
        """Test verifying response includes variety_assumed=false when variety provided"""
        print("\n" + "-"*80)
        print("TEST 8: Response includes variety_assumed=false when variety provided")
        print("-"*80)
        
        request = self._create_base_request(
            crop_type='Wheat',
            location_name='Chandigarh',
            latitude=30.7333,
            longitude=76.7794,
            variety_name='PBW 725'
        )
        
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            if 'error' in response:
                print(f"❌ Prediction failed: {response['error']}")
                return False
            
            print(f"✅ Prediction successful")
            
            # Check prediction section has variety_assumed field
            if 'variety_assumed' not in response['prediction']:
                print("  ❌ variety_assumed field missing from prediction section")
                return False
            
            # Verify it's False
            if response['prediction']['variety_assumed'] != False:
                print(f"  ❌ variety_assumed should be False, got {response['prediction']['variety_assumed']}")
                return False
            
            print(f"  ✅ variety_assumed = {response['prediction']['variety_assumed']}")
            print(f"  ✅ variety_used = {response['prediction']['variety_used']}")
            
            print("✅ TEST 8 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_response_includes_selection_metadata(self):
        """Test verifying response includes selection_metadata when variety assumed"""
        print("\n" + "-"*80)
        print("TEST 9: Response includes selection_metadata when variety assumed")
        print("-"*80)
        
        request = self._create_base_request(
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
            
            # Verify selection metadata exists in factors
            if 'default_variety_selection' not in response['factors']:
                print("  ❌ default_variety_selection missing from factors section")
                return False
            
            metadata = response['factors']['default_variety_selection']
            
            # Verify required fields
            required_fields = ['region', 'reason']
            for field in required_fields:
                if field not in metadata:
                    print(f"  ❌ Required field '{field}' missing from selection metadata")
                    return False
            
            print(f"  ✅ Selection metadata present:")
            print(f"     - region: {metadata['region']}")
            print(f"     - reason: {metadata['reason']}")
            if 'yield_potential' in metadata:
                print(f"     - yield_potential: {metadata['yield_potential']}")
            if 'alternatives' in metadata:
                print(f"     - alternatives: {metadata['alternatives']}")
            
            print("✅ TEST 9 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_backward_compatibility(self):
        """Test for backward compatibility with existing request format"""
        print("\n" + "-"*80)
        print("TEST 10: Backward compatibility with existing request format")
        print("-"*80)
        
        # Test with explicit variety (old format)
        request = self._create_base_request(
            crop_type='Rice',
            location_name='Bhopal',
            latitude=23.2599,
            longitude=77.4126,
            variety_name='Swarna'
        )
        
        print(f"📤 Request (old format with variety): {json.dumps(request, indent=2)}")
        
        try:
            response = self.service.predict_yield(request)
            
            if 'error' in response:
                print(f"❌ Prediction failed: {response['error']}")
                return False
            
            print(f"✅ Prediction successful with old format")
            
            # Verify the specified variety was used
            if response['prediction']['variety_used'] != 'Swarna':
                print(f"  ❌ Expected 'Swarna', got '{response['prediction']['variety_used']}'")
                return False
            
            # Verify variety_assumed is False (backward compatibility)
            if response['prediction']['variety_assumed'] != False:
                print(f"  ❌ variety_assumed should be False for explicit variety")
                return False
            
            # Verify no selection metadata (backward compatibility)
            if 'default_variety_selection' in response['factors']:
                print("  ❌ default_variety_selection should NOT be present for explicit variety")
                return False
            
            # Verify all standard fields are present
            if not self._verify_response_structure(response, "Backward Compatibility"):
                return False
            
            print(f"  ✅ Variety used: {response['prediction']['variety_used']}")
            print(f"  ✅ variety_assumed: {response['prediction']['variety_assumed']}")
            print(f"  ✅ No selection metadata (as expected)")
            print(f"  ✅ All standard response fields present")
            
            print("✅ TEST 10 PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        if not self.setup():
            print("\n❌ Setup failed, cannot run tests")
            return False
        
        tests = [
            ("Prediction without variety for Bhopal + Rice", 
             self.test_prediction_without_variety_bhopal_rice),
            ("Prediction without variety for Chandigarh + Wheat", 
             self.test_prediction_without_variety_chandigarh_wheat),
            ("Prediction without variety for Lucknow + Maize", 
             self.test_prediction_without_variety_lucknow_maize),
            ("Prediction with variety (unchanged behavior)", 
             self.test_prediction_with_variety_unchanged_behavior),
            ("Prediction with variety_name=null", 
             self.test_prediction_with_null_variety),
            ("Prediction with variety_name=\"\"", 
             self.test_prediction_with_empty_string_variety),
            ("Response includes variety_assumed=true", 
             self.test_response_includes_variety_assumed_true),
            ("Response includes variety_assumed=false", 
             self.test_response_includes_variety_assumed_false),
            ("Response includes selection_metadata", 
             self.test_response_includes_selection_metadata),
            ("Backward compatibility", 
             self.test_backward_compatibility)
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
        print("TEST SUMMARY")
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
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("Optional variety feature is fully integrated and working correctly.")
            return True
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
            return False


def main():
    """Main test runner"""
    tester = TestOptionalVarietyIntegration()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
