#!/usr/bin/env python3
"""
Test script for Task 4: Verify optional variety handling in predict_yield method
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test the predict_yield method with optional variety
def test_optional_variety_handling():
    """Test that predict_yield handles optional variety correctly"""
    print("🧪 Testing Task 4: Optional Variety Handling in predict_yield")
    print("=" * 60)
    
    try:
        from prediction_api import CropYieldPredictionService
        
        # Initialize service
        print("\n1️⃣ Initializing prediction service...")
        service = CropYieldPredictionService()
        print("   ✅ Service initialized")
        
        # Test case 1: Request WITHOUT variety_name (should trigger selection)
        print("\n2️⃣ Testing prediction WITHOUT variety_name...")
        request_without_variety = {
            'crop_type': 'Rice',
            'variety_name': None,  # Missing variety
            'location_name': 'Bhopal',
            'latitude': 23.2599,
            'longitude': 77.4126,
            'sowing_date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
            'use_real_time_data': False  # Use fallback data for faster testing
        }
        
        print(f"   Request: {json.dumps(request_without_variety, indent=2)}")
        
        # This should trigger variety selection
        result = service.predict_yield(request_without_variety)
        
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
            return False
        
        print(f"   ✅ Prediction successful!")
        print(f"   Selected variety: {result['input']['variety_name']}")
        
        # Verify variety was selected
        if result['input']['variety_name'] is None:
            print("   ❌ FAIL: Variety was not selected")
            return False
        
        print("   ✅ PASS: Variety was automatically selected")
        
        # Test case 2: Request WITH variety_name (should preserve existing behavior)
        print("\n3️⃣ Testing prediction WITH variety_name...")
        request_with_variety = {
            'crop_type': 'Rice',
            'variety_name': 'Basmati 370',  # Explicit variety
            'location_name': 'Bhopal',
            'latitude': 23.2599,
            'longitude': 77.4126,
            'sowing_date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
            'use_real_time_data': False
        }
        
        print(f"   Request: {json.dumps(request_with_variety, indent=2)}")
        
        result = service.predict_yield(request_with_variety)
        
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
            return False
        
        print(f"   ✅ Prediction successful!")
        print(f"   Used variety: {result['input']['variety_name']}")
        
        # Verify the specified variety was used
        if result['input']['variety_name'] != 'Basmati 370':
            print(f"   ❌ FAIL: Expected 'Basmati 370', got '{result['input']['variety_name']}'")
            return False
        
        print("   ✅ PASS: Specified variety was used")
        
        # Test case 3: Request with empty string variety_name
        print("\n4️⃣ Testing prediction with empty string variety_name...")
        request_empty_variety = {
            'crop_type': 'Wheat',
            'variety_name': '',  # Empty string
            'location_name': 'Chandigarh',
            'latitude': 30.7333,
            'longitude': 76.7794,
            'sowing_date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
            'use_real_time_data': False
        }
        
        result = service.predict_yield(request_empty_variety)
        
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
            return False
        
        print(f"   ✅ Prediction successful!")
        print(f"   Selected variety: {result['input']['variety_name']}")
        
        # Verify variety was selected (empty string should trigger selection)
        if not result['input']['variety_name']:
            print("   ❌ FAIL: Variety was not selected for empty string")
            return False
        
        print("   ✅ PASS: Empty string triggered variety selection")
        
        print("\n" + "=" * 60)
        print("🎉 All Task 4 tests PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_optional_variety_handling()
    sys.exit(0 if success else 1)
