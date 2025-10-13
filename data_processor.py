#!/usr/bin/env python3
"""
Phase 3: Data Processing Pipeline for North India Crop Prediction

Processes and integrates raw data from Phase 2:
- Cleans weather data (24k+ records across 4 states)
- Integrates geospatial boundaries
- Creates training-ready datasets
- Handles missing data and quality checks

Target States: Punjab, Haryana, Uttar Pradesh, Bihar, Madhya Pradesh
Major Crops: Rice, Wheat, Maize
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class NorthIndiaDataProcessor:
    def __init__(self):
        self.raw_data_dir = 'data/raw'
        self.processed_data_dir = 'data/processed'

        # Create processed data directory
        os.makedirs(self.processed_data_dir, exist_ok=True)

        # Target states and mapping
        self.target_states = ['Punjab', 'Haryana', 'UP', 'Bihar', 'MP']
        self.state_capital_mapping = {
            'Chandigarh': ['Punjab', 'Haryana'],
            'Lucknow': 'UP',
            'Patna': 'Bihar',
            'Bhopal': 'MP'
        }

        # Crop seasonality in North India
        self.crop_seasons = {
            'Rice': {'kharif': [6, 7, 8, 9, 10, 11], 'rabi': None, 'zaid': None},
            'Wheat': {'kharif': None, 'rabi': [10, 11, 12, 1, 2, 3], 'zaid': None},
            'Maize': {'kharif': [6, 7, 8, 9], 'rabi': None, 'zaid': None}
        }

    def process_weather_data(self):
        """Clean and process weather data from all states"""
        print("🌤️ Processing Weather Data...")

        weather_files = [f for f in os.listdir(self.raw_data_dir)
                        if f.startswith('weather_') and f.endswith('.csv')]

        if not weather_files:
            print("❌ No weather files found!")
            return pd.DataFrame()

        all_weather_data = []
        processed_states = 0

        for weather_file in weather_files:
            state_name = weather_file.replace('weather_', '').replace('.csv', '').replace('_', ' ').title()
            file_path = os.path.join(self.raw_data_dir, weather_file)

            try:
                print(f"  📊 Processing {state_name} weather data...")

                # Load weather data
                df = pd.read_csv(file_path)

                # Clean and standardize columns
                df_cleaned = self._clean_weather_dataframe(df, state_name)

                if df_cleaned is not None and not df_cleaned.empty:
                    all_weather_data.append(df_cleaned)
                    processed_states += 1
                    print(f"    ✅ Processed {len(df_cleaned)} records for {state_name}")

                # Quality check summary
                self._generate_weather_quality_report(df_cleaned, state_name)

            except Exception as e:
                print(f"    ⚠️  Failed to process {state_name}: {e}")

        if all_weather_data:
            combined_weather = pd.concat(all_weather_data, ignore_index=True)

            # Final quality checks
            combined_weather = self._apply_global_weather_cleaning(combined_weather)

            # Save processed weather data
            output_file = os.path.join(self.processed_data_dir, 'north_india_weather_processed.csv')
            combined_weather.to_csv(output_file, index=False)

            print(f"🗂️  Saved combined weather data: {len(combined_weather)} records across {processed_states} states")

            return combined_weather

        return pd.DataFrame()

    def _clean_weather_dataframe(self, df, state_name):
        """Clean individual state weather dataframe"""
        if df.empty:
            return None

        # Rename columns for consistency - mapping to match main crop yield data
        column_mapping = {
            'date_formatted': 'date',
            'PRECTOT': 'precipitation_mm',
            'ALLSKY_SFC_SW_DWN': 'solar_radiation_w_per_m2',
            'T2M_MAX': 'temp_max_celsius',
            'T2M_MIN': 'temp_min_celsius',
            'RH2M': 'humidity_percent',
            # Map to match main crop yield data column names
            'temp_max': 'temp_max',
            'temp_min': 'temp_min',
            'temp_mean': 'temp_mean',
            'precipitation': 'precipitation',
            'humidity': 'humidity',
            'solar_radiation': 'solar_radiation'
        }

        df = df.rename(columns=column_mapping)

        # Ensure date column exists and is parsed
        if 'date' not in df.columns:
            # Try to find date column
            date_cols = [col for col in df.columns if 'date' in col.lower()]
            if date_cols:
                df['date'] = pd.to_datetime(df[date_cols[0]], errors='coerce')
            else:
                # Create date from index if no date column
                df['date'] = pd.date_range(start='2015-01-01', periods=len(df), freq='D')
        else:
            # Handle different date formats
            try:
                # Try parsing as integer date first (YYYYMMDD format)
                if df['date'].dtype == 'int64':
                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce')
                else:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
            except:
                # If parsing fails, try to extract from the date values
                try:
                    # Handle cases where date might be in different format
                    df['date'] = pd.to_datetime(df['date'].astype(str), errors='coerce')
                except:
                    # Last resort: create sequential dates
                    df['date'] = pd.date_range(start='2015-01-01', periods=len(df), freq='D')

        # Clean numeric columns
        numeric_cols = ['temp_max', 'temp_min', 'temp_mean', 'precipitation', 'humidity', 'solar_radiation']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Add state information
        df['state'] = state_name
        df['data_source'] = 'nasa_power'  # Default to NASA as primary

        # Remove invalid/null dates
        df = df.dropna(subset=['date'])

        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)

        # Calculate derived features
        df = self._calculate_derived_weather_features(df)

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

    def _apply_global_weather_cleaning(self, df):
        """Apply global cleaning rules across all states"""
        if df.empty:
            return df

        # Remove extreme outliers (physical impossibilities)
        df = df[df['temp_max'] <= 50]  # Max temperature realistic upper bound
        df = df[df['temp_min'] >= -10]  # Min temperature realistic lower bound

        # Handle precipitation - allow NaN values but remove negative values
        if 'precipitation' in df.columns:
            df = df[(df['precipitation'].isna()) | (df['precipitation'] >= 0)]

        # Fill missing values with rolling averages where appropriate
        for col in ['temp_mean', 'humidity']:
            if col in df.columns:
                df[col] = df.groupby('state')[col].transform(
                    lambda x: x.fillna(x.rolling(window=7, min_periods=1).mean())
                )

        # Ensure date uniqueness per state
        df = df.drop_duplicates(subset=['date', 'state'], keep='first')

        # Add month and year columns for analysis
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month

        return df

    def integrate_with_crop_yield_data(self, weather_df):
        """Integrate processed weather data with main crop yield data"""
        print("🌾 Integrating with Main Crop Yield Data...")

        # Load main crop yield data
        main_data_file = 'crop_yield_climate_soil_data_2019_2023.csv'
        if not os.path.exists(main_data_file):
            print("❌ Main crop yield data file not found!")
            return weather_df

        try:
            main_df = pd.read_csv(main_data_file)

            # Use Combined_Crop_Yield as the target variable
            if 'Combined_Crop_Yield' not in main_df.columns:
                print("❌ Combined_Crop_Yield column not found in main data!")
                return weather_df

            # Map main data columns to match weather data naming
            main_df_mapped = main_df.copy()

            # Rename columns to match weather data structure
            column_mapping_main = {
                'Temperature': 'temp_mean',
                'Rainfall': 'precipitation',
                'Sunlight': 'solar_radiation',
                'Soil_PH': 'soil_ph',
                'Combined_Crop_Yield': 'yield_proxy'  # Use as proxy for training
            }

            for old_col, new_col in column_mapping_main.items():
                if old_col in main_df_mapped.columns:
                    main_df_mapped[new_col] = main_df_mapped[old_col]

            # Ensure month and year columns exist
            if 'month' not in main_df_mapped.columns and 'year' in main_df_mapped.columns:
                main_df_mapped['month'] = 1  # Default to January for aggregation
                main_df_mapped['date'] = pd.to_datetime(main_df_mapped['year'].astype(str) + '-01-01')

            # Aggregate main data by month/year to match weather data structure
            if 'month' in main_df_mapped.columns and 'year' in main_df_mapped.columns:
                main_aggregated = main_df_mapped.groupby(['year', 'month']).agg({
                    'yield_proxy': 'mean',
                    'temp_mean': 'mean',
                    'precipitation': 'sum',  # Sum rainfall over the month
                    'solar_radiation': 'mean',
                    'soil_ph': 'mean',
                    'Fpar': 'mean',
                    'NDVI': 'mean',
                    'Lai': 'mean'
                }).reset_index()

                print(f"Main data aggregated: {main_aggregated.shape}")
                print(f"Weather data: {weather_df.shape}")

                # Merge with weather data - use left join to keep all weather data
                integrated_df = weather_df.merge(
                    main_aggregated,
                    on=['year', 'month'],
                    how='left',
                    suffixes=('', '_main')
                )

                print(f"After merge: {integrated_df.shape}")
                print(f"Non-null yield_proxy values: {integrated_df['yield_proxy'].notna().sum()}")

                # Save integrated dataset
                output_file = os.path.join(self.processed_data_dir, 'integrated_crop_weather_data.csv')
                integrated_df.to_csv(output_file, index=False)

                print(f"✅ Integrated {len(integrated_df)} records with crop yield data")
                print(f"💾 Saved integrated data to {output_file}")

                return integrated_df
            else:
                print("❌ Month/Year columns not found in main data!")
                return weather_df

        except Exception as e:
            print(f"❌ Failed to integrate with crop yield data: {e}")
            return weather_df

    def _generate_weather_quality_report(self, df, state_name):
        """Generate quality report for weather data"""
        if df is None or df.empty:
            return

        report_file = os.path.join(self.processed_data_dir, f'weather_quality_{state_name.lower().replace(" ", "_")}.txt')

        with open(report_file, 'w') as f:
            f.write(f"WEATHER DATA QUALITY REPORT - {state_name.upper()}\n")
            f.write("="*50 + "\n\n")
            f.write(f"Records: {len(df)}\n")
            f.write(f"Date Range: {df['date'].min()} to {df['date'].max()}\n\n")

            f.write("COLUMN STATISTICS:\n")
            for col in df.select_dtypes(include=[np.number]).columns:
                if col in df.columns:
                    stats = df[col].describe()
                    f.write(f"\n{col.upper()}:\n")
                    f.write(f"  Count: {stats['count']}\n")
                    f.write(f"  Mean: {stats['mean']:.2f}\n")
                    f.write(".2f")
                    f.write(f"  Missing: {df[col].isnull().sum()}\n")

            f.write("\nQUALITY METRICS:\n")
            date_gaps = df['date'].diff().dt.days.dropna()
            if len(date_gaps) > 0:
                avg_gap = date_gaps.mean()
                max_gap = date_gaps.max()
                f.write(f"  Average Date Gap: {avg_gap:.1f} days\n")
                f.write(f"  Maximum Date Gap: {max_gap:.0f} days\n")

    def process_geospatial_data(self):
        """Process state boundaries and calculate spatial features"""
        print("🗺️ Processing Geospatial Data...")

        boundaries_file = os.path.join(self.raw_data_dir, 'state_boundaries.geojson')

        if not os.path.exists(boundaries_file):
            print("❌ Boundaries file not found!")
            return pd.DataFrame()

        try:
            with open(boundaries_file, 'r', encoding='utf-8') as f:
                boundaries_data = json.load(f)

            processed_boundaries = []
            valid_states = 0

            for feature in boundaries_data.get('features', []):
                props = feature['properties']
                geom = feature['geometry']

                # Extract state information
                boundary_record = {
                    'state_code': props.get('state'),
                    'state_name': props.get('name'),
                    'area_km2': None,  # Will calculate if coordinates available
                    'center_lat': None,
                    'center_lon': None,
                    'geometry_type': geom.get('type'),
                    'coordinates_count': None
                }

                # Calculate area and center from coordinates
                if geom['type'] == 'Polygon' and geom.get('coordinates'):
                    coords = geom['coordinates'][0]  # Use outer ring

                    if coords and len(coords) > 0:
                        # Calculate approximate center
                        boundary_record['center_lat'] = sum(c[1] for c in coords) / len(coords)
                        boundary_record['center_lon'] = sum(c[0] for c in coords) / len(coords)

                        # Approximate area calculation (simplified)
                        area_km2 = self._calculate_polygon_area_km2(coords)
                        boundary_record['area_km2'] = area_km2
                        boundary_record['coordinates_count'] = len(coords)

                        valid_states += 1

                processed_boundaries.append(boundary_record)

            if processed_boundaries:
                boundaries_df = pd.DataFrame(processed_boundaries)

                # Save processed boundaries
                output_file = os.path.join(self.processed_data_dir, 'north_india_state_boundaries.csv')
                boundaries_df.to_csv(output_file, index=False)

                print(f"🗂️  Saved processed boundaries: {len(boundaries_df)} states")

                return boundaries_df

        except Exception as e:
            print(f"⚠️  Failed to process boundaries: {e}")

        return pd.DataFrame()

    def _calculate_polygon_area_km2(self, coordinates):
        """Calculate approximate area of polygon in square kilometers"""
        if not coordinates or len(coordinates) < 3:
            return 0

        # Simplified area calculation using shoelace formula
        # This is approximate and assumes planar geometry
        # For accurate calculations, would need proper geodesic area

        try:
            coords = [[c[1], c[0]] for c in coordinates]  # Convert to [lat, lon]

            # Use first coordinate as origin for simplification
            lat0, lon0 = coords[0]

            # Convert to approximate cartesian coordinates
            x_coords = [(lon - lon0) * 111320 * np.cos(np.radians(lat0)) for lat, lon in coords]
            y_coords = [(lat - lat0) * 111320 for lat, lon in coords]

            # Shoelace formula
            area = 0.5 * abs(sum(x_coords[i] * y_coords[(i+1) % len(coords)] -
                                x_coords[(i+1) % len(coords)] * y_coords[i]
                                for i in range(len(coords))))

            # Convert square meters to square kilometers
            return area / 1_000_000

        except:
            return 0

    def integrate_weather_and_geospatial(self, weather_df, boundaries_df):
        """Integrate weather and geospatial data for comprehensive analysis"""
        print("🔗 Integrating Weather and Geospatial Data...")

        if weather_df.empty or boundaries_df.empty:
            print("⚠️  Missing data for integration")
            return pd.DataFrame()

        # Ensure state name consistency
        weather_df['state_normalized'] = weather_df['state'].str.title()

        # Match weather data to state boundaries
        integrated_data = weather_df.merge(
            boundaries_df,
            left_on='state_normalized',
            right_on='state_name',
            how='left',
            suffixes=('', '_boundary')
        )

        # Calculate distance-based weights (in a real scenario)
        # For now, just mark which states have boundary data
        integrated_data['has_boundary_data'] = ~integrated_data['area_km2'].isnull()

        # Save integrated dataset
        output_file = os.path.join(self.processed_data_dir, 'north_india_integrated_weather_boundaries.csv')
        integrated_data.to_csv(output_file, index=False)

        print(f"🗂️  Saved integrated data: {len(integrated_data)} records")

        return integrated_data

    def create_crop_seasonal_indicators(self, weather_df):
        """Create crop-specific seasonal indicators"""
        print("🌾 Creating Crop Seasonal Indicators...")

        if weather_df.empty:
            return weather_df

        # Add crop season indicators for each major crop
        weather_copy = weather_df.copy()

        for crop in ['Rice', 'Wheat', 'Maize']:
            for season_type, months in self.crop_seasons[crop].items():
                if months:
                    season_col = f'{crop.lower()}_{season_type}_season'
                    weather_copy[season_col] = weather_copy['month'].isin(months)

        # Add North Indian agricultural cycle indicators
        weather_copy['is_kharif_season'] = weather_copy['month'].isin([6, 7, 8, 9, 10])
        weather_copy['is_rabi_season'] = weather_copy['month'].isin([10, 11, 12, 1, 2, 3])
        weather_copy['is_zaid_season'] = weather_copy['month'].isin([3, 4, 5, 6])

        # Save enhanced dataset
        output_file = os.path.join(self.processed_data_dir, 'north_india_weather_with_crop_seasons.csv')
        weather_copy.to_csv(output_file, index=False)

        print(f"🗂️  Saved crop seasonal indicators: {len(weather_copy)} records")

        return weather_copy

    def generate_training_datasets(self):
        """Generate training-ready datasets for ML models"""
        print("🤖 Generating Training Datasets...")

        # Load integrated crop weather data instead of just weather data
        integrated_file = os.path.join(self.processed_data_dir, 'integrated_crop_weather_data.csv')

        if not os.path.exists(integrated_file):
            print("❌ Integrated crop weather data not found!")
            # Fallback to weather data only
            weather_file = os.path.join(self.processed_data_dir, 'north_india_weather_with_crop_seasons.csv')
            if not os.path.exists(weather_file):
                print("❌ Processed weather data not found!")
                return {}
            integrated_df = pd.read_csv(weather_file, parse_dates=['date'])
        else:
            integrated_df = pd.read_csv(integrated_file, parse_dates=['date'])
            print(f"✅ Using integrated crop weather data: {integrated_df.shape}")

        training_datasets = {}

        # 1. State-wise training datasets
        for state in integrated_df['state'].unique():
            state_data = integrated_df[integrated_df['state'] == state].copy()

            # Ensure data quality thresholds (at least 2 years of data)
            if len(state_data) > 700:  # ~2 years of daily data
                training_datasets[f'{state.lower().replace(" ", "_")}_training'] = state_data
                print(f"  ✅ Created training set for {state} ({len(state_data)} records)")

        # 2. Regional aggregated dataset (North India as region)
        regional_data = integrated_df.copy()
        regional_data['region'] = 'North_India'

        # Add regional aggregations
        regional_features = self._calculate_regional_features(regional_data)
        training_datasets['north_india_regional'] = regional_features

        # 3. Crop-specific datasets
        crop_datasets = self._create_crop_specific_datasets(integrated_df)
        training_datasets.update(crop_datasets)

        # Save training datasets
        for name, dataset in training_datasets.items():
            output_file = os.path.join(self.processed_data_dir, f'training_{name}.csv')
            dataset.to_csv(output_file, index=False)

        print(f"\n📊 Generated {len(training_datasets)} training datasets")
        print("Training datasets:", list(training_datasets.keys()))

        # Create metadata summary
        self._create_training_metadata(training_datasets)

        return training_datasets

    def _calculate_regional_features(self, df):
        """Calculate region-wide features"""
        # Add regional indices
        df['monsoon_intensity'] = df.groupby('year')['precipitation_7d_sum'].transform('max')
        df['heat_wave_frequency'] = df.groupby('year')['heat_stress_days'].transform('sum')

        return df

    def _create_crop_specific_datasets(self, weather_df):
        """Create crop-specific training datasets"""
        crop_datasets = {}

        for crop in ['Rice', 'Wheat', 'Maize']:
            crop_df = weather_df.copy()

            # Filter for crop-specific growing seasons
            season_cols = [col for col in crop_df.columns if col.startswith(f'{crop.lower()}_') and col.endswith('_season')]
            if season_cols:
                # Include records during any season for this crop
                season_filter = crop_df[season_cols[0]].copy()
                for col in season_cols[1:]:
                    season_filter = season_filter | crop_df[col]

                crop_dataset = crop_df[season_filter].copy()
                crop_dataset['target_crop'] = crop

                crop_datasets[f'{crop.lower()}_specific'] = crop_dataset
                print(f"  ✅ Created crop-specific dataset for {crop} ({len(crop_dataset)} records)")

        return crop_datasets

    def _create_training_metadata(self, training_datasets):
        """Create metadata summary for training datasets"""
        metadata_file = os.path.join(self.processed_data_dir, 'training_datasets_metadata.json')

        metadata = {
            'created_at': datetime.now().isoformat(),
            'total_datasets': len(training_datasets),
            'datasets': {}
        }

        for name, dataset in training_datasets.items():
            metadata['datasets'][name] = {
                'record_count': len(dataset),
                'date_range': {
                    'start': dataset['date'].min().isoformat() if 'date' in dataset.columns else None,
                    'end': dataset['date'].max().isoformat() if 'date' in dataset.columns else None
                },
                'features_count': len(dataset.columns),
                'states_covered': dataset['state'].unique().tolist() if 'state' in dataset.columns else [],
                'target_columns': [col for col in dataset.columns if 'season' in col.lower() or 'crop' in col.lower()]
            }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"📋 Saved training metadata to {metadata_file}")

    def run_full_data_processing_pipeline(self):
        """Execute complete data processing pipeline"""
        print("🔄 PHASE 3: NORTH INDIA DATA PROCESSING PIPELINE")
        print("="*60)

        # Step 1: Process weather data
        weather_data = self.process_weather_data()

        # Step 2: Process geospatial data
        boundary_data = self.process_geospatial_data()

        # Step 3: Integrate datasets
        integrated_data = self.integrate_weather_and_geospatial(weather_data, boundary_data)

        # Step 4: Add crop seasonal indicators
        seasonal_data = self.create_crop_seasonal_indicators(weather_data)

        # Step 5: Integrate with main crop yield data
        integrated_crop_data = self.integrate_with_crop_yield_data(weather_data)

        # Step 6: Generate training datasets
        training_datasets = self.generate_training_datasets()

        # Create final summary
        self._create_processing_summary({
            'weather_records': len(weather_data),
            'boundary_states': len(boundary_data),
            'integrated_records': len(integrated_data),
            'seasonal_records': len(seasonal_data),
            'training_datasets': len(training_datasets)
        })

        print("\n🎉 PHASE 3 Complete: Data Processing Pipeline")
        print("📁 Processed data available in 'data/processed/' directory")
        print("🔄 Ready for Phase 4: Model Training!")

        return training_datasets

    def _create_processing_summary(self, metrics):
        """Create comprehensive processing summary"""
        summary = {
            'phase': '3_data_processing',
            'completed_at': datetime.now().isoformat(),
            'metrics': metrics,
            'output_directory': self.processed_data_dir,
            'output_files': [f for f in os.listdir(self.processed_data_dir) if f.endswith('.csv')]
        }

        summary_file = os.path.join(self.processed_data_dir, 'data_processing_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print("📊 Processing Summary:")
        print(f"  🌤️  Weather records: {metrics['weather_records']:,}")
        print(f"  🗺️  Boundary states: {metrics['boundary_states']}")
        print(f"  🔗 Integrated records: {metrics['integrated_records']:,}")
        print(f"  🌾 Seasonal records: {metrics['seasonal_records']:,}")
        print(f"  🤖 Training datasets: {metrics['training_datasets']}")

def run_phase3_pipeline():
    """Main function to run Phase 3 data processing"""
    print("🌾 NORTH INDIA CROP PREDICTION")
    print("Phase 3: Data Processing Pipeline")
    print("="*50)

    processor = NorthIndiaDataProcessor()
    training_datasets = processor.run_full_data_processing_pipeline()

    return training_datasets

if __name__ == "__main__":
    run_phase3_pipeline()
