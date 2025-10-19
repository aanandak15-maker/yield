#!/usr/bin/env python3
"""
Extract original model metrics from backed up model files.
This creates a training_summary_backup.json file for validation comparison.
"""

import json
import joblib
import logging
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_metrics_from_backup():
    """Extract metrics from backed up model files"""
    backup_dir = Path("models_backup")
    
    if not backup_dir.exists():
        logger.error("models_backup directory not found!")
        return None
    
    # Get the OLDEST model files for each location/algorithm combination
    # (to get the original pre-retraining metrics)
    model_files = defaultdict(lambda: {'path': None, 'timestamp': '99999999_999999'})
    
    for model_file in backup_dir.glob("*.pkl"):
        # Parse filename: location_algorithm_timestamp.pkl
        parts = model_file.stem.split('_')
        
        # Handle multi-word locations (e.g., north_india_regional)
        if 'north_india_regional' in model_file.name:
            location = 'north_india_regional'
            algorithm_parts = parts[3:]
        else:
            location = parts[0]
            algorithm_parts = parts[2:]
        
        # Get algorithm name (everything except timestamp)
        algorithm = '_'.join(algorithm_parts[:-1])
        timestamp = algorithm_parts[-1]
        
        key = f"{location}_{algorithm}"
        
        # Keep the OLDEST file (original models before any retraining)
        if timestamp < model_files[key]['timestamp']:
            model_files[key] = {'path': model_file, 'timestamp': timestamp}
    
    logger.info(f"Found {len(model_files)} unique model combinations in backup")
    
    # Extract metrics from each model
    datasets = defaultdict(lambda: {'models': {}})
    
    for key, info in model_files.items():
        model_path = info['path']
        
        try:
            logger.info(f"Loading {model_path.name}...")
            model_data = joblib.load(model_path)
            
            # Extract dataset and algorithm
            if 'north_india_regional' in model_path.name:
                dataset = 'north_india_regional'
                algorithm = key.replace('north_india_regional_', '')
            else:
                parts = key.split('_')
                dataset = parts[0] + '_training'
                algorithm = '_'.join(parts[1:])
            
            # Remove timestamp suffix from algorithm name if present
            algorithm_parts = algorithm.split('_')
            if algorithm_parts[-1].isdigit() and len(algorithm_parts[-1]) == 8:
                algorithm = '_'.join(algorithm_parts[:-1])
            
            # Get metrics
            if isinstance(model_data, dict) and 'metrics' in model_data:
                metrics = model_data['metrics']
                
                datasets[dataset]['models'][algorithm] = {
                    'r2_score': metrics.get('test_r2', 0.0),
                    'mae': metrics.get('test_mae', 0.0),
                    'rmse': metrics.get('test_rmse', 0.0),
                    'train_r2': metrics.get('train_r2', 0.0),
                    'train_mae': metrics.get('train_mae', 0.0),
                    'train_rmse': metrics.get('train_rmse', 0.0)
                }
                
                logger.info(f"  ✓ Extracted metrics for {dataset} - {algorithm}")
            else:
                logger.warning(f"  ✗ No metrics found in {model_path.name}")
                
        except Exception as e:
            logger.error(f"  ✗ Failed to load {model_path.name}: {e}")
    
    # Create training summary structure
    training_summary = {
        'datasets': dict(datasets),
        'metadata': {
            'source': 'extracted_from_backup_models',
            'backup_directory': str(backup_dir)
        }
    }
    
    return training_summary


def main():
    """Main entry point"""
    logger.info("Extracting original metrics from backed up models...")
    
    training_summary = extract_metrics_from_backup()
    
    if training_summary is None:
        logger.error("Failed to extract metrics")
        return 1
    
    # Save to backup file
    output_path = Path("model_results/training_summary_backup.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(training_summary, f, indent=2)
    
    logger.info(f"\n✅ Original metrics saved to: {output_path}")
    
    # Print summary
    total_models = sum(len(d['models']) for d in training_summary['datasets'].values())
    logger.info(f"   Total datasets: {len(training_summary['datasets'])}")
    logger.info(f"   Total models: {total_models}")
    
    return 0


if __name__ == '__main__':
    exit(main())
