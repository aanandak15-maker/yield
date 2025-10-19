#!/usr/bin/env python3
"""
End-to-End Prediction Tests for Model Compatibility Fix

Tests all 5 locations with sample data to verify:
- Predictions are valid with yield value, confidence score, and model metadata
- Response includes new model timestamp (not fallback)
- All locations are covered
- Models are working correctly after retraining

Requirements: 4.3, 4.4
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# API base URL
BASE_URL = "http://localhost:8000"

# Test data for all 5 locations
TEST_LOCATIONS = [
    {
        "name": "Bhopal",
        "latitude": 23.2599,
        "longitude": 77.4126,
        "crop_type": "Rice",
        "variety_name": "Basmati 370"
    },
    {
        "name": "Lucknow",
        "latitude": 26.8467,
        "longitude": 80.9462,
        "crop_type": "Wheat",
        "variety_name": "HD 3086"  # Valid wheat variety
    },
    {
        "name": "Chandigarh",
        "latitude": 30.7333,
        "longitude": 76.7794,
        "crop_type": "Rice",
        "variety_name": "PR 126"  # Valid rice variety
    },
    {
        "name": "Patna",
        "latitude": 25.5941,
        "longitude": 85.1376,
        "crop_type": "Maize",
        "variety_name": "DHM 117"
    },
    {
        "name": "North India",  # Regional model
        "latitude": 28.6139,
        "longitude": 77.2090,
        "crop_type": "Rice",
        "variety_name": "Swarna"
    }
]


class PredictionTestResults:
    """Track test results"""
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
        print("\n" + "=" * 70)
        print("📊 END-TO-END PREDICTION TEST RESULTS")
        print("=" * 70)
        
        for detail in self.test_details:
            status = "✅ PASS" if detail["passed"] else "❌ FAIL"
            print(f"{status} {detail['test']}")
            if detail["details"]:
                print(f"     {detail['details']}")
        
        print("-" * 70)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print("=" * 70)
        
        if self.failed_tests == 0:
            print("🎉 All end-to-end prediction tests passed!")
            return True
        else:
            print(f"⚠️  {self.failed_tests} test(s) failed. Review details above.")
            return False


def check_api_running() -> bool:
    """Check if API server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def validate_prediction_response(response_data: Dict, location_name: str) -> Tuple[bool, List[str]]:
    """
    Validate prediction response structure and content
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check required top-level keys
    required_keys = ['prediction_id', 'timestamp', 'input', 'prediction', 'model', 'data_sources']
    for key in required_keys:
        if key not in response_data:
            issues.append(f"Missing required key: {key}")
    
    # Validate prediction section
    if 'prediction' in response_data:
        pred = response_data['prediction']
        
        # Check yield value
        if 'yield_tons_per_hectare' not in pred:
            issues.append("Missing yield_tons_per_hectare")
        else:
            yield_value = pred['yield_tons_per_hectare']
            if not isinstance(yield_value, (int, float)):
                issues.append(f"Invalid yield type: {type(yield_value)}")
            elif yield_value <= 0 or yield_value > 20:
                issues.append(f"Yield value out of reasonable range: {yield_value}")
        
        # Check confidence score
        if 'confidence_score' not in pred:
            issues.append("Missing confidence_score")
        else:
            confidence = pred['confidence_score']
            if not isinstance(confidence, (int, float)):
                issues.append(f"Invalid confidence type: {type(confidence)}")
            elif confidence < 0 or confidence > 1:
                issues.append(f"Confidence score out of range [0,1]: {confidence}")
        
        # Check bounds
        if 'lower_bound' not in pred or 'upper_bound' not in pred:
            issues.append("Missing prediction bounds")
    else:
        issues.append("Missing prediction section")
    
    # Validate model metadata
    if 'model' in response_data:
        model = response_data['model']
        
        # Check model timestamp (should not be fallback)
        if 'model_timestamp' not in model:
            issues.append("Missing model_timestamp")
        else:
            timestamp = model['model_timestamp']
            if 'fallback' in str(timestamp).lower():
                issues.append(f"Using fallback model: {timestamp}")
            else:
                # Check if timestamp is recent (after Oct 18, 2024)
                try:
                    # Extract date from timestamp like "20251018_235001"
                    if '_' in timestamp:
                        date_part = timestamp.split('_')[0]
                        if len(date_part) == 8:
                            year = int(date_part[:4])
                            month = int(date_part[4:6])
                            day = int(date_part[6:8])
                            model_date = datetime(year, month, day)
                            cutoff_date = datetime(2024, 10, 18)
                            
                            if model_date < cutoff_date:
                                issues.append(f"Model timestamp is old: {timestamp}")
                except:
                    pass  # If parsing fails, we'll just check it's not fallback
        
        # Check algorithm
        if 'algorithm' not in model:
            issues.append("Missing algorithm")
        
        # Check location used
        if 'location_used' not in model:
            issues.append("Missing location_used")
    else:
        issues.append("Missing model section")
    
    return len(issues) == 0, issues


def test_single_location_prediction(location_data: Dict, results: PredictionTestResults) -> Dict:
    """Test prediction for a single location"""
    location_name = location_data['name']
    print(f"\n🧪 Testing prediction for {location_name}...")
    
    # Calculate a valid sowing date (90 days ago for most crops)
    sowing_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    # Prepare prediction request
    prediction_request = {
        "crop_type": location_data['crop_type'],
        "variety_name": location_data['variety_name'],
        "location_name": location_name,
        "latitude": location_data['latitude'],
        "longitude": location_data['longitude'],
        "sowing_date": sowing_date,
        "use_real_time_data": False  # Use fallback data for consistent testing
    }
    
    try:
        # Make prediction request
        response = requests.post(
            f"{BASE_URL}/predict/yield",
            json=prediction_request,
            timeout=30
        )
        
        # Check HTTP status
        if response.status_code != 200:
            results.add_result(
                f"{location_name} - HTTP Status",
                False,
                f"Expected 200, got {response.status_code}"
            )
            return None
        
        results.add_result(
            f"{location_name} - HTTP Status",
            True,
            "Status 200 OK"
        )
        
        # Parse response
        response_data = response.json()
        
        # Validate response structure
        is_valid, issues = validate_prediction_response(response_data, location_name)
        
        if is_valid:
            results.add_result(
                f"{location_name} - Response Validation",
                True,
                "All required fields present and valid"
            )
        else:
            results.add_result(
                f"{location_name} - Response Validation",
                False,
                f"Issues: {', '.join(issues)}"
            )
        
        # Print prediction details
        if 'prediction' in response_data:
            pred = response_data['prediction']
            print(f"   Yield: {pred.get('yield_tons_per_hectare', 'N/A')} tons/ha")
            print(f"   Confidence: {pred.get('confidence_score', 'N/A'):.3f}")
            print(f"   Range: [{pred.get('lower_bound', 'N/A')}, {pred.get('upper_bound', 'N/A')}]")
        
        if 'model' in response_data:
            model = response_data['model']
            print(f"   Model: {model.get('algorithm', 'N/A')}")
            print(f"   Location: {model.get('location_used', 'N/A')}")
            print(f"   Timestamp: {model.get('model_timestamp', 'N/A')}")
        
        return response_data
        
    except requests.exceptions.Timeout:
        results.add_result(
            f"{location_name} - Request",
            False,
            "Request timeout (>30s)"
        )
        return None
    except requests.exceptions.RequestException as e:
        results.add_result(
            f"{location_name} - Request",
            False,
            f"Request failed: {str(e)}"
        )
        return None
    except json.JSONDecodeError as e:
        results.add_result(
            f"{location_name} - Response Parsing",
            False,
            f"Invalid JSON response: {str(e)}"
        )
        return None
    except Exception as e:
        results.add_result(
            f"{location_name} - Unexpected Error",
            False,
            f"Error: {str(e)}"
        )
        return None


def test_all_locations():
    """Test predictions for all 5 locations"""
    print("🚀 End-to-End Prediction Tests")
    print("=" * 70)
    print("Testing predictions for all 5 locations with new models")
    print("=" * 70)
    
    # Check if API is running
    print("\n🔍 Checking API server status...")
    if not check_api_running():
        print("❌ API Server not running!")
        print("Please start the server first with: python run_api.py")
        return False
    
    print("✅ API server is running")
    
    # Initialize results tracker
    results = PredictionTestResults()
    
    # Test each location
    prediction_responses = []
    for location_data in TEST_LOCATIONS:
        response = test_single_location_prediction(location_data, results)
        if response:
            prediction_responses.append({
                'location': location_data['name'],
                'response': response
            })
    
    # Additional validation: Check coverage
    print(f"\n📍 Location Coverage Check...")
    locations_tested = len(prediction_responses)
    expected_locations = len(TEST_LOCATIONS)
    
    if locations_tested == expected_locations:
        results.add_result(
            "Location Coverage",
            True,
            f"All {expected_locations} locations tested successfully"
        )
        print(f"✅ All {expected_locations} locations covered")
    else:
        results.add_result(
            "Location Coverage",
            False,
            f"Only {locations_tested}/{expected_locations} locations tested"
        )
        print(f"⚠️  Only {locations_tested}/{expected_locations} locations tested")
    
    # Check for fallback models
    print(f"\n🔍 Checking for fallback models...")
    fallback_count = 0
    for pred_data in prediction_responses:
        model_timestamp = pred_data['response'].get('model', {}).get('model_timestamp', '')
        if 'fallback' in str(model_timestamp).lower():
            fallback_count += 1
            print(f"⚠️  {pred_data['location']} using fallback model")
    
    if fallback_count == 0:
        results.add_result(
            "No Fallback Models",
            True,
            "All predictions using newly trained models"
        )
        print("✅ No fallback models detected")
    else:
        results.add_result(
            "No Fallback Models",
            False,
            f"{fallback_count} location(s) using fallback models"
        )
    
    # Print summary
    success = results.print_summary()
    
    # Save detailed results to file
    output_file = "test_results_end_to_end_predictions.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': results.total_tests,
                'passed': results.passed_tests,
                'failed': results.failed_tests,
                'success_rate': results.passed_tests / results.total_tests if results.total_tests > 0 else 0
            },
            'test_details': results.test_details,
            'predictions': prediction_responses
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    
    return success


if __name__ == "__main__":
    success = test_all_locations()
    sys.exit(0 if success else 1)
