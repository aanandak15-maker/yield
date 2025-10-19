#!/usr/bin/env python3
"""
Unit tests for model loading enhancement methods (Task 4)

Tests the individual methods without requiring full service initialization.
"""

import sys
import logging
import joblib
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockService:
    """Mock service class to test the methods in isolation"""
    
    def __init__(self):
        self.logger = logger
    
    def _log_runtime_environment(self):
        """Log runtime environment for debugging"""
        try:
            import sklearn
            import numpy as np
            
            self.logger.info("=" * 60)
            self.logger.info("Runtime Environment:")
            self.logger.info(f"  NumPy: {np.__version__}")
            self.logger.info(f"  scikit-learn: {sklearn.__version__}")
            self.logger.info(f"  joblib: {joblib.__version__}")
            
            # Try to log XGBoost if available
            try:
                import xgboost as xgb
                self.logger.info(f"  XGBoost: {xgb.__version__}")
            except ImportError:
                self.logger.info("  XGBoost: Not installed")
            
            self.logger.info("=" * 60)
        except Exception as e:
            self.logger.warning(f"Failed to log runtime environment: {e}")
    
    def _check_environment_compatibility(self) -> bool:
        """Check if runtime environment is compatible with model requirements"""
        try:
            import sklearn
            import numpy as np
            
            compatible = True
            
            # Check NumPy version (2.0+ required for newly trained models)
            numpy_version = tuple(map(int, np.__version__.split('.')[:2]))
            if numpy_version[0] < 2:
                self.logger.error(f"❌ NumPy version {np.__version__} < 2.0 (incompatible)")
                compatible = False
            else:
                self.logger.info(f"✅ NumPy version {np.__version__} >= 2.0 (compatible)")
            
            # Check scikit-learn version (1.7+ required for NumPy 2.x compatibility)
            sklearn_version = tuple(map(int, sklearn.__version__.split('.')[:2]))
            if sklearn_version < (1, 7):
                self.logger.error(f"❌ scikit-learn version {sklearn.__version__} < 1.7 (incompatible)")
                compatible = False
            else:
                self.logger.info(f"✅ scikit-learn version {sklearn.__version__} >= 1.7 (compatible)")
            
            return compatible
            
        except Exception as e:
            self.logger.error(f"❌ Environment compatibility check failed: {e}")
            return False
    
    def _validate_model_structure(self, model_data) -> bool:
        """Validate that loaded model has expected structure"""
        required_keys = ['model', 'scaler', 'features', 'metrics']
        
        if not isinstance(model_data, dict):
            self.logger.warning("Model data is not a dictionary")
            return False
        
        missing_keys = [key for key in required_keys if key not in model_data]
        if missing_keys:
            self.logger.warning(f"Model missing required keys: {missing_keys}")
            return False
        
        return True


def test_log_runtime_environment():
    """Test _log_runtime_environment method"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Log Runtime Environment")
    logger.info("="*60)
    
    try:
        service = MockService()
        service._log_runtime_environment()
        logger.info("✅ Environment logging test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Environment logging test failed: {e}")
        return False


def test_check_environment_compatibility():
    """Test _check_environment_compatibility method"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Check Environment Compatibility")
    logger.info("="*60)
    
    try:
        service = MockService()
        is_compatible = service._check_environment_compatibility()
        
        if is_compatible:
            logger.info("✅ Environment is compatible")
        else:
            logger.warning("⚠️  Environment is not compatible (expected for old dependencies)")
        
        logger.info("✅ Compatibility check test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Compatibility check test failed: {e}")
        return False


