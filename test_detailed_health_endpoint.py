#!/usr/bin/env python3
"""
Test script for the detailed health check endpoint
"""

import requests
import json
import sys

def test_detailed_health_endpoint():
    """Test the /health/detailed endpoint"""
    
    # Test endpoint URL
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/health/detailed"
    
    print("=" * 60)
    print("Testing /health/detailed endpoint")
    print("=" * 60)
    
    try:
        # Make request to detailed health endpoint
        print(f"\n📡 Sending GET request to {endpoint}...")
        response = requests.get(endpoint, timeout=10)
        
        print(f"✅ Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n📊 Response Data:")
            print(json.dumps(data, indent=2))
            
            # Validate response structure
            print("\n🔍 Validating response structure...")
            
            required_fields = ['status', 'timestamp', 'environment', 'models']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            # Check environment section
            env = data.get('environment', {})
            env_fields = ['numpy_version', 'sklearn_version', 'joblib_version']
            missing_env = [field for field in env_fields if field not in env]
            
            if missing_env:
                print(f"❌ Missing environment fields: {missing_env}")
                return False
            
            print(f"✅ Environment versions:")
            print(f"   - NumPy: {env['numpy_version']}")
            print(f"   - scikit-learn: {env['sklearn_version']}")
            print(f"   - joblib: {env['joblib_version']}")
            
            # Check models section
            models = data.get('models', {})
            model_fields = ['total_loaded', 'locations', 'by_location', 'fallback_mode']
            missing_models = [field for field in model_fields if field not in models]
            
            if missing_models:
                print(f"❌ Missing model fields: {missing_models}")
                return False
            
            print(f"\n✅ Model status:")
            print(f"   - Total loaded: {models['total_loaded']}")
            print(f"   - Locations: {models['locations']}")
            print(f"   - Fallback mode: {models['fallback_mode']}")
            print(f"   - By location: {json.dumps(models['by_location'], indent=6)}")
            
            # Check overall status
            status = data.get('status')
            print(f"\n✅ Overall service status: {status}")
            
            if status == 'healthy':
                print("✅ Service is healthy!")
            elif status == 'degraded':
                print("⚠️  Service is degraded (using fallback models or limited models)")
            else:
                print(f"❓ Unknown status: {status}")
            
            print("\n" + "=" * 60)
            print("✅ All validation checks passed!")
            print("=" * 60)
            return True
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the API server running?")
        print("   Start the server with: python src/prediction_api.py")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_with_basic_health():
    """Compare detailed health with basic health endpoint"""
    base_url = "http://localhost:8000"
    
    print("\n" + "=" * 60)
    print("Comparing /health and /health/detailed endpoints")
    print("=" * 60)
    
    try:
        # Get basic health
        basic_response = requests.get(f"{base_url}/health", timeout=10)
        detailed_response = requests.get(f"{base_url}/health/detailed", timeout=10)
        
        if basic_response.status_code == 200 and detailed_response.status_code == 200:
            basic_data = basic_response.json()
            detailed_data = detailed_response.json()
            
            print("\n📊 Basic Health Response:")
            print(json.dumps(basic_data, indent=2))
            
            print("\n📊 Detailed Health Response:")
            print(json.dumps(detailed_data, indent=2))
            
            # Compare model counts
            basic_models = basic_data.get('components', {}).get('models_loaded', 0)
            detailed_models = detailed_data.get('models', {}).get('total_loaded', 0)
            
            print(f"\n🔍 Model count comparison:")
            print(f"   - Basic health: {basic_models} models")
            print(f"   - Detailed health: {detailed_models} models")
            
            if basic_models == detailed_models:
                print("✅ Model counts match!")
            else:
                print("⚠️  Model counts differ")
            
            return True
        else:
            print("❌ One or both endpoints failed")
            return False
            
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting detailed health endpoint tests...\n")
    
    # Test detailed health endpoint
    test_passed = test_detailed_health_endpoint()
    
    if test_passed:
        # Compare with basic health
        compare_with_basic_health()
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
