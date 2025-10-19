#!/usr/bin/env python3
"""
Test Task 5: Enhance prediction response with variety selection metadata

This test verifies that the prediction response includes:
1. variety_used field in prediction section
2. variety_assumed boolean field in prediction section
3. default_variety_selection object in factors section when variety was assumed
4. API version updated to 6.1.0
"""

import sys
import json
import requests
from datetime import datetime, timedelta

# Test configuration
API_BASE_URL = "http://localhost:8000"
PREDICT_ENDPOINT = f"{API_BASE_URL}/predict/yield"


def test_response_with_variety_specified():
    """Test response when variety is explicitly specified"""
    print("\n" + "="*80)
    print("TEST 1: Response with variety specified (variety_assumed should be False)")
    print("="*80)
    
    request_data = {
        "crop_type": "Rice",
        "variety_name": "Basmati 370",
        "location_name": "Bhopal",
        "latitude": 23.2599,
        "longitude": 77.4126,
        "sowing_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
        "use_real_time_data": False
    }
    
    print(f"\n📤 Sending request with variety: {request_data['variety_name']}")
    
    try:
        response = requests.post(PREDICT_ENDPOINT, json=request_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        
        # Check prediction section has required fields
        prediction = result.get('prediction', {})
        
        print("\n✅ Response received successfully")
        print(f"\n📊 Prediction section:")
        print(f"  - yield_tons_per_hectare: {prediction.get('yield_tons_per_hectare')}")
        print(f"  - variety_used: {prediction.get('variety_used')}")
        print(f"  - variety_assumed: {prediction.get('variety_assumed')}")
        
        # Verify variety_used field exists
        if 'variety_used' not in prediction:
            print("❌ FAIL: 'variety_used' field missing from prediction section")
            return False
        
        # Verify variety_assumed field exists
        if 'variety_assumed' not in prediction:
            print("❌ FAIL: 'variety_assumed' field missing from prediction section")
            return False
        
        # Verify variety_used matches the specified variety
        if prediction['variety_used'] != request_data['variety_name']:
            print(f"❌ FAIL: variety_used '{prediction['variety_used']}' doesn't match specified '{request_data['variety_name']}'")
            return False
        
        # Verify variety_assumed is False
        if prediction['variety_assumed'] != False:
            print(f"❌ FAIL: variety_assumed should be False, got {prediction['variety_assumed']}")
            return False
        
        # Verify default_variety_selection is NOT in factors
        factors = result.get('factors', {})
        if 'default_variety_selection' in factors:
            print("❌ FAIL: default_variety_selection should NOT be present when variety is specified")
            return False
        
        # Verify API version is 6.1.0
        api_version = result.get('api_version')
        if api_version != '6.1.0':
            print(f"❌ FAIL: API version should be '6.1.0', got '{api_version}'")
            return False
        
        print(f"\n✅ API version: {api_version}")
        print("\n✅ TEST 1 PASSED: All fields correct when variety is specified")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_response_without_variety():
    """Test response when variety is NOT specified (auto-selected)"""
    print("\n" + "="*80)
    print("TEST 2: Response without variety (variety_assumed should be True)")
    print("="*80)
    
    request_data = {
        "crop_type": "Rice",
        # variety_name is omitted
        "location_name": "Bhopal",
        "latitude": 23.2599,
        "longitude": 77.4126,
        "sowing_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
        "use_real_time_data": False
    }
    
    print(f"\n📤 Sending request WITHOUT variety_name")
    
    try:
        response = requests.post(PREDICT_ENDPOINT, json=request_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        
        # Check prediction section has required fields
        prediction = result.get('prediction', {})
        
        print("\n✅ Response received successfully")
        print(f"\n📊 Prediction section:")
        print(f"  - yield_tons_per_hectare: {prediction.get('yield_tons_per_hectare')}")
        print(f"  - variety_used: {prediction.get('variety_used')}")
        print(f"  - variety_assumed: {prediction.get('variety_assumed')}")
        
        # Verify variety_used field exists and has a value
        if 'variety_used' not in prediction:
            print("❌ FAIL: 'variety_used' field missing from prediction section")
            return False
        
        if not prediction['variety_used']:
            print("❌ FAIL: 'variety_used' should have a value")
            return False
        
        # Verify variety_assumed field exists
        if 'variety_assumed' not in prediction:
            print("❌ FAIL: 'variety_assumed' field missing from prediction section")
            return False
        
        # Verify variety_assumed is True
        if prediction['variety_assumed'] != True:
            print(f"❌ FAIL: variety_assumed should be True, got {prediction['variety_assumed']}")
            return False
        
        # Verify default_variety_selection IS in factors
        factors = result.get('factors', {})
        if 'default_variety_selection' not in factors:
            print("❌ FAIL: default_variety_selection should be present when variety is auto-selected")
            return False
        
        selection_metadata = factors['default_variety_selection']
        print(f"\n📊 Default variety selection metadata:")
        print(f"  - region: {selection_metadata.get('region')}")
        print(f"  - reason: {selection_metadata.get('reason')}")
        print(f"  - yield_potential: {selection_metadata.get('yield_potential')}")
        print(f"  - alternatives: {selection_metadata.get('alternatives', [])}")
        
        # Verify required fields in selection_metadata
        required_fields = ['region', 'reason']
        for field in required_fields:
            if field not in selection_metadata:
                print(f"❌ FAIL: '{field}' missing from default_variety_selection")
                return False
        
        # Verify API version is 6.1.0
        api_version = result.get('api_version')
        if api_version != '6.1.0':
            print(f"❌ FAIL: API version should be '6.1.0', got '{api_version}'")
            return False
        
        print(f"\n✅ API version: {api_version}")
        print("\n✅ TEST 2 PASSED: All fields correct when variety is auto-selected")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_response_with_null_variety():
    """Test response when variety is explicitly null"""
    print("\n" + "="*80)
    print("TEST 3: Response with variety_name=null (should auto-select)")
    print("="*80)
    
    request_data = {
        "crop_type": "Wheat",
        "variety_name": None,  # Explicitly null
        "location_name": "Chandigarh",
        "latitude": 30.7333,
        "longitude": 76.7794,
        "sowing_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
        "use_real_time_data": False
    }
    
    print(f"\n📤 Sending request with variety_name=null")
    
    try:
        response = requests.post(PREDICT_ENDPOINT, json=request_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        prediction = result.get('prediction', {})
        
        print("\n✅ Response received successfully")
        print(f"\n📊 Prediction section:")
        print(f"  - variety_used: {prediction.get('variety_used')}")
        print(f"  - variety_assumed: {prediction.get('variety_assumed')}")
        
        # Verify variety_assumed is True
        if prediction.get('variety_assumed') != True:
            print(f"❌ FAIL: variety_assumed should be True for null variety, got {prediction.get('variety_assumed')}")
            return False
        
        # Verify default_variety_selection is present
        factors = result.get('factors', {})
        if 'default_variety_selection' not in factors:
            print("❌ FAIL: default_variety_selection should be present when variety is null")
            return False
        
        print("\n✅ TEST 3 PASSED: Null variety handled correctly")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_response_structure_completeness():
    """Test that response structure is complete and well-formed"""
    print("\n" + "="*80)
    print("TEST 4: Response structure completeness")
    print("="*80)
    
    request_data = {
        "crop_type": "Maize",
        "location_name": "Lucknow",
        "latitude": 26.8467,
        "longitude": 80.9462,
        "sowing_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
        "use_real_time_data": False
    }
    
    print(f"\n📤 Sending request for {request_data['crop_type']} in {request_data['location_name']}")
    
    try:
        response = requests.post(PREDICT_ENDPOINT, json=request_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            return False
        
        result = response.json()
        
        # Check all major sections exist
        required_sections = ['prediction_id', 'timestamp', 'input', 'prediction', 'model', 'data_sources', 'factors', 'api_version']
        for section in required_sections:
            if section not in result:
                print(f"❌ FAIL: Missing section '{section}' in response")
                return False
        
        # Check prediction section fields
        prediction = result['prediction']
        required_prediction_fields = ['yield_tons_per_hectare', 'variety_used', 'variety_assumed', 'lower_bound', 'upper_bound', 'confidence_score']
        for field in required_prediction_fields:
            if field not in prediction:
                print(f"❌ FAIL: Missing field '{field}' in prediction section")
                return False
        
        # Check factors section
        factors = result['factors']
        if prediction['variety_assumed'] and 'default_variety_selection' not in factors:
            print("❌ FAIL: default_variety_selection missing when variety_assumed is True")
            return False
        
        print("\n✅ All required sections present:")
        print(f"  - prediction_id: {result['prediction_id']}")
        print(f"  - api_version: {result['api_version']}")
        print(f"  - variety_used: {prediction['variety_used']}")
        print(f"  - variety_assumed: {prediction['variety_assumed']}")
        
        if 'default_variety_selection' in factors:
            print(f"  - default_variety_selection.region: {factors['default_variety_selection'].get('region')}")
            print(f"  - default_variety_selection.reason: {factors['default_variety_selection'].get('reason')}")
        
        print("\n✅ TEST 4 PASSED: Response structure is complete")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("TASK 5: RESPONSE METADATA ENHANCEMENT TESTS")
    print("="*80)
    print("\nTesting prediction response enhancements:")
    print("  1. variety_used field in prediction section")
    print("  2. variety_assumed boolean field in prediction section")
    print("  3. default_variety_selection in factors when variety assumed")
    print("  4. API version updated to 6.1.0")
    
    # Check if API is running
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"\n❌ API health check failed. Is the API running at {API_BASE_URL}?")
            print("Start the API with: python run_api.py")
            return False
    except requests.exceptions.RequestException:
        print(f"\n❌ Cannot connect to API at {API_BASE_URL}")
        print("Start the API with: python run_api.py")
        return False
    
    print(f"\n✅ API is running at {API_BASE_URL}")
    
    # Run all tests
    tests = [
        ("Response with variety specified", test_response_with_variety_specified),
        ("Response without variety", test_response_without_variety),
        ("Response with null variety", test_response_with_null_variety),
        ("Response structure completeness", test_response_structure_completeness)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
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
        print("\n🎉 ALL TESTS PASSED! Task 5 implementation is complete.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
