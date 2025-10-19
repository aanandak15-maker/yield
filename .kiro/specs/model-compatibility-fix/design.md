# Design Document

## Overview

This design addresses the NumPy version incompatibility issue preventing ML models from loading in the crop yield prediction API. The solution involves updating dependency specifications, retraining models with current library versions, and enhancing model loading robustness.

The root cause is that models were serialized with NumPy 1.24.3 (which has `numpy._core`) but the runtime environment has NumPy 2.3.3 (which reorganized internal modules). When joblib attempts to unpickle the models, it fails because the internal module structure has changed.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Dependency Management                      │
│  - requirements.txt (updated to NumPy 2.x compatible)       │
│  - Version validation at startup                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Model Training Pipeline                    │
│  - model_trainer.py (retrain with current versions)         │
│  - Validation against original model performance            │
│  - Model metadata tracking                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Model Loading Service                      │
│  - Enhanced error handling and logging                      │
│  - Version compatibility checks                             │
│  - Graceful fallback mechanisms                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Prediction API                             │
│  - Health check with model status                           │
│  - Model metadata in responses                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Dependency Update**: Update requirements.txt to specify NumPy 2.x compatible versions
2. **Model Retraining**: Execute model_trainer.py to retrain all models with current dependencies
3. **Model Validation**: Compare new model performance against original metrics
4. **Model Deployment**: Replace old model files with newly trained models
5. **API Startup**: Load models with enhanced error handling and version validation
6. **Runtime**: Serve predictions using successfully loaded models

## Components and Interfaces

### 1. Dependency Configuration

**File**: `requirements.txt`

**Changes**:
- Update NumPy from `1.24.3` to `>=2.3.0,<3.0.0` (NumPy 2.x compatible)
- Update scikit-learn from `1.6.0` to `>=1.7.0,<1.8.0` (compatible with NumPy 2.x)
- Update joblib to `>=1.5.0` (supports NumPy 2.x serialization)
- Remove XGBoost version pin if not actively used (or update to `>=2.0.0`)

**Rationale**: Align dependency specifications with actual runtime environment to prevent version mismatches.

### 2. Model Training Script Enhancement

**File**: `model_trainer.py`

**Enhancements**:

```python
class NorthIndiaModelTrainer:
    def __init__(self):
        # ... existing code ...
        self._log_environment_info()
    
    def _log_environment_info(self):
        """Log current environment versions for reproducibility"""
        import sklearn, numpy, joblib
        logger.info(f"Training Environment:")
        logger.info(f"  NumPy: {numpy.__version__}")
        logger.info(f"  scikit-learn: {sklearn.__version__}")
        logger.info(f"  joblib: {joblib.__version__}")
    
    def _save_model(self, model_info, dataset_name, model_key):
        """Enhanced model saving with version metadata"""
        import sklearn, numpy, joblib
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_data = {
            'model': model_info['model'],
            'scaler': model_info['scaler'],
            'poly': model_info['poly'],
            'features': model_info['features'],
            'metrics': model_info['metrics'],
            'dataset': model_info['dataset'],
            'created_at': timestamp,
            'environment': {
                'numpy_version': numpy.__version__,
                'sklearn_version': sklearn.__version__,
                'joblib_version': joblib.__version__,
                'python_version': sys.version
            }
        }
        
        filename = f"{self.models_dir}/{dataset_name}_{model_key}_{timestamp}.pkl"
        
        # Use protocol 5 for better NumPy 2.x compatibility
        with open(filename, 'wb') as f:
            joblib.dump(model_data, f, protocol=5)
```

### 3. Model Loading Enhancement

**File**: `src/prediction_api.py`

**Method**: `_load_models()`

**Enhanced Logic**:

