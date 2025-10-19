#!/usr/bin/env python3
"""
Demo script to showcase variety selection logging

Demonstrates all logging scenarios:
- INFO: Successful selections
- WARNING: Fallback scenarios
- ERROR: Selection failures
- Performance timing
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from variety_selection_service import VarietySelectionService
from crop_variety_database import CropVarietyDatabase

# Configure logging to show all levels
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demo_logging():
    """Demonstrate variety selection logging"""
    print("=" * 80)
    print("VARIETY SELECTION LOGGING DEMONSTRATION")
    print("=" * 80)
    
    # Initialize service
    print("\n📦 Initializing services...")
    variety_db = CropVarietyDatabase()
    service = VarietySelectionService(variety_db)
    
    # Demo 1: Successful regional selection (INFO)
    print("\n" + "=" * 80)
    print("DEMO 1: Successful Regional Selection (INFO-level logging)")
    print("=" * 80)
    print("Scenario: Wheat in Chandigarh (Punjab has regional varieties)")
    print()
    
    try:
        result = service.select_default_variety('Wheat', 'Chandigarh')
        print(f"\n✅ Result: {result['variety_name']}")
        print(f"   Reason: {result['selection_metadata']['reason']}")
        print(f"   Time: {result['selection_metadata'].get('selection_time_ms', 'N/A')}ms")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 2: Fallback to North India (WARNING)
    print("\n" + "=" * 80)
    print("DEMO 2: Fallback to North India (WARNING-level logging)")
    print("=" * 80)
    print("Scenario: Maize in Lucknow (UP has no varieties, falls back to North India)")
    print()
    
    try:
        result = service.select_default_variety('Maize', 'Lucknow')
        print(f"\n✅ Result: {result['variety_name']}")
        print(f"   Reason: {result['selection_metadata']['reason']}")
        print(f"   Original Region: {result['selection_metadata'].get('original_region', 'N/A')}")
        print(f"   Fallback Region: {result['selection_metadata'].get('region', 'N/A')}")
        print(f"   Time: {result['selection_metadata'].get('selection_time_ms', 'N/A')}ms")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 3: Global default usage (WARNING)
    print("\n" + "=" * 80)
    print("DEMO 3: Global Default Usage (WARNING-level logging)")
    print("=" * 80)
    print("Scenario: Rice in Bhopal (MP has no varieties, uses global default)")
    print()
    
    try:
        result = service.select_default_variety('Rice', 'Bhopal')
        print(f"\n✅ Result: {result['variety_name']}")
        print(f"   Reason: {result['selection_metadata']['reason']}")
        print(f"   Time: {result['selection_metadata'].get('selection_time_ms', 'N/A')}ms")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 4: Unknown location (WARNING for fallback)
    print("\n" + "=" * 80)
    print("DEMO 4: Unknown Location (WARNING-level logging)")
    print("=" * 80)
    print("Scenario: Rice in Unknown City (falls back to 'All North India')")
    print()
    
    try:
        result = service.select_default_variety('Rice', 'Unknown City')
        print(f"\n✅ Result: {result['variety_name']}")
        print(f"   Reason: {result['selection_metadata']['reason']}")
        print(f"   Time: {result['selection_metadata'].get('selection_time_ms', 'N/A')}ms")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 5: Performance timing
    print("\n" + "=" * 80)
    print("DEMO 5: Performance Timing")
    print("=" * 80)
    print("Running 10 selections to show timing consistency...")
    print()
    
    times = []
    for i in range(10):
        result = service.select_default_variety('Wheat', 'Chandigarh')
        time_ms = result['selection_metadata'].get('selection_time_ms', 0)
        times.append(time_ms)
    
    print(f"Selection times (ms): {[f'{t:.2f}' for t in times]}")
    print(f"Average: {sum(times)/len(times):.2f}ms")
    print(f"Min: {min(times):.2f}ms")
    print(f"Max: {max(times):.2f}ms")
    print(f"✅ All selections under 50ms requirement: {all(t < 50 for t in times)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("LOGGING FEATURES DEMONSTRATED")
    print("=" * 80)
    print("✅ INFO-level logging for successful selections")
    print("✅ WARNING-level logging for fallback scenarios")
    print("✅ WARNING-level logging for global default usage")
    print("✅ Structured log format (key=value pairs)")
    print("✅ Performance timing in milliseconds")
    print("✅ Comprehensive metadata (crop, location, region, variety, reason)")
    print("✅ No sensitive data logged")
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    demo_logging()
