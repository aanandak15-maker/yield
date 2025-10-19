# Model Compatibility Fix - Deployment Guide

## Overview

This guide documents the complete process for deploying the NumPy 2.x and scikit-learn 1.7.x model compatibility fix for the crop yield prediction API. This fix resolves the issue where models trained with NumPy 1.24.3 fail to load in environments with NumPy 2.3.3.

**Issue Summary**: Models serialized with NumPy 1.x reference `numpy._core` which doesn't exist in NumPy 2.x, causing all model loading to fail.

**Solution**: Retrain all models with NumPy 2.x and scikit-learn 1.7.x, update dependencies, and enhance model loading robustness.

---

## Prerequisites

- Python 3.9 or higher
- Access to training data in `data/` directory
- Backup storage for existing models
- API downtime window (approximately 30 minutes)

---

## Complete Deployment Process

### Phase 1: Pre-Deployment Preparation

#### 1.1 Backup Existing Models

```bash
# Create backup directory
mkdir -p models_backup

# Copy all existing model files
cp models/*.pkl models_backup/

# Verify backup
ls -lh models_backup/
# Expected: 15 .pkl files (5 locations × 3 algorithms)
```

#### 1.2 Backup Current Dependencies

```bash
# Save current environment
pip freeze > requirements_old.txt

# Backup training summary
cp model_results/training_summary.json model_results/training_summary_backup.json
```

#### 1.3 Document Current State

```bash
# Check current versions
python -c "import numpy, sklearn, joblib; print(f'NumPy: {numpy.__version__}'); print(f'scikit-learn: {sklearn.__version__}'); print(f'joblib: {joblib.__version__}')"

# Count loaded models (if API is running)
curl http://localhost:8000/health/detailed | jq '.models.total_loaded'
```

### Phase 2: Dependency Update

#### 2.1 Update requirements.txt

The requirements.txt file has been updated with:
- `numpy>=2.3.0,<3.0.0`
- `scikit-learn>=1.7.0,<1.8.0`
- `joblib>=1.5.0,<2.0.0`

#### 2.2 Install Updated Dependencies

```bash
# Create fresh virtual environment (recommended)
python -m venv .venv_new
source .venv_new/bin/activate  # On Windows: .venv_new\Scripts\activate

# Install updated dependencies
pip install -r requirements.txt

# Verify versions
python -c "import numpy, sklearn, joblib; print(f'NumPy: {numpy.__version__}'); print(f'scikit-learn: {sklearn.__version__}'); print(f'joblib: {joblib.__version__}')"
```

Expected output:
```
NumPy: 2.3.3
scikit-learn: 1.7.2
joblib: 1.5.2
```

### Phase 3: Model Retraining

#### 3.1 Run Model Training

```bash
# Ensure you're in the project root directory
# Activate the virtual environment with updated dependencies
source .venv_new/bin/activate

# Run model training
python model_trainer.py
```

Expected output:
- Training progress for 5 locations (Bhopal, Chandigarh, Lucknow, Patna, North India Regional)
- 3 algorithms per location (Ridge, Random Forest, Gradient Boosting)
- Total: 15 models trained
- Training summary saved to `model_results/training_summary.json`

#### 3.2 Verify Model Files Created

```bash
# Check model files
ls -lh models/*.pkl | wc -l
# Expected: 15 files

# Check file sizes (should be similar to originals)
ls -lh models/*.pkl
```

#### 3.3 Extract Original Metrics

```bash
# Extract original model metrics for comparison
python extract_original_metrics.py
```

This creates `model_results/final_training_report.json` with original model performance metrics.

### Phase 4: Model Validation

#### 4.1 Run Performance Validation

```bash
# Compare old vs new model performance
python validate_model_performance.py
```

Expected output:
- Validation report saved to `model_results/validation_report.json`
- Console output showing performance deltas for each model
- All models should be within 5% performance threshold

#### 4.2 Review Validation Report

```bash
# View validation summary
cat model_results/validation_report.json | jq '.summary'
```

Expected:
```json
{
  "total_models": 15,
  "acceptable_models": 15,
  "degraded_models": 0,
  "overall_status": "pass"
}
```

