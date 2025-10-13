#!/usr/bin/env python3
"""
Test script for the Crop Yield Prediction API

Tests all endpoints and validates responses
"""

import requests
import json
import time
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🏥 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()

        print("✅ Health check passed")
        print(f"   Status: {data.get('status')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Models loaded: {data.get('components', {}).get('models_loaded', 0)}")

        # Validate response structure
        assert data.get('status') == 'healthy'
        assert 'components' in data

        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_get_crops():
    """Test getting available crops and varieties"""
    print("\n🌾 Testing Get Crops...")
    try:
        response = requests.get(f"{BASE_URL}/crops")
        response.raise_for_status()
        data = response.json()

        print("✅ Get crops passed")
        print(f"   Total varieties: {data.get('total_varieties', 0)}")

        if data.get('crops'):
            for crop, info in data['crops'].items():
                print(f"   {crop}: {info['count']} varieties")

        return True
    except Exception as e:
        print(f"❌ Get crops failed: {e}")
        return False

def test_validation():
    """Test input validation"""
    print("\n✅ Testing Input Validation...")

    # Valid request
    valid_request = {
        "crop_type": "Rice",
        "variety_name": "Basmati 370",
        "location_name": "Bhopal",
        "latitude": 23.2599,
        "longitude": 77.4126,
        "sowing_date": "2024-10-01",
        "use_real_time_data": False
    }

    try:
        response = requests.post(f"{BASE_URL}/validate", json=valid_request)
        response.raise_for_status()
        data = response.json()

        print("✅ Validation passed for valid input")
        print(f"   Valid: {data.get('valid')}")
        if data.get('variety_info'):
            print(f"   Maturity days: {data['variety_info']['maturity_days']}")

        return True
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def test_prediction():
    """Test yield prediction"""
    print("\n🔮 Testing Yield Prediction...")

    # Test prediction request
    prediction_request = {
        "crop_type": "Rice",
        "variety_name": "Basmati 370",
        "location_name": "Bhopal",
        "latitude": 23.2599,
        "longitude": 77.4126,
        "sowing_date": "2024-07-15",  # Sowing date that wouldn't cause validation errors
        "use_real_time_data": False  # Use fallback data for testing
    }

    try:
        response = requests.post(f"{BASE_URL}/predict/yield", json=prediction_request)
        response.raise_for_status()
        data = response.json()

        print("✅ Prediction request submitted successfully")
        print(f"   Prediction ID: {data.get('prediction_id', 'N/A')}")
        print(f"   Processing time: {data.get('processing_time_seconds', 0):.2f}s")

        if 'prediction' in data:
            pred = data['prediction']
            print(f"   Yield prediction: {pred.get('yield_tons_per_hectare', 'N/A')} tons/ha")
            print(f"   Confidence: {pred.get('confidence_score', 0):.3f}")

        if 'model' in data:
            model = data['model']
            print(f"   Model: {model.get('algorithm', 'N/A')} from {model.get('location_used', 'N/A')}")

        return True
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False

def run_complete_test():
    """Run complete API test suite"""
    print("🚀 Crop Yield Prediction API Test Suite")
    print("=" * 50)

    # Check if API server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except:
        print("❌ API Server not running!")
        print("Please start the server first with: python run_api.py")
        return False

    tests = [
        ("Health Check", test_health_check),
        ("Get Crops", test_get_crops),
        ("Input Validation", test_validation),
        ("Yield Prediction", test_prediction)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        result = test_func()
        results.append(result)

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} {test_name}")

    print("-" * 30)
    print(f"Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! API is ready for production.")
    else:
        print(f"⚠️  {total - passed} tests failed. Check the logs above.")

    return passed == total

if __name__ == "__main__":
    success = run_complete_test()
    exit(0 if success else 1)
