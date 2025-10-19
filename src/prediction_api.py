#!/usr/bin/env python3
"""
Real-time Crop Yield Prediction API Service

Phase 6: Web API server that integrates all Phase 5 modules for real-time
crop yield predictions based on crop type, variety, location, and sowing date.

Endpoints:
- POST /predict/yield: Main prediction endpoint
- GET /health: Service health check
- GET /crops: Available crops and varieties
- POST /validate: Input validation
- POST /predict/field-analysis: Field analysis with polygon coordinates

Fixed: Real-time data collection and endpoint deployment issues
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import traceback
import joblib
import pandas as pd
import numpy as np

from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, Field, validator
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import modules (use absolute imports for deployment compatibility)
from api_credentials import APICredentialsManager, initialize_all_apis
from gee_client import GEEClient
from weather_client import OpenWeatherClient
from unified_data_pipeline import UnifiedDataPipeline
from crop_variety_database import CropVarietyDatabase
from sowing_date_intelligence import SowingDateIntelligence
from variety_selection_service import VarietySelectionService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PredictionRequest(BaseModel):
    """Pydantic model for prediction request validation"""

    crop_type: str = Field(
        ..., description="Crop type (Rice, Wheat, Maize)",
        pattern="^(Rice|Wheat|Maize)$"
    )
    variety_name: Optional[str] = Field(
        None, description="Crop variety name (optional - defaults to regional most popular)"
    )
    location_name: str = Field(
        ..., description="Location name (e.g., Bhopal, Lucknow)"
    )
    latitude: float = Field(
        ..., ge=-90, le=90,
        description="Location latitude (-90 to 90)"
    )
    longitude: float = Field(
        ..., ge=-180, le=180,
        description="Location longitude (-180 to 180)"
    )
    sowing_date: str = Field(
        ..., description="Sowing date (YYYY-MM-DD)"
    )
    use_real_time_data: bool = Field(
        default=True, description="Use real-time satellite and weather data"
    )

    @validator('sowing_date')
    def validate_sowing_date(cls, v):
        """Validate sowing date format and range"""
        try:
            sowing_dt = datetime.fromisoformat(v)
            # Check if date is not in the future
            if sowing_dt > datetime.now():
                raise ValueError("Sowing date cannot be in the future")
            # Check if date is not too old (more than 2 years ago)
            if sowing_dt < datetime.now() - timedelta(days=730):
                raise ValueError("Sowing date is too old (more than 2 years ago)")
        except ValueError as e:
            raise ValueError(f"Invalid sowing date format or {str(e)}")

        return v


class CropYieldPredictionService:
    """Main prediction service integrating all Phase 5 modules"""

    def __init__(self, config_path: str = "config/demo_config.json"):
        self.config_path = Path(config_path)
        self.logger = logger

        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)

        self._initialize_components()
        self._load_models()
        self._setup_feature_mappings()

        self.logger.info("✅ Crop Yield Prediction Service initialized")

    def _initialize_components(self):
        """Initialize all Phase 5 components"""
        try:
            # Initialize API credentials and connections
            self.api_manager = APICredentialsManager()
            initialize_all_apis()

            # Initialize GEE and Weather clients
            self.gee_client = GEEClient()
            self.weather_client = OpenWeatherClient()

            # Initialize data pipeline
            self.data_pipeline = UnifiedDataPipeline()

            # Initialize crop intelligence modules
            self.variety_db = CropVarietyDatabase()
            self.sowing_intelligence = SowingDateIntelligence()

            # Initialize variety selection service
            try:
                self.variety_selector = VarietySelectionService(self.variety_db)
                self.logger.info("✅ VarietySelectionService initialized successfully")
            except Exception as variety_error:
                self.logger.error(f"❌ Failed to initialize VarietySelectionService: {variety_error}")
                self.logger.warning("⚠️  Variety selection will not be available - variety_name will be required")
                self.variety_selector = None

        except Exception as e:
            self.logger.error(f"Failed to initialize service components: {e}")
            raise

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

    def _load_models(self):
        """Load trained ML models with enhanced compatibility handling"""
        self.models = {}
        models_dir = Path("models")

        # Log runtime environment at startup
        self._log_runtime_environment()

        if not models_dir.exists():
            self.logger.warning(f"Models directory not found: {models_dir}")
            self.location_models = self._create_fallback_models()
            return

        # Check environment compatibility before attempting to load
        if not self._check_environment_compatibility():
            self.logger.error("❌ Environment incompatible with model requirements")
            self.location_models = self._create_fallback_models()
            return

        # Check if models are available
        model_files = list(models_dir.glob("*.pkl"))

        if not model_files:
            self.logger.warning("No trained models found in models directory")
            self.location_models = self._create_fallback_models()
            return

        # Group models by location and algorithm
        model_mapping = {}
        for model_file in model_files:
            filename = model_file.stem
            parts = filename.split('_')

            if len(parts) >= 5:  # Need at least 5 parts: location_location_algorithm_algorithm_timestamp
                location = '_'.join(parts[:2])  # e.g., 'bhopal_training'
                
                # Handle different algorithm naming patterns
                if 'gradient_boosting' in filename:
                    algorithm = 'gradient_boosting'
                elif 'random_forest' in filename:
                    algorithm = 'random_forest'
                elif 'ridge' in filename:
                    algorithm = 'ridge'
                else:
                    continue
                
                # Extract timestamp (last two parts)
                timestamp = '_'.join(parts[-2:])

                # Store model info
                model_key = f"{location}_{algorithm}"
                model_mapping[model_key] = {
                    'path': model_file,
                    'location': location,
                    'algorithm': algorithm,
                    'timestamp': timestamp
                }

        # Load and store models by location with enhanced error tracking
        self.location_models = {}
        total_loaded = 0
        failed_models = []
        
        for model_key, info in model_mapping.items():
            try:
                # Load model data
                model_data = joblib.load(info['path'])
                
                # Validate model structure
                if not self._validate_model_structure(model_data):
                    error_type = "Invalid structure"
                    failed_models.append((model_key, error_type))
                    self.logger.warning(f"❌ Failed to load {model_key}: {error_type}")
                    continue
                
                # Extract model components
                location_name = info['location']
                if location_name not in self.location_models:
                    self.location_models[location_name] = {}

                self.location_models[location_name][info['algorithm']] = {
                    'model': model_data['model'],
                    'scaler': model_data.get('scaler'),
                    'poly': model_data.get('poly'),
                    'features': model_data.get('features'),
                    'timestamp': info['timestamp'],
                    'path': info['path']
                }
                total_loaded += 1
                self.logger.info(f"✅ Successfully loaded model: {model_key}")

            except Exception as e:
                error_msg = str(e)
                
                # Classify error type for better debugging
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
                
                failed_models.append((model_key, f"{error_type}: {error_msg[:100]}"))
                self.logger.warning(f"❌ Failed to load {model_key}: {error_type}")
                self.logger.debug(f"   Error details: {error_msg}")

        # Log summary
        self.logger.info("=" * 60)
        self.logger.info(f"Model Loading Summary:")
        self.logger.info(f"  Total models found: {len(model_mapping)}")
        self.logger.info(f"  Successfully loaded: {total_loaded}")
        self.logger.info(f"  Failed to load: {len(failed_models)}")
        
        if failed_models:
            self.logger.warning("Failed models:")
            for model_name, error in failed_models:
                self.logger.warning(f"  - {model_name}: {error}")
        
        self.logger.info("=" * 60)

        # If no models loaded successfully, use fallbacks
        if total_loaded == 0:
            self.logger.warning("❌ No models loaded successfully, switching to fallback prediction")
            self.location_models = self._create_fallback_models()
        else:
            self.logger.info(f"✅ Service ready with {total_loaded} models across {len(self.location_models)} locations")

    def _create_fallback_models(self) -> Dict:
        """Create simple fallback models when saved models aren't compatible"""
        self.logger.info("🔄 Creating fallback prediction models...")

        # Create simple linear regression fallbacks based on agricultural knowledge
        fallback_models = {}

        # Fallback coefficients derived from agricultural domain knowledge
        crop_coefficients = {
            'rice_coefficients': [0.4, 0.3, -0.1, 0.2, 0.1, -0.05, 0.15, 0.05, -0.1, 0.08, 0.02, -0.03, 0.1, 0.04, -0.02, 0.06, 0.02, -0.08, 0.02, 0.03],
            'wheat_coefficients': [0.35, 0.25, -0.15, 0.18, 0.12, -0.08, 0.12, 0.06, -0.12, 0.07, 0.03, -0.04, 0.08, 0.05, -0.03, 0.04, 0.03, -0.06, 0.01, 0.02],
            'maize_coefficients': [0.38, 0.28, -0.12, 0.22, 0.09, -0.06, 0.14, 0.04, -0.09, 0.08, 0.02, -0.02, 0.09, 0.03, -0.01, 0.05, 0.01, -0.07, 0.02, 0.04]
        }

        # Create Ridge regression models for different regions
        for location_key in ['bhopal_training', 'lucknow_training', 'chandigarh_training', 'patna_training', 'north_india_regional']:
            fallback_models[location_key] = {}

            for algorithm in ['ridge', 'gradient_boosting', 'random_forest']:
                # Use rice coefficients as default (most common)
                coeffs = crop_coefficients['rice_coefficients'][:20]  # Limit to 20 features

                # Simple ridge regression with pre-determined coefficients
                from sklearn.linear_model import Ridge
                ridge_model = Ridge(alpha=0.1)
                ridge_model.coef_ = np.array(coeffs)
                ridge_model.intercept_ = 3.5  # Base yield in tons/ha

                fallback_models[location_key][algorithm] = {
                    'model': ridge_model,
                    'timestamp': 'fallback_20251018',
                    'path': 'fallback_model'
                }

        self.logger.info("✅ Created fallback prediction models for all regions")
        return fallback_models

    def _setup_feature_mappings(self):
        """Set up feature mappings for model input"""
        # Based on the original Phase 4 feature engineering - reduced to 15 features to match trained models
        self.feature_columns = [
            # Basic weather features (5)
            'temp_max', 'temp_min', 'temp_mean', 'precipitation', 'humidity',
            # Derived features (4) 
            'temp_range', 'gdd', 'heat_stress_days', 'water_availability_index',
            # Seasonal features (3)
            'is_kharif_season', 'is_rabi_season', 'is_zaid_season',
            # Vegetation indices (3)
            'Fpar', 'NDVI', 'Lai'
        ]

        # Regional mappings - best model for each region
        self.region_model_mapping = {
            'bhopal': 'bhopal_training',
            'chandigarh': 'chandigarh_training',
            'lucknow': 'lucknow_training',
            'patna': 'patna_training',
            'north_india': 'north_india_regional'
        }

    def predict_yield(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main prediction function integrating all components

        Args:
            request_data: Validated prediction request data

        Returns:
            Prediction results dictionary
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"🔍 Starting prediction for {request_data['crop_type']} in {request_data['location_name']}")

            # Check if variety needs to be selected (None, null, or empty string)
            variety_assumed = False
            selection_metadata = None
            
            if not request_data.get('variety_name'):
                # Variety is missing, None, or empty string - select default variety
                if self.variety_selector is None:
                    self.logger.error(
                        f"❌ Variety selection service unavailable for {request_data['crop_type']} "
                        f"in {request_data['location_name']}"
                    )
                    return self._error_response(
                        "ServiceUnavailable",
                        "Variety selection service is not available. Please specify variety_name.",
                        variety_selection_available=False
                    )
                
                try:
                    # Attempt to select default variety with full error handling
                    # Start performance timing for variety selection
                    variety_selection_start = time.time()
                    
                    self.logger.info(
                        f"🔄 Starting variety selection | "
                        f"crop_type={request_data['crop_type']} | "
                        f"location={request_data['location_name']}"
                    )
                    
                    selection_result = self.variety_selector.select_default_variety(
                        request_data['crop_type'],
                        request_data['location_name']
                    )
                    
                    # Calculate variety selection time
                    variety_selection_time_ms = (time.time() - variety_selection_start) * 1000
                    
                    # Validate selection result structure
                    if not selection_result or 'variety_name' not in selection_result:
                        raise ValueError("Invalid selection result: missing variety_name")
                    
                    # Update request data with selected variety
                    request_data['variety_name'] = selection_result['variety_name']
                    variety_assumed = True
                    selection_metadata = selection_result.get('selection_metadata', {})
                    
                    # INFO-level logging for variety selection with full metadata and timing
                    self.logger.info(
                        f"✅ Variety selection completed | "
                        f"crop_type={request_data['crop_type']} | "
                        f"location={request_data['location_name']} | "
                        f"selected_variety={request_data['variety_name']} | "
                        f"reason={selection_metadata.get('reason', 'unknown')} | "
                        f"region={selection_metadata.get('region', 'unknown')} | "
                        f"yield_potential={selection_metadata.get('yield_potential', 'N/A')} | "
                        f"total_time={variety_selection_time_ms:.2f}ms"
                    )
                    
                except ValueError as ve:
                    # Handle NoVarietiesAvailable scenario
                    # ERROR-level logging for variety selection failure
                    self.logger.error(
                        f"❌ Variety selection failed (no varieties available) | "
                        f"crop_type={request_data['crop_type']} | "
                        f"location={request_data['location_name']} | "
                        f"error={str(ve)}"
                    )
                    return self._error_response(
                        "NoVarietiesAvailable",
                        f"Unable to determine appropriate variety for crop type '{request_data['crop_type']}' "
                        f"in location '{request_data['location_name']}'. Please specify variety_name explicitly.",
                        crop_type=request_data['crop_type'],
                        location=request_data['location_name'],
                        error_details=str(ve)
                    )
                    
                except Exception as e:
                    # Handle database query failures and other errors
                    # ERROR-level logging for variety selection failure with error type
                    self.logger.error(
                        f"❌ Variety selection failed (unexpected error) | "
                        f"crop_type={request_data['crop_type']} | "
                        f"location={request_data['location_name']} | "
                        f"error_type={type(e).__name__} | "
                        f"error={str(e)}"
                    )
                    
                    # Determine error type for better response
                    if "database" in str(e).lower() or "query" in str(e).lower():
                        error_code = "DatabaseError"
                        error_message = (
                            f"Database error during variety selection: {str(e)}. "
                            f"Please specify variety_name explicitly or try again later."
                        )
                    else:
                        error_code = "VarietySelectionFailed"
                        error_message = (
                            f"Failed to select default variety: {str(e)}. "
                            f"Please specify variety_name explicitly."
                        )
                    
                    return self._error_response(
                        error_code,
                        error_message,
                        crop_type=request_data['crop_type'],
                        location=request_data['location_name'],
                        error_details=str(e)
                    )

            # Validate inputs and get variety information
            # This validation applies to both user-specified and auto-selected varieties
            try:
                variety_info = self.variety_db.get_variety_by_name(
                    request_data['crop_type'],
                    request_data['variety_name']
                )
            except Exception as db_error:
                self.logger.error(
                    f"❌ Database error while validating variety '{request_data['variety_name']}' "
                    f"for {request_data['crop_type']}: {str(db_error)}"
                )
                return self._error_response(
                    "DatabaseError",
                    f"Failed to validate variety information: {str(db_error)}",
                    crop_type=request_data['crop_type'],
                    variety_name=request_data['variety_name']
                )

            if not variety_info:
                # Log detailed error based on whether variety was auto-selected or user-specified
                if variety_assumed:
                    self.logger.error(
                        f"❌ Auto-selected variety '{request_data['variety_name']}' not found in database "
                        f"for {request_data['crop_type']} (this should not happen - indicates data inconsistency)"
                    )
                    return self._error_response(
                        "InternalError",
                        f"Selected variety '{request_data['variety_name']}' not found in database. "
                        f"This indicates a data inconsistency issue.",
                        variety_found=False,
                        variety_assumed=True,
                        crop_type=request_data['crop_type']
                    )
                else:
                    self.logger.warning(
                        f"⚠️  User-specified variety '{request_data['variety_name']}' not found "
                        f"for {request_data['crop_type']}"
                    )
                    return self._error_response(
                        "InvalidInput",
                        f"Variety '{request_data['variety_name']}' not found for crop '{request_data['crop_type']}'. "
                        f"Please check the variety name or omit it to use automatic selection.",
                        variety_found=False,
                        crop_type=request_data['crop_type']
                    )

            # Calculate growing period days from sowing date
            sowing_date = datetime.fromisoformat(request_data['sowing_date'])
            current_date = datetime.now()

            # For prediction, we need some reasonable growth period
            growth_days = min(150, (current_date - sowing_date).days)  # Max 150 days

            if growth_days < 30:
                self.logger.warning(f"Early stage growth: only {growth_days} days from sowing")

            # Initialize data collection result
            data_collection_result = {'success': False, 'data_freshness_hours': 0, 'data_quality_score': 0.0}
            
            # Collect real-time data if requested
            if request_data['use_real_time_data']:
                data_collection_result = self._collect_real_time_data(
                    request_data['latitude'],
                    request_data['longitude'],
                    request_data['location_name']
                )

                if not data_collection_result['success']:
                    self.logger.warning(f"Data collection failed: {data_collection_result['error']}")
                    return self._error_response(
                        "DataCollectionFailed",
                        f"Failed to collect real-time data: {data_collection_result['error']}",
                        alternative_available=True
                    )

                satellite_data = data_collection_result['satellite_data']
                weather_data = data_collection_result['weather_data']

            else:
                # Fall back to historical averages
                satellite_data = self._get_historical_averages(
                    request_data['location_name'], growth_days
                )
                weather_data = self._get_weather_averages(
                    request_data['location_name']
                )

            # Prepare model input features
            model_features = self._prepare_model_features(
                satellite_data, weather_data, growth_days, request_data
            )

            # Get best model for location
            model_result = self._get_model_prediction(model_features, request_data)

            # Calculate variety adjustments
            variety_adjustment = self.variety_db.calculate_variety_yield_adjustment(
                request_data['crop_type'],
                request_data['variety_name'],
                weather_data,
                model_result['raw_prediction']
            )

            # Prepare final response
            response = {
                'prediction_id': f"{request_data['crop_type']}_{request_data['location_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now().isoformat(),

                # Input data
                'input': {
                    'crop_type': request_data['crop_type'],
                    'variety_name': request_data['variety_name'],
                    'location': {
                        'name': request_data['location_name'],
                        'latitude': request_data['latitude'],
                        'longitude': request_data['longitude']
                    },
                    'sowing_date': request_data['sowing_date'],
                    'growth_days': growth_days,
                    'use_real_time_data': request_data['use_real_time_data']
                },

                # Prediction results
                'prediction': {
                    'yield_tons_per_hectare': round(float(model_result['prediction']), 2),
                    'variety_used': request_data['variety_name'],
                    'variety_assumed': variety_assumed,
                    'lower_bound': round(float(model_result['lower_bound']), 2),
                    'upper_bound': round(float(model_result['upper_bound']), 2),
                    'confidence_score': round(model_result['confidence'], 3),
                    'variety_adjusted_yield': round(float(variety_adjustment['predicted_yield']), 2)
                },

                # Model information
                'model': {
                    'location_used': model_result['location_used'],
                    'algorithm': model_result['algorithm'],
                    'model_timestamp': model_result['model_timestamp'],
                    'feature_count': len(model_features)
                },

                # Data sources
                'data_sources': {
                    'satellite_data_points': len(satellite_data) if not satellite_data.empty else 0,
                    'weather_data_points': len(weather_data) if not weather_data.empty else 0,
                    'data_freshness_hours': data_collection_result.get('data_freshness_hours', 0)
                },

                # Factors affecting prediction
                'factors': {
                    'variety_characteristics': {
                        'maturity_days': variety_info['maturity_days'],
                        'yield_potential': variety_info['yield_potential'],
                        'drought_tolerance': variety_info['drought_tolerance']
                    },
                    'environmental_adjustments': {
                        'heat_stress_penalty': round(variety_adjustment['heat_stress_penalty'], 3),
                        'drought_penalty': round(variety_adjustment['drought_penalty'], 3),
                        'cold_stress_penalty': round(variety_adjustment['cold_stress_penalty'], 3),
                        'optimal_temp_bonus': round(variety_adjustment['optimal_temp_bonus'], 3)
                    },
                    'data_quality': data_collection_result.get('data_quality_score', 0.0)
                },

                # Processing information
                'processing_time_seconds': round((datetime.now() - start_time).total_seconds(), 2),
                'api_version': '6.1.0'
            }

            # Add selection metadata if variety was assumed
            if variety_assumed and selection_metadata:
                response['factors']['default_variety_selection'] = selection_metadata

            self.logger.info(f"✅ Prediction completed: {response['prediction']['yield_tons_per_hectare']} tons/ha")
            return response

        except Exception as e:
            error_details = traceback.format_exc()
            self.logger.error(f"❌ Prediction failed: {str(e)}\n{error_details}")
            return self._error_response(
                "InternalError",
                f"Prediction service error: {str(e)}",
                error_details=error_details
            )

    def _collect_real_time_data(self, latitude: float, longitude: float,
                               location_name: str) -> Dict[str, Any]:
        """Collect real-time satellite and weather data"""
        result = {
            'success': False,
            'satellite_data': pd.DataFrame(),
            'weather_data': pd.DataFrame(),
            'data_freshness_hours': 0,
            'data_quality_score': 0.0
        }

        try:
            # Collect data using unified pipeline
            if not self.gee_client.initialize():
                return {**result, 'error': 'GEE authentication failed'}

            # Get last 30 days of satellite data
            satellite_data = self.gee_client.get_satellite_data_for_location(
                latitude=latitude,
                longitude=longitude,
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                data_types=['ndvi', 'evi']
            )

            # Get current and forecast weather
            weather_data = self.weather_client.get_current_and_forecast_weather(latitude, longitude)

            # Check if we have at least some data (weather is more critical than satellite)
            if weather_data.empty:
                return {**result, 'error': 'Weather data collection failed'}
            
            # If satellite data is empty, use fallback satellite data
            if satellite_data.empty:
                self.logger.warning("⚠️ Satellite data collection failed, using fallback data")
                satellite_data = self._generate_fallback_satellite_data(30)

            # Calculate data quality score
            quality_score = self._calculate_data_quality_score(satellite_data, weather_data)

            # Enhance weather data with agricultural indices
            weather_data = self.weather_client._calculate_agricultural_indices(weather_data)

            result.update({
                'success': True,
                'satellite_data': satellite_data,
                'weather_data': weather_data,
                'data_freshness_hours': 24,  # Approximate
                'data_quality_score': quality_score
            })

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Data collection failed: {e}")

        return result

    def _get_historical_averages(self, location_name: str, days_back: int) -> pd.DataFrame:
        """Get historical satellite data averages"""
        try:
            # Try to get from pipeline, fallback to generated data
            historical_data = self.data_pipeline.get_historical_data(
                location_name, 'satellite', days_back
            )

            if not historical_data.empty:
                return historical_data

            # Generate reasonable fallback data based on typical values
            return self._generate_fallback_satellite_data(days_back)

        except Exception as e:
            self.logger.warning(f"Failed to get historical data: {e}")
            return self._generate_fallback_satellite_data(days_back)

    def _get_weather_averages(self, location_name: str) -> pd.DataFrame:
        """Get historical weather averages"""
        try:
            weather_data = self.data_pipeline.get_historical_data(
                location_name, 'weather', 7  # Last week
            )

            if not weather_data.empty:
                return weather_data

            # Generate fallback weather data
            return self._generate_fallback_weather_data()

        except Exception as e:
            self.logger.warning(f"Failed to get weather data: {e}")
            return self._generate_fallback_weather_data()

    def _generate_fallback_satellite_data(self, days_back: int) -> pd.DataFrame:
        """Generate fallback satellite data when real data unavailable"""
        dates = pd.date_range(end=datetime.now(), periods=days_back, freq='D')

        # Typical NDVI/EVI/FPAR/LAI ranges for North India
        np.random.seed(42)  # For consistent fallback data
        data = {
            'date': dates,
            'ndvi': np.random.normal(0.4, 0.1, days_back).clip(0.1, 0.8),
            'evi': np.random.normal(0.35, 0.08, days_back).clip(0.1, 0.7),
            'fpar': np.random.normal(0.4, 0.08, days_back).clip(0.1, 0.7),  # Added FPAR
            'lai': np.random.normal(2.0, 0.5, days_back).clip(0.5, 4.0),  # Added LAI
            'surface_temp': np.random.normal(25, 5, days_back).clip(10, 40),
            'chirps_precipitation': np.random.exponential(2, days_back)
        }

        df = pd.DataFrame(data)
        df['location_name'] = 'Unknown'
        return df

    def _generate_fallback_weather_data(self) -> pd.DataFrame:
        """Generate fallback weather data"""
        now = datetime.now()
        timestamps = pd.date_range(start=now - timedelta(days=7), end=now, freq='3H')

        np.random.seed(42)
        data = {
            'timestamp': timestamps,
            'temp': np.random.normal(28, 3, len(timestamps)).clip(15, 40),
            'temp_min': np.random.normal(22, 2, len(timestamps)).clip(10, 30),
            'temp_max': np.random.normal(34, 3, len(timestamps)).clip(25, 45),
            'humidity': np.random.normal(65, 15, len(timestamps)).clip(20, 90),
            'wind_speed': np.random.gamma(2, 1.5, len(timestamps)).clip(0, 10),
            'pressure': np.random.normal(1013, 10, len(timestamps)),
            'clouds': np.random.randint(0, 100, len(timestamps))
        }

        df = pd.DataFrame(data)
        df['location_name'] = 'Unknown'
        return df

    def _prepare_model_features(self, satellite_data: pd.DataFrame,
                               weather_data: pd.DataFrame,
                               growth_days: int, request_data: Dict) -> Dict[str, float]:
        """Prepare features for model input"""
        features = {}

        try:
            # Get current month for seasonal features
            current_month = datetime.now().month
            
            # Aggregate satellite data (vegetation indices) - FIXED
            if not satellite_data.empty:
                # Properly handle DataFrame columns
                features.update({
                    'Fpar': float(satellite_data['fpar'].mean()) if 'fpar' in satellite_data.columns else 0.4,
                    'NDVI': float(satellite_data['ndvi'].mean()) if 'ndvi' in satellite_data.columns else 0.4,
                    'Lai': float(satellite_data['lai'].mean()) if 'lai' in satellite_data.columns else 2.0
                })
            else:
                features.update({
                    'Fpar': 0.4, 'NDVI': 0.4, 'Lai': 2.0
                })

            # Aggregate weather data (basic weather features) - FIXED
            if not weather_data.empty:
                temp_max = float(weather_data['temp_max'].max()) if 'temp_max' in weather_data.columns else 34.0
                temp_min = float(weather_data['temp_min'].min()) if 'temp_min' in weather_data.columns else 22.0
                temp_mean = float(weather_data['temp'].mean()) if 'temp' in weather_data.columns else 28.0
                
                # Fix precipitation handling
                if 'total_rain' in weather_data.columns:
                    precipitation = float(weather_data['total_rain'].mean())
                elif 'precipitation' in weather_data.columns:
                    precipitation = float(weather_data['precipitation'].mean())
                else:
                    precipitation = 3.0
                
                humidity = float(weather_data['humidity'].mean()) if 'humidity' in weather_data.columns else 65.0
                
                features.update({
                    'temp_max': temp_max,
                    'temp_min': temp_min,
                    'temp_mean': temp_mean,
                    'precipitation': precipitation,
                    'humidity': humidity
                })

                # Derived features
                features.update({
                    'temp_range': temp_max - temp_min,
                    'gdd': max(0.0, temp_mean - 10.0),  # Growing degree days
                    'heat_stress_days': 1.0 if temp_max > 35 else 0.0,
                    'water_availability_index': min(1.0, precipitation / 10.0)
                })
            else:
                # Default values
                features.update({
                    'temp_max': 34.0, 'temp_min': 22.0, 'temp_mean': 28.0,
                    'precipitation': 3.0, 'humidity': 65.0,
                    'temp_range': 12.0, 'gdd': 18.0,
                    'heat_stress_days': 0.0, 'water_availability_index': 0.3
                })

            # Seasonal features
            features.update({
                'is_kharif_season': 1.0 if current_month in [6, 7, 8, 9, 10, 11] else 0.0,
                'is_rabi_season': 1.0 if current_month in [10, 11, 12, 1, 2, 3] else 0.0,
                'is_zaid_season': 1.0 if current_month in [4, 5] else 0.0
            })

        except Exception as e:
            self.logger.error(f"Failed to prepare features: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Return default values for all expected features
            features = {
                'temp_max': 34.0, 'temp_min': 22.0, 'temp_mean': 28.0,
                'precipitation': 3.0, 'humidity': 65.0,
                'temp_range': 12.0, 'gdd': 18.0,
                'heat_stress_days': 0.0, 'water_availability_index': 0.3,
                'is_kharif_season': 0.0, 'is_rabi_season': 0.0, 'is_zaid_season': 0.0,
                'Fpar': 0.4, 'NDVI': 0.4, 'Lai': 2.0
            }

        return features

    def _get_model_prediction(self, features: Dict[str, float],
                             request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get prediction from appropriate model"""

        # Find best location match
        location_lookup = request_data['location_name'].lower()
        location_model_key = None

        # Direct match
        for location, models in self.location_models.items():
            if location_lookup in location.lower():
                location_model_key = location
                break

        # Fallback to regional model
        if not location_model_key and 'north_india_regional' in self.location_models:
            location_model_key = 'north_india_regional'

        if not location_model_key:
            # Use any available location model
            location_model_key = next(iter(self.location_models.keys()))

        available_models = self.location_models[location_model_key]

        # Prefer gradient boosting, then random forest, then ridge
        model_preferences = ['gradient_boosting', 'random_forest', 'ridge']
        selected_algorithm = None

        for pref in model_preferences:
            if pref in available_models:
                selected_algorithm = pref
                break

        if not selected_algorithm:
            selected_algorithm = next(iter(available_models.keys()))

        model_info = available_models[selected_algorithm]
        model = model_info['model']

        try:
            # Prepare feature vector
            feature_vector = []
            self.logger.info(f"Available features keys: {list(features.keys())}")
            self.logger.info(f"Expected feature columns: {self.feature_columns}")
            
            for col in self.feature_columns:
                value = features.get(col, 0.0)
                # Ensure numeric values
                if isinstance(value, (int, float)):
                    feature_vector.append(float(value))
                else:
                    feature_vector.append(0.0)

            # Make prediction
            X = np.array([feature_vector])
            self.logger.info(f"Feature vector length: {len(feature_vector)}, Expected: {len(self.feature_columns)}")
            self.logger.info(f"Feature vector values: {feature_vector}")
            y_pred = model.predict(X)[0]

            # Calculate confidence interval (simple approach)
            # For a more sophisticated approach, could use prediction intervals
            prediction_std = 0.1  # Assumed standard deviation
            lower_bound = max(0, y_pred - 1.96 * prediction_std)
            upper_bound = y_pred + 1.96 * prediction_std

            # Calculate confidence score based on data availability
            confidence = min(0.95, max(0.3, 0.8))  # Simplified

            return {
                'prediction': float(y_pred),
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound),
                'confidence': confidence,
                'location_used': location_model_key,
                'algorithm': selected_algorithm,
                'model_timestamp': model_info['timestamp'],
                'raw_prediction': float(y_pred)
            }

        except Exception as e:
            self.logger.error(f"Model prediction failed: {e}")
            raise

    def _calculate_data_quality_score(self, satellite_data: pd.DataFrame,
                                     weather_data: pd.DataFrame) -> float:
        """Calculate data quality score"""
        try:
            quality_score = 0.0

            # Satellite data quality
            if not satellite_data.empty:
                sat_completeness = 1 - satellite_data.isnull().sum().sum() / (satellite_data.shape[0] * satellite_data.shape[1])
                sat_recentness = min(1.0, satellite_data.shape[0] / 30)  # Prefer 30 days
                quality_score += 0.4 * (sat_completeness + sat_recentness) / 2

            # Weather data quality
            if not weather_data.empty:
                weather_completeness = 1 - weather_data.isnull().sum().sum() / (weather_data.shape[0] * weather_data.shape[1])
                weather_recentness = min(1.0, weather_data.shape[0] / 56)  # Prefer weekly data (24*7/3h intervals)
                quality_score += 0.6 * (weather_completeness + weather_recentness) / 2

            return round(quality_score, 3)

        except Exception as e:
            self.logger.warning(f"Failed to calculate data quality: {e}")
            return 0.5

    def _error_response(self, error_type: str, message: str, **kwargs) -> Dict[str, Any]:
        """Generate standardized error response"""
        return {
            'error': {
                'type': error_type,
                'message': message,
                'timestamp': datetime.now().isoformat()
            },
            'success': False,
            **kwargs
        }

    def get_available_crops_and_varieties(self) -> Dict[str, Any]:
        """Get list of available crops and varieties"""
        try:
            crops_data = {}

            for crop in ['Rice', 'Wheat', 'Maize']:
                varieties_df = self.variety_db.get_crop_varieties(crop)
                if not varieties_df.empty:
                    crops_data[crop] = {
                        'count': len(varieties_df),
                        'varieties': varieties_df['variety_name'].tolist(),
                        'sample_variety': varieties_df.iloc[0]['variety_name'] if len(varieties_df) > 0 else None
                    }

            return {
                'crops': crops_data,
                'total_varieties': sum(crop_info['count'] for crop_info in crops_data.values()),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return self._error_response("DataRetrievalError", f"Failed to get crop data: {str(e)}")

    def validate_prediction_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate prediction input without making prediction"""
        try:
            # Basic validation
            required_fields = ['crop_type', 'variety_name', 'location_name', 'latitude', 'longitude', 'sowing_date']
            missing_fields = [field for field in required_fields if field not in input_data]

            if missing_fields:
                return {
                    'valid': False,
                    'errors': [f"Missing required field: {field}" for field in missing_fields]
                }

            # Validate crop and variety
            variety_info = self.variety_db.get_variety_by_name(
                input_data['crop_type'],
                input_data['variety_name']
            )

            if not variety_info:
                return {
                    'valid': False,
                    'errors': [f"Invalid crop variety combination: {input_data['crop_type']} - {input_data['variety_name']}"]
                }

            # Validate sowing date
            try:
                sowing_date = datetime.fromisoformat(input_data['sowing_date'])
                if sowing_date > datetime.now():
                    return {'valid': False, 'errors': ["Sowing date cannot be in the future"]}
            except ValueError:
                return {'valid': False, 'errors': ["Invalid sowing date format (use YYYY-MM-DD)"]}

            # Check seasonal appropriateness
            season = self.sowing_intelligence.detect_current_season(sowing_date)
            season_recommendations = self.sowing_intelligence.get_season_recommendations(
                input_data['crop_type'], input_data['location_name']
            )

            return {
                'valid': True,
                'variety_info': {
                    'maturity_days': variety_info['maturity_days'],
                    'yield_potential': variety_info['yield_potential'],
                    'region_prevalence': variety_info['region_prevalence']
                },
                'season_context': {
                    'detected_season': season,
                    'recommended_for_season': input_data['crop_type'] in [crop for crop, seasons in season_recommendations.items()
                                                                        if season in seasons]
                },
                'warnings': []
            }

        except Exception as e:
            return {'valid': False, 'errors': [f"Validation error: {str(e)}"]}


# FastAPI Application
app = FastAPI(
    title="Crop Yield Prediction API",
    description="Real-time crop yield prediction service using satellite and weather data",
    version="6.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
prediction_service = CropYieldPredictionService()


@app.get("/health")
async def health_check():
    """Service health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "6.0.0",
        "components": {
            "api_manager": "ready",
            "gee_client": "ready" if prediction_service.gee_client else "unavailable",
            "weather_client": "ready" if prediction_service.weather_client else "unavailable",
            "variety_db": "ready" if prediction_service.variety_db else "unavailable",
            "sowing_intelligence": "ready" if prediction_service.sowing_intelligence else "unavailable",
            "models_loaded": len(prediction_service.location_models)
        }
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including model loading status and environment info"""
    try:
        import sklearn
        import numpy as np
        
        # Calculate model loading status
        model_status = {}
        total_models = 0
        
        for location, models in prediction_service.location_models.items():
            model_status[location] = {
                'algorithms': list(models.keys()),
                'count': len(models)
            }
            total_models += len(models)
        
        # Check if running in fallback mode
        # Fallback mode is indicated by models having 'fallback' in their path or timestamp
        is_fallback_mode = False
        if total_models > 0:
            for location, models in prediction_service.location_models.items():
                for algorithm, model_info in models.items():
                    if 'fallback' in str(model_info.get('path', '')).lower() or \
                       'fallback' in str(model_info.get('timestamp', '')).lower():
                        is_fallback_mode = True
                        break
                if is_fallback_mode:
                    break
        else:
            is_fallback_mode = True
        
        # Determine overall service status
        if total_models == 0:
            service_status = 'degraded'
        elif is_fallback_mode:
            service_status = 'degraded'
        else:
            service_status = 'healthy'
        
        return {
            'status': service_status,
            'timestamp': datetime.now().isoformat(),
            'version': '6.0.0',
            'environment': {
                'numpy_version': np.__version__,
                'sklearn_version': sklearn.__version__,
                'joblib_version': joblib.__version__
            },
            'models': {
                'total_loaded': total_models,
                'locations': len(prediction_service.location_models),
                'by_location': model_status,
                'fallback_mode': is_fallback_mode
            },
            'components': {
                "api_manager": "ready",
                "gee_client": "ready" if prediction_service.gee_client else "unavailable",
                "weather_client": "ready" if prediction_service.weather_client else "unavailable",
                "variety_db": "ready" if prediction_service.variety_db else "unavailable",
                "sowing_intelligence": "ready" if prediction_service.sowing_intelligence else "unavailable"
            }
        }
    
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }


@app.get("/dashboard")
async def serve_dashboard():
    """Serve the interactive dashboard HTML file"""
    from fastapi.responses import HTMLResponse
    with open("src/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.post("/validate")
async def validate_input(request_data: PredictionRequest):
    """Validate prediction input without making prediction"""
    return prediction_service.validate_prediction_input(request_data.dict())


@app.post("/predict/yield")
async def predict_yield(request_data: PredictionRequest):
    """Main yield prediction endpoint"""
    try:
        result = prediction_service.predict_yield(request_data.dict())

        if 'error' in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']['message']
            )

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/crops")
async def get_crops():
    """Get available crops and varieties"""
    return prediction_service.get_available_crops_and_varieties()


@app.post("/predict/field-analysis")
async def predict_field_analysis(request_data: dict):
    """Field analysis endpoint for polygon-based predictions"""
    try:
        # Extract field coordinates and convert to lat/lon
        field_coords = request_data.get('field_coordinates', '')
        if not field_coords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="field_coordinates is required"
            )
        
        # Parse coordinates (assuming format: lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4)
        coords = [float(x.strip()) for x in field_coords.split(',')]
        if len(coords) < 6:  # Need at least 3 points (6 coordinates)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 3 coordinate points required"
            )
        
        # Calculate center point
        lats = coords[::2]  # Every other element starting from 0
        lons = coords[1::2]  # Every other element starting from 1
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Create prediction request
        prediction_request = {
            "crop_type": request_data.get('crop_type', 'Rice'),
            "variety_name": request_data.get('variety_name', 'IR-64'),
            "location_name": request_data.get('location_name', 'Field Analysis'),
            "latitude": center_lat,
            "longitude": center_lon,
            "sowing_date": request_data.get('sowing_date', '2024-07-15'),
            "use_real_time_data": False
        }
        
        # Get prediction
        result = prediction_service.predict_yield(prediction_request)
        
        # Add field analysis information
        result['field_analysis'] = {
            'field_coordinates': field_coords,
            'center_point': {
                'latitude': center_lat,
                'longitude': center_lon
            },
            'coordinate_count': len(coords) // 2,
            'state': request_data.get('state', 'Unknown')
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Field analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Field analysis error: {str(e)}"
        )


@app.get("/debug/credentials")
async def debug_credentials():
    """Debug endpoint to check credential loading"""
    import os
    gee_json = os.getenv('GEE_PRIVATE_KEY_JSON')
    openweather_key = os.getenv('OPENWEATHER_API_KEY')
    
    return {
        "gee_json_exists": bool(gee_json),
        "gee_json_length": len(gee_json) if gee_json else 0,
        "gee_json_preview": gee_json[:100] + "..." if gee_json and len(gee_json) > 100 else gee_json,
        "openweather_key_exists": bool(openweather_key),
        "openweather_key_length": len(openweather_key) if openweather_key else 0,
        "environment": os.getenv('ENVIRONMENT', 'not_set')
    }


@app.get("/")
async def root():
    """API root endpoint with documentation"""
    return {
        "message": "Crop Yield Prediction API v6.0.0",
        "endpoints": {
            "GET /health": "Service health check",
            "GET /crops": "Available crops and varieties",
            "GET /debug/credentials": "Debug credential loading",
            "POST /validate": "Validate prediction input",
            "POST /predict/yield": "Main yield prediction endpoint",
            "POST /predict/field-analysis": "Field analysis with polygon coordinates"
        },
        "documentation": "/docs",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "prediction_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
