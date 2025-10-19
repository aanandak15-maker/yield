#!/usr/bin/env python3
"""
Test script to verify VarietySelectionService integration into CropYieldPredictionService
"""

import sys
sys.path.insert(0, 'src')

from prediction_api import CropYieldPredictionService

def test_variety_selector_integration():
    """Test that VarietySelectionService is properly integrated"""
    print("🧪 Testing VarietySelectionService integration...")
    
    try:
        # Initialize the prediction service
        service = CropYieldPredictionService()
        
        # Check that variety_selector attribute exists
        assert hasattr(service, 'variety_selector'), "❌ variety_selector attribute not found"
        print("✅ variety_selector attribute exists")
        
        # Check that variety_selector is not None
        assert service.variety_selector is not None, "❌ variety_selector is None"
        print("✅ variety_selector is initialized (not None)")
        
        # Check that variety_selector has the expected methods
        assert hasattr(service.variety_selector, 'select_default_variety'), "❌ select_default_variety method not found"
        print("✅ select_default_variety method exists")
        
        assert hasattr(service.variety_selector, 'map_location_to_region'), "❌ map_location_to_region method not found"
        print("✅ map_location_to_region method exists")
        
        assert hasattr(service.variety_selector, 'get_regional_varieties'), "❌ get_regional_varieties method not found"
        print("✅ get_regional_varieties method exists")
        
        assert hasattr(service.variety_selector, 'get_global_default'), "❌ get_global_default method not found"
        print("✅ get_global_default method exists")
        
        # Check that variety_db was passed correctly
        assert service.variety_selector.variety_db is service.variety_db, "❌ variety_db not passed correctly"
        print("✅ variety_db instance passed correctly to VarietySelectionService")
        
        print("\n✅ All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_variety_selector_integration()
    sys.exit(0 if success else 1)
