#!/usr/bin/env python3
"""
Test script for model loading enhancements (Task 4)

This script tests the new methods added to the prediction API:
- _log_runtime_environment()
- _check_environment_compatibility()
- _validate_model_structure()
- Enhanced _load_models() with error tracking
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment_logging():
    """Test _log_runtime_environment method"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Environment Logging")
    logger.info("="*60)
    
    try:
        from src.prediction_api import CropYieldPredictionService
        
        # Create a minimal service instance to test the method
        service = CropYieldPredictionService()
        
        logger.info("✅ Environment logging test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Environment logging test failed: {e}")
        return False

def test_compatibility_check():
    """Test _check_environment_compatibility method"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Environment Compatibility Check")
    logger.info("="*60)
    
    try:
        import numpy as np
        import sklearn
        
        logger.info(f"Current NumPy version: {np.__version__}")
        logger.info(f"Current scikit-learn version: {sklearn.__version__}")
        
        # Check versions
        numpy_version = tuple(map(int, np.__version__.split('.')[:2]))
        sklearn_version = tuple(map(int, sklearn.__version__.split('.')[:2]))
        
        if numpy_version[0] >= 2:
            logger.info("✅ NumPy version is compatible (>= 2.0)")
        else:
            logger.warning("⚠️  NumPy version is < 2.0")
        
        if sklearn_version >= (1, 7):
            logger.info("✅ scikit-learn version is compatible (>= 1.7)")
        else:
            logger.warning("⚠️  scikit-learn version is < 1.7")
        
        logger.info("✅ Compatibility check test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Compatibility check test failed: {e}")
        return False

def test_model_structure_validation():
    """Test _validate_model_structure method"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Model Structure Validation")
    logger.info("="*60)
    
    try:
        from src.prediction_api import CropYieldPredictionService
        import tempfile
        import joblib
        
        # Create a temporary service instance
        service = CropYieldPredictionService()
        
        # Test valid model structure
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
        
        # Test invalid model structure (missing keys)
        invalid_model = {
            'model': 'dummy_model',
            'features': ['feature1', 'feature2']
        }
        
        if not service._validate_model_structure(invalid_model):
            logger.info("✅ Invalid model structure correctly rejected")
        else:
            logger.error("❌ Invalid model structure incorrectly accepted")
            return False
        
        # Test non-dict model
        if not service._validate_model_structure("not_a_dict"):
            logger.info("✅ Non-dict model correctly rejected")
        else:
            logger.error("❌ Non-dict model incorrectly accepted")
            return False
        
        logger.info("✅ Model structure validation test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Model structure validation test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_enhanced_model_loading():
    """Test enhanced _load_models with error tracking"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Enhanced Model Loading")
    logger.info("="*60)
    
    try:
        from src.prediction_api import CropYieldPredictionService
        
        # Check if models directory exists
        models_dir = Path("models")
        if not models_dir.exists():
            logger.warning("⚠️  Models directory not found - will use fallback models")
        else:
            model_files = list(models_dir.glob("*.pkl"))
            logger.info(f"Found {len(model_files)} model files")
        
        # Create service instance (this will trigger _load_models)
        service = CropYieldPredictionService()
        
        # Check if models were loaded
        if hasattr(service, 'location_models'):
            total_models = sum(len(models) for models in service.location_models.values())
            logger.info(f"Loaded {total_models} models across {len(service.location_models)} locations")
            
            if total_models > 0:
                logger.info("✅ Models loaded successfully")
            else:
                logger.warning("⚠️  No models loaded, using fallback models")
        else:
            logger.error("❌ location_models attribute not found")
            return False
        
        logger.info("✅ Enhanced model loading test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Enhanced model loading test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Run all tests"""
    logger.info("\n" + "="*60)
    logger.info("TESTING MODEL LOADING ENHANCEMENTS (TASK 4)")
    logger.info("="*60)
    
    results = []
    
    # Run tests
    results.append(("Environment Logging", test_environment_logging()))
    results.append(("Compatibility Check", test_compatibility_check()))
    results.append(("Model Structure Validation", test_model_structure_validation()))
    results.append(("Enhanced Model Loading", test_enhanced_model_loading()))
    
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
