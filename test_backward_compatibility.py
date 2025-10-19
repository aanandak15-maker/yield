#!/usr/bin/env python3
"""
Backward Compatibility Test Suite

Verifies that the optional variety feature maintains backward compatibility:
- All existing prediction tests pass without modifications
- Requests with variety_name specified work exactly as before
- Response format is unchanged when variety is provided
- variety_assumed=false when variety is explicitly provided
- No breaking changes to API contract

Requirements: 6.1, 6.2, 6.3, 6.4
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from prediction_api import CropYieldPredictionService


class BackwardCompatibilityTestResults:
    """Track backward compatibility test results"""
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_details = []
    
    def add_result(self, test_name: str, passed: bool, details: str = ""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
        
        self.test_details.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def print_summary(self):
        print("\n" + "=" * 80)
        print("📊 BACKWARD COMPATIBILITY TEST RESULTS")
        print("=" * 80)
        
        for detail in self.test_details:
            status = "✅ PASS" if detail["passed"] else "❌ FAIL"
            print(f"{status} {detail['test']}")
            if detail["details"]:
                print(f"     {detail['details']}")
        
        print("-" * 80)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print("=" * 80)
        
        if self.failed_tests == 0:
            print("🎉 All backward compatibility tests passed!")
            return True
        else:
            print(f"⚠️  {self.failed_tests} test(s) failed. Review details above.")
            return False


def test_prediction_with_variety_specified(
    service: CropYieldPredictionService,
    results: BackwardCompatibilityTestResults
):
    """
    Test that predictions with variety_name specified work exactly as before
    
    Requirements: 6.1, 6.3
    """
    print("\n🧪 Test 1: Prediction with variety_name specified")
    print("-" * 80)
    
    test_cases = [
        {
            "name": "Bhopal + Rice + Basmati 370",
            "request": {
                "crop_type": "Rice",
                "variety_name": "Basmati 370",
                "location_name": "Bhopal",
                "latitude": 23.2599,
                "longitude": 77.4126,
                "sowing_date": (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                "use_real_time_data": False
            }
        },
        {
            "name": "Chandigarh + Wheat + HD 3086",
            "request": {
                "crop_type": "Wheat",
                "variety_name": "HD 3086",
                "location_name": "Chandigarh",
                "latitude": 30.7333,
                "longitude": 76.7794,
                "sowing_date": (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d'),
                "use_real_time_data": False
            }
        },
        {
            "name": "Lucknow + Maize + DHM 117",
            "request": {
                "crop_type": "Maize",
                "variety_name": "DHM 117",
                "location_name": "Lucknow",
                "latitude": 26.8467,
                "longitude": 80.9462,
                "sowing_date": (datetime.now() - timedelta(days=80)).strftime('%Y-%m-%d'),
                "use_real_time_data": False
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   Testing: {test_case['name']}")
        
        try:
            response = service.predict_yield(test_case['request'])
            
            # Check 1: No error in response
            if 'error' in response:
                results.add_result(
                    f"With Variety - {test_case['name']} - No Error",
                    False,
                    f"Got error: {response['error']}"
                )
                continue
            
            results.add_result(
                f"With Variety - {test_case['name']} - No Error",
                True
            )
            
            # Check 2: Response has required fields
            required_fields = ['prediction_id', 'timestamp', 'input', 'prediction', 'model']
            missing_fields = [f for f in required_fields if f not in response]
            
            if missing_fields:
                results.add_result(
                    f"With Variety - {test_case['name']} - Response Structure",
                    False,
                    f"Missing fields: {missing_fields}"
                )
            else:
                results.add_result(
                    f"With Variety - {test_case['name']} - Response Structure",
                    True
                )
            
            # Check 3: Specified variety was used
            variety_used = response.get('prediction', {}).get('variety_used')
            expected_variety = test_case['request']['variety_name']
            
            if variety_used != expected_variety:
                results.add_result(
                    f"With Variety - {test_case['name']} - Correct Variety Used",
                    False,
                    f"Expected '{expected_variety}', got '{variety_used}'"
                )
            else:
                results.add_result(
                    f"With Variety - {test_case['name']} - Correct Variety Used",
                    True
                )
                print(f"   ✅ Used specified variety: {variety_used}")
            
            # Check 4: variety_assumed should be False
            variety_assumed = response.get('prediction', {}).get('variety_assumed')
            
            if variety_assumed is not False:
                results.add_result(
                    f"With Variety - {test_case['name']} - variety_assumed=False",
                    False,
                    f"Expected False, got {variety_assumed}"
                )
            else:
                results.add_result(
                    f"With Variety - {test_case['name']} - variety_assumed=False",
                    True
                )
                print(f"   ✅ variety_assumed=False")
            
            # Check 5: No default_variety_selection metadata should be present
            has_selection_metadata = 'default_variety_selection' in response.get('factors', {})
            
            if has_selection_metadata:
                results.add_result(
                    f"With Variety - {test_case['name']} - No Selection Metadata",
                    False,
                    "default_variety_selection should not be present when variety is specified"
                )
            else:
                results.add_result(
                    f"With Variety - {test_case['name']} - No Selection Metadata",
                    True
                )
                print(f"   ✅ No selection metadata (as expected)")
            
            # Check 6: Prediction has valid yield value
            yield_value = response.get('prediction', {}).get('yield_tons_per_hectare')
            
            if yield_value is None or not isinstance(yield_value, (int, float)) or yield_value <= 0:
                results.add_result(
                    f"With Variety - {test_case['name']} - Valid Yield",
                    False,
                    f"Invalid yield value: {yield_value}"
                )
            else:
                results.add_result(
                    f"With Variety - {test_case['name']} - Valid Yield",
                    True
                )
                print(f"   ✅ Yield: {yield_value} tons/ha")
            
        except Exception as e:
            results.add_result(
                f"With Variety - {test_case['name']} - Exception",
                False,
                f"Exception: {str(e)}"
            )
            print(f"   ❌ Exception: {str(e)}")


def test_response_format_unchanged(
    service: CropYieldPredictionService,
    results: BackwardCompatibilityTestResults
):
    """
    Test that response format is unchanged when variety is provided
    
    Requirements: 6.3
    """
    print("\n🧪 Test 2: Response format unchanged with variety specified")
    print("-" * 80)
    
    request = {
        "crop_type": "Rice",
        "variety_name": "Swarna",
        "location_name": "Bhopal",
        "latitude": 23.2599,
        "longitude": 77.4126,
        "sowing_date": (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
        "use_real_time_data": False
    }
    
    try:
        response = service.predict_yield(request)
        
        if 'error' in response:
            results.add_result(
                "Response Format - No Error",
                False,
                f"Got error: {response['error']}"
            )
            return
        
        results.add_result("Response Format - No Error", True)
        
        # Expected response structure (based on existing API)
        expected_structure = {
            'prediction_id': str,
            'timestamp': str,
            'input': dict,
            'prediction': dict,
            'model': dict,
            'factors': dict,
            'data_sources': dict,
            'processing_time_seconds': (int, float),
            'api_version': str
        }
        
        # Check all expected fields are present
        for field, expected_type in expected_structure.items():
            if field not in response:
                results.add_result(
                    f"Response Format - Has '{field}'",
                    False,
                    f"Missing field: {field}"
                )
            else:
                # Check type
                actual_value = response[field]
                if isinstance(expected_type, tuple):
                    type_match = isinstance(actual_value, expected_type)
                else:
                    type_match = isinstance(actual_value, expected_type)
                
                if not type_match:
                    results.add_result(
                        f"Response Format - '{field}' Type",
                        False,
                        f"Expected {expected_type}, got {type(actual_value)}"
                    )
                else:
                    results.add_result(
                        f"Response Format - '{field}' Type",
                        True
                    )
        
        # Check prediction section has expected fields
        prediction = response.get('prediction', {})
        expected_prediction_fields = [
            'yield_tons_per_hectare',
            'variety_used',
            'variety_assumed',
            'lower_bound',
            'upper_bound',
            'confidence_score'
        ]
        
        for field in expected_prediction_fields:
            if field not in prediction:
                results.add_result(
                    f"Response Format - prediction.{field}",
                    False,
                    f"Missing field in prediction: {field}"
                )
            else:
                results.add_result(
                    f"Response Format - prediction.{field}",
                    True
                )
        
        print(f"   ✅ Response structure matches expected format")
        
    except Exception as e:
        results.add_result(
            "Response Format - Exception",
            False,
            f"Exception: {str(e)}"
        )


def test_existing_client_requests(
    service: CropYieldPredictionService,
    results: BackwardCompatibilityTestResults
):
    """
    Test existing client request patterns work unchanged
    
    Requirements: 6.1, 6.2
    """
    print("\n🧪 Test 3: Existing client request patterns")
    print("-" * 80)
    
    # Simulate various existing client request patterns
    client_patterns = [
        {
            "name": "Standard request with all fields",
            "request": {
                "crop_type": "Rice",
                "variety_name": "Basmati 370",
                "location_name": "Bhopal",
                "latitude": 23.2599,
                "longitude": 77.4126,
                "sowing_date": "2024-07-15",
                "use_real_time_data": False
            }
        },
        {
            "name": "Request with use_real_time_data=True",
            "request": {
                "crop_type": "Wheat",
                "variety_name": "HD 3086",
                "location_name": "Chandigarh",
                "latitude": 30.7333,
                "longitude": 76.7794,
                "sowing_date": "2024-11-01",
                "use_real_time_data": True
            }
        },
        {
            "name": "Request with different crop type",
            "request": {
                "crop_type": "Maize",
                "variety_name": "DHM 117",
                "location_name": "Lucknow",
                "latitude": 26.8467,
                "longitude": 80.9462,
                "sowing_date": "2024-06-20",
                "use_real_time_data": False
            }
        }
    ]
    
    for pattern in client_patterns:
        print(f"\n   Testing: {pattern['name']}")
        
        try:
            response = service.predict_yield(pattern['request'])
            
            # Check for successful response
            if 'error' in response:
                results.add_result(
                    f"Client Pattern - {pattern['name']}",
                    False,
                    f"Got error: {response['error']}"
                )
            else:
                # Verify basic response validity
                has_prediction = 'prediction' in response
                has_yield = response.get('prediction', {}).get('yield_tons_per_hectare') is not None
                
                if has_prediction and has_yield:
                    results.add_result(
                        f"Client Pattern - {pattern['name']}",
                        True
                    )
                    print(f"   ✅ Request processed successfully")
                else:
                    results.add_result(
                        f"Client Pattern - {pattern['name']}",
                        False,
                        "Response missing prediction or yield"
                    )
        
        except Exception as e:
            results.add_result(
                f"Client Pattern - {pattern['name']}",
                False,
                f"Exception: {str(e)}"
            )


def test_variety_assumed_false_when_provided(
    service: CropYieldPredictionService,
    results: BackwardCompatibilityTestResults
):
    """
    Test that variety_assumed=false when variety is explicitly provided
    
    Requirements: 6.3
    """
    print("\n🧪 Test 4: variety_assumed=false when variety provided")
    print("-" * 80)
    
    test_cases = [
        ("Rice", "Basmati 370", "Bhopal", 23.2599, 77.4126),
        ("Wheat", "HD 3086", "Chandigarh", 30.7333, 76.7794),
        ("Maize", "DHM 117", "Lucknow", 26.8467, 80.9462),
        ("Rice", "Swarna", "Patna", 25.5941, 85.1376),
        ("Wheat", "PBW 725", "Chandigarh", 30.7333, 76.7794)
    ]
    
    for crop_type, variety_name, location, lat, lon in test_cases:
        test_name = f"{crop_type} + {variety_name}"
        
        request = {
            "crop_type": crop_type,
            "variety_name": variety_name,
            "location_name": location,
            "latitude": lat,
            "longitude": lon,
            "sowing_date": (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            "use_real_time_data": False
        }
        
        try:
            response = service.predict_yield(request)
            
            if 'error' in response:
                results.add_result(
                    f"variety_assumed=false - {test_name}",
                    False,
                    f"Got error: {response['error']}"
                )
                continue
            
            variety_assumed = response.get('prediction', {}).get('variety_assumed')
            
            if variety_assumed is False:
                results.add_result(
                    f"variety_assumed=false - {test_name}",
                    True
                )
                print(f"   ✅ {test_name}: variety_assumed=False")
            else:
                results.add_result(
                    f"variety_assumed=false - {test_name}",
                    False,
                    f"Expected False, got {variety_assumed}"
                )
                print(f"   ❌ {test_name}: variety_assumed={variety_assumed} (expected False)")
        
        except Exception as e:
            results.add_result(
                f"variety_assumed=false - {test_name}",
                False,
                f"Exception: {str(e)}"
            )


def test_no_breaking_changes(
    service: CropYieldPredictionService,
    results: BackwardCompatibilityTestResults
):
    """
    Confirm no breaking changes to API contract
    
    Requirements: 6.4
    """
    print("\n🧪 Test 5: No breaking changes to API contract")
    print("-" * 80)
    
    # Test 1: variety_name field still accepted
    print("\n   Testing: variety_name field still accepted")
    request_with_variety = {
        "crop_type": "Rice",
        "variety_name": "Basmati 370",
        "location_name": "Bhopal",
        "latitude": 23.2599,
        "longitude": 77.4126,
        "sowing_date": (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
        "use_real_time_data": False
    }
    
    try:
        response = service.predict_yield(request_with_variety)
        if 'error' not in response:
            results.add_result(
                "No Breaking Changes - variety_name accepted",
                True
            )
            print("   ✅ variety_name field still accepted")
        else:
            results.add_result(
                "No Breaking Changes - variety_name accepted",
                False,
                f"Error: {response['error']}"
            )
    except Exception as e:
        results.add_result(
            "No Breaking Changes - variety_name accepted",
            False,
            f"Exception: {str(e)}"
        )
    
    # Test 2: All required fields still required (except variety_name)
    print("\n   Testing: Required fields validation")
    required_fields = ['crop_type', 'location_name', 'latitude', 'longitude', 'sowing_date']
    
    for field in required_fields:
        incomplete_request = request_with_variety.copy()
        del incomplete_request[field]
        
        try:
            response = service.predict_yield(incomplete_request)
            # Should get an error for missing required field
            if 'error' in response:
                results.add_result(
                    f"No Breaking Changes - {field} required",
                    True
                )
                print(f"   ✅ {field} still required")
            else:
                results.add_result(
                    f"No Breaking Changes - {field} required",
                    False,
                    f"Missing {field} did not produce error"
                )
        except Exception as e:
            # Exception is also acceptable for missing required field
            results.add_result(
                f"No Breaking Changes - {field} required",
                True
            )
            print(f"   ✅ {field} still required (exception raised)")
    
    # Test 3: Response structure unchanged
    print("\n   Testing: Response structure unchanged")
    response = service.predict_yield(request_with_variety)
    
    if 'error' not in response:
        # Check that all traditional fields are still present
        traditional_fields = [
            'prediction_id',
            'timestamp',
            'input',
            'prediction',
            'model',
            'factors',
            'data_sources',
            'processing_time_seconds'
        ]
        
        all_present = all(field in response for field in traditional_fields)
        
        if all_present:
            results.add_result(
                "No Breaking Changes - Response structure",
                True
            )
            print("   ✅ All traditional response fields present")
        else:
            missing = [f for f in traditional_fields if f not in response]
            results.add_result(
                "No Breaking Changes - Response structure",
                False,
                f"Missing fields: {missing}"
            )


def run_backward_compatibility_tests():
    """Run all backward compatibility tests"""
    print("=" * 80)
    print("🔄 BACKWARD COMPATIBILITY TEST SUITE")
    print("=" * 80)
    print("Verifying that optional variety feature maintains backward compatibility")
    print("=" * 80)
    
    # Initialize service
    print("\n🔧 Initializing prediction service...")
    try:
        service = CropYieldPredictionService()
        print("✅ Service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return False
    
    # Initialize results tracker
    results = BackwardCompatibilityTestResults()
    
    # Run all tests
    test_prediction_with_variety_specified(service, results)
    test_response_format_unchanged(service, results)
    test_existing_client_requests(service, results)
    test_variety_assumed_false_when_provided(service, results)
    test_no_breaking_changes(service, results)
    
    # Print summary
    success = results.print_summary()
    
    # Save results to file
    output_file = "test_results_backward_compatibility.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': results.total_tests,
                'passed': results.passed_tests,
                'failed': results.failed_tests,
                'success_rate': results.passed_tests / results.total_tests if results.total_tests > 0 else 0
            },
            'test_details': results.test_details
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    
    return success


if __name__ == "__main__":
    success = run_backward_compatibility_tests()
    sys.exit(0 if success else 1)