**Action Required**: If any models show `degraded_models > 0`, investigate before proceeding.

### Phase 5: API Deployment

#### 5.1 Stop Current API Service

```bash
# If running as a service
sudo systemctl stop crop-yield-api

# If running in terminal, press Ctrl+C

# Verify API is stopped
curl http://localhost:8000/health
# Should fail or timeout
```

#### 5.2 Deploy New Models

Models are already in the `models/` directory from Phase 3. No additional deployment needed.

#### 5.3 Start API Service

```bash
# Ensure correct virtual environment is activated
source .venv_new/bin/activate

# Start API
python run_api.py

# Or if using uvicorn directly
uvicorn src.prediction_api:app --host 0.0.0.0 --port 8000
```

#### 5.4 Verify Model Loading

Check the startup logs for:
```
✅ Successfully loaded model: bhopal_training_ridge_...
✅ Successfully loaded model: bhopal_training_random_forest_...
✅ Successfully loaded model: bhopal_training_gradient_boosting_...
...
✅ Successfully loaded 15/15 models
```

**No warnings about NumPy compatibility should appear.**

### Phase 6: Post-Deployment Verification

#### 6.1 Health Check

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed | jq '.'
```

Expected response:
```json
{
  "status": "healthy",
  "environment": {
    "numpy_version": "2.3.3",
    "sklearn_version": "1.7.2",
    "joblib_version": "1.5.2"
  },
  "models": {
    "total_loaded": 15,
    "locations": 5,
    "by_location": { ... }
  },
  "fallback_mode": false
}
```

#### 6.2 Test Predictions

```bash
# Run end-to-end prediction tests
python test_end_to_end_predictions.py
```

Expected: All tests pass with valid predictions for all locations.

#### 6.3 Manual Prediction Test

```bash
# Test prediction for Bhopal
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Rice",
    "location": "Bhopal",
    "sowing_date": "2024-06-15",
    "area_hectares": 10.0
  }' | jq '.'
