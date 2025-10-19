#!/usr/bin/env python3
"""
Test script to verify database indexes are created successfully
"""

import sys
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from crop_variety_database import CropVarietyDatabase

def test_database_indexes():
    """Test that database indexes are created successfully"""
    print("🔍 Testing Database Indexes...")
    print("=" * 60)
    
    # Initialize database (this will create indexes)
    db = CropVarietyDatabase()
    
    # Connect to database and check indexes
    with sqlite3.connect(str(db.db_path)) as conn:
        cursor = conn.cursor()
        
        # Get all indexes for crop_varieties table
        cursor.execute('''
            SELECT name, sql FROM sqlite_master 
            WHERE type='index' AND tbl_name='crop_varieties'
            ORDER BY name
        ''')
        
        indexes = cursor.fetchall()
        
        print(f"\n📊 Found {len(indexes)} indexes on crop_varieties table:\n")
        
        expected_indexes = {
            'idx_crop_varieties_crop_type': 'crop_type',
            'idx_crop_varieties_region': 'region_prevalence',
            'idx_crop_varieties_crop_region': 'crop_type, region_prevalence'
        }
        
        found_indexes = {}
        for idx_name, idx_sql in indexes:
            if idx_name and not idx_name.startswith('sqlite_'):
                found_indexes[idx_name] = idx_sql
                print(f"  ✅ {idx_name}")
                if idx_sql:
                    print(f"     SQL: {idx_sql}")
                print()
        
        # Verify expected indexes exist
        print("\n🔍 Verification Results:\n")
        all_found = True
        
        for expected_idx, columns in expected_indexes.items():
            if expected_idx in found_indexes:
                print(f"  ✅ {expected_idx} - FOUND (columns: {columns})")
            else:
                print(f"  ❌ {expected_idx} - MISSING (expected columns: {columns})")
                all_found = False
        
        print("\n" + "=" * 60)
        
        if all_found:
            print("✅ All expected indexes are present!")
            
            # Test query performance with indexes
            print("\n🚀 Testing Query Performance with Indexes...\n")
            
            # Test 1: Query by crop_type (uses idx_crop_varieties_crop_type)
            cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM crop_varieties WHERE crop_type = 'Rice'")
            plan = cursor.fetchall()
            print("  Query 1: SELECT * FROM crop_varieties WHERE crop_type = 'Rice'")
            for row in plan:
                print(f"    {row}")
            
            # Test 2: Query by region (uses idx_crop_varieties_region)
            cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM crop_varieties WHERE region_prevalence LIKE '%Punjab%'")
            plan = cursor.fetchall()
            print("\n  Query 2: SELECT * FROM crop_varieties WHERE region_prevalence LIKE '%Punjab%'")
            for row in plan:
                print(f"    {row}")
            
            # Test 3: Query by crop_type and region (uses idx_crop_varieties_crop_region)
            cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM crop_varieties WHERE crop_type = 'Rice' AND region_prevalence LIKE '%Punjab%'")
            plan = cursor.fetchall()
            print("\n  Query 3: SELECT * FROM crop_varieties WHERE crop_type = 'Rice' AND region_prevalence LIKE '%Punjab%'")
            for row in plan:
                print(f"    {row}")
            
            print("\n" + "=" * 60)
            print("✅ Database indexes test PASSED!")
            return True
        else:
            print("❌ Some expected indexes are missing!")
            return False

if __name__ == "__main__":
    success = test_database_indexes()
    sys.exit(0 if success else 1)
