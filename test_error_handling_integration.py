#!/usr/bin/env python3
"""
Quick integration test to verify error handling works end-to-end
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from variety_selection_service import VarietySelectionService
from crop_variety_database import CropVarietyDatabase


def test_error_handling_integration():
    """Test error handling with real database"""
    print("🧪 Testing Error Handling Integration...")
    print("=" * 60)
    
    # Initialize real database and service
    variety_db = CropVarietyDatabase()
    service = VarietySelectionService(variety_db)
    
    # Test 1: Input sanitization
    print("\n1. Testing input sanitization:")
    test_locations = [
        "Bhopal'; DROP TABLE--",
        "Lucknow<script>alert('xss')</script>",
        "",
        None,
        123
    ]
    
    for location in test_locations:
        try:
            region = service.map_location_to_region(location)
            print(f"   ✅ {repr(location)} → {region}")
        except Exception as e:
            print(f"   ❌ {repr(location)} → Error: {e}")
    
    # Test 2: Valid variety selection
    print("\n2. Testing valid variety selection:")
    test_cases = [
        ("Rice", "Bhopal"),
        ("Wheat", "Chandigarh"),
        ("Maize", "Lucknow")
    ]
    
    for crop_type, location in test_cases:
        try:
            result = service.select_default_variety(crop_type, location)
            print(f"   ✅ {crop_type} in {location}: {result['variety_name']} "
                  f"(reason: {result['selection_metadata']['reason']})")
        except Exception as e:
            print(f"   ❌ {crop_type} in {location}: {e}")
    
    # Test 3: Invalid inputs
    print("\n3. Testing invalid inputs:")
    invalid_cases = [
        ("", "Bhopal"),
        ("Rice", ""),
        (None, "Bhopal"),
        ("Rice", None),
        ("InvalidCrop", "Bhopal")
    ]
    
    for crop_type, location in invalid_cases:
        try:
            result = service.select_default_variety(crop_type, location)
            print(f"   ⚠️  {repr(crop_type)} in {repr(location)}: Unexpectedly succeeded")
        except ValueError as e:
            print(f"   ✅ {repr(crop_type)} in {repr(location)}: Correctly raised ValueError")
        except Exception as e:
            print(f"   ❌ {repr(crop_type)} in {repr(location)}: Unexpected error: {e}")
    
    # Test 4: Unknown location (should use fallback)
    print("\n4. Testing unknown location fallback:")
    try:
        result = service.select_default_variety("Rice", "UnknownCity")
        print(f"   ✅ Unknown location handled: {result['variety_name']} "
              f"(region: {result['selection_metadata']['region']})")
    except Exception as e:
        print(f"   ❌ Unknown location failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Error handling integration test completed!")


if __name__ == "__main__":
    test_error_handling_integration()
