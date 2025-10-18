#!/usr/bin/env python3
"""
Crop Variety Database for North India Crop Yield Prediction

Manages crop variety data including growth parameters, regional prevalence,
maturity periods, and water/temperature requirements for Rice, Wheat, and Maize.
"""

import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
import sqlite3
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

class CropVarietyDatabase:
    """Database for managing crop variety information"""

    def __init__(self, config_path: str = "config/api_config.json"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._load_config()
        self._setup_database()
        self._initialize_crop_data()

    def _load_config(self):
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            self.db_config = config.get('storage', {})
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.db_config = {}

    def _setup_database(self):
        """Set up SQLite database for crop variety data"""
        db_path = Path(self.db_config.get('database_path', 'data/database/crop_prediction.db'))

        # Ensure database exists and create variety tables
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()

            # Crop variety data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crop_varieties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    crop_type TEXT NOT NULL,
                    variety_name TEXT NOT NULL,
                    maturity_days INTEGER,
                    water_requirement REAL,
                    temperature_optimal REAL,
                    temperature_max REAL,
                    temperature_min REAL,
                    region_prevalence TEXT,
                    season_type TEXT,
                    yield_potential REAL,
                    drought_tolerance TEXT,
                    disease_resistance TEXT,
                    market_value REAL,
                    UNIQUE(crop_type, variety_name)
                )
            ''')

            # Variety performance metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS variety_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    crop_type TEXT,
                    variety_name TEXT,
                    region TEXT,
                    season TEXT,
                    year INTEGER,
                    actual_yield REAL,
                    expected_yield REAL,
                    yield_ratio REAL,
                    weather_stress_impact REAL,
                    disease_impact REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Climate adaptation data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS climate_adaptation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    crop_type TEXT,
                    variety_name TEXT,
                    climate_zone TEXT,
                    adaptation_score REAL,
                    heat_tolerance INTEGER,
                    drought_tolerance INTEGER,
                    flood_tolerance INTEGER,
                    cold_tolerance INTEGER,
                    disease_tolerance TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

        # Ensure path is relative to project root
        if not db_path.is_absolute():
            db_path = Path(os.path.join(os.path.dirname(__file__), "..", str(db_path)))
        self.db_path = db_path
        self.logger.info(f"✅ Crop variety database initialized at {db_path}")
    def _initialize_crop_data(self):
        """Initialize crop variety data for North India"""
        # Check for reset_db flag (production database reset)
        import os
        reset_db = os.getenv('RESET_DB') == 'true'

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                # Handle table reset if needed
                if reset_db:
                    self.logger.info("🔄 RESET_DB flag detected - recreating tables")
                    cursor.execute('DROP TABLE IF EXISTS crop_varieties')

                # Always ensure table exists (creation is atomic)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS crop_varieties (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        crop_type TEXT NOT NULL,
                        variety_name TEXT NOT NULL,
                        maturity_days INTEGER,
                        water_requirement REAL,
                        temperature_optimal REAL,
                        temperature_max REAL,
                        temperature_min REAL,
                        region_prevalence TEXT,
                        season_type TEXT,
                        yield_potential REAL,
                        drought_tolerance TEXT,
                        disease_resistance TEXT,
                        market_value REAL,
                        UNIQUE(crop_type, variety_name)
                    )
                ''')

                # Check existing data count (table must exist now)
                cursor.execute("SELECT COUNT(*) FROM crop_varieties")
                count = cursor.fetchone()[0]

                if count == 0:
                    self.logger.info("🔄 Initializing crop variety data...")
                    # Initialize with base crop variety data
                    crop_data = self._get_north_india_crop_varieties()

                    for variety in crop_data:
                        cursor.execute('''
                            INSERT INTO crop_varieties
                            (crop_type, variety_name, maturity_days, water_requirement,
                             temperature_optimal, temperature_max, temperature_min,
                             region_prevalence, season_type, yield_potential,
                             drought_tolerance, disease_resistance, market_value)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            variety['crop_type'],
                            variety['variety_name'],
                            variety['maturity_days'],
                            variety['water_requirement'],
                            variety['temperature_optimal'],
                            variety['temperature_max'],
                            variety['temperature_min'],
                            variety['region_prevalence'],
                            variety['season_type'],
                            variety['yield_potential'],
                            variety['drought_tolerance'],
                            variety['disease_resistance'],
                            variety['market_value']
                        ))

                    conn.commit()
                    self.logger.info(f"✅ Initialized {len(crop_data)} crop variety records")
                else:
                    self.logger.info(f"✅ Crop variety data already exists ({count} records)")

        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            raise

    def _get_north_india_crop_varieties(self) -> List[Dict]:
        """Get comprehensive crop variety data for North India"""
        varieties = []

        # Rice varieties for North India (primarily kharif)
        rice_varieties = [
            {
                'crop_type': 'Rice',
                'variety_name': 'Basmati 370',
                'maturity_days': 150,
                'water_requirement': 1200,
                'temperature_optimal': 25,
                'temperature_max': 35,
                'temperature_min': 15,
                'region_prevalence': 'Punjab,Haryana,UP',
                'season_type': 'Kharif',
                'yield_potential': 4.5,
                'drought_tolerance': 'Medium',
                'disease_resistance': 'Bacterial blight, Blast',
                'market_value': 8.50
            },
            {
                'crop_type': 'Rice',
                'variety_name': 'PR 126',
                'maturity_days': 135,
                'water_requirement': 1100,
                'temperature_optimal': 26,
                'temperature_max': 36,
                'temperature_min': 16,
                'region_prevalence': 'Punjab',
                'season_type': 'Kharif',
                'yield_potential': 5.2,
                'drought_tolerance': 'High',
                'disease_resistance': 'Blast, Sheath blight',
                'market_value': 7.20
            },
            {
                'crop_type': 'Rice',
                'variety_name': 'IR-64',
                'maturity_days': 120,
                'water_requirement': 1000,
                'temperature_optimal': 27,
                'temperature_max': 37,
                'temperature_min': 17,
                'region_prevalence': 'UP,Bihar',
                'season_type': 'Kharif',
                'yield_potential': 6.0,
                'drought_tolerance': 'Low',
                'disease_resistance': 'Blast, Tungro',
                'market_value': 6.80
            },
            {
                'crop_type': 'Rice',
                'variety_name': 'Swarna',
                'maturity_days': 140,
                'water_requirement': 1300,
                'temperature_optimal': 28,
                'temperature_max': 38,
                'temperature_min': 18,
                'region_prevalence': 'UP,MP,Bihar',
                'season_type': 'Kharif',
                'yield_potential': 5.8,
                'drought_tolerance': 'Medium',
                'disease_resistance': 'Blast, Bacterial blight',
                'market_value': 7.00
            },
            {
                'crop_type': 'Rice',
                'variety_name': 'Arize 6129',
                'maturity_days': 125,
                'water_requirement': 950,
                'temperature_optimal': 26,
                'temperature_max': 36,
                'temperature_min': 16,
                'region_prevalence': 'Haryana,Punjab',
                'season_type': 'Kharif',
                'yield_potential': 6.2,
                'drought_tolerance': 'High',
                'disease_resistance': 'Blast, Brown spot',
                'market_value': 7.50
            }
        ]

        # Wheat varieties for North India (primarily rabi)
        wheat_varieties = [
            {
                'crop_type': 'Wheat',
                'variety_name': 'HD 3086',
                'maturity_days': 155,
                'water_requirement': 450,
                'temperature_optimal': 18,
                'temperature_max': 28,
                'temperature_min': 8,
                'region_prevalence': 'UP,Punjab,Haryana',
                'season_type': 'Rabi',
                'yield_potential': 6.5,
                'drought_tolerance': 'Medium',
                'disease_resistance': 'Rust, Powdery mildew',
                'market_value': 5.20
            },
            {
                'crop_type': 'Wheat',
                'variety_name': 'PBW 725',
                'maturity_days': 150,
                'water_requirement': 420,
                'temperature_optimal': 17,
                'temperature_max': 27,
                'temperature_min': 7,
                'region_prevalence': 'Punjab,Haryana',
                'season_type': 'Rabi',
                'yield_potential': 7.0,
                'drought_tolerance': 'High',
                'disease_resistance': 'Leaf rust, Yellow rust',
                'market_value': 5.80
            },
            {
                'crop_type': 'Wheat',
                'variety_name': 'C 306',
                'maturity_days': 160,
                'water_requirement': 480,
                'temperature_optimal': 19,
                'temperature_max': 29,
                'temperature_min': 9,
                'region_prevalence': 'UP,Bihar,MP',
                'season_type': 'Rabi',
                'yield_potential': 5.8,
                'drought_tolerance': 'Low',
                'disease_resistance': 'Brown rust, Loose smut',
                'market_value': 4.90
            },
            {
                'crop_type': 'Wheat',
                'variety_name': 'HW 2004',
                'maturity_days': 145,
                'water_requirement': 400,
                'temperature_optimal': 16,
                'temperature_max': 26,
                'temperature_min': 6,
                'region_prevalence': 'Haryana',
                'season_type': 'Rabi',
                'yield_potential': 6.8,
                'drought_tolerance': 'High',
                'disease_resistance': 'Karnal bunt, Spot blotch',
                'market_value': 5.50
            },
            {
                'crop_type': 'Wheat',
                'variety_name': 'Sharbati Sonora',
                'maturity_days': 140,
                'water_requirement': 380,
                'temperature_optimal': 18,
                'temperature_max': 28,
                'temperature_min': 8,
                'region_prevalence': 'UP,MP',
                'season_type': 'Rabi',
                'yield_potential': 4.2,
                'drought_tolerance': 'Medium',
                'disease_resistance': 'Rust diseases',
                'market_value': 6.20  # Premium variety
            }
        ]

        # Maize varieties for North India
        maize_varieties = [
            {
                'crop_type': 'Maize',
                'variety_name': 'HQPM 1',
                'maturity_days': 110,
                'water_requirement': 600,
                'temperature_optimal': 25,
                'temperature_max': 35,
                'temperature_min': 15,
                'region_prevalence': 'UP,Bihar,MP',
                'season_type': 'Kharif',
                'yield_potential': 8.0,
                'drought_tolerance': 'Medium',
                'disease_resistance': 'Downy mildew, Rust',
                'market_value': 4.80
            },
            {
                'crop_type': 'Maize',
                'variety_name': 'Baby Corn Hybrid',
                'maturity_days': 85,
                'water_requirement': 550,
                'temperature_optimal': 24,
                'temperature_max': 34,
                'temperature_min': 14,
                'region_prevalence': 'Punjab,Haryana',
                'season_type': 'Kharif',
                'yield_potential': 4.5,
                'drought_tolerance': 'Low',
                'disease_resistance': 'Fusarium, Smut',
                'market_value': 12.00  # Premium for baby corn
            },
            {
                'crop_type': 'Maize',
                'variety_name': 'Sweet Corn 75',
                'maturity_days': 95,
                'water_requirement': 580,
                'temperature_optimal': 23,
                'temperature_max': 33,
                'temperature_min': 13,
                'region_prevalence': 'Punjab,Haryana,UP',
                'season_type': 'Kharif',
                'yield_potential': 6.5,
                'drought_tolerance': 'Medium',
                'disease_resistance': 'Turcicum leaf blight',
                'market_value': 8.50
            },
            {
                'crop_type': 'Maize',
                'variety_name': 'Popcorn variety',
                'maturity_days': 105,
                'water_requirement': 620,
                'temperature_optimal': 26,
                'temperature_max': 36,
                'temperature_min': 16,
                'region_prevalence': 'MP,UP',
                'season_type': 'Kharif',
                'yield_potential': 5.2,
                'drought_tolerance': 'High',
                'disease_resistance': 'Maydis leaf blight',
                'market_value': 15.00
            },
            {
                'crop_type': 'Maize',
                'variety_name': 'DHM 117',
                'maturity_days': 115,
                'water_requirement': 650,
                'temperature_optimal': 25,
                'temperature_max': 35,
                'temperature_min': 15,
                'region_prevalence': 'All North India',
                'season_type': 'Kharif',
                'yield_potential': 9.5,
                'drought_tolerance': 'High',
                'disease_resistance': 'Multiple resistance',
                'market_value': 5.20
            }
        ]

        varieties.extend(rice_varieties)
        varieties.extend(wheat_varieties)
        varieties.extend(maize_varieties)

        return varieties

    def get_crop_varieties(self, crop_type: str = None, region: str = None) -> pd.DataFrame:
        """
        Get crop variety data with optional filtering

        Args:
            crop_type: Filter by crop type (Rice, Wheat, Maize)
            region: Filter by region (state name)

        Returns:
            DataFrame with variety information
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            query = "SELECT * FROM crop_varieties WHERE 1=1"
            params = []

            if crop_type:
                query += " AND crop_type = ?"
                params.append(crop_type)

            if region:
                query += " AND region_prevalence LIKE ?"
                params.append(f"%{region}%")

            df = pd.read_sql_query(query, conn, params=params)

        return df

    def get_variety_by_name(self, crop_type: str, variety_name: str) -> Optional[Dict]:
        """
        Get specific variety information

        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
            variety_name: Variety name

        Returns:
            Dictionary with variety information or None if not found
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            query = "SELECT * FROM crop_varieties WHERE crop_type = ? AND variety_name = ?"
            df = pd.read_sql_query(query, conn, params=[crop_type, variety_name])

        if df.empty:
            return None

        return df.iloc[0].to_dict()

    def calculate_variety_yield_adjustment(
        self,
        crop_type: str,
        variety_name: str,
        weather_data: pd.DataFrame,
        base_yield: float = None
    ) -> Dict[str, float]:
        """
        Calculate variety-specific yield adjustments based on weather conditions

        Args:
            crop_type: Crop type
            variety_name: Variety name
            weather_data: Weather data DataFrame
            base_yield: Base yield to adjust (optional)

        Returns:
            Dictionary with adjustment factors and predicted yield
        """
        variety_info = self.get_variety_by_name(crop_type, variety_name)

        if not variety_info:
            return {
                'adjustment_factor': 1.0,
                'heat_stress_penalty': 0.0,
                'drought_penalty': 0.0,
                'cold_stress_penalty': 0.0,
                'predicted_yield': base_yield if base_yield else 0.0,
                'variety_found': False
            }

        # Extract variety parameters
        temp_optimal = variety_info['temperature_optimal']
        temp_max = variety_info['temperature_max']
        temp_min = variety_info['temperature_min']
        water_req = variety_info['water_requirement']
        drought_tolerance = variety_info['drought_tolerance']

        # Calculate weather stress indices from weather data
        heat_stress = self._calculate_heat_stress(weather_data, temp_max)
        cold_stress = self._calculate_cold_stress(weather_data, temp_min)
        drought_stress = self._calculate_drought_stress(weather_data, water_req, drought_tolerance)
        optimal_temp_bonus = self._calculate_optimal_temperature_bonus(weather_data, temp_optimal)

        # Calculate total adjustment factor
        adjustment_factor = 1.0 + optimal_temp_bonus - heat_stress - cold_stress - drought_stress

        # Ensure adjustment factor is reasonable (0.3 to 2.0)
        adjustment_factor = np.clip(adjustment_factor, 0.3, 2.0)

        # Calculate predicted yield if base yield provided
        predicted_yield = base_yield * adjustment_factor if base_yield else 0.0

        return {
            'adjustment_factor': adjustment_factor,
            'heat_stress_penalty': heat_stress,
            'drought_penalty': drought_stress,
            'cold_stress_penalty': cold_stress,
            'optimal_temp_bonus': optimal_temp_bonus,
            'predicted_yield': predicted_yield,
            'variety_found': True,
            'variety_info': variety_info
        }

    def _calculate_heat_stress(self, weather_df: pd.DataFrame, variety_temp_max: float) -> float:
        """Calculate heat stress impact"""
        if 'temp_max' not in weather_df.columns:
            return 0.0

        heat_days = (weather_df['temp_max'] > variety_temp_max).sum()
        total_days = len(weather_df)

        if total_days == 0:
            return 0.0

        # Heat stress penalty (0.05 per heat day, max 0.5)
        heat_penalty = min(heat_days * 0.05, 0.5)
        return heat_penalty

    def _calculate_cold_stress(self, weather_df: pd.DataFrame, variety_temp_min: float) -> float:
        """Calculate cold stress impact"""
        if 'temp_min' not in weather_df.columns:
            return 0.0

        cold_days = (weather_df['temp_min'] < variety_temp_min - 5).sum()
        total_days = len(weather_df)

        if total_days == 0:
            return 0.0

        # Cold stress penalty (0.03 per cold day, max 0.3)
        cold_penalty = min(cold_days * 0.03, 0.3)
        return cold_penalty

    def _calculate_drought_stress(self, weather_df: pd.DataFrame, water_requirement: float, drought_tolerance: str) -> float:
        """Calculate drought stress impact"""
        # Simplified drought calculation based on precipitation and humidity
        if 'rain_7d_sum' not in weather_df.columns or 'humidity' in weather_df.columns:
            return 0.0

        # Average 7-day rain and humidity
        avg_rain = weather_df['rain_7d_sum'].mean() if 'rain_7d_sum' in weather_df.columns else 0
        avg_humidity = weather_df['humidity'].mean() if 'humidity' in weather_df.columns else 50

        # Drought tolerance multiplier
        tolerance_multipliers = {'Low': 1.2, 'Medium': 1.0, 'High': 0.8}

        # Calculate water availability index
        water_index = (avg_rain * 0.7 + avg_humidity * 0.3) / 100
        required_water_index = min(water_requirement / 1500, 1.0)  # Normalize to 1500mm max

        # Drought penalty calculation
        water_deficit = max(0, required_water_index - water_index)
        drought_penalty = water_deficit * tolerance_multipliers.get(drought_tolerance, 1.0)

        # Cap at 0.6
        return min(drought_penalty, 0.6)

    def _calculate_optimal_temperature_bonus(self, weather_df: pd.DataFrame, optimal_temp: float) -> float:
        """Calculate bonus for optimal temperature conditions"""
        if 'temp' not in weather_df.columns:
            return 0.0

        # Count days within optimal temperature range (+/- 3°C)
        optimal_range = (weather_df['temp'] >= optimal_temp - 3) & (weather_df['temp'] <= optimal_temp + 3)
        optimal_days = optimal_range.sum()
        total_days = len(weather_df)

        if total_days == 0:
            return 0.0

        # Optimal temperature bonus (0.02 per optimal day, max 0.3)
        temp_bonus = min(optimal_days * 0.02, 0.3)
        return temp_bonus

    def get_season_recommendations(self, crop_type: str, region: str) -> Dict[str, List[str]]:
        """
        Get season-based variety recommendations

        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
            region: Region/state name

        Returns:
            Dictionary with season recommendations
        """
        season_map = {
            'Rice': {'Kharif': ['PR 126', 'IR-64', 'Swarna'], 'Rabi': []},
            'Wheat': {'Rabi': ['HD 3086', 'PBW 725', 'HW 2004', 'C 306'], 'Kharif': []},
            'Maize': {'Kharif': ['HQPM 1', 'DHM 117', 'Baby Corn Hybrid', 'Sweet Corn 75']}
        }

        return season_map.get(crop_type, {})

    def add_variety_performance_data(self, performance_data: Dict):
        """
        Add variety performance data for continuous learning

        Args:
            performance_data: Dictionary with performance metrics
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute('''
                INSERT INTO variety_performance
                (crop_type, variety_name, region, season, year, actual_yield,
                 expected_yield, yield_ratio, weather_stress_impact, disease_impact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                performance_data.get('crop_type'),
                performance_data.get('variety_name'),
                performance_data.get('region'),
                performance_data.get('season'),
                performance_data.get('year'),
                performance_data.get('actual_yield'),
                performance_data.get('expected_yield'),
                performance_data.get('yield_ratio'),
                performance_data.get('weather_stress_impact'),
                performance_data.get('disease_impact')
            ))

            conn.commit()

        self.logger.info(f"✅ Added performance data for {performance_data.get('crop_type')} {performance_data.get('variety_name')}")

    def get_variety_performance_history(self, crop_type: str, variety_name: str, region: str = None) -> pd.DataFrame:
        """
        Get historical performance data for a variety

        Args:
            crop_type: Crop type
            variety_name: Variety name
            region: Optional region filter

        Returns:
            DataFrame with performance history
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            query = """
                SELECT * FROM variety_performance
                WHERE crop_type = ? AND variety_name = ?
            """
            params = [crop_type, variety_name]

            if region:
                query += " AND region = ?"
                params.append(region)

            df = pd.read_sql_query(query, conn, params=params)

        return df


def test_crop_variety_database():
    """Test the crop variety database functionality"""
    print("🌾 Testing Crop Variety Database...")

    db = CropVarietyDatabase()

    # Test getting varieties
    rice_varieties = db.get_crop_varieties('Rice')
    print(f"✅ Found {len(rice_varieties)} Rice varieties:")
    if not rice_varieties.empty:
        print(f"   Sample: {rice_varieties.iloc[0]['variety_name']} ({rice_varieties.iloc[0]['maturity_days']} days)")

    wheat_varieties = db.get_crop_varieties('Wheat')
    print(f"✅ Found {len(wheat_varieties)} Wheat varieties")

    maize_varieties = db.get_crop_varieties('Maize')
    print(f"✅ Found {len(maize_varieties)} Maize varieties")

    # Test getting specific variety
    basmati_info = db.get_variety_by_name('Rice', 'Basmati 370')
    if basmati_info:
        print(f"✅ Basmati 370 details: Maturity {basmati_info['maturity_days']} days, Yield potential {basmati_info['yield_potential']} t/ha")

    # Test season recommendations
    rice_seasons = db.get_season_recommendations('Rice', 'Punjab')
    print(f"✅ Rice season recommendations: {rice_seasons}")

    wheat_seasons = db.get_season_recommendations('Wheat', 'Punjab')
    print(f"✅ Wheat season recommendations: {wheat_seasons}")

    print("🎉 Crop variety database test completed")


if __name__ == "__main__":
    test_crop_variety_database()