```python
def _load_models(self):
    """Load trained ML models with enhanced compatibility handling"""
    self.models = {}
    models_dir = Path("models")
    
    # Log current environment
    self._log_runtime_environment()
    
    # Check compatibility before attempting to load
    if not self._check_environment_compatibility():
        self.logger.error("❌ Environment incompatible with model requirements")
        self.location_models = self._create_fallback_models()
        return
    
    model_files = list(models_dir.glob("*.pkl"))
    
    if not model_files:
        self.logger.warning("No trained models found")
        self.location_models = self._create_fallback_models()
        return
    
    # Load models with enhanced error handling
    loaded_count = 0
    failed_models = []
    
    for model_file in model_files:
        try:
            model_data = joblib.load(model_file)
            
            # Validate model structure
            if not self._validate_model_structure(model_data):
                failed_models.append((model_file.name, "Invalid structure"))
                continue
            
            # Extract model info and store
            # ... existing model storage logic ...
            loaded_count += 1
            
        except Exception as e:
            error_msg = str(e)
            if 'numpy._core' in error_msg:
                error_type = "NumPy version incompatibility"
            elif '_loss' in error_msg:
                error_type = "XGBoost version incompatibility"
            else:
                error_type = "Unknown error"
            
            failed_models.append((model_file.name, f"{error_type}: {error_msg}"))
    
    # Log results
    self.logger.info(f"✅ Successfully loaded {loaded_count}/{len(model_files)} models")
    
    if failed_models:
        self.logger.warning(f"⚠️  Failed to load {len(failed_models)} models:")
        for model_name, error in failed_models:
            self.logger.warning(f"  - {model_name}: {error}")
    
    # Use fallback if no models loaded
    if loaded_count == 0:
        self.logger.warning("❌ No models loaded, using fallback models")
        self.location_models = self._create_fallback_models()

def _log_runtime_environment(self):
    """Log runtime environment for debugging"""
    import sklearn, numpy, joblib
    self.logger.info(f"Runtime Environment:")
    self.logger.info(f"  NumPy: {numpy.__version__}")
    self.logger.info(f"  scikit-learn: {sklearn.__version__}")
    self.logger.info(f"  joblib: {joblib.__version__}")

def _check_environment_compatibility(self) -> bool:
    """Check if runtime environment is compatible with model requirements"""
    try:
        import sklearn, numpy, joblib
        
        # Check NumPy version (2.x required)
        numpy_version = tuple(map(int, numpy.__version__.split('.')[:2]))
        if numpy_version[0] < 2:
            self.logger.error(f"NumPy version {numpy.__version__} < 2.0 (incompatible)")
            return False
        
        # Check scikit-learn version (1.7+ required)
        sklearn_version = tuple(map(int, sklearn.__version__.split('.')[:2]))
        if sklearn_version < (1, 7):
            self.logger.error(f"scikit-learn version {sklearn.__version__} < 1.7 (incompatible)")
            return False
        
        return True
        
    except Exception as e:
        self.logger.error(f"Environment compatibility check failed: {e}")
        return False

def _validate_model_structure(self, model_data) -> bool:
    """Validate that loaded model has expected structure"""
    required_keys = ['model', 'scaler', 'features', 'metrics']
    
    if isinstance(model_data, dict):
        return all(key in model_data for key in required_keys)
    
    return False
```

### 4. Health Check Enhancement

**File**: `src/prediction_api.py`

**New Endpoint**: `/health/detailed`

```python
@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including model loading status"""
    import sklearn, numpy, joblib
    
    model_status = {}
    for location, models in service.location_models.items():
        model_status[location] = {
            'algorithms': list(models.keys()),
            'count': len(models)
        }
    
    return {
        'status': 'healthy' if service.location_models else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'numpy_version': numpy.__version__,
            'sklearn_version': sklearn.__version__,
            'joblib_version': joblib.__version__
        },
        'models': {
            'total_loaded': sum(len(models) for models in service.location_models.values()),
            'locations': len(service.location_models),
            'by_location': model_status
        },
        'fallback_mode': len(service.location_models) == 0 or 
                        all('fallback' in str(m.get('path', '')) 
                            for models in service.location_models.values() 
                            for m in models.values())
    }
```

## Data Models

### Model Metadata Structure

```python
{
    'model': <sklearn_model_object>,
    'scaler': <StandardScaler_object>,
    'poly': <PolynomialFeatures_object>,
    'features': ['feature1', 'feature2', ...],
    'metrics': {
        'train_r2': float,
        'test_r2': float,
        'train_mae': float,
        'test_mae': float,
        'train_rmse': float,
        'test_rmse': float
    },
    'dataset': str,
    'created_at': str,  # ISO timestamp
    'environment': {
        'numpy_version': str,
        'sklearn_version': str,
        'joblib_version': str,
        'python_version': str
    }
}
```

### Model Validation Report Structure

```python
{
    'validation_timestamp': str,
    'original_models': {
        'location_algorithm': {
            'r2_score': float,
            'mae': float,
            'rmse': float
        }
    },
    'retrained_models': {
        'location_algorithm': {
            'r2_score': float,
            'mae': float,
            'rmse': float
        }
    },
    'comparison': {
        'location_algorithm': {
            'r2_delta': float,  # percentage change
            'mae_delta': float,
            'rmse_delta': float,
            'acceptable': bool  # within 5% threshold
        }
    },
    'summary': {
        'total_models': int,
        'acceptable_models': int,
        'degraded_models': int,
        'overall_status': str  # 'pass' or 'fail'
    }
}
```

## Error Handling

### Model Loading Errors

1. **NumPy Version Mismatch**
   - Detection: Check for `numpy._core` in error message
   - Response: Log specific error, increment failed counter, continue to next model
   - Fallback: Use fallback models if all models fail

2. **Scikit-learn Version Mismatch**
   - Detection: Check for sklearn-related import errors
   - Response: Log version incompatibility, suggest retraining
   - Fallback: Use fallback models

3. **Corrupted Model Files**
   - Detection: Catch pickle/joblib loading exceptions
   - Response: Log file corruption, skip file
   - Fallback: Continue with other models

