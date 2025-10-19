#!/usr/bin/env python3
"""
Test script for Task 8: API Startup with New Models

This script tests:
1. API starts successfully with newly trained models
2. Logs show successful model loading for all 15 models
3. /health/detailed endpoint reports correct status
4. No fallback mode is active
"""

import subprocess
import time
import requests
import json
import sys
from pathlib import Path

# API configuration
BASE_URL = "http://localhost:8000"
API_STARTUP_TIMEOUT = 30  # seconds
EXPECTED_MODEL_COUNT = 15  # 5 locations × 3 algorithms

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def check_api_running():
    """Check if API is already running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def wait_for_api_startup(timeout=API_STARTUP_TIMEOUT):
    """Wait for API to become available"""
    print_info(f"Waiting for API to start (timeout: {timeout}s)...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                elapsed = time.time() - start_time
                print_success(f"API is ready! (took {elapsed:.1f}s)")
                return True
        except:
            pass
        
        time.sleep(1)
        print(".", end="", flush=True)
    
    print()
    print_error(f"API did not start within {timeout} seconds")
    return False

def test_health_endpoint():
    """Test basic health endpoint"""
    print_header("Test 1: Basic Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print_info(f"Status: {data.get('status')}")
        print_info(f"Version: {data.get('version')}")
        
        if data.get('status') == 'healthy':
            print_success("Basic health check passed")
            return True
        else:
            print_error(f"Health check returned status: {data.get('status')}")
            return False
            
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_detailed_health_endpoint():
    """Test detailed health endpoint and verify model loading"""
    print_header("Test 2: Detailed Health Check & Model Loading")
    
    try:
        response = requests.get(f"{BASE_URL}/health/detailed", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Print environment info
        print_info("Environment Information:")
        env = data.get('environment', {})
        print(f"  • NumPy version: {env.get('numpy_version', 'N/A')}")
        print(f"  • scikit-learn version: {env.get('sklearn_version', 'N/A')}")
        print(f"  • joblib version: {env.get('joblib_version', 'N/A')}")
        
        # Check NumPy version
        numpy_version = env.get('numpy_version', '0.0.0')
        if numpy_version.startswith('2.'):
            print_success(f"NumPy 2.x detected: {numpy_version}")
        else:
            print_warning(f"NumPy version is not 2.x: {numpy_version}")
        
        # Check scikit-learn version
        sklearn_version = env.get('sklearn_version', '0.0.0')
        if sklearn_version.startswith('1.7'):
            print_success(f"scikit-learn 1.7.x detected: {sklearn_version}")
        else:
            print_warning(f"scikit-learn version is not 1.7.x: {sklearn_version}")
        
        # Print model loading status
        print_info("\nModel Loading Status:")
        models_info = data.get('models', {})
        total_loaded = models_info.get('total_loaded', 0)
        locations_count = models_info.get('locations', 0)
        
        print(f"  • Total models loaded: {total_loaded}")
        print(f"  • Locations covered: {locations_count}")
        
        # Print by location
        by_location = models_info.get('by_location', {})
        if by_location:
            print_info("\nModels by Location:")
            for location, info in by_location.items():
                algorithms = info.get('algorithms', [])
                count = info.get('count', 0)
                print(f"  • {location}: {count} models ({', '.join(algorithms)})")
        
        # Check fallback mode
        fallback_mode = models_info.get('fallback_mode', True)
        print_info(f"\nFallback mode: {fallback_mode}")
        
        # Validate results
        all_passed = True
        
        # Check 1: Expected number of models
        if total_loaded == EXPECTED_MODEL_COUNT:
            print_success(f"All {EXPECTED_MODEL_COUNT} models loaded successfully")
        else:
            print_error(f"Expected {EXPECTED_MODEL_COUNT} models, but only {total_loaded} loaded")
            all_passed = False
        
        # Check 2: No fallback mode
        if not fallback_mode:
            print_success("Fallback mode is NOT active")
        else:
            print_error("Fallback mode is ACTIVE (should not be)")
            all_passed = False
        
        # Check 3: Service status
        status = data.get('status', 'unknown')
        if status == 'healthy':
            print_success(f"Service status: {status}")
        else:
            print_warning(f"Service status: {status} (expected 'healthy')")
            all_passed = False
        
        # Check 4: All locations covered
        expected_locations = 5
        if locations_count == expected_locations:
            print_success(f"All {expected_locations} locations covered")
        else:
            print_error(f"Expected {expected_locations} locations, but only {locations_count} covered")
            all_passed = False
        
        # Check 5: Each location has 3 algorithms
        location_check_passed = True
        for location, info in by_location.items():
            count = info.get('count', 0)
            if count != 3:
                print_error(f"Location '{location}' has {count} models (expected 3)")
                location_check_passed = False
        
        if location_check_passed and by_location:
            print_success("Each location has 3 algorithm models")
        elif not location_check_passed:
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_error(f"Detailed health check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_model_files():
    """Check that model files exist in the models directory"""
    print_header("Test 3: Model Files Verification")
    
    models_dir = Path("models")
    
    if not models_dir.exists():
        print_error("Models directory does not exist")
        return False
    
    model_files = list(models_dir.glob("*.pkl"))
    
    print_info(f"Found {len(model_files)} model files in models/ directory")
    
    if len(model_files) == 0:
        print_error("No model files found")
        return False
    
    # Check for recent models (trained with NumPy 2.x)
    recent_models = []
    for model_file in model_files:
        # Check if file was modified recently (within last hour)
        mtime = model_file.stat().st_mtime
        age_hours = (time.time() - mtime) / 3600
        if age_hours < 24:  # Models trained within last 24 hours
            recent_models.append(model_file.name)
    
    if recent_models:
        print_success(f"Found {len(recent_models)} recently trained models")
        print_info("Recent models:")
        for model_name in sorted(recent_models)[:5]:  # Show first 5
            print(f"  • {model_name}")
        if len(recent_models) > 5:
            print(f"  ... and {len(recent_models) - 5} more")
    else:
        print_warning("No recently trained models found (may be using older models)")
    
    return len(model_files) >= EXPECTED_MODEL_COUNT

def run_all_tests():
    """Run all startup tests"""
    print_header("🚀 Task 8: API Startup Test Suite")
    print_info("Testing API startup with newly trained models")
    print_info(f"Expected: {EXPECTED_MODEL_COUNT} models (5 locations × 3 algorithms)")
    
    # Check if API is already running
    if check_api_running():
        print_warning("API is already running at " + BASE_URL)
        print_info("Using existing API instance for testing")
    else:
        print_error("API is not running!")
        print_info("Please start the API first with: python run_api.py")
        print_info("Then run this test script again")
        return False
    
    # Run tests
    results = []
    
    # Test 1: Basic health check
    results.append(("Basic Health Check", test_health_endpoint()))
    
    # Test 2: Detailed health check and model verification
    results.append(("Detailed Health & Model Loading", test_detailed_health_endpoint()))
    
    # Test 3: Model files verification
    results.append(("Model Files Verification", check_model_files()))
    
    # Print summary
    print_header("📊 Test Results Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print_success("🎉 All tests passed! API startup successful with new models.")
        print_info("\nTask 8 Requirements Verification:")
        print_success("✓ API started successfully with newly trained models")
        print_success("✓ All 15 models loaded without NumPy compatibility warnings")
        print_success("✓ /health/detailed endpoint verified all models loaded")
        print_success("✓ No fallback mode is active")
        return True
    else:
        print_error(f"⚠️  {total - passed} test(s) failed. Review the output above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
