#!/usr/bin/env python3
"""
Model Performance Validation Script

Compares original model metrics with retrained model metrics to ensure
performance is maintained within acceptable thresholds (5% degradation).
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelPerformanceValidator:
    """Validates retrained model performance against original baselines"""
    
    def __init__(self, threshold_percent: float = 5.0):
        """
        Initialize validator
        
        Args:
            threshold_percent: Maximum acceptable performance degradation (%)
        """
        self.threshold_percent = threshold_percent
        self.original_metrics_path = Path("model_results/training_summary.json")
        self.new_metrics_path = Path("model_results/training_summary.json")
        self.backup_metrics_path = Path("model_results/training_summary_backup.json")
        
    def load_original_metrics(self) -> Dict[str, Any]:
        """Load original model metrics from backup or current file"""
        # Try backup first (if models were retrained)
        if self.backup_metrics_path.exists():
            logger.info(f"Loading original metrics from backup: {self.backup_metrics_path}")
            with open(self.backup_metrics_path, 'r') as f:
                return json.load(f)
        
        # Fall back to current file
        if self.original_metrics_path.exists():
            logger.info(f"Loading original metrics from: {self.original_metrics_path}")
            with open(self.original_metrics_path, 'r') as f:
                return json.load(f)
        
        raise FileNotFoundError(
            f"Could not find original metrics at {self.original_metrics_path} "
            f"or {self.backup_metrics_path}"
        )
    
    def load_new_metrics(self) -> Dict[str, Any]:
        """Load newly trained model metrics"""
        if not self.new_metrics_path.exists():
            raise FileNotFoundError(
                f"Could not find new model metrics at {self.new_metrics_path}. "
                "Please retrain models first."
            )
        
        logger.info(f"Loading new metrics from: {self.new_metrics_path}")
        with open(self.new_metrics_path, 'r') as f:
            return json.load(f)
    
    def calculate_delta(self, original: float, new: float) -> Tuple[float, float]:
        """
        Calculate absolute and percentage change
        
        Args:
            original: Original metric value
            new: New metric value
            
        Returns:
            Tuple of (absolute_delta, percentage_delta)
        """
        absolute_delta = new - original
        
        # For metrics where higher is better (R²), negative delta is degradation
        # For metrics where lower is better (MAE, RMSE), positive delta is degradation
        if original != 0:
            percentage_delta = (absolute_delta / abs(original)) * 100
        else:
            percentage_delta = 0.0
        
        return absolute_delta, percentage_delta
    
    def is_acceptable(self, metric_name: str, percentage_delta: float) -> bool:
        """
        Check if performance change is within acceptable threshold
        
        Args:
            metric_name: Name of metric (r2_score, mae, rmse)
            percentage_delta: Percentage change in metric
            
        Returns:
            True if within acceptable threshold
        """
        # For R² (higher is better), check if it decreased more than threshold
        if metric_name == 'r2_score':
            return percentage_delta >= -self.threshold_percent
        
        # For MAE and RMSE (lower is better), check if it increased more than threshold
        else:
            return percentage_delta <= self.threshold_percent
    
    def compare_models(self, original_data: Dict, new_data: Dict) -> Dict[str, Any]:
        """
        Compare original and new model metrics
        
        Args:
            original_data: Original training summary
            new_data: New training summary
            
        Returns:
            Comparison report dictionary
        """
        comparison = {}
        
        for dataset_name, dataset_info in original_data.get('datasets', {}).items():
            if dataset_name not in new_data.get('datasets', {}):
                logger.warning(f"Dataset {dataset_name} not found in new metrics")
                continue
            
            new_dataset_info = new_data['datasets'][dataset_name]
            
            for model_name, original_metrics in dataset_info.get('models', {}).items():
                if model_name not in new_dataset_info.get('models', {}):
                    logger.warning(
                        f"Model {model_name} for {dataset_name} not found in new metrics"
                    )
                    continue
                
                new_metrics = new_dataset_info['models'][model_name]
                
                # Create comparison key
                comparison_key = f"{dataset_name}_{model_name}"
                
                # Compare each metric
                r2_delta_abs, r2_delta_pct = self.calculate_delta(
                    original_metrics['r2_score'],
                    new_metrics['r2_score']
                )
                
                mae_delta_abs, mae_delta_pct = self.calculate_delta(
                    original_metrics['mae'],
                    new_metrics['mae']
                )
                
                rmse_delta_abs, rmse_delta_pct = self.calculate_delta(
                    original_metrics['rmse'],
                    new_metrics['rmse']
                )
                
                # Check if all metrics are acceptable
                r2_acceptable = self.is_acceptable('r2_score', r2_delta_pct)
                mae_acceptable = self.is_acceptable('mae', mae_delta_pct)
                rmse_acceptable = self.is_acceptable('rmse', rmse_delta_pct)
                
                all_acceptable = r2_acceptable and mae_acceptable and rmse_acceptable
                
                comparison[comparison_key] = {
                    'dataset': dataset_name,
                    'model': model_name,
                    'original': {
                        'r2_score': original_metrics['r2_score'],
                        'mae': original_metrics['mae'],
                        'rmse': original_metrics['rmse']
                    },
                    'new': {
                        'r2_score': new_metrics['r2_score'],
                        'mae': new_metrics['mae'],
                        'rmse': new_metrics['rmse']
                    },
                    'deltas': {
                        'r2_score': {
                            'absolute': r2_delta_abs,
                            'percentage': r2_delta_pct,
                            'acceptable': r2_acceptable
                        },
                        'mae': {
                            'absolute': mae_delta_abs,
                            'percentage': mae_delta_pct,
                            'acceptable': mae_acceptable
                        },
                        'rmse': {
                            'absolute': rmse_delta_abs,
                            'percentage': rmse_delta_pct,
                            'acceptable': rmse_acceptable
                        }
                    },
                    'acceptable': all_acceptable
                }
        
        return comparison
    
    def generate_summary(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary statistics from comparison
        
        Args:
            comparison: Model comparison dictionary
            
        Returns:
            Summary statistics
        """
        total_models = len(comparison)
        acceptable_models = sum(1 for v in comparison.values() if v['acceptable'])
        degraded_models = total_models - acceptable_models
        
        overall_status = 'pass' if degraded_models == 0 else 'fail'
        
        return {
            'total_models': total_models,
            'acceptable_models': acceptable_models,
            'degraded_models': degraded_models,
            'pass_rate': (acceptable_models / total_models * 100) if total_models > 0 else 0,
            'overall_status': overall_status,
            'threshold_percent': self.threshold_percent
        }
    
    def print_report(self, comparison: Dict[str, Any], summary: Dict[str, Any]):
        """Print human-readable validation report"""
        print("\n" + "="*80)
        print("MODEL PERFORMANCE VALIDATION REPORT")
        print("="*80)
        print(f"\nValidation Timestamp: {datetime.now().isoformat()}")
        print(f"Performance Threshold: ±{self.threshold_percent}%")
        print(f"\nOverall Status: {summary['overall_status'].upper()}")
        print(f"Total Models: {summary['total_models']}")
        print(f"Acceptable Models: {summary['acceptable_models']}")
        print(f"Degraded Models: {summary['degraded_models']}")
        print(f"Pass Rate: {summary['pass_rate']:.1f}%")
        
        print("\n" + "-"*80)
        print("DETAILED MODEL COMPARISON")
        print("-"*80)
        
        for model_key, data in sorted(comparison.items()):
            status_icon = "✅" if data['acceptable'] else "❌"
            print(f"\n{status_icon} {data['dataset']} - {data['model']}")
            print(f"   {'Metric':<15} {'Original':<15} {'New':<15} {'Delta %':<12} {'Status'}")
            print(f"   {'-'*15} {'-'*15} {'-'*15} {'-'*12} {'-'*10}")
            
            for metric in ['r2_score', 'mae', 'rmse']:
                orig_val = data['original'][metric]
                new_val = data['new'][metric]
                delta_pct = data['deltas'][metric]['percentage']
                acceptable = data['deltas'][metric]['acceptable']
                
                status = "✓" if acceptable else "✗"
                
                # Format values based on magnitude
                if abs(orig_val) < 0.001:
                    orig_str = f"{orig_val:.2e}"
                    new_str = f"{new_val:.2e}"
                else:
                    orig_str = f"{orig_val:.6f}"
                    new_str = f"{new_val:.6f}"
                
                delta_str = f"{delta_pct:+.2f}%"
                
                print(f"   {metric:<15} {orig_str:<15} {new_str:<15} {delta_str:<12} {status}")
        
        print("\n" + "="*80)
        
        if summary['degraded_models'] > 0:
            print("\n⚠️  WARNING: Some models show performance degradation beyond threshold!")
            print("   Review the models marked with ❌ above.")
            print("   Consider retraining with different hyperparameters or more data.")
        else:
            print("\n✅ SUCCESS: All models meet performance requirements!")
            print("   Models are ready for deployment.")
        
        print("\n" + "="*80 + "\n")
    
    def save_report(self, comparison: Dict[str, Any], summary: Dict[str, Any], 
                   output_path: str = "model_results/validation_report.json"):
        """
        Save validation report to JSON file
        
        Args:
            comparison: Model comparison dictionary
            summary: Summary statistics
            output_path: Path to save report
        """
        report = {
            'validation_timestamp': datetime.now().isoformat(),
            'threshold_percent': self.threshold_percent,
            'summary': summary,
            'comparison': comparison
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to: {output_file}")
    
    def validate(self) -> bool:
        """
        Run complete validation process
        
        Returns:
            True if all models pass validation, False otherwise
        """
        try:
            # Load metrics
            logger.info("Loading model metrics...")
            original_data = self.load_original_metrics()
            new_data = self.load_new_metrics()
            
            # Compare models
            logger.info("Comparing model performance...")
            comparison = self.compare_models(original_data, new_data)
            
            # Generate summary
            summary = self.generate_summary(comparison)
            
            # Print report
            self.print_report(comparison, summary)
            
            # Save report
            self.save_report(comparison, summary)
            
            # Return validation result
            return summary['overall_status'] == 'pass'
            
        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate retrained model performance against original baselines'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=5.0,
        help='Maximum acceptable performance degradation percentage (default: 5.0)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='model_results/validation_report.json',
        help='Path to save validation report (default: model_results/validation_report.json)'
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = ModelPerformanceValidator(threshold_percent=args.threshold)
    
    # Run validation
    try:
        success = validator.validate()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
