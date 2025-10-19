# Model Performance Validation Script

## Overview

The `validate_model_performance.py` script compares retrained model performance against original baseline metrics to ensure models maintain acceptable accuracy after retraining with updated dependencies.

## Purpose

This script is part of the model compatibility fix workflow. It validates that models retrained with NumPy 2.x and scikit-learn 1.7.x maintain performance within acceptable thresholds (default: 5% degradation).

## Usage

### Basic Usage

```bash
python validate_model_performance.py
```

This will:
1. Load original model metrics from `model_results/training_summary.json` (or backup)
2. Load new model metrics from `model_results/training_summary.json`
3. Compare all models across all metrics (R², MAE, RMSE)
4. Generate a detailed validation report
5. Save the report to `model_results/validation_report.json`
6. Exit with code 0 if all models pass, 1 if any fail, 2 on error

### Custom Threshold

```bash
python validate_model_performance.py --threshold 3.0
```

Set a custom performance degradation threshold (default: 5.0%)

### Custom Output Path

```bash
python validate_model_performance.py --output reports/my_validation.json
```

Save the validation report to a custom location

### Combined Options

```bash
python validate_model_performance.py --threshold 10.0 --output reports/lenient_validation.json
```

## Validation Criteria

### Metrics Compared

- **R² Score**: Higher is better (measures model fit)
- **MAE (Mean Absolute Error)**: Lower is better
- **RMSE (Root Mean Squared Error)**: Lower is better

### Acceptance Rules

A model is considered acceptable if ALL of the following are true:

1. **R² Score**: Degradation ≤ threshold% (e.g., if R² drops from 0.95 to 0.90, that's -5.26% degradation)
2. **MAE**: Increase ≤ threshold% (e.g., if MAE increases from 0.1 to 0.11, that's +10% increase)
3. **RMSE**: Increase ≤ threshold% (e.g., if RMSE increases from 0.15 to 0.16, that's +6.67% increase)

### Overall Status

- **PASS**: All models meet the acceptance criteria
- **FAIL**: One or more models exceed the degradation threshold

## Output

### Console Output

The script prints a detailed report showing:
- Overall validation status
- Summary statistics (total models, acceptable, degraded, pass rate)
- Detailed comparison for each model with:
  - Original and new metric values
  - Percentage deltas
  - Pass/fail status for each metric
  - Overall model status (✅ or ❌)

### JSON Report

The script saves a JSON report with:
- Validation timestamp
- Threshold used
- Summary statistics
- Detailed comparison data for all models

Example structure:
```json
{
  "validation_timestamp": "2025-10-18T23:34:57.656227",
  "threshold_percent": 5.0,
  "summary": {
    "total_models": 15,
    "acceptable_models": 15,
    "degraded_models": 0,
    "pass_rate": 100.0,
    "overall_status": "pass"
  },
  "comparison": {
    "location_model": {
      "dataset": "location",
      "model": "algorithm",
      "original": { "r2_score": 0.95, "mae": 0.1, "rmse": 0.15 },
      "new": { "r2_score": 0.94, "mae": 0.11, "rmse": 0.16 },
      "deltas": {
        "r2_score": { "absolute": -0.01, "percentage": -1.05, "acceptable": true },
        "mae": { "absolute": 0.01, "percentage": 10.0, "acceptable": false },
        "rmse": { "absolute": 0.01, "percentage": 6.67, "acceptable": false }
      },
      "acceptable": false
    }
  }
}
```

## Workflow Integration

### Before Retraining

Before retraining models, backup the original metrics:

```bash
cp model_results/training_summary.json model_results/training_summary_backup.json
```

### After Retraining

After retraining models with updated dependencies:

```bash
# Run validation
python validate_model_performance.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ All models passed validation"
else
    echo "❌ Some models failed validation - review the report"
fi
```

### In CI/CD Pipeline

```bash
# Retrain models
python model_trainer.py

# Validate performance
python validate_model_performance.py --threshold 5.0

# Exit code determines pipeline success
```

## Troubleshooting

### "Could not find original metrics"

**Problem**: The script can't find `model_results/training_summary.json` or backup.

**Solution**: 
- Ensure models have been trained at least once
- Check that the file path is correct
- If comparing after retraining, ensure you created a backup first

### "Could not find new model metrics"

**Problem**: The script can't find new model metrics to compare.

**Solution**:
- Run `model_trainer.py` to generate new metrics
- Ensure the training script completed successfully

### All Models Show 0% Delta

**Problem**: Comparing the same file against itself.

**Solution**:
- Create a backup of original metrics before retraining
- Retrain models to generate new metrics
- The script will automatically use the backup for comparison

### Models Fail Validation

**Problem**: Some models exceed the degradation threshold.

**Solution**:
1. Review the detailed report to identify which models and metrics failed
2. Check if the threshold is too strict (consider increasing it)
3. Investigate training data or hyperparameters
4. Consider retraining with different random seeds
5. Verify that the training environment is correct

## Exit Codes

- **0**: Success - all models passed validation
- **1**: Failure - one or more models failed validation
- **2**: Error - validation process encountered an error

## Requirements

The script requires the following Python packages:
- Python 3.7+
- Standard library only (json, logging, pathlib, datetime, typing, sys, argparse)

No additional dependencies are required.
