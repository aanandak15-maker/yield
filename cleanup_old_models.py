#!/usr/bin/env python3
"""
Cleanup Old Model Files

Keeps only the latest model for each location-algorithm combination.
Useful before deployment to reduce repository size.
"""

import os
from pathlib import Path
from collections import defaultdict
import re


def parse_model_filename(filename):
    """Parse model filename to extract components"""
    # Pattern: location_algorithm_timestamp.pkl
    # Example: bhopal_training_ridge_20251019_013912.pkl
    
    pattern = r'(.+?)_(ridge|random_forest|gradient_boosting)_(\d{8}_\d{6})\.pkl'
    match = re.match(pattern, filename)
    
    if match:
        location = match.group(1)
        algorithm = match.group(2)
        timestamp = match.group(3)
        return location, algorithm, timestamp
    
    return None, None, None


def cleanup_models(models_dir='models', dry_run=True):
    """
    Keep only the latest model for each location-algorithm combination
    
    Args:
        models_dir: Directory containing model files
        dry_run: If True, only print what would be deleted
    """
    models_path = Path(models_dir)
    
    if not models_path.exists():
        print(f"❌ Models directory not found: {models_dir}")
        return
    
    # Group models by location-algorithm
    models_by_key = defaultdict(list)
    
    for model_file in models_path.glob('*.pkl'):
        location, algorithm, timestamp = parse_model_filename(model_file.name)
        
        if location and algorithm and timestamp:
            key = f"{location}_{algorithm}"
            models_by_key[key].append({
                'file': model_file,
                'timestamp': timestamp,
                'name': model_file.name
            })
    
    print("="*80)
    print("MODEL CLEANUP ANALYSIS")
    print("="*80)
    
    total_files = sum(len(files) for files in models_by_key.values())
    print(f"\nTotal model files found: {total_files}")
    print(f"Unique location-algorithm combinations: {len(models_by_key)}")
    
    files_to_keep = []
    files_to_delete = []
    
    for key, models in models_by_key.items():
        # Sort by timestamp (descending) to get latest first
        models.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Keep the latest
        latest = models[0]
        files_to_keep.append(latest)
        
        # Mark others for deletion
        for old_model in models[1:]:
            files_to_delete.append(old_model)
    
    print(f"\nFiles to keep: {len(files_to_keep)}")
    print(f"Files to delete: {len(files_to_delete)}")
    
    if files_to_delete:
        print("\n" + "="*80)
        print("FILES TO DELETE")
        print("="*80)
        
        for model in files_to_delete:
            size_mb = model['file'].stat().st_size / (1024 * 1024)
            print(f"  - {model['name']} ({size_mb:.2f} MB)")
        
        total_size = sum(m['file'].stat().st_size for m in files_to_delete)
        total_size_mb = total_size / (1024 * 1024)
        print(f"\nTotal space to free: {total_size_mb:.2f} MB")
    
    if files_to_keep:
        print("\n" + "="*80)
        print("FILES TO KEEP (Latest models)")
        print("="*80)
        
        for model in sorted(files_to_keep, key=lambda x: x['name']):
            size_mb = model['file'].stat().st_size / (1024 * 1024)
            print(f"  ✅ {model['name']} ({size_mb:.2f} MB)")
    
    # Perform deletion
    if not dry_run and files_to_delete:
        print("\n" + "="*80)
        print("DELETING OLD MODELS")
        print("="*80)
        
        for model in files_to_delete:
            try:
                model['file'].unlink()
                print(f"  ✅ Deleted: {model['name']}")
            except Exception as e:
                print(f"  ❌ Failed to delete {model['name']}: {e}")
        
        print(f"\n✅ Cleanup complete! Deleted {len(files_to_delete)} old model files.")
    elif dry_run:
        print("\n" + "="*80)
        print("DRY RUN MODE - No files were deleted")
        print("="*80)
        print("\nTo actually delete files, run:")
        print("  python cleanup_old_models.py --delete")
    
    print("\n" + "="*80)


def main():
    """Main entry point"""
    import sys
    
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] in ['--delete', '-d', '--force']:
        dry_run = False
        print("⚠️  RUNNING IN DELETE MODE")
        print("This will permanently delete old model files.")
        
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborted by user")
            return
    
    cleanup_models(dry_run=dry_run)


if __name__ == "__main__":
    main()