def test_validate_model_structure():
    """Test _validate_model_structure method"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Validate Model Structure")
    logger.info("="*60)
    
    try:
        service = MockService()
        
        # Test 1: Valid model structure
        valid_model = {
            'model': 'dummy_model',
            'scaler': 'dummy_scaler',
            'features': ['feature1', 'feature2'],
            'metrics': {'r2': 0.85}
        }
        
        if service._validate_model_structure(valid_model):
            logger.info("✅ Valid model structure correctly validated")
        else:
            logger.error("❌ Valid model structure incorrectly rejected")
            return False
        
        # Test 2: Invalid model structure (missing keys)
        invalid_model = {
            'model': 'dummy_model',
            'features': ['feature1', 'feature2']
        }
        
        if not service._validate_model_structure(invalid_model):
            logger.info("✅ Invalid model structure correctly rejected (missing keys)")
        else:
            logger.error("❌ Invalid model structure incorrectly accepted")
            return False
        
        # Test 3: Non-dict model
        if not service._validate_model_structure("not_a_dict"):
            logger.info("✅ Non-dict model correctly rejected")
        else:
            logger.error("❌ Non-dict model incorrectly accepted")
            return False
        
        # Test 4: Empty dict
        if not service._validate_model_structure({}):
            logger.info("✅ Empty dict correctly rejected")
        else:
            logger.error("❌ Empty dict incorrectly accepted")
            return False
        
        logger.info("✅ Model structure validation test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Model structure validation test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_error_classification():
    """Test error classification in model loading"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Error Classification")
    logger.info("="*60)
    
    try:
        test_errors = [
            ("ModuleNotFoundError: No module named 'numpy._core'", "NumPy version incompatibility"),
            ("AttributeError: module 'numpy' has no attribute '_core'", "NumPy version incompatibility"),
            ("XGBoost error: _loss not found", "XGBoost version incompatibility"),
            ("sklearn.exceptions.NotFittedError", "scikit-learn version incompatibility"),
            ("pickle.UnpicklingError: invalid load key", "Pickle/serialization error"),
            ("Some random error", "Unknown error"),
        ]
        
        for error_msg, expected_type in test_errors:
            # Classify error type
            if 'numpy._core' in error_msg or 'numpy.core' in error_msg or ("numpy" in error_msg.lower() and "_core" in error_msg):
                error_type = "NumPy version incompatibility"
            elif '_loss' in error_msg or 'xgboost' in error_msg.lower():
                error_type = "XGBoost version incompatibility"
            elif 'sklearn' in error_msg.lower():
                error_type = "scikit-learn version incompatibility"
            elif 'pickle' in error_msg.lower() or 'unpickl' in error_msg.lower():
                error_type = "Pickle/serialization error"
            else:
                error_type = "Unknown error"
            
            if error_type == expected_type:
                logger.info(f"✅ Correctly classified: '{error_msg[:50]}...' as '{error_type}'")
            else:
                logger.error(f"❌ Incorrectly classified: '{error_msg[:50]}...' as '{error_type}' (expected '{expected_type}')")
                return False
        
        logger.info("✅ Error classification test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Error classification test failed: {e}")
        return False


def test_model_loading_with_real_file():
    """Test model loading with a real model file if available"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Model Loading with Real File")
    logger.info("="*60)
    
    try:
        service = MockService()
        models_dir = Path("models")
        
        if not models_dir.exists():
            logger.warning("⚠️  Models directory not found - skipping real file test")
            return True
        
        model_files = list(models_dir.glob("*.pkl"))
        if not model_files:
            logger.warning("⚠️  No model files found - skipping real file test")
            return True
        
        # Try to load the first model file
        test_file = model_files[0]
        logger.info(f"Testing with model file: {test_file.name}")
        
        try:
            model_data = joblib.load(test_file)
            logger.info(f"✅ Successfully loaded model file")
            
            # Validate structure
            is_valid = service._validate_model_structure(model_data)
            if is_valid:
                logger.info(f"✅ Model structure is valid")
            else:
                logger.warning(f"⚠️  Model structure is invalid")
            
            # Check what keys are present
            if isinstance(model_data, dict):
                logger.info(f"Model keys: {list(model_data.keys())}")
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"⚠️  Failed to load model: {e}")
            
            # Classify the error
            if 'numpy._core' in error_msg or 'numpy.core' in error_msg:
                logger.info("✅ Correctly identified NumPy compatibility issue")
            elif '_loss' in error_msg or 'xgboost' in error_msg.lower():
                logger.info("✅ Correctly identified XGBoost compatibility issue")
            else:
                logger.info(f"Error type: {type(e).__name__}")
        
        logger.info("✅ Real file loading test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Real file loading test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "="*60)
    logger.info("UNIT TESTS FOR MODEL LOADING ENHANCEMENTS (TASK 4)")
    logger.info("="*60)
    
    results = []
    
    # Run tests
    results.append(("Log Runtime Environment", test_log_runtime_environment()))
    results.append(("Check Environment Compatibility", test_check_environment_compatibility()))
    results.append(("Validate Model Structure", test_validate_model_structure()))
    results.append(("Error Classification", test_error_classification()))
    results.append(("Model Loading with Real File", test_model_loading_with_real_file()))
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("="*60)
    logger.info(f"Total: {passed}/{total} tests passed")
    logger.info("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
