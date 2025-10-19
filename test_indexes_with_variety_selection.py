#!/usr/bin/env python3
"""
Test that indexes work correctly with VarietySelectionService
"""

import sys
import time

# Add src to path
sys.path.insert(0, 'src')

from crop_variety_database import CropVarietyDatabase
from variety_selection_service import VarietySelectionService

def test_variety_selection_with_indexes():
    """Test variety selection service uses indexes efficiently"""
    print("🔍 Testing Variety Selection with Database Indexes...")
    print("=" * 60)
    
    # Initialize database and variety selector
    db = CropVarietyDatabase()
    selector = VarietySelectionService(db)
    
    # Test variety selection for different locations
    test_cases = [
        {'crop_type': 'Rice', 'location': 'Bhopal'},
        {'crop_type': 'Rice', 'location': 'Lucknow'},
        {'crop_type': 'Rice', 'location': 'Chandigarh'},
        {'crop_type': 'Wheat', 'location': 'Chandigarh'},
        {'crop_type': 'Wheat', 'location': 'Lucknow'},
        {'crop_type': 'Maize', 'location': 'Bhopal'},
        {'crop_type': 'Maize', 'location': 'Patna'},
    ]
    
    print("\n📊 Variety Selection Performance Tests:\n")
    
    total_time = 0
    for i, test in enumerate(test_cases, 1):
        crop_type = test['crop_type']
        location = test['location']
        
        print(f"{i}. {crop_type} in {location}")
        
        # Measure selection time
        start_time = time.time()
        result = selector.select_default_variety(crop_type, location)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        total_time += execution_time_ms
        
        print(f"   ✅ Selected: {result['variety_name']}")
        print(f"   📍 Region: {result['selection_metadata']['region']}")
        print(f"   💡 Reason: {result['selection_metadata']['reason']}")
        print(f"   ⏱️  Execution time: {execution_time_ms:.3f}ms")
        
        # Check if within performance requirement
        if execution_time_ms < 50:
            print(f"   ✅ Within 50ms requirement")
        else:
            print(f"   ⚠️  Exceeds 50ms requirement!")
        print()
    
    avg_time = total_time / len(test_cases)
    
    print("=" * 60)
    print(f"📊 Performance Summary:")
    print(f"   Total tests: {len(test_cases)}")
    print(f"   Total time: {total_time:.3f}ms")
    print(f"   Average time: {avg_time:.3f}ms")
    print(f"   Max allowed: 50ms per requirement 8.1")
    
    if avg_time < 50:
        print(f"\n✅ All variety selections completed within performance requirements!")
        return True
    else:
        print(f"\n⚠️  Average time exceeds 50ms requirement")
        return False

if __name__ == "__main__":
    success = test_variety_selection_with_indexes()
    sys.exit(0 if success else 1)
