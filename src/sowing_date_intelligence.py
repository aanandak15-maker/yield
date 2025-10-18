#!/usr/bin/env python3
"""
Sowing Date Intelligence for North India Crop Yield Prediction

Manages sowing date data, season detection algorithms, crop calendars,
and sowing date recommendations based on weather patterns and variety requirements.
"""

import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Union, Any
import logging
from pathlib import Path
import sqlite3
import warnings
import calendar

# Suppress warnings
warnings.filterwarnings('ignore')

class SowingDateIntelligence:
    """Intelligence system for crop sowing date management"""

    def __init__(self, config_path: str = "../config/api_config.json"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._load_config()
        self._setup_database()
        self._initialize_sowing_data()

    def _load_config(self):
        """Load configuration with multiple path fallbacks for production"""
        # Try multiple config file locations
        config_paths = [
            self.config_path,  # Original path (e.g., '../config/api_config.json')
            'config/api_config.json',  # Direct from app root
            '/app/config/api_config.json',  # Docker absolute path
            'config/demo_config.json',  # Fallback to demo config
            '/app/config/demo_config.json',  # Docker demo config
        ]

        current_dir = os.path.dirname(__file__)

        for config_file in config_paths:
            # Resolve relative paths
            if not os.path.isabs(config_file):
                config_file = os.path.join(current_dir, config_file)

            # Also try from parent directory if relative
            if not os.path.isabs(config_file) and config_file.startswith('..'):
                config_file = os.path.join(current_dir, config_file)

            try:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    self.db_config = config.get('storage', {})
                    self.region_config = config.get('north_india_region', {})
                    self.logger.info(f"Config loaded successfully from: {config_file}")
                    return
            except Exception as e:
                continue  # Try next path

        # If all paths fail, use production defaults (no warning needed)
        self.logger.info("Using production default configuration")
        self.db_config = {'database_path': 'data/database/crop_prediction.db'}
        self.region_config = {
            'states': [
                {'name': 'Punjab', 'lat': 30.7333, 'lon': 76.7794},
                {'name': 'Haryana', 'lat': 29.0588, 'lon': 76.0856},
                {'name': 'UP', 'lat': 26.8467, 'lon': 80.9462},
                {'name': 'Bihar', 'lat': 25.0961, 'lon': 85.3131},
                {'name': 'MP', 'lat': 23.2599, 'lon': 77.4126}
            ]
        }

    def _setup_database(self):
        """Set up SQLite database for sowing date data"""
        db_path = Path(self.db_config.get('database_path', 'data/database/crop_prediction.db'))

        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()

            # Sowing date data table - bulletproof schema creation
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sowing_dates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state TEXT,
                    district TEXT,
                    crop_type TEXT,
                    variety_name TEXT,
                    sowing_date DATE,
                    season_type TEXT,
                    year INTEGER,
                    latitude REAL,
                    longitude REAL,
                    sowing_method TEXT,
                    seed_rate REAL,
                    irrigation_scheduled TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Dynamic column management - ensure all required columns exist
            cursor.execute("PRAGMA table_info(sowing_dates)")
            existing_columns = [column[1] for column in cursor.fetchall()]

            required_columns = {
                'sowing_method': 'TEXT',
                'seed_rate': 'REAL',
                'irrigation_scheduled': 'TEXT',
                'notes': 'TEXT',
                'district': 'TEXT',
                'latitude': 'REAL',
                'longitude': 'REAL'
            }

            for column_name, column_type in required_columns.items():
                if column_name not in existing_columns:
                    try:
                        cursor.execute(f'ALTER TABLE sowing_dates ADD COLUMN {column_name} {column_type}')
                        self.logger.info(f"✅ Added missing {column_name} column to sowing_dates table")
                    except sqlite3.OperationalError as e:
                        self.logger.warning(f"Could not add {column_name} column: {e}")
                        # Column might already exist or table might be in use

            # Season patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS season_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state TEXT,
                    crop_type TEXT,
                    season_name TEXT,
                    start_month INTEGER,
                    start_day INTEGER,
                    end_month INTEGER,
                    end_day INTEGER,
                    optimal_sowing_window_start DATE,
                    optimal_sowing_window_end DATE,
                    rainfall_pattern TEXT,
                    temperature_pattern TEXT,
                    soil_moisture_preferred TEXT,
                    risk_factors TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Weather-based sowing recommendations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sowing_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state TEXT,
                    crop_type TEXT,
                    variety_name TEXT,
                    recommended_date DATE,
                    confidence_score REAL,
                    risk_assessment TEXT,
                    weather_forecast_used TEXT,
                    alternative_dates TEXT,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

        # Ensure path is relative to project root
        if not db_path.is_absolute():
            db_path = Path(os.path.join(os.path.dirname(__file__), "..", str(db_path)))
        self.db_path = db_path
        self.logger.info(f"✅ Sowing date intelligence database initialized at {db_path}")

    def _initialize_sowing_data(self):
        """Initialize sowing date data and season patterns"""
        # Check if data already exists
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sowing_dates")
            sowing_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM season_patterns")
            season_count = cursor.fetchone()[0]

        if sowing_count > 0 and season_count > 0:
            self.logger.info(f"📊 Sowing date data already exists ({sowing_count} dates, {season_count} patterns)")
            return

        # Initialize season patterns
        if season_count == 0:
            season_patterns = self._get_north_india_season_patterns()
            self._initialize_season_patterns(season_patterns)

        # Initialize historical sowing dates
        if sowing_count == 0:
            sowing_records = self._generate_historical_sowing_dates()
            self._initialize_sowing_records(sowing_records)

    def _get_north_india_season_patterns(self) -> List[Dict]:
        """Get comprehensive season patterns for North India crops"""
        patterns = []

        # Rice (Kharif) patterns
        rice_kharif_patterns = [
            {
                'state': 'Punjab',
                'crop_type': 'Rice',
                'season_name': 'Kharif',
                'start_month': 6,
                'start_day': 15,
                'end_month': 7,
                'end_day': 15,
                'rainfall_pattern': 'High rainfall expected',
                'temperature_pattern': '25-30°C optimal',
                'soil_moisture_preferred': 'High',
                'risk_factors': 'Waterlogging, Heavy rain'
            },
            {
                'state': 'Haryana',
                'crop_type': 'Rice',
                'season_name': 'Kharif',
                'start_month': 6,
                'start_day': 20,
                'end_month': 7,
                'end_day': 20,
                'rainfall_pattern': 'Moderate to high rainfall',
                'temperature_pattern': '24-28°C optimal',
                'soil_moisture_preferred': 'Medium to High',
                'risk_factors': 'Terminal heat stress'
            },
            {
                'state': 'UP',
                'crop_type': 'Rice',
                'season_name': 'Kharif',
                'start_month': 6,
                'start_day': 25,
                'end_month': 7,
                'end_day': 25,
                'rainfall_pattern': 'Monsoon dependent',
                'temperature_pattern': '25-32°C range',
                'soil_moisture_preferred': 'Medium',
                'risk_factors': 'Drought, Flooding'
            }
        ]

        # Wheat (Rabi) patterns
        wheat_rabi_patterns = [
            {
                'state': 'Punjab',
                'crop_type': 'Wheat',
                'season_name': 'Rabi',
                'start_month': 11,
                'start_day': 1,
                'end_month': 11,
                'end_day': 30,
                'rainfall_pattern': 'Low rainfall preferred',
                'temperature_pattern': '15-20°C optimal',
                'soil_moisture_preferred': 'Low to Medium',
                'risk_factors': 'Excessive rainfall'
            },
            {
                'state': 'Haryana',
                'crop_type': 'Wheat',
                'season_name': 'Rabi',
                'start_month': 11,
                'start_day': 5,
                'end_month': 12,
                'end_day': 5,
                'rainfall_pattern': 'Minimal rainfall',
                'temperature_pattern': '12-18°C optimal',
                'soil_moisture_preferred': 'Medium',
                'risk_factors': 'Cold wave stress'
            }
        ]

        # Maize patterns (can be both kharif and rabi in some regions)
        maize_patterns = [
            {
                'state': 'Punjab',
                'crop_type': 'Maize',
                'season_name': 'Kharif',
                'start_month': 6,
                'start_day': 1,
                'end_month': 6,
                'end_day': 30,
                'rainfall_pattern': 'Early monsoon',
                'temperature_pattern': '20-28°C optimal',
                'soil_moisture_preferred': 'Medium',
                'risk_factors': 'Drought stress'
            }
        ]

        patterns.extend(rice_kharif_patterns)
        patterns.extend(wheat_rabi_patterns)
        patterns.extend(maize_patterns)

        # Add optimal sowing windows (calculated dynamically)
        for pattern in patterns:
            year = datetime.now().year
            optimal_start = date(year, pattern['start_month'], pattern['start_day'])
            optimal_end = date(year, pattern['end_month'], pattern['end_day'])
            pattern['optimal_sowing_window_start'] = optimal_start.isoformat()
            pattern['optimal_sowing_window_end'] = optimal_end.isoformat()

        return patterns

    def _initialize_season_patterns(self, patterns: List[Dict]):
        """Initialize season patterns in database"""
        with sqlite3.connect(str(self.db_path)) as conn:
            for pattern in patterns:
                conn.execute('''
                    INSERT INTO season_patterns
                    (state, crop_type, season_name, start_month, start_day,
                     end_month, end_day, optimal_sowing_window_start,
                     optimal_sowing_window_end, rainfall_pattern,
                     temperature_pattern, soil_moisture_preferred, risk_factors)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pattern['state'],
                    pattern['crop_type'],
                    pattern['season_name'],
                    pattern['start_month'],
                    pattern['start_day'],
                    pattern['end_month'],
                    pattern['end_day'],
                    pattern['optimal_sowing_window_start'],
                    pattern['optimal_sowing_window_end'],
                    pattern['rainfall_pattern'],
                    pattern['temperature_pattern'],
                    pattern['soil_moisture_preferred'],
                    pattern['risk_factors']
                ))

            conn.commit()

        self.logger.info(f"✅ Initialized {len(patterns)} season patterns")

    def _generate_historical_sowing_dates(self) -> List[Dict]:
        """Generate historical sowing date records for the past 10 years"""
        sowing_records = []

        # Use current year as base and go back 10 years
        current_year = datetime.now().year
        years = range(current_year - 10, current_year + 1)

        states = [state['name'] for state in self.region_config.get('states', [])]

        crop_configs = {
            'Rice': {
                'varieties': ['PR 126', 'IR-64', 'Swarna', 'Basmati 370'],
                'method': 'Transplanting',
                'seed_rate': 20.0
            },
            'Wheat': {
                'varieties': ['HD 3086', 'PBW 725', 'C 306'],
                'method': 'Broadcasting',
                'seed_rate': 100.0
            },
            'Maize': {
                'varieties': ['HQPM 1', 'DHM 117', 'Baby Corn Hybrid'],
                'method': 'Ridge sowing',
                'seed_rate': 15.0
            }
        }

        for year in years:
            for state in states:
                for crop_type, config in crop_configs.items():
                    season = self._get_season_for_crop_state(crop_type, state)
                    if season:
                        # Generate 3-5 records per crop/type/year/state combination
                        num_records = np.random.randint(3, 6)

                        for _ in range(num_records):
                            record = self._generate_sowing_record(
                                state, crop_type, config, season, year
                            )
                            if record:
                                sowing_records.append(record)

        return sowing_records

    def _generate_sowing_record(self, state: str, crop_type: str, config: Dict,
                               season: str, year: int) -> Optional[Dict]:
        """Generate a single sowing date record"""
        try:
            # Get state info
            state_info = next((s for s in self.region_config.get('states', [])
                             if s['name'] == state), None)
            if not state_info:
                return None

            lat, lon = state_info['lat'], state_info['lon']

            # Get optimal sowing window
            optimal_window = self.get_optimal_sowing_window(crop_type, state, season)
            if not optimal_window:
                return None

            # Generate random date within optimal window with some variation
            days_diff = (optimal_window['end'] - optimal_window['start']).days
            random_days = np.random.randint(-5, days_diff + 6)  # Allow ±5 days variation
            sowing_date = optimal_window['start'] + timedelta(days=random_days)

            # Adjust to current year
            sowing_date = sowing_date.replace(year=year)

            # Select random variety
            variety = np.random.choice(config['varieties'])

            record = {
                'state': state,
                'district': f"{state}_district_{np.random.randint(1, 5)}",  # Simplified
                'crop_type': crop_type,
                'variety_name': variety,
                'sowing_date': sowing_date.isoformat(),
                'season_type': season,
                'year': year,
                'latitude': lat,
                'longitude': lon,
                'sowing_method': config['method'],
                'seed_rate': config['seed_rate'],
                'irrigation_scheduled': 'Yes' if np.random.random() > 0.3 else 'No',
                'notes': f"Historical sowing record for {year}"
            }

            return record

        except Exception as e:
            self.logger.warning(f"Failed to generate sowing record: {e}")
            return None

    def _initialize_sowing_records(self, records: List[Dict]):
        """Initialize sowing date records in database"""
        with sqlite3.connect(str(self.db_path)) as conn:
            for record in records:
                conn.execute('''
                    INSERT INTO sowing_dates
                    (state, district, crop_type, variety_name, sowing_date,
                     season_type, year, latitude, longitude, sowing_method,
                     seed_rate, irrigation_scheduled, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record['state'],
                    record['district'],
                    record['crop_type'],
                    record['variety_name'],
                    record['sowing_date'],
                    record['season_type'],
                    record['year'],
                    record['latitude'],
                    record['longitude'],
                    record['sowing_method'],
                    record['seed_rate'],
                    record['irrigation_scheduled'],
                    record['notes']
                ))

            conn.commit()

        self.logger.info(f"✅ Initialized {len(records)} historical sowing records")

    def _get_season_for_crop_state(self, crop_type: str, state: str) -> Optional[str]:
        """Get the primary season for a crop in a state"""
        season_map = {
            'Rice': {
                'Punjab': 'Kharif',
                'Haryana': 'Kharif',
                'UP': 'Kharif',
                'Bihar': 'Kharif',
                'MP': 'Kharif'
            },
            'Wheat': {
                'Punjab': 'Rabi',
                'Haryana': 'Rabi',
                'UP': 'Rabi',
                'Bihar': 'Rabi',
                'MP': 'Rabi'
            },
            'Maize': {
                'Punjab': 'Kharif',
                'Haryana': 'Kharif',
                'UP': 'Kharif',
                'Bihar': 'Kharif',
                'MP': 'Kharif'
            }
        }

        return season_map.get(crop_type, {}).get(state)

    def get_optimal_sowing_window(self, crop_type: str, state: str, season: str) -> Optional[Dict]:
        """
        Get optimal sowing window for a crop in a state and season

        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
            state: State name
            season: Season name (Kharif, Rabi)

        Returns:
            Dictionary with start and end dates
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            df = pd.read_sql_query('''
                SELECT optimal_sowing_window_start, optimal_sowing_window_end
                FROM season_patterns
                WHERE crop_type = ? AND state = ? AND season_name = ?
            ''', conn, params=[crop_type, state, season])

        if df.empty:
            return None

        start_date = date.fromisoformat(df.iloc[0]['optimal_sowing_window_start'])
        end_date = date.fromisoformat(df.iloc[0]['optimal_sowing_window_end'])

        return {'start': start_date, 'end': end_date}

    def detect_current_season(self, target_date: date = None) -> str:
        """
        Detect the current growing season based on date

        Args:
            target_date: Date to check (defaults to today)

        Returns:
            Season name (Kharif, Rabi, Zaid)
        """
        if target_date is None:
            target_date = date.today()

        month = target_date.month
        day = target_date.day

        # North India seasons (approximate)
        if (month == 6 and day >= 15) or (month in [7, 8]) or (month == 9 and day <= 30):
            return 'Kharif'  # June-September
        elif (month == 10 and day >= 15) or (month in [11, 12, 1, 2]) or (month == 3 and day <= 15):
            return 'Rabi'    # October-March
        else:
            return 'Zaid'    # April-June

    def recommend_sowing_date(
        self,
        crop_type: str,
        variety_name: str,
        state: str,
        weather_forecast: pd.DataFrame = None,
        flexibility_days: int = 14
    ) -> Dict:
        """
        Recommend optimal sowing date based on crop, variety, location, and weather

        Args:
            crop_type: Crop type
            variety_name: Specific variety
            state: State name
            weather_forecast: Weather forecast DataFrame
            flexibility_days: Days to look forward/back for optimal conditions

        Returns:
            Dictionary with recommendation details
        """
        season = self._get_season_for_crop_state(crop_type, state)
        if not season:
            return {
                'recommended_date': None,
                'confidence_score': 0.0,
                'risk_assessment': 'No season data available',
                'alternative_dates': [],
                'reason': f'No sowing season defined for {crop_type} in {state}'
            }

        optimal_window = self.get_optimal_sowing_window(crop_type, state, season)
        if not optimal_window:
            return {
                'recommended_date': None,
                'confidence_score': 0.0,
                'risk_assessment': 'No optimal window data available',
                'alternative_dates': [],
                'reason': f'No optimal sowing window for {crop_type} in {state}'
            }

        current_date = date.today()

        # Check if current date is within optimal window
        if optimal_window['start'] <= current_date <= optimal_window['end']:
            recommended_date = current_date
            confidence = 0.9
            reason = f"Within optimal sowing window for {season} season"
        else:
            # Check if we can recommend within flexibility window
            latest_possible = optimal_window['end'] + timedelta(days=flexibility_days)

            if current_date <= latest_possible:
                recommended_date = min(current_date, optimal_window['end'])
                confidence = 0.7
                reason = f"Late sowing but within flexibility window"
            else:
                # Too late for this season
                recommended_date = None
                confidence = 0.0
                reason = f"Current date is too late for {season} season sowing"

        # Analyze weather forecast for additional insights
        risk_assessment = self._assess_sowing_risks(weather_forecast, crop_type, recommended_date)
        alternative_dates = self._generate_alternative_dates(optimal_window, current_date, flexibility_days)

        result = {
            'recommended_date': recommended_date,
            'confidence_score': confidence,
            'risk_assessment': risk_assessment,
            'alternative_dates': alternative_dates,
            'season': season,
            'optimal_window': {
                'start': optimal_window['start'].isoformat(),
                'end': optimal_window['end'].isoformat()
            },
            'reason': reason
        }

        # Store recommendation in database
        self._store_sowing_recommendation(crop_type, variety_name, state, result)

        return result

    def _assess_sowing_risks(self, weather_forecast: pd.DataFrame, crop_type: str, sowing_date: date) -> str:
        """Assess risks for sowing on a specific date"""
        if weather_forecast is None or weather_forecast.empty or sowing_date is None:
            return "Weather data not available for risk assessment"

        # Filter forecast around sowing date
        sowing_datetime = datetime.combine(sowing_date, datetime.min.time())
        forecast_window = weather_forecast[
            (weather_forecast['timestamp'] >= sowing_datetime - timedelta(days=3)) &
            (weather_forecast['timestamp'] <= sowing_datetime + timedelta(days=7))
        ]

        risks = []

        if not forecast_window.empty:
            # Check for heavy rainfall (flooding risk)
            heavy_rain_days = (forecast_window.get('total_rain', 0) > 50).sum()
            if heavy_rain_days > 2:
                if crop_type == 'Rice':
                    risks.append("High risk of waterlogging (suitable for rice)")
                else:
                    risks.append("High risk of flooding damage")

            # Check for drought conditions
            low_rain_periods = (forecast_window.get('rain_7d_sum', 0) < 10).sum()
            if low_rain_periods > 3:
                risks.append("Potential drought stress in initial growth phase")

            # Check temperature extremes
            if 'temp' in forecast_window.columns:
                cold_days = (forecast_window['temp'] < 15).sum()
                hot_days = (forecast_window['temp'] > 35).sum()

                if crop_type == 'Wheat' and cold_days > 2:
                    risks.append("Cold stress risk for wheat germination")

                if hot_days > 1:
                    risks.append("Heat stress during germination")

        if not risks:
            risks.append("Weather conditions appear favorable")

        return "; ".join(risks)

    def _generate_alternative_dates(self, optimal_window: Dict, current_date: date,
                                  flexibility_days: int) -> List[str]:
        """Generate alternative sowing dates around optimal window"""
        alternatives = []

        window_start = optimal_window['start']
        window_end = optimal_window['end']
        latest_possible = window_end + timedelta(days=flexibility_days)

        # Generate 3-5 alternative dates
        if current_date < window_start:
            # Suggest dates around optimal start
            alternatives.append((window_start + timedelta(days=3)).isoformat())
            alternatives.append((window_start + timedelta(days=7)).isoformat())
        elif current_date > latest_possible:
            # Current date too late, suggest for next season
            alternatives.append(f"Next season: {window_start.replace(year=window_start.year + 1).isoformat()}")
        else:
            # Suggest dates around current date within acceptable range
            for days_offset in [-7, -3, 3, 7]:
                alt_date = current_date + timedelta(days=days_offset)
                if window_start <= alt_date <= latest_possible:
                    alternatives.append(alt_date.isoformat())

                if len(alternatives) >= 3:
                    break

        return alternatives[:5]  # Limit to 5 alternatives

    def _store_sowing_recommendation(self, crop_type: str, variety_name: str,
                                   state: str, recommendation: Dict):
        """Store sowing recommendation in database"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT INTO sowing_recommendations
                    (state, crop_type, variety_name, recommended_date,
                     confidence_score, risk_assessment, weather_forecast_used, alternative_dates)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    state,
                    crop_type,
                    variety_name,
                    recommendation.get('recommended_date').isoformat() if recommendation.get('recommended_date') else None,
                    recommendation.get('confidence_score', 0.0),
                    recommendation.get('risk_assessment', ''),
                    'forecast_used' if recommendation.get('weather_forecast') else '',
                    json.dumps(recommendation.get('alternative_dates', []))
                ))

                conn.commit()

        except Exception as e:
            self.logger.warning(f"Failed to store sowing recommendation: {e}")

    def get_sowing_date_history(self, crop_type: str = None, state: str = None,
                               year: int = None) -> pd.DataFrame:
        """
        Get historical sowing date data

        Args:
            crop_type: Filter by crop type
            state: Filter by state
            year: Filter by year

        Returns:
            DataFrame with sowing date history
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            query = "SELECT * FROM sowing_dates WHERE 1=1"
            params = []

            if crop_type:
                query += " AND crop_type = ?"
                params.append(crop_type)

            if state:
                query += " AND state = ?"
                params.append(state)

            if year:
                query += " AND year = ?"
                params.append(year)

            query += " ORDER BY sowing_date DESC"

            df = pd.read_sql_query(query, conn, params=params)

        if not df.empty:
            df['sowing_date'] = pd.to_datetime(df['sowing_date'])

        return df

    def analyze_sowing_patterns(self, crop_type: str, state: str) -> Dict[str, Any]:
        """
        Analyze sowing date patterns for insights

        Args:
            crop_type: Crop type to analyze
            state: State to analyze

        Returns:
            Dictionary with pattern analysis
        """
        history_df = self.get_sowing_date_history(crop_type=crop_type, state=state)

        if history_df.empty:
            return {'error': 'No historical data available for analysis'}

        # Extract month-day patterns
        history_df['sowing_month'] = history_df['sowing_date'].dt.month
        history_df['sowing_day'] = history_df['sowing_date'].dt.day

        # Calculate patterns
        pattern_analysis = {
            'total_records': len(history_df),
            'years_covered': sorted(history_df['year'].unique().tolist()),
            'most_common_sowing_month': history_df['sowing_month'].mode().iloc[0] if not history_df['sowing_month'].empty else None,
            'earliest_sowing': history_df['sowing_date'].min().date() if not history_df['sowing_date'].empty else None,
            'latest_sowing': history_df['sowing_date'].max().date() if not history_df['sowing_date'].empty else None,
            'average_sowing_date': history_df['sowing_date'].dt.dayofyear.mean(),
            'sowing_date_variability': history_df['sowing_date'].dt.dayofyear.std(),
            'popular_varieties': history_df['variety_name'].value_counts().head(3).to_dict()
        }

        # Calculate month distribution
        month_dist = history_df['sowing_month'].value_counts().sort_index()

        # Convert month numbers to names
        month_names = {m: calendar.month_name[m] for m in range(1, 13)}
        pattern_analysis['month_distribution'] = {
            month_names.get(month, f'Month {month}'): count
            for month, count in month_dist.items()
        }

        # Success rate estimation (simplified)
        pattern_analysis['variability_assessment'] = self._assess_pattern_variability(history_df)

        return pattern_analysis

    def _assess_pattern_variability(self, history_df: pd.DataFrame) -> str:
        """Assess variability in sowing patterns"""
        if len(history_df) < 5:
            return "Insufficient data for variability assessment"

        std_days = history_df['sowing_date'].dt.dayofyear.std()

        if std_days < 10:
            return "Low variability - consistent sowing patterns"
        elif std_days < 20:
            return "Moderate variability - some seasonal adaptation"
        else:
            return "High variability - weather-dependent sowing decisions"


def test_sowing_date_intelligence():
    """Test the sowing date intelligence functionality"""
    print("🌱 Testing Sowing Date Intelligence...")

    sdi = SowingDateIntelligence()

    # Test getting optimal sowing window
    rice_window = sdi.get_optimal_sowing_window('Rice', 'Punjab', 'Kharif')
    if rice_window:
        print(f"✅ Rice sowing window in Punjab: {rice_window['start']} to {rice_window['end']}")

    wheat_window = sdi.get_optimal_sowing_window('Wheat', 'Haryana', 'Rabi')
    if wheat_window:
        print(f"✅ Wheat sowing window in Haryana: {wheat_window['start']} to {wheat_window['end']}")

    # Test season detection
    current_season = sdi.detect_current_season()
    print(f"✅ Current season: {current_season}")

    # Test sowing recommendation
    recommendation = sdi.recommend_sowing_date('Rice', 'PR 126', 'Punjab')
    if recommendation['recommended_date']:
        print(f"✅ Rice sowing recommendation: {recommendation['recommended_date']}")
        print(f"   Confidence: {recommendation['confidence_score']:.2f}")
        print(f"   Reason: {recommendation['reason']}")
    else:
        print(f"⚠️  No current recommendation: {recommendation.get('reason', 'Unknown')}")

    # Test pattern analysis
    rice_patterns = sdi.analyze_sowing_patterns('Rice', 'Punjab')
    if 'total_records' in rice_patterns:
        print("✅ Pattern analysis for Rice in Punjab:")
        print(f"   Records: {rice_patterns['total_records']}")
        print(f"   Years: {len(rice_patterns['years_covered'])}")
        if rice_patterns['most_common_sowing_month']:
            print(f"   Common month: {calendar.month_name[rice_patterns['most_common_sowing_month']]}")

    print("🎉 Sowing date intelligence test completed")


if __name__ == "__main__":
    test_sowing_date_intelligence()
