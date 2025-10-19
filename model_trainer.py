#!/usr/bin/env python3
"""
Phase 4: Model Training for North India Crop Prediction

Trains ML models using processed datasets from Phase 3:
- State-wise models for regional accuracy
- Crop-specific models for different crops
- Regional model for North India as a whole
- Performance evaluation and validation
- Model persistence for production use

Target States: Punjab, Haryana, Uttar Pradesh, Bihar, Madhya Pradesh
Major Crops: Rice, Wheat, Maize
"""

import pandas as pd
import numpy as np
import json
import os
import pickle
import sys
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.feature_selection import SelectKBest, f_regression
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class NorthIndiaModelTrainer:
    def __init__(self):
        self.processed_data_dir = 'data/processed'
        self.models_dir = 'models'
        self.results_dir = 'model_results'

        # Create directories
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Log environment information at initialization
        self._log_environment_info()

        # Model configurations
        self.models_config = {
            'ridge': {
                'model': Ridge(alpha=1.0),
                'name': 'Ridge Regression',
                'params': {'alpha': [0.1, 1.0, 10.0]}
            },
            'random_forest': {
                'model': RandomForestRegressor(n_estimators=100, random_state=42),
                'name': 'Random Forest',
                'params': {'n_estimators': [50, 100, 200]}
            },
            'gradient_boosting': {
                'model': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'name': 'Gradient Boosting',
                'params': {'n_estimators': [50, 100, 200]}
            }
        }

        # Feature sets for different modeling approaches - updated to match processed data
        self.feature_sets = {
            'basic_weather': ['temp_max', 'temp_min', 'temp_mean', 'precipitation', 'humidity', 'solar_radiation'],
            'derived_features': ['temp_range', 'gdd', 'precipitation_7d_sum', 'heat_stress_days', 'water_availability_index'],
            'seasonal_features': ['is_kharif_season', 'is_rabi_season', 'is_zaid_season'],
            'crop_specific': ['rice_kharif_season', 'rice_rabi_season', 'rice_zaid_season',
                             'wheat_kharif_season', 'wheat_rabi_season', 'wheat_zaid_season',
                             'maize_kharif_season', 'maize_rabi_season', 'maize_zaid_season'],
            'vegetation_indices': ['Fpar', 'NDVI', 'Lai'],  # From main crop yield data
            'soil_features': ['soil_ph']  # From main crop yield data
        }

        # Crop seasonality in North India
        self.crop_seasons = {
            'Rice': {'kharif': [6, 7, 8, 9, 10, 11], 'rabi': None, 'zaid': None},
            'Wheat': {'kharif': None, 'rabi': [10, 11, 12, 1, 2, 3], 'zaid': None},
            'Maize': {'kharif': [6, 7, 8, 9], 'rabi': None, 'zaid': None}
        }

    def _log_environment_info(self):
        """Log current environment versions for reproducibility"""
        import sklearn
        print("🔧 Training Environment:")
        print(f"  NumPy: {np.__version__}")
        print(f"  scikit-learn: {sklearn.__version__}")
        print(f"  joblib: {joblib.__version__}")
        print(f"  Python: {sys.version.split()[0]}")
        print()

    def load_training_datasets(self):
        """Load all processed training datasets"""
        print("📊 Loading Training Datasets...")

        datasets = {}
        metadata_file = os.path.join(self.processed_data_dir, 'training_datasets_metadata.json')

        if not os.path.exists(metadata_file):
            print("❌ Training metadata not found!")
            return datasets

        # Load metadata to understand available datasets
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Load each training dataset
        for dataset_name in metadata['datasets'].keys():
            file_path = os.path.join(self.processed_data_dir, f'training_{dataset_name}.csv')

            if os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path, parse_dates=['date'])
                    datasets[dataset_name] = df
                    print(f"  ✅ Loaded {dataset_name}: {len(df)} records")
                except Exception as e:
                    print(f"  ⚠️  Failed to load {dataset_name}: {e}")

        return datasets

    def prepare_features_and_target(self, df, target_column='yield_proxy'):
        """Prepare features and target for training"""
        if df.empty:
            return None, None, None

        # Check if yield_proxy already exists in the data
        if target_column in df.columns:
            print(f"  📊 Using existing {target_column} from data")
        else:
            print(f"  📊 Creating {target_column} from weather features")
            # Create yield proxy (since we don't have actual yield data)
            df = self._create_yield_proxy(df)

        # Select features based on available columns
        available_features = []

        for feature_set, features in self.feature_sets.items():
            available_features.extend([f for f in features if f in df.columns])

        # Remove duplicates
        available_features = list(set(available_features))

        if not available_features:
            print("  ⚠️  No features available for training")
            return None, None, None

        # Prepare feature matrix
        X = df[available_features].fillna(0)  # Fill missing values with 0

        # Create target variable
        y = df[target_column]

        # Remove rows with missing target
        valid_rows = ~y.isnull()
        X = X[valid_rows]
        y = y[valid_rows]

        if len(X) < 50:  # Reduced minimum data requirement for training
            print(f"  ⚠️  Insufficient data: {len(X)} samples")
            return None, None, None

        return X, y, available_features

    def _create_yield_proxy(self, df):
        """Create a yield proxy based on weather conditions"""
        # This is a simplified proxy - in reality, would use historical yield data
        df = df.copy()

        # Base yield proxy on temperature and precipitation
        df['yield_proxy'] = (
            df.get('gdd', 0) * 0.1 +  # Growing degree days
            df.get('precipitation_7d_sum', 0) * 0.05 +  # Recent precipitation
            df.get('water_availability_index', 0) * 0.3 +  # Water availability
            (35 - df.get('temp_max', 25)) * 0.02 +  # Optimal temperature (35°C max)
            df.get('humidity', 50) * 0.001  # Humidity factor
        )

        # Adjust for crop seasons (simplified)
        if 'is_kharif_season' in df.columns:
            df['yield_proxy'] *= (1 + df['is_kharif_season'] * 0.2)  # Kharif bonus
        if 'is_rabi_season' in df.columns:
            df['yield_proxy'] *= (1 + df['is_rabi_season'] * 0.1)   # Rabi bonus

        # Add some noise to simulate real variability
        np.random.seed(42)
        df['yield_proxy'] += np.random.normal(0, 0.1, len(df))

        # Ensure positive values
        df['yield_proxy'] = np.maximum(0, df['yield_proxy'])

        return df

    def train_models_for_dataset(self, dataset_name, df):
        """Train multiple models for a specific dataset"""
        print(f"\n🤖 Training Models for {dataset_name}...")

        # Prepare features and target
        X, y, features = self.prepare_features_and_target(df)

        if X is None or y is None:
            return None

        print(f"  📊 Training with {len(features)} features and {len(X)} samples")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Apply polynomial features for linear models
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_train_poly = poly.fit_transform(X_train_scaled)
        X_test_poly = poly.transform(X_test_scaled)

        trained_models = {}
        model_results = {}

        for model_key, config in self.models_config.items():
            try:
                print(f"    🏋️  Training {config['name']}...")

                # Use polynomial features for linear models
                if model_key in ['ridge']:
                    X_train_model = X_train_poly
                    X_test_model = X_test_poly
                else:
                    X_train_model = X_train_scaled
                    X_test_model = X_test_scaled

                # Train model
                model = config['model']
                model.fit(X_train_model, y_train)

                # Evaluate model
                y_pred_train = model.predict(X_train_model)
                y_pred_test = model.predict(X_test_model)

                # Calculate metrics
                train_r2 = r2_score(y_train, y_pred_train)
                test_r2 = r2_score(y_test, y_pred_test)
                train_mae = mean_absolute_error(y_train, y_pred_train)
                test_mae = mean_absolute_error(y_test, y_pred_test)
                train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
                test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

                model_results[model_key] = {
                    'model': model,
                    'scaler': scaler,
                    'poly': poly,
                    'features': features,
                    'metrics': {
                        'train_r2': train_r2,
                        'test_r2': test_r2,
                        'train_mae': train_mae,
                        'test_mae': test_mae,
                        'train_rmse': train_rmse,
                        'test_rmse': test_rmse
                    },
                    'dataset': dataset_name,
                    'samples': len(X),
                    'feature_count': len(features)
                }

                print(f"      ✅ {config['name']}: R² = {test_r2:.3f}, MAE = {test_mae:.3f}")

                # Save model
                self._save_model(model_results[model_key], dataset_name, model_key)

            except Exception as e:
                print(f"      ⚠️  Failed to train {config['name']}: {e}")

        return model_results

    def _save_model(self, model_info, dataset_name, model_key):
        """Save trained model and metadata with environment information"""
        import sklearn
        
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
                'numpy_version': np.__version__,
                'sklearn_version': sklearn.__version__,
                'joblib_version': joblib.__version__,
                'python_version': sys.version
            }
        }

        filename = f"{self.models_dir}/{dataset_name}_{model_key}_{timestamp}.pkl"

        # Use joblib with protocol 5 for better NumPy 2.x compatibility
        joblib.dump(model_data, filename, protocol=5)

        print(f"      💾 Saved model to {filename}")

    def train_all_datasets(self, datasets):
        """Train models for all available datasets"""
        print("🚀 PHASE 4: MODEL TRAINING FOR NORTH INDIA")
        print("="*60)

        all_results = {}

        for dataset_name, df in datasets.items():
            print(f"\n{'='*50}")
            print(f"DATASET: {dataset_name.upper()}")
            print('='*50)

            # Train models for this dataset
            results = self.train_models_for_dataset(dataset_name, df)

            if results:
                all_results[dataset_name] = results

                # Generate evaluation plots
                self._generate_model_evaluation_plots(results, dataset_name)

        # Create comprehensive results summary
        self._create_training_summary(all_results)

        return all_results

    def _generate_model_evaluation_plots(self, model_results, dataset_name):
        """Generate evaluation plots for trained models"""
        try:
            # Create plots directory if it doesn't exist
            plots_dir = os.path.join(self.results_dir, 'model_evaluation')
            os.makedirs(plots_dir, exist_ok=True)

            # Model comparison plot
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))

            model_names = list(model_results.keys())
            test_r2_scores = [results['metrics']['test_r2'] for results in model_results.values()]
            test_mae_scores = [results['metrics']['test_mae'] for results in model_results.values()]

            # R² comparison
            axes[0, 0].bar(model_names, test_r2_scores, color='skyblue')
            axes[0, 0].set_title('Model R² Scores')
            axes[0, 0].set_ylabel('R² Score')
            axes[0, 0].tick_params(axis='x', rotation=45)

            # MAE comparison
            axes[0, 1].bar(model_names, test_mae_scores, color='lightcoral')
            axes[0, 1].set_title('Model MAE Scores')
            axes[0, 1].set_ylabel('Mean Absolute Error')
            axes[0, 1].tick_params(axis='x', rotation=45)

            # Feature importance (for tree-based models)
            if 'random_forest' in model_results:
                rf_model = model_results['random_forest']['model']
                features = model_results['random_forest']['features']

                if hasattr(rf_model, 'feature_importances_'):
                    importance = rf_model.feature_importances_
                    axes[1, 0].barh(features[:10], importance[:10])  # Top 10 features
                    axes[1, 0].set_title('Top 10 Feature Importances (Random Forest)')
                    axes[1, 0].set_xlabel('Importance')

            # Model performance summary
            axes[1, 1].axis('off')
            summary_text = f"Dataset: {dataset_name}\n\n"
            for model_key, results in model_results.items():
                metrics = results['metrics']
                summary_text += f"{model_key.upper()}:\n"
                summary_text += f"  R²: {metrics['test_r2']:.3f}\n"
                summary_text += f"  MAE: {metrics['test_mae']:.3f}\n"
                summary_text += f"  Samples: {results['samples']}\n\n"

            axes[1, 1].text(0.1, 0.5, summary_text, fontsize=10, verticalalignment='center',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))

            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, f'{dataset_name}_model_evaluation.png'),
                       dpi=300, bbox_inches='tight')
            plt.close()

            print(f"    📊 Saved evaluation plots for {dataset_name}")

        except Exception as e:
            print(f"    ⚠️  Failed to generate plots: {e}")

    def _create_training_summary(self, all_results):
        """Create comprehensive training summary"""
        summary = {
            'training_completed': datetime.now().isoformat(),
            'total_datasets': len(all_results),
            'total_models': sum(len(models) for models in all_results.values()),
            'datasets': {}
        }

        for dataset_name, model_results in all_results.items():
            summary['datasets'][dataset_name] = {
                'models_trained': len(model_results),
                'best_model': None,
                'best_r2': 0,
                'models': {}
            }

            for model_key, results in model_results.items():
                metrics = results['metrics']
                summary['datasets'][dataset_name]['models'][model_key] = {
                    'r2_score': metrics['test_r2'],
                    'mae': metrics['test_mae'],
                    'rmse': metrics['test_rmse'],
                    'samples': results['samples'],
                    'features': len(results['features'])
                }

                # Track best model
                if metrics['test_r2'] > summary['datasets'][dataset_name]['best_r2']:
                    summary['datasets'][dataset_name]['best_r2'] = metrics['test_r2']
                    summary['datasets'][dataset_name]['best_model'] = model_key

        # Save summary
        summary_file = os.path.join(self.results_dir, 'training_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Print summary
        print("\n📊 TRAINING SUMMARY:")
        print(f"  📁 Datasets trained: {summary['total_datasets']}")
        print(f"  🤖 Models trained: {summary['total_models']}")

        for dataset_name, dataset_info in summary['datasets'].items():
            best_model = dataset_info['best_model']
            best_r2 = dataset_info['best_r2']
            print(f"  ✅ {dataset_name}: Best model = {best_model} (R² = {best_r2:.3f})")

        print(f"\n💾 Detailed results saved to: {summary_file}")

    def generate_predictions(self, datasets, all_results):
        """Generate predictions for 2024 using trained models"""
        print("\n🔮 Generating 2024 Predictions...")

        # Load 2024 parameters (if available)
        params_2024_file = '2024_params.csv'

        if not os.path.exists(params_2024_file):
            print("❌ 2024 parameters file not found!")
            return None

        try:
            params_2024 = pd.read_csv(params_2024_file)

            # Process 2024 data similar to training data
            params_2024_processed = self._process_2024_data(params_2024)

            predictions = {}

            for dataset_name, model_results in all_results.items():
                dataset_predictions = {}

                for model_key, results in model_results.items():
                    try:
                        # Get the best model for this dataset
                        model = results['model']
                        scaler = results['scaler']
                        poly = results['poly']
                        features = results['features']

                        # Prepare 2024 features
                        X_2024 = params_2024_processed[features].fillna(0)

                        # Apply same preprocessing
                        X_2024_scaled = scaler.transform(X_2024)
                        X_2024_poly = poly.transform(X_2024_scaled)

                        # Generate predictions
                        if model_key in ['ridge']:
                            X_pred = X_2024_poly
                        else:
                            X_pred = X_2024_scaled

                        y_pred_2024 = model.predict(X_pred)

                        dataset_predictions[model_key] = {
                            'predictions': y_pred_2024,
                            'features_used': features,
                            'model_metrics': results['metrics']
                        }

                        print(f"    ✅ Generated {model_key} predictions for {dataset_name}")

                    except Exception as e:
                        print(f"    ⚠️  Failed to generate {model_key} predictions: {e}")

                if dataset_predictions:
                    predictions[dataset_name] = dataset_predictions

            # Save predictions
            self._save_predictions(predictions, params_2024)

            return predictions

        except Exception as e:
            print(f"⚠️  Failed to generate predictions: {e}")
            return None

    def _process_2024_data(self, df):
        """Process 2024 parameters data for prediction"""
        df = df.copy()

        # Map 2024 data columns to match processed data naming
        column_mapping_2024 = {
            'Temperature': 'temp_mean',
            'Rainfall': 'precipitation',
            'Sunlight': 'solar_radiation',
            'Soil_PH': 'soil_ph'
        }

        for old_col, new_col in column_mapping_2024.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]

        # Add month information if available
        if 'month' in df.columns:
            df['year'] = 2024
            df['date'] = pd.to_datetime(df['year'].astype(int).astype(str) + '-' +
                                       df['month'].astype(int).astype(str) + '-01')

        # Calculate derived features (this will create temp_max, temp_min if missing)
        df = self._calculate_derived_weather_features_2024(df)

        # Add crop season indicators
        for crop in ['Rice', 'Wheat', 'Maize']:
            for season_type, months in self.crop_seasons[crop].items():
                if months:
                    season_col = f'{crop.lower()}_{season_type}_season'
                    df[season_col] = df.get('month', 1).isin(months)

        return df

    def _calculate_derived_weather_features(self, df):
        """Calculate additional weather features for crop modeling"""
        if df.empty:
            return df

        # Temperature range (diurnal variation)
        if 'temp_max' in df.columns and 'temp_min' in df.columns:
            df['temp_range'] = df['temp_max'] - df['temp_min']

        # Growing degree days (base temperature 10°C for cereals)
        base_temp = 10.0
        if 'temp_mean' in df.columns:
            df['gdd'] = np.maximum(0, df['temp_mean'] - base_temp)

        # Cumulative precipitation (7-day running sum)
        if 'precipitation' in df.columns:
            df['precipitation_7d_sum'] = df['precipitation'].fillna(0).rolling(window=7, min_periods=0).sum()

        # Heat stress indicators (days > 35°C)
        if 'temp_max' in df.columns:
            df['heat_stress_days'] = (df['temp_max'] > 35).astype(int)

        # Water availability index (precipitation / evapotranspiration proxy)
        if 'solar_radiation' in df.columns and 'precipitation' in df.columns:
            # Simplified evapotranspiration using solar radiation
            df['et_proxy'] = df['solar_radiation'] * 0.01  # Simplified coefficient
            df['water_availability_index'] = df['precipitation'] / (df['et_proxy'] + 1)  # +1 to avoid division by zero

        return df

    def _calculate_derived_weather_features_2024(self, df):
        """Calculate additional weather features for 2024 prediction data"""
        if df.empty:
            return df

        # Map basic weather columns
        df['temp_mean'] = df.get('Temperature', 25)
        df['precipitation'] = df.get('Rainfall', 0)
        df['solar_radiation'] = df.get('Sunlight', 200)
        df['soil_ph'] = df.get('Soil_PH', 6.5)

        # Since 2024 data may not have detailed temp data, estimate from temp_mean
        # Estimate temp_max as temp_mean + 5°C (typical diurnal range)
        df['temp_max'] = df['temp_mean'] + 5
        # Estimate temp_min as temp_mean - 5°C
        df['temp_min'] = df['temp_mean'] - 5

        # Temperature range (diurnal variation)
        df['temp_range'] = df['temp_max'] - df['temp_min']

        # Growing degree days (base temperature 10°C for cereals)
        base_temp = 10.0
        df['gdd'] = np.maximum(0, df['temp_mean'] - base_temp)

        # Cumulative precipitation (7-day running sum)
        df['precipitation_7d_sum'] = df['precipitation'].fillna(0).rolling(window=7, min_periods=0).sum()

        # Heat stress indicators (days > 35°C) - assume low heat stress for limited data
        df['heat_stress_days'] = 0  # Default for 2024 predictions

        # Assume average humidity for North India
        df['humidity'] = 50.0

        # Water availability index (precipitation / evapotranspiration proxy)
        # Simplified evapotranspiration using solar radiation
        df['et_proxy'] = df['solar_radiation'] * 0.01  # Simplified coefficient
        df['water_availability_index'] = df['precipitation'] / (df['et_proxy'] + 1)  # +1 to avoid division by zero

        return df

    def _save_predictions(self, predictions, params_2024):
        """Save predictions to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create predictions summary
        predictions_summary = {
            'generated_at': timestamp,
            'datasets': list(predictions.keys()),
            'predictions': {}
        }

        for dataset_name, model_predictions in predictions.items():
            dataset_summary = {}

            for model_key, pred_data in model_predictions.items():
                # Create prediction dataframe
                pred_df = pd.DataFrame({
                    'month': params_2024.get('month', range(1, 13)),
                    'predicted_yield': pred_data['predictions'],
                    'model': model_key,
                    'dataset': dataset_name
                })

                # Save individual predictions
                pred_file = os.path.join(self.results_dir, f'predictions_{dataset_name}_{model_key}_{timestamp}.csv')
                pred_df.to_csv(pred_file, index=False)

                dataset_summary[model_key] = {
                    'file': pred_file,
                    'mean_prediction': float(np.mean(pred_data['predictions'])),
                    'std_prediction': float(np.std(pred_data['predictions'])),
                    'metrics': pred_data['model_metrics']
                }

            predictions_summary['predictions'][dataset_name] = dataset_summary

        # Save summary
        summary_file = os.path.join(self.results_dir, f'predictions_summary_{timestamp}.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(predictions_summary, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved predictions to {self.results_dir}/")

    def run_full_model_training_pipeline(self):
        """Execute complete model training pipeline"""
        print("🔄 PHASE 4: NORTH INDIA MODEL TRAINING PIPELINE")
        print("="*60)

        # Load training datasets
        datasets = self.load_training_datasets()

        if not datasets:
            print("❌ No training datasets available!")
            return None

        # Train models for all datasets
        all_results = self.train_all_datasets(datasets)

        if not all_results:
            print("❌ No models were successfully trained!")
            return None

        # Generate 2024 predictions
        predictions = self.generate_predictions(datasets, all_results)

        # Create final summary
        self._create_final_training_report(all_results, predictions)

        print("\n🎉 PHASE 4 Complete: Model Training Pipeline")
        print("🤖 Trained models available in 'models/' directory")
        print("📊 Results and predictions in 'model_results/' directory")
        print("🔄 Ready for Phase 5: Production Deployment!")

        return all_results

    def _create_final_training_report(self, all_results, predictions):
        """Create comprehensive final training report"""
        report = {
            'phase': '4_model_training',
            'completed_at': datetime.now().isoformat(),
            'summary': {
                'datasets_trained': len(all_results),
                'models_trained': sum(len(models) for models in all_results.values()),
                'predictions_generated': predictions is not None,
                'model_files': len([f for f in os.listdir(self.models_dir) if f.endswith('.pkl')]),
                'result_files': len([f for f in os.listdir(self.results_dir) if f.endswith('.json')])
            },
            'model_performance': {}
        }

        # Best model for each dataset
        for dataset_name, model_results in all_results.items():
            best_model = None
            best_r2 = -999

            for model_key, results in model_results.items():
                if results['metrics']['test_r2'] > best_r2:
                    best_r2 = results['metrics']['test_r2']
                    best_model = model_key

            report['model_performance'][dataset_name] = {
                'best_model': best_model,
                'best_r2': best_r2,
                'models_trained': len(model_results)
            }

        # Save report
        report_file = os.path.join(self.results_dir, 'final_training_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print("📋 Final training report saved")

def run_phase4_training():
    """Main function to run Phase 4 model training"""
    print("🌾 NORTH INDIA CROP PREDICTION")
    print("Phase 4: Model Training Pipeline")
    print("="*50)

    trainer = NorthIndiaModelTrainer()
    results = trainer.run_full_model_training_pipeline()

    return results

if __name__ == "__main__":
    run_phase4_training()
