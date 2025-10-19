#!/usr/bin/env python3
"""
Test script to verify error handling when VarietySelectionService initialization fails
"""

import sys
sys.path.insert(0, 'src')

def test_error_handling():
    """Test that service handles VarietySelectionService initialization failures gracefully"""
    print("🧪 Testing VarietySelectionService error handling...")
    
    # Mock a failure scenario by temporarily breaking the import
    import unittest.mock as mock
    
    try:
        # Patch VarietySelectionService to raise an exception during initialization
        with mock.patch('prediction_api.VarietySelectionService') as MockVarietySelector:
            MockVarietySelector.side_effect = Exception("Simulated initialization failure")
            
            from prediction_api import CropYieldPredictionService
            
            # Try to initialize the service
            service = CropYieldPredictionService()
            
            # Check that variety_selector is None (graceful degradation)
            assert service.variety_selector is None, "❌ variety_selector should be None on failure"
            print("✅ variety_selector is None when initialization fails (graceful degradation)")
            
            # Check that the service still initialized successfully
            assert hasattr(service, 'variety_db'), "❌ Service should still have variety_db"
            print("✅ Service still initialized successfully despite VarietySelectionService failure")
            
        print("\n✅ Error handling test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_error_handling()
    sys.exit(0 if success else 1)
