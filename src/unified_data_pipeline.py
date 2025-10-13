#!/usr/bin/env python3
"""
Unified Data Pipeline for Crop Yield Prediction System

Orchestrates data collection from multiple APIs (GEE, OpenWeather),
handles data storage, caching, and ensures data quality and freshness.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
import logging
import json
import os
from pathlib import Path
import sqlite3
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress warnings
warnings.filterwarnings('ignore')

class UnifiedDataPipeline:
    """Unified pipeline for collecting and managing satellite and weather data"""

    def __init__(self, config_path: str = "config/api_config.json"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._load_config()
        self._setup_database()
        self._cache_manager = DataCacheManager()

    def _load_config(self):
        """Load pipeline configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            self.data_refresh_config = config.get('data_refresh', {})
            self.storage_config = config.get('storage', {})
            self.north_india_config = config.get('north_india_region', {})

        except Exception as e:
            self.logger.error(f"Failed to load pipeline config: {e}")
            self.data_refresh_config = {}
            self.storage_config = {}
            self.north_india_config = {}

    def _setup_database(self):
        """Set up SQLite database for data storage"""
        db_path = Path(self.storage_config.get('database_path', 'data/database/crop_prediction.db'))

        # Create database directory
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect to database and create tables
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()

            # Satellite data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS satellite_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_name TEXT,
                    latitude REAL,
                    longitude REAL,
                    date DATE,
                    ndvi REAL,
                    evi REAL,
                    surface_temp REAL,
                    chirps_precipitation REAL,
                    data_source TEXT,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Weather data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_name TEXT,
                    latitude REAL,
                    longitude REAL,
                    timestamp TIMESTAMP,
                    temp REAL,
                    temp_min REAL,
                    temp_max REAL,
                    humidity REAL,
                    wind_speed REAL,
                    wind_deg REAL,
                    pressure REAL,
                    clouds REAL,
                    rain_1h REAL,
                    rain_3h REAL,
                    total_rain REAL,
                    gdd_daily REAL,
                    gdd_cumulative REAL,
                    heat_stress INTEGER,
                    cold_stress INTEGER,
                    weather_stress_index REAL,
                    data_source TEXT,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Crop variety data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crop_varieties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    crop_type TEXT,
                    variety_name TEXT,
                    maturity_days INTEGER,
                    water_requirement REAL,
                    temperature_optimal REAL,
                    temperature_max REAL,
                    temperature_min REAL,
                    region_prevalence TEXT,
                    season_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Sowing date data table
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Data collection metadata
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_collection_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_type TEXT,
                    location_name TEXT,
                    start_date DATE,
                    end_date DATE,
                    records_collected INTEGER,
                    data_quality_score REAL,
                    collection_status TEXT,
                    error_message TEXT,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

        self.db_path = db_path
        self.logger.info(f"✅ Database initialized at {db_path}")

    def collect_all_data_for_location(
        self,
        latitude: float,
        longitude: float,
        location_name: str = "Unknown",
        days_back_satellite: int = 30,
        days_back_weather: int = 7
    ) -> Dict[str, pd.DataFrame]:
        """
        Collect both satellite and weather data for a location

        Args:
            latitude: Location latitude
            longitude: Location longitude
            location_name: Human-readable location name
            days_back_satellite: Days of historical satellite data to collect
            days_back_weather: Days of weather data to collect

        Returns:
            Dictionary with satellite and weather DataFrames
        """
        results = {}

        try:
            # Collect satellite data
            satellite_data = self._collect_satellite_data_for_location(
                latitude, longitude, location_name, days_back_satellite
            )

            if not satellite_data.empty:
                results['satellite'] = satellite_data
                self.logger.info(f"✅ Collected {len(satellite_data)} satellite records for {location_name}")

            # Collect weather data
            weather_data = self._collect_weather_data_for_location(
                latitude, longitude, location_name, days_back_weather
            )

            if not weather_data.empty:
                results['weather'] = weather_data
                self.logger.info(f"✅ Collected {len(weather_data)} weather records for {location_name}")

        except Exception as e:
            self.logger.error(f"❌ Failed to collect data for {location_name}: {e}")

        return results

    def _collect_satellite_data_for_location(
        self,
        latitude: float,
        longitude: float,
        location_name: str,
        days_back: int
    ) -> pd.DataFrame:
        """Collect satellite data using GEE client"""
        try:
            from .gee_client import GEEClient

            gee_client = GEEClient()

            if not gee_client.initialize():
                return pd.DataFrame()

            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            satellite_data = gee_client.get_satellite_data_for_location(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                data_types=['ndvi', 'evi']
            )

            if not satellite_data.empty:
                satellite_data['location_name'] = location_name

                # Store in database
                self._store_satellite_data(satellite_data)

            return satellite_data

        except Exception as e:
            self.logger.error(f"Failed to collect satellite data: {e}")
            return pd.DataFrame()

    def _collect_weather_data_for_location(
        self,
        latitude: float,
        longitude: float,
        location_name: str,
        days_forecast: int
    ) -> pd.DataFrame:
        """Collect weather data using OpenWeather client"""
        try:
            from .weather_client import OpenWeatherClient

            weather_client = OpenWeatherClient()

            # Get current and forecast weather
            weather_data = weather_client.get_current_and_forecast_weather(latitude, longitude)

            if not weather_data.empty:
                weather_data['location_name'] = location_name

                # Calculate agricultural indices
                weather_data = weather_client._calculate_agricultural_indices(weather_data)

                # Store in database
                self._store_weather_data(weather_data)

            return weather_data

        except Exception as e:
            self.logger.error(f"Failed to collect weather data: {e}")
            return pd.DataFrame()

    def collect_north_india_data(
        self,
        data_types: List[str] = None,
        max_workers: int = 3
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Collect data for all North India state capitals

        Args:
            data_types: List of data types to collect ('satellite', 'weather')
            max_workers: Maximum number of concurrent requests

        Returns:
            Nested dictionary: location -> data_type -> DataFrame
        """
        if data_types is None:
            data_types = ['satellite', 'weather']

        results = {}
        locations_to_process = []

        # Prepare locations for processing
        for state_info in self.north_india_config.get('states', []):
            location_name = state_info['capital']
            lat, lon = state_info['lat'], state_info['lon']

            locations_to_process.append({
                'name': location_name,
                'lat': lat,
                'lon': lon,
                'state': state_info.get('state', 'Unknown')
            })

        # Process locations with controlled concurrency
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_location = {}

            for location in locations_to_process:
                future = executor.submit(
                    self._process_single_location,
                    location,
                    data_types
                )
                future_to_location[future] = location['name']

            # Collect results
            for future in as_completed(future_to_location):
                location_name = future_to_location[future]

                try:
                    location_data = future.result()
                    if location_data:
                        results[location_name] = location_data
                        self.logger.info(f"✅ Completed data collection for {location_name}")

                except Exception as e:
                    self.logger.error(f"❌ Failed to collect data for {location_name}: {e}")

        # Log summary
        locations_processed = len(results)
        total_records = sum(
            len(data_df) for location_data in results.values()
            for data_df in location_data.values()
        )

        self.logger.info(f"📊 North India data collection complete: {locations_processed} locations, {total_records} total records")

        return results

    def _process_single_location(self, location: Dict, data_types: List[str]) -> Dict[str, pd.DataFrame]:
        """Process data collection for a single location"""
        location_name = location['name']
        lat, lon = location['lat'], location['lon']

        return self.collect_all_data_for_location(
            latitude=lat,
            longitude=lon,
            location_name=location_name
        )

    def _store_satellite_data(self, df: pd.DataFrame):
        """Store satellite data in database"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                df.to_sql('satellite_data', conn, if_exists='append', index=False)
        except Exception as e:
            self.logger.error(f"Failed to store satellite data: {e}")

    def _store_weather_data(self, df: pd.DataFrame):
        """Store weather data in database"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                df.to_sql('weather_data', conn, if_exists='append', index=False)
        except Exception as e:
            self.logger.error(f"Failed to store weather data: {e}")

    def get_historical_data(
        self,
        location_name: str,
        data_type: str = 'weather',
        days_back: int = 30
    ) -> pd.DataFrame:
        """
        Retrieve historical data from database

        Args:
            location_name: Location name
            data_type: Type of data ('satellite' or 'weather')
            days_back: Days of historical data to retrieve

        Returns:
            DataFrame with historical data
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).date()

            with sqlite3.connect(str(self.db_path)) as conn:
                if data_type == 'satellite':
                    query = '''
                        SELECT * FROM satellite_data
                        WHERE location_name = ? AND date >= ?
                        ORDER BY date DESC
                    '''
                    df = pd.read_sql_query(query, conn, params=[location_name, cutoff_date])

                elif data_type == 'weather':
                    query = '''
                        SELECT * FROM weather_data
                        WHERE location_name = ? AND date(timestamp) >= ?
                        ORDER BY timestamp DESC
                    '''
                    df = pd.read_sql_query(query, conn, params=[location_name, cutoff_date])

                else:
                    return pd.DataFrame()

                # Parse dates
                if data_type == 'satellite' and 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                elif data_type == 'weather' and 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['date'] = df['timestamp'].dt.date

                return df

        except Exception as e:
            self.logger.error(f"Failed to retrieve historical {data_type} data: {e}")
            return pd.DataFrame()

    def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate data quality report for the pipeline"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Satellite data quality
                satellite_stats = pd.read_sql_query('''
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT location_name) as locations_covered,
                        COUNT(DISTINCT date) as unique_dates,
                        AVG(ndvi) as avg_ndvi,
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date
                    FROM satellite_data
                ''', conn).iloc[0].to_dict()

                # Weather data quality
                weather_stats = pd.read_sql_query('''
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT location_name) as locations_covered,
                        COUNT(DISTINCT date(timestamp)) as unique_dates,
                        AVG(temp) as avg_temp,
                        AVG(humidity) as avg_humidity,
                        MIN(timestamp) as earliest_timestamp,
                        MAX(timestamp) as latest_timestamp
                    FROM weather_data
                ''', conn).iloc[0].to_dict()

                # Missing data analysis
                missing_satellite = pd.read_sql_query('''
                    SELECT
                        location_name,
                        COUNT(*) as total_records,
                        SUM(CASE WHEN ndvi IS NULL THEN 1 ELSE 0 END) as missing_ndvi,
                        SUM(CASE WHEN evi IS NULL THEN 1 ELSE 0 END) as missing_evi
                    FROM satellite_data
                    GROUP BY location_name
                ''', conn)

                missing_weather = pd.read_sql_query('''
                    SELECT
                        location_name,
                        COUNT(*) as total_records,
                        SUM(CASE WHEN temp IS NULL THEN 1 ELSE 0 END) as missing_temp,
                        SUM(CASE WHEN humidity IS NULL THEN 1 ELSE 0 END) as missing_humidity
                    FROM weather_data
                    GROUP BY location_name
                ''', conn)

            report = {
                'satellite_data': {
                    'total_records': satellite_stats['total_records'],
                    'locations_covered': satellite_stats['locations_covered'],
                    'date_range': {
                        'earliest': satellite_stats.get('earliest_date'),
                        'latest': satellite_stats.get('latest_date')
                    },
                    'average_ndvi': satellite_stats.get('avg_ndvi'),
                    'missing_data_summary': missing_satellite.to_dict('records')
                },
                'weather_data': {
                    'total_records': weather_stats['total_records'],
                    'locations_covered': weather_stats['locations_covered'],
                    'date_range': {
                        'earliest': weather_stats.get('earliest_timestamp'),
                        'latest': weather_stats.get('latest_timestamp')
                    },
                    'average_temp': weather_stats.get('avg_temp'),
                    'average_humidity': weather_stats.get('avg_humidity'),
                    'missing_data_summary': missing_weather.to_dict('records')
                },
                'generated_at': datetime.now().isoformat()
            }

            return report

        except Exception as e:
            self.logger.error(f"Failed to generate quality report: {e}")
            return {'error': str(e)}

    def run_scheduled_data_refresh(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Run scheduled data refresh based on configuration

        Args:
            force_refresh: Force refresh regardless of timing

        Returns:
            Dictionary with refresh results
        """
        self.logger.info("🔄 Starting scheduled data refresh...")

        results = {
            'satellite_refresh': False,
            'weather_refresh': False,
            'locations_processed': 0,
            'total_records_collected': 0,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Check if refresh is needed (based on config intervals)
            config = self.data_refresh_config

            need_satellite_refresh = force_refresh or self._should_refresh_data(
                'satellite_data',
                config.get('satellite_data_hourly', 6) * 3600  # Convert hours to seconds
            )

            need_weather_refresh = force_refresh or self._should_refresh_data(
                'weather_data',
                config.get('weather_forecast_daily', 24) * 3600
            )

            if need_satellite_refresh:
                # Refresh satellite data
                satellite_results = self.collect_north_india_data(['satellite'])
                results['satellite_refresh'] = True
                results['locations_processed'] += len(satellite_results)
                results['total_records_collected'] += sum(
                    len(data['satellite']) for data in satellite_results.values() if 'satellite' in data
                )

            if need_weather_refresh:
                # Refresh weather data
                weather_results = self.collect_north_india_data(['weather'])
                results['weather_refresh'] = True
                results['locations_processed'] += len(weather_results)
                results['total_records_collected'] += sum(
                    len(data['weather']) for data in weather_results.values() if 'weather' in data
                )

            self.logger.info("✅ Scheduled data refresh completed")

        except Exception as e:
            error_msg = f"Scheduled refresh failed: {e}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)

        return results

    def _should_refresh_data(self, data_table: str, max_age_seconds: int) -> bool:
        """Check if data should be refreshed based on age"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                if data_table == 'satellite_data':
                    query = "SELECT MAX(collected_at) as latest_update FROM satellite_data"
                else:
                    query = "SELECT MAX(collected_at) as latest_update FROM weather_data"

                result = pd.read_sql_query(query, conn)

                if result.empty or result.iloc[0]['latest_update'] is None:
                    return True  # No data exists, refresh needed

                latest_update = datetime.fromisoformat(result.iloc[0]['latest_update'])
                age_seconds = (datetime.now() - latest_update).total_seconds()

                return age_seconds > max_age_seconds

        except Exception as e:
            self.logger.warning(f"Failed to check data age: {e}")
            return True  # Refresh on error to be safe


class DataCacheManager:
    """Manages data caching to avoid redundant API calls"""

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, location: str, data_type: str, date: str) -> str:
        """Generate cache key for data request"""
        return f"{location}_{data_type}_{date}.pkl"

    def is_cached(self, cache_key: str) -> bool:
        """Check if data is cached"""
        cache_file = self.cache_dir / cache_key
        return cache_file.exists()

    def save_to_cache(self, cache_key: str, data: pd.DataFrame):
        """Save data to cache"""
        try:
            cache_file = self.cache_dir / cache_key
            data.to_pickle(cache_file)
            return True
        except Exception:
            return False

    def load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Load data from cache"""
        try:
            cache_file = self.cache_dir / cache_key
            if cache_file.exists():
                return pd.read_pickle(cache_file)
        except Exception:
            pass
        return None

    def clear_old_cache(self, max_age_days: int = 7):
        """Clear cache files older than max_age_days"""
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

            for cache_file in self.cache_dir.glob("*.pkl"):
                if cache_file.stat().st_mtime < cutoff_time:
                    cache_file.unlink()

        except Exception:
            pass


def test_unified_pipeline():
    """Test the unified data pipeline"""
    print("🔄 Testing Unified Data Pipeline...")

    pipeline = UnifiedDataPipeline()

    # Test database setup
    try:
        pipeline._setup_database()
        print("✅ Database setup successful")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return

    # Test data quality report
    try:
        quality_report = pipeline.get_data_quality_report()
        if 'error' not in quality_report:
            print("✅ Data quality report generated")
            print(f"   Satellite records: {quality_report.get('satellite_data', {}).get('total_records', 0)}")
            print(f"   Weather records: {quality_report.get('weather_data', {}).get('total_records', 0)}")
        else:
            print("ℹ️  No data in database yet (expected for first run)")
    except Exception as e:
        print(f"❌ Data quality report failed: {e}")

    print("🎉 Pipeline test completed")


if __name__ == "__main__":
    test_unified_pipeline()
