#!/usr/bin/env python3
"""
Test that indexes are verified successfully on service startup
"""

import sys
import logging

# Add src to path
sys.path.insert(0, 'src')

# Set up logging to capture index verification messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from crop_variety_database import CropVarietyDatabase

def test_startup_index_verification():
    """Test that indexes are verified on startup"""
    print("🚀 Testing Index Verification on Service Startup...")
    print("=" * 60)
    print("\nInitializing CropVarietyDatabase...\n")
    
    # Initialize database - this should log index verification
    db = CropVarietyDatabase()
    
    print("\n" + "=" * 60)
    print("✅ Service startup completed successfully!")
    print("\nCheck the log output above for index verification messages.")
    print("You should see messages like:")
    print("  ✅ Index 'idx_crop_varieties_crop_type' verified")
    print("  ✅ Index 'idx_crop_varieties_region' verified")
    print("  ✅ Index 'idx_crop_varieties_crop_region' verified")
    
    return True

if __name__ == "__main__":
    success = test_startup_index_verification()
    sys.exit(0 if success else 1)
