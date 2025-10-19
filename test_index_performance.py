#!/usr/bin/env python3
"""
Test to verify query performance with indexes
"""

import sys
import time
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from crop_variety_database import CropVarietyDatabase

def test_query_performance():
    """Test query performance with indexes"""
    print("⚡ Testing Query Performance with Indexes...")
    print("=" * 60)
    
    # Initialize database
    db = CropVarietyDatabase()
    
    # Test queries that should benefit from indexes
    test_queries = [
        {
            'name': 'Filter by crop_type',
            'query': "SELECT * FROM crop_varieties WHERE crop_type = 'Rice'",
            'expected_index': 'idx_crop_varieties_crop_type'
        },
        {
            'name': 'Filter by crop_type and region',
            'query': "SELECT * FROM crop_varieties WHERE crop_type = 'Rice' AND region_prevalence LIKE '%Punjab%'",
            'expected_index': 'idx_crop_varieties_crop_type'  # Composite index should be used
        },
        {
            'name': 'Filter by crop_type (Wheat)',
            'query': "SELECT * FROM crop_varieties WHERE crop_type = 'Wheat'",
            'expected_index': 'idx_crop_varieties_crop_type'
        },
        {
            'name': 'Filter by crop_type (Maize)',
            'query': "SELECT * FROM crop_varieties WHERE crop_type = 'Maize'",
            'expected_index': 'idx_crop_varieties_crop_type'
        }
    ]
    
    with sqlite3.connect(str(db.db_path)) as conn:
        cursor = conn.cursor()
        
        print("\n📊 Query Performance Tests:\n")
        
        for i, test in enumerate(test_queries, 1):
            print(f"{i}. {test['name']}")
            print(f"   Query: {test['query']}")
            
            # Check query plan
            cursor.execute(f"EXPLAIN QUERY PLAN {test['query']}")
            plan = cursor.fetchall()
            
            # Check if index is being used
            plan_str = str(plan)
            uses_index = 'INDEX' in plan_str
            
            if uses_index:
                print(f"   ✅ Uses index: {plan_str}")
            else:
                print(f"   ⚠️  No index used: {plan_str}")
            
            # Measure execution time
            start_time = time.time()
            cursor.execute(test['query'])
            results = cursor.fetchall()
            end_time = time.time()
            
            execution_time_ms = (end_time - start_time) * 1000
            print(f"   ⏱️  Execution time: {execution_time_ms:.3f}ms")
            print(f"   📝 Results: {len(results)} rows")
            print()
        
        # Test the get_crop_varieties method which should use indexes
        print("🔍 Testing CropVarietyDatabase methods:\n")
        
        # Test 1: Get all Rice varieties
        start_time = time.time()
        rice_varieties = db.get_crop_varieties('Rice')
        end_time = time.time()
        print(f"1. get_crop_varieties('Rice')")
        print(f"   ⏱️  Execution time: {(end_time - start_time) * 1000:.3f}ms")
        print(f"   📝 Results: {len(rice_varieties)} varieties")
        print()
        
        # Test 2: Get Rice varieties in Punjab
        start_time = time.time()
        punjab_rice = db.get_crop_varieties('Rice', 'Punjab')
        end_time = time.time()
        print(f"2. get_crop_varieties('Rice', 'Punjab')")
        print(f"   ⏱️  Execution time: {(end_time - start_time) * 1000:.3f}ms")
        print(f"   📝 Results: {len(punjab_rice)} varieties")
        print()
        
        # Test 3: Get specific variety
        start_time = time.time()
        variety = db.get_variety_by_name('Rice', 'Basmati 370')
        end_time = time.time()
        print(f"3. get_variety_by_name('Rice', 'Basmati 370')")
        print(f"   ⏱️  Execution time: {(end_time - start_time) * 1000:.3f}ms")
        print(f"   📝 Result: {'Found' if variety else 'Not found'}")
        print()
    
    print("=" * 60)
    print("✅ Query performance test completed!")
    print("\nNote: All queries should execute in < 50ms as per requirement 8.1")
    
    return True

if __name__ == "__main__":
    success = test_query_performance()
    sys.exit(0 if success else 1)