```

Expected response:
```json
{
  "predicted_yield_tons_per_hectare": 3.45,
  "total_yield_tons": 34.5,
  "confidence_score": 0.85,
  "model_used": "gradient_boosting",
  "location": "Bhopal",
  "model_timestamp": "20251019_..."
}
```

---

## Rollback Procedure

If issues are detected after deployment, follow this rollback procedure:

### Step 1: Stop API Service

```bash
# Stop the API
sudo systemctl stop crop-yield-api
# Or press Ctrl+C if running in terminal
```

### Step 2: Restore Original Models

```bash
# Remove new models
rm models/*.pkl

# Restore from backup
cp models_backup/*.pkl models/

# Verify restoration
ls -lh models/*.pkl | wc -l
# Expected: Original number of model files
```

### Step 3: Downgrade Dependencies

```bash
# Deactivate current environment
deactivate

# Activate old environment or create new one
source .venv/bin/activate  # Your original environment

# Install old dependencies
pip install -r requirements_old.txt

# Verify versions
python -c "import numpy, sklearn, joblib; print(f'NumPy: {numpy.__version__}'); print(f'scikit-learn: {sklearn.__version__}'); print(f'joblib: {joblib.__version__}')"
```

Expected:
```
NumPy: 1.24.3
scikit-learn: 1.6.0
joblib: 1.3.0
```

### Step 4: Restart API

```bash
# Start API with old environment
python run_api.py
```

### Step 5: Verify Rollback

```bash
# Check health
curl http://localhost:8000/health/detailed | jq '.models.total_loaded'

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Rice",
    "location": "Bhopal",
    "sowing_date": "2024-06-15",
    "area_hectares": 10.0
  }' | jq '.predicted_yield_tons_per_hectare'
```

### Step 6: Document Rollback Reason

```bash
# Create rollback report
echo "Rollback performed at $(date)" > rollback_report.txt
echo "Reason: [DESCRIBE ISSUE]" >> rollback_report.txt
echo "Models restored from: models_backup/" >> rollback_report.txt
```

---

## Post-Deployment Monitoring

### Monitoring Checklist (First 24 Hours)

#### Immediate (First 15 Minutes)
- [ ] API responds to `/health` endpoint
- [ ] `/health/detailed` shows all 15 models loaded
- [ ] `fallback_mode` is `false`
- [ ] No NumPy compatibility warnings in logs
- [ ] Test prediction returns valid response
- [ ] Response times < 500ms

#### First Hour
- [ ] Monitor error logs for any model loading failures
- [ ] Check prediction accuracy against historical data
- [ ] Verify all 5 locations return predictions
- [ ] Monitor memory usage (should be stable)
- [ ] Check CPU usage during predictions

#### First 24 Hours
- [ ] Review prediction distribution (should match historical patterns)
- [ ] Monitor API response times (track any degradation)
- [ ] Check for any error spikes in logs
- [ ] Verify confidence scores are reasonable (0.5-1.0)
- [ ] Compare prediction volumes with historical data

### Key Metrics to Monitor

```bash
# Model loading status
curl http://localhost:8000/health/detailed | jq '.models.total_loaded'

# Check for errors in logs
tail -f logs/api.log | grep -i error

# Monitor response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

Create `curl-format.txt`:
```
time_total: %{time_total}s
```

### Automated Monitoring Script

```bash
#!/bin/bash
# monitor_api.sh

while true; do
    echo "=== $(date) ==="
    
    # Check health
    HEALTH=$(curl -s http://localhost:8000/health/detailed)
    MODELS_LOADED=$(echo $HEALTH | jq -r '.models.total_loaded')
    FALLBACK=$(echo $HEALTH | jq -r '.fallback_mode')
    
    echo "Models loaded: $MODELS_LOADED/15"
    echo "Fallback mode: $FALLBACK"
    
    if [ "$MODELS_LOADED" != "15" ] || [ "$FALLBACK" != "false" ]; then
        echo "⚠️  WARNING: Model loading issue detected!"
    fi
    
    # Test prediction
    PRED_RESPONSE=$(curl -s -X POST http://localhost:8000/predict \
        -H "Content-Type: application/json" \
        -d '{"crop_type":"Rice","location":"Bhopal","sowing_date":"2024-06-15","area_hectares":10.0}')
    
    YIELD=$(echo $PRED_RESPONSE | jq -r '.predicted_yield_tons_per_hectare')
    
    if [ "$YIELD" != "null" ]; then
        echo "✅ Prediction test passed: $YIELD tons/ha"
    else
        echo "❌ Prediction test failed!"
    fi
    
    echo ""
    sleep 300  # Check every 5 minutes
done
```

Usage:
```bash
chmod +x monitor_api.sh
./monitor_api.sh > monitoring.log 2>&1 &
```

---

## Troubleshooting Guide

### Issue 1: Models Fail to Load After Deployment

**Symptoms**:
- Logs show "❌ Failed to load X models"
- `/health/detailed` shows `total_loaded < 15`
- `fallback_mode` is `true`

**Diagnosis**:
```bash
# Check model files exist
ls -lh models/*.pkl | wc -l

# Check file permissions
ls -l models/

# Verify environment versions
python -c "import numpy, sklearn, joblib; print(f'NumPy: {numpy.__version__}'); print(f'scikit-learn: {sklearn.__version__}')"
```

**Solutions**:

1. **Wrong environment activated**:
   ```bash
   deactivate
   source .venv_new/bin/activate
   python run_api.py
   ```

2. **Model files missing**:
   ```bash
   # Retrain models
   python model_trainer.py
   ```

3. **File permissions**:
   ```bash
   chmod 644 models/*.pkl
   ```

### Issue 2: NumPy Compatibility Warnings Still Appear

**Symptoms**:
- Logs show warnings about `numpy._core`
- Models load but with warnings

**Diagnosis**:
```bash
# Check NumPy version
python -c "import numpy; print(numpy.__version__)"

# Check if old models are being loaded
ls -lh models/*.pkl
# Check timestamps - should be recent
```

**Solutions**:

1. **Old models still present**:
   ```bash
   # Remove old models
   rm models/*.pkl
   
   # Retrain with current environment
   python model_trainer.py
   ```

2. **Wrong NumPy version**:
   ```bash
   pip install --upgrade numpy>=2.3.0
   python model_trainer.py
   ```

### Issue 3: Model Performance Degraded

**Symptoms**:
- Validation report shows `degraded_models > 0`
- R² scores decreased by more than 5%
- Predictions seem unreasonable

**Diagnosis**:
```bash
# Review validation report
cat model_results/validation_report.json | jq '.comparison'

# Check specific model metrics
cat model_results/validation_report.json | jq '.comparison.bhopal_training_gradient_boosting'
```

**Solutions**:

1. **Training data issue**:
   ```bash
   # Verify training data integrity
   python -c "import pandas as pd; df = pd.read_csv('crop_yield_climate_soil_data_2019_2023.csv'); print(df.shape); print(df.isnull().sum())"
   ```

2. **Random seed variation**:
   - Some variation is expected due to random initialization
   - If within 5%, this is acceptable
   - If > 5%, investigate training parameters

3. **Retrain specific model**:
   ```bash
   # Edit model_trainer.py to focus on specific location/algorithm
   # Then retrain
   python model_trainer.py
   ```

### Issue 4: API Returns 503 Service Unavailable

**Symptoms**:
- API responds but returns 503 status
- Health check shows "degraded" status

**Diagnosis**:
```bash
# Check detailed health
curl http://localhost:8000/health/detailed | jq '.'

# Check logs
tail -100 logs/api.log
```

**Solutions**:

1. **No models loaded**:
   ```bash
   # Check if models directory is empty
   ls models/
   
   # Retrain if needed
   python model_trainer.py
   
   # Restart API
   pkill -f run_api.py
   python run_api.py
   ```

2. **Fallback mode active**:
   - API is running but using fallback models
   - Check why primary models didn't load
   - Review logs for specific errors

### Issue 5: Predictions Return Unreasonable Values

**Symptoms**:
- Yield predictions are negative or extremely high (> 15 tons/ha)
- Confidence scores are very low (< 0.3)

**Diagnosis**:
```bash
# Test multiple predictions
for loc in Bhopal Chandigarh Lucknow Patna; do
    echo "Testing $loc:"
    curl -s -X POST http://localhost:8000/predict \
        -H "Content-Type: application/json" \
        -d "{\"crop_type\":\"Rice\",\"location\":\"$loc\",\"sowing_date\":\"2024-06-15\",\"area_hectares\":10.0}" \
        | jq '.predicted_yield_tons_per_hectare'
done
```

**Solutions**:

1. **Model not properly trained**:
   ```bash
   # Check training metrics
   cat model_results/training_summary.json | jq '.models[] | select(.dataset | contains("bhopal")) | .metrics'
   
   # If R² < 0.5, retrain
   python model_trainer.py
   ```

2. **Input data preprocessing issue**:
   - Verify input data format matches training data
   - Check feature scaling is applied correctly
   - Review `src/prediction_api.py` preprocessing logic

3. **Wrong model loaded**:
   ```bash
   # Check which model is being used
   curl -s -X POST http://localhost:8000/predict \
        -H "Content-Type: application/json" \
        -d '{"crop_type":"Rice","location":"Bhopal","sowing_date":"2024-06-15","area_hectares":10.0}' \
        | jq '.model_used, .model_timestamp'
   ```

### Issue 6: High Memory Usage

**Symptoms**:
- API process consuming excessive memory (> 2GB)
- System becomes slow after API starts

**Diagnosis**:
```bash
# Check memory usage
ps aux | grep python

# Monitor over time
watch -n 5 'ps aux | grep run_api.py'
```

**Solutions**:

1. **Too many models loaded in memory**:
   - This is expected behavior (15 models)
   - Ensure system has adequate RAM (minimum 4GB recommended)

2. **Memory leak**:
   - Restart API periodically
   - Monitor for gradual memory increase
   - Review code for circular references

3. **Optimize model loading**:
   - Consider lazy loading models (load on first use)
   - Implement model caching with size limits

### Issue 7: Slow Prediction Response Times

**Symptoms**:
- Predictions take > 1 second
- API feels sluggish

**Diagnosis**:
```bash
# Measure response time
time curl -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"crop_type":"Rice","location":"Bhopal","sowing_date":"2024-06-15","area_hectares":10.0}'

# Check if models are loaded
curl http://localhost:8000/health/detailed | jq '.models.total_loaded'
```

**Solutions**:

1. **Models not preloaded**:
   - Ensure models are loaded at startup, not on first request
   - Check `_load_models()` is called in `__init__`

2. **Feature engineering overhead**:
   - Profile the prediction code
   - Optimize date parsing and feature extraction

3. **System resources**:
   - Check CPU usage
   - Ensure no other heavy processes running

---

## Common Commands Reference

### Environment Management
```bash
# Create virtual environment
python -m venv .venv_new

# Activate (Linux/Mac)
source .venv_new/bin/activate

# Activate (Windows)
.venv_new\Scripts\activate

# Deactivate
deactivate

# Check installed packages
pip list

# Save environment
pip freeze > requirements_current.txt
```

### Model Management
```bash
# List models
ls -lh models/*.pkl

# Count models
ls models/*.pkl | wc -l

# Check model file sizes
du -sh models/

# Backup models
cp -r models/ models_backup_$(date +%Y%m%d_%H%M%S)/

# Clean old models
rm models/*_old.pkl
```

### API Management
```bash
# Start API (development)
python run_api.py

# Start API (production with uvicorn)
uvicorn src.prediction_api:app --host 0.0.0.0 --port 8000 --workers 4

# Check if API is running
curl http://localhost:8000/health

# Stop API (if running in background)
pkill -f run_api.py

# View logs
tail -f logs/api.log
```

### Testing Commands
```bash
# Run all tests
python -m pytest

# Run specific test file
python test_api_startup.py

# Run end-to-end tests
python test_end_to_end_predictions.py

# Run validation
python validate_model_performance.py
```

---

## Success Criteria

Deployment is considered successful when:

- ✅ All 15 models load without errors
- ✅ No NumPy compatibility warnings in logs
- ✅ `/health/detailed` shows `total_loaded: 15` and `fallback_mode: false`
- ✅ All validation tests pass
- ✅ Model performance within 5% of original metrics
- ✅ Predictions return reasonable values (0-10 tons/ha for rice)
- ✅ Response times < 500ms
- ✅ API stable for 24 hours without errors

---

## Support and Escalation

If issues persist after following this guide:

1. **Collect diagnostic information**:
   ```bash
   # Create diagnostic bundle
   mkdir -p diagnostics
   cp logs/api.log diagnostics/
   pip freeze > diagnostics/requirements.txt
   curl http://localhost:8000/health/detailed > diagnostics/health.json
   python -c "import numpy, sklearn, joblib; print(f'NumPy: {numpy.__version__}\nscikit-learn: {sklearn.__version__}\njoblib: {joblib.__version__}')" > diagnostics/versions.txt
   tar -czf diagnostics_$(date +%Y%m%d_%H%M%S).tar.gz diagnostics/
   ```

2. **Review documentation**:
   - `VALIDATION_README.md` - Validation process details
   - `DETAILED_HEALTH_ENDPOINT.md` - Health endpoint documentation
   - Design document: `.kiro/specs/model-compatibility-fix/design.md`

3. **Check implementation summaries**:
   - `TASK_4_IMPLEMENTATION_SUMMARY.md` - Model loading enhancements
   - `TASK_5_IMPLEMENTATION_SUMMARY.md` - Health endpoint
   - `TASK_6_IMPLEMENTATION_SUMMARY.md` - Model retraining
   - `TASK_7_VALIDATION_SUMMARY.md` - Validation results
   - `TASK_8_IMPLEMENTATION_SUMMARY.md` - API startup testing
   - `TASK_9_IMPLEMENTATION_SUMMARY.md` - End-to-end testing

---

## Document Version

- **Version**: 1.0
- **Last Updated**: 2025-10-19
- **Author**: Kiro AI Assistant
- **Related Spec**: `.kiro/specs/model-compatibility-fix/`