4. **Missing Model Files**
   - Detection: Empty models directory
   - Response: Log warning about missing models
   - Fallback: Immediately use fallback models

### API Runtime Errors

1. **No Models Loaded**
   - Response: Return HTTP 503 with degraded status
   - Fallback: Use simple regression fallback models
   - Message: "Service running in fallback mode - predictions may be less accurate"

2. **Partial Model Loading**
   - Response: Continue with successfully loaded models
   - Log: Warning about missing location coverage
   - Fallback: Use nearest location model or regional model

## Testing Strategy

### Unit Tests

1. **Dependency Version Tests**
   - Test: Verify NumPy version >= 2.0
   - Test: Verify scikit-learn version >= 1.7
   - Test: Verify joblib version >= 1.5

2. **Model Training Tests**
   - Test: Model training completes without errors
   - Test: Model files are created with correct naming
   - Test: Model metadata includes environment info
   - Test: Models can be loaded immediately after training

3. **Model Loading Tests**
   - Test: Successfully load newly trained models
   - Test: Handle missing model files gracefully
   - Test: Validate model structure after loading
   - Test: Fallback models are created when needed

4. **Compatibility Check Tests**
   - Test: Environment compatibility check passes with correct versions
   - Test: Environment compatibility check fails with incompatible versions
   - Test: Model structure validation catches invalid models

### Integration Tests

1. **End-to-End Retraining**
   - Test: Complete retraining pipeline from data to saved models
   - Test: All 15 models (5 locations × 3 algorithms) are created
   - Test: Model performance metrics are within acceptable ranges

2. **API Startup Tests**
   - Test: API starts successfully with new models
   - Test: All models load without errors
   - Test: Health check reports correct model count

3. **Prediction Tests**
   - Test: API accepts prediction requests
   - Test: Predictions use newly trained models
   - Test: Prediction responses include model metadata
   - Test: Predictions are numerically reasonable (within expected yield ranges)

### Performance Validation Tests

1. **Model Accuracy Comparison**
   - Test: New model R² scores within 5% of original
   - Test: New model MAE within 5% of original
   - Test: New model RMSE within 5% of original

2. **Prediction Consistency**
   - Test: Same input produces consistent predictions
   - Test: Predictions fall within expected yield ranges (0-10 tons/ha)
   - Test: Confidence scores are reasonable (0.5-1.0)

### Manual Testing Checklist

1. ✅ Install updated dependencies
2. ✅ Run model retraining script
3. ✅ Verify all 15 model files created
4. ✅ Check model file sizes (should be similar to originals)
5. ✅ Start API server
6. ✅ Verify no NumPy compatibility warnings in logs
7. ✅ Call `/health/detailed` endpoint
8. ✅ Verify all models loaded successfully
9. ✅ Make test prediction request
10. ✅ Verify prediction response is valid
11. ✅ Check prediction uses new model (check timestamp in response)
12. ✅ Compare prediction values with historical predictions for sanity

## Deployment Strategy

### Phase 1: Dependency Update
1. Update requirements.txt with NumPy 2.x compatible versions
2. Create virtual environment with new dependencies
3. Verify all imports work correctly

### Phase 2: Model Retraining
1. Backup existing model files to `models_backup/`
2. Run model_trainer.py with current dependencies
3. Verify all 15 models are created
4. Generate validation report comparing old vs new models

### Phase 3: Validation
1. Review validation report
2. Ensure all models meet performance thresholds (within 5%)
3. If any models fail validation, investigate and retrain

### Phase 4: Deployment
1. Stop API service
2. Replace old model files with new models
3. Restart API service
4. Monitor logs for successful model loading
5. Run smoke tests on prediction endpoints

### Phase 5: Monitoring
1. Monitor API logs for any model loading errors
2. Track prediction latency and accuracy
3. Compare prediction distributions with historical data
4. Set up alerts for model loading failures

## Rollback Plan

If issues occur after deployment:

1. **Immediate Rollback**
   - Stop API service
   - Restore models from `models_backup/`
   - Downgrade dependencies to original versions
   - Restart API service

2. **Dependency Rollback**
   ```bash
   pip install numpy==1.24.3 scikit-learn==1.6.0 joblib==1.3.0
   ```

3. **Verification**
   - Verify old models load successfully
   - Run test predictions
   - Monitor for 15 minutes

## Performance Considerations

1. **Model Loading Time**: Should remain under 10 seconds for all 15 models
2. **Memory Usage**: NumPy 2.x may have different memory characteristics - monitor
3. **Prediction Latency**: Should remain under 500ms per prediction
4. **Model File Size**: New models should be similar size to old models (±20%)

## Security Considerations

1. **Dependency Vulnerabilities**: Ensure NumPy 2.x and scikit-learn 1.7.x have no known CVEs
2. **Model Integrity**: Store checksums of model files to detect tampering
3. **Access Control**: Restrict write access to models directory
4. **Audit Logging**: Log all model loading attempts and failures
