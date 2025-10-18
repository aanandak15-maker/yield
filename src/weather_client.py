#!/usr/bin/env python3
"""
OpenWeather API Client for Crop Yield Prediction

Retrieves weather data including temperature, precipitation, humidity,
and wind data for agricultural weather monitoring and yield prediction.
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

class OpenWeatherClient:
    """OpenWeather API client for weather data retrieval"""

    def __init__(self, config_path: str = "config/api_config.json"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._load_config()
        self._session = requests.Session()
        self._api_key = None

    def _load_config(self):
        """Load OpenWeather configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            self.weather_config = config.get('openweather', {})
            self.data_refresh = config.get('data_refresh', {})
            self.north_india_bounds = config.get('north_india_region', {})

        except Exception as e:
            self.logger.error(f"Failed to load weather config: {e}")
            self.weather_config = {}
            self.data_refresh = {}
            self.north_india_bounds = {}

    def _get_api_key(self) -> str:
        """Get OpenWeather API key"""
        if self._api_key is None:
            try:
                from .api_credentials import get_credentials_manager
            except ImportError:
                from api_credentials import get_credentials_manager

            credentials_manager = get_credentials_manager()
            if not credentials_manager.load_credentials():
                raise RuntimeError("Failed to load credentials")

            ow_creds = credentials_manager.get_openweather_credentials()
            self._api_key = ow_creds['api_key']

        except Exception as e:
            self.logger.error(f"Failed to get API key: {e}")
            raise

        return self._api_key

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to OpenWeather API"""
        if params is None:
            params = {}

        # Add API key to params
        params['appid'] = self._get_api_key()

        base_url = self.weather_config.get('base_url', 'https://api.openweathermap.org/data')
        endpoint_path = self.weather_config.get('endpoints', {}).get(endpoint, endpoint)

        url = f"{base_url}/{endpoint_path}"

        try:
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"OpenWeather API request failed: {e}")
            raise

    def get_current_weather(self, lat: float, lon: float, units: str = 'metric') -> Dict:
        """
        Get current weather conditions for a location

        Args:
            lat: Latitude
            lon: Longitude
            units: Units (metric, imperial, kelvin)

        Returns:
            Weather data dictionary
        """
        params = {
            'lat': lat,
            'lon': lon,
            'units': units
        }

        return self._make_request('current', params)

    def get_weather_forecast(self, lat: float, lon: float, units: str = 'metric') -> Dict:
        """
        Get 5-day weather forecast for a location

        Args:
            lat: Latitude
            lon: Longitude
            units: Units (metric, imperial, kelvin)

        Returns:
            Forecast data dictionary
        """
        params = {
            'lat': lat,
            'lon': lon,
            'units': units
        }

        return self._make_request('forecast', params)

    def get_historical_weather(
        self,
        lat: float,
        lon: float,
        start_date: Union[str, datetime],
        end_date: Optional[Union[str, datetime]] = None,
        units: str = 'metric'
    ) -> pd.DataFrame:
        """
        Get historical weather data for a location and date range

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date (YYYY-MM-DD or datetime object)
            end_date: End date (YYYY-MM-DD or datetime object, defaults to today)
            units: Units (metric, imperial, kelvin)

        Returns:
            DataFrame with historical weather data
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # OpenWeather free tier only provides 5 days of historical data
        # For longer periods, we need to implement batching
        if (end_date - start_date).days > 5:
            self.logger.warning("OpenWeather free tier limited to 5 days of historical data")
            end_date = start_date + timedelta(days=5)

        # Convert dates to Unix timestamps
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())

        params = {
            'lat': lat,
            'lon': lon,
            'type': 'hour',
            'start': start_ts,
            'end': end_ts,
            'units': units
        }

        try:
            data = self._make_request('history', params)

            # Process the response into a DataFrame
            if 'list' in data:
                weather_records = []

                for record in data['list']:
                    weather_data = record.get('main', {})
                    wind_data = record.get('wind', {})
                    weather_condition = record.get('weather', [{}])[0] if record.get('weather') else {}

                    processed_record = {
                        'timestamp': datetime.fromtimestamp(record['dt']),
                        'date': datetime.fromtimestamp(record['dt']).date(),
                        'temp': weather_data.get('temp'),
                        'temp_feels_like': weather_data.get('feels_like'),
                        'temp_min': weather_data.get('temp_min'),
                        'temp_max': weather_data.get('temp_max'),
                        'pressure': weather_data.get('pressure'),
                        'humidity': weather_data.get('humidity'),
                        'visibility': record.get('visibility'),
                        'wind_speed': wind_data.get('speed'),
                        'wind_deg': wind_data.get('deg'),
                        'wind_gust': wind_data.get('gust'),
                        'clouds': record.get('clouds', {}).get('all'),
                        'rain_1h': record.get('rain', {}).get('1h'),
                        'rain_3h': record.get('rain', {}).get('3h'),
                        'snow_1h': record.get('snow', {}).get('1h'),
                        'snow_3h': record.get('snow', {}).get('3h'),
                        'weather_main': weather_condition.get('main'),
                        'weather_description': weather_condition.get('description'),
                        'latitude': lat,
                        'longitude': lon
                    }

                    weather_records.append(processed_record)

                df = pd.DataFrame(weather_records)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('timestamp').reset_index(drop=True)

                return df
            else:
                self.logger.warning("No historical weather data returned")
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Failed to get historical weather: {e}")
            return pd.DataFrame()

    def get_current_and_forecast_weather(self, lat: float, lon: float, units: str = 'metric') -> pd.DataFrame:
        """
        Get current weather and 5-day forecast combined

        Args:
            lat: Latitude
            lon: Longitude
            units: Units (metric, imperial, kelvin)

        Returns:
            DataFrame with combined current and forecast data
        """
        dataframes = []

        try:
            # Get current weather
            current_data = self.get_current_weather(lat, lon, units)
            if current_data:
                current_records = self._process_weather_record(current_data, is_current=True)
                if current_records:
                    dataframes.append(pd.DataFrame([current_records]))

        except Exception as e:
            self.logger.warning(f"Failed to get current weather: {e}")

        try:
            # Get forecast weather
            forecast_data = self.get_weather_forecast(lat, lon, units)
            if forecast_data and 'list' in forecast_data:
                forecast_records = []
                for record in forecast_data['list']:
                    processed_record = self._process_weather_record({
                        'main': record['main'],
                        'wind': record.get('wind', {}),
                        'weather': record.get('weather', []),
                        'clouds': record.get('clouds', {}),
                        'rain': record.get('rain', {}),
                        'snow': record.get('snow', {}),
                        'dt': record['dt'],
                        'visibility': record.get('visibility')
                    }, is_current=False)
                    if processed_record:
                        forecast_records.append(processed_record)

                if forecast_records:
                    dataframes.append(pd.DataFrame(forecast_records))

        except Exception as e:
            self.logger.warning(f"Failed to get forecast weather: {e}")

        # Combine dataframes
        if dataframes:
            combined_df = pd.concat(dataframes, ignore_index=True)
            combined_df['latitude'] = lat
            combined_df['longitude'] = lon
            combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
            return combined_df
        else:
            return pd.DataFrame()

    def _process_weather_record(self, record: Dict, is_current: bool = False) -> Optional[Dict]:
        """Process a single weather record into standardized format"""
        try:
            weather_data = record.get('main', {})
            wind_data = record.get('wind', {})
            weather_condition = record.get('weather', [{}])[0] if record.get('weather') else {}

            timestamp = datetime.fromtimestamp(record['dt']) if 'dt' in record else datetime.now()

            processed_record = {
                'timestamp': timestamp,
                'date': timestamp.date(),
                'temp': weather_data.get('temp'),
                'temp_feels_like': weather_data.get('feels_like'),
                'temp_min': weather_data.get('temp_min'),
                'temp_max': weather_data.get('temp_max'),
                'pressure': weather_data.get('pressure'),
                'humidity': weather_data.get('humidity'),
                'visibility': record.get('visibility'),
                'wind_speed': wind_data.get('speed'),
                'wind_deg': wind_data.get('deg'),
                'wind_gust': wind_data.get('gust'),
                'clouds': record.get('clouds', {}).get('all'),
                'rain_1h': record.get('rain', {}).get('1h'),
                'rain_3h': record.get('rain', {}).get('3h'),
                'snow_1h': record.get('snow', {}).get('1h'),
                'snow_3h': record.get('snow', {}).get('3h'),
                'weather_main': weather_condition.get('main'),
                'weather_description': weather_condition.get('description'),
                'is_current': is_current,
                'data_source': 'openweather'
            }

            return processed_record

        except Exception as e:
            self.logger.error(f"Failed to process weather record: {e}")
            return None

    def get_agricultural_weather_index(
        self,
        lat: float,
        lon: float,
        start_date: Union[str, datetime],
        end_date: Optional[Union[str, datetime]] = None
    ) -> pd.DataFrame:
        """
        Calculate agricultural weather indices from weather data

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            DataFrame with weather data and calculated indices
        """
        # Get basic weather data
        weather_df = self.get_current_and_forecast_weather(lat, lon)

        if weather_df.empty:
            return pd.DataFrame()

        # Calculate agricultural indices
        weather_df = self._calculate_agricultural_indices(weather_df)

        return weather_df

    def _calculate_agricultural_indices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate agricultural weather indices from raw weather data"""
        df = df.copy()

        # Growing Degree Days (GDD) - simplified base temperature of 10°C
        if 'temp' in df.columns:
            base_temp = 10.0
            df['gdd_daily'] = np.maximum(0, df['temp'] - base_temp).fillna(0)
            df['gdd_cumulative'] = df['gdd_daily'].cumsum()

        # Heat stress indicators
        if 'temp_max' in df.columns:
            df['heat_stress'] = (df['temp_max'] > 30).astype(int)  # Days > 30°C
            df['extreme_heat'] = (df['temp_max'] > 35).astype(int)  # Days > 35°C

        # Cold stress indicators
        if 'temp_min' in df.columns:
            df['cold_stress'] = (df['temp_min'] < 5).astype(int)  # Days < 5°C

        # Precipitation indices
        if 'rain_1h' in df.columns:
            df['rain_1h'] = df['rain_1h'].fillna(0)
            df['rain_3h'] = df['rain_3h'].fillna(0)
            df['total_rain'] = df['rain_1h'] + df['rain_3h']

        # Accumulated rainfall over 7 days (running sum)
        if 'total_rain' in df.columns:
            df['rain_7d_sum'] = df['total_rain'].fillna(0).rolling(window=7, min_periods=1).sum()

        # Humidity indices (good range is typically 40-70%)
        if 'humidity' in df.columns:
            df['optimal_humidity'] = ((df['humidity'] >= 40) & (df['humidity'] <= 70)).astype(int)
            df['low_humidity'] = (df['humidity'] < 30).astype(int)
            df['high_humidity'] = (df['humidity'] > 80).astype(int)

        # Wind damage potential (sustained winds > 15 km/h are concerning)
        if 'wind_speed' in df.columns:
            df['wind_damage_risk'] = (df['wind_speed'] > 15).astype(int)

        # Combined weather stress index
        stress_factors = []
        if 'heat_stress' in df.columns:
            stress_factors.append(df['heat_stress'])
        if 'cold_stress' in df.columns:
            stress_factors.append(df['cold_stress'])
        if 'wind_damage_risk' in df.columns:
            stress_factors.append(df['wind_damage_risk'])

        if stress_factors:
            df['weather_stress_index'] = sum(stress_factors) / len(stress_factors)

        return df

    def get_north_india_weather_data(self, days_forecast: int = 7) -> Dict[str, pd.DataFrame]:
        """
        Get weather data for all North India state capitals

        Args:
            days_forecast: Number of days to forecast

        Returns:
            Dictionary with location names as keys and DataFrames as values
        """
        results = {}

        # Get forecast data for each state capital
        for state_info in self.north_india_bounds.get('states', []):
            location_name = state_info['capital']
            lat, lon = state_info['lat'], state_info['lon']

            self.logger.info(f"🌤️  Getting weather data for {location_name}...")

            try:
                # Get combined current weather and forecast
                weather_data = self.get_current_and_forecast_weather(lat, lon)

                if not weather_data.empty:
                    weather_data['location'] = location_name
                    weather_data['state'] = state_info.get('state', 'Unknown')

                    # Calculate agricultural indices
                    weather_data = self._calculate_agricultural_indices(weather_data)

                    results[location_name] = weather_data
                    self.logger.info(f"✅ Retrieved {len(weather_data)} weather records for {location_name}")

            except Exception as e:
                self.logger.error(f"❌ Failed to get weather data for {location_name}: {e}")

        return results

    def get_crop_specific_weather_alerts(
        self,
        weather_df: pd.DataFrame,
        crop_type: str = 'rice'
    ) -> List[Dict]:
        """
        Generate crop-specific weather alerts from weather data

        Args:
            weather_df: Weather DataFrame
            crop_type: Type of crop (rice, wheat, maize)

        Returns:
            List of alert dictionaries
        """
        alerts = []

        if weather_df.empty:
            return alerts

        # Crop-specific thresholds
        thresholds = {
            'rice': {
                'heat_temp': 35,
                'cold_temp': 10,
                'rain_min_weekly': 25,
                'humidity_min': 40,
                'humidity_max': 80
            },
            'wheat': {
                'heat_temp': 30,
                'cold_temp': 0,
                'rain_min_weekly': 20,
                'humidity_min': 35,
                'humidity_max': 75
            },
            'maize': {
                'heat_temp': 40,
                'cold_temp': 8,
                'rain_min_weekly': 30,
                'humidity_min': 45,
                'humidity_max': 85
            }
        }

        crop_thresholds = thresholds.get(crop_type, thresholds['rice'])

        # Check each record for alerts
        for _, row in weather_df.iterrows():
            record_alerts = []

            # Temperature alerts
            if pd.notna(row.get('temp_max')) and row['temp_max'] > crop_thresholds['heat_temp']:
                record_alerts.append({
                    'type': 'heat_stress',
                    'severity': 'high',
                    'message': f"Heat stress risk - max temp {row['temp_max']:.1f}°C exceeds {crop_thresholds['heat_temp']}°C threshold",
                    'timestamp': row['timestamp'],
                    'metric': 'temperature'
                })

            if pd.notna(row.get('temp_min')) and row['temp_min'] < crop_thresholds['cold_temp']:
                record_alerts.append({
                    'type': 'cold_stress',
                    'severity': 'medium',
                    'message': f"Cold stress risk - min temp {row['temp_min']:.1f}°C below {crop_thresholds['cold_temp']}°C threshold",
                    'timestamp': row['timestamp'],
                    'metric': 'temperature'
                })

            # Humidity alerts
            if pd.notna(row.get('humidity')):
                if row['humidity'] < crop_thresholds['humidity_min']:
                    record_alerts.append({
                        'type': 'low_humidity',
                        'severity': 'medium',
                        'message': f"Low humidity {row['humidity']:.1f}% below {crop_thresholds['humidity_min']}% optimal range",
                        'timestamp': row['timestamp'],
                        'metric': 'humidity'
                    })
                elif row['humidity'] > crop_thresholds['humidity_max']:
                    record_alerts.append({
                        'type': 'high_humidity',
                        'severity': 'low',
                        'message': f"High humidity {row['humidity']:.1f}% above {crop_thresholds['humidity_max']}% optimal range",
                        'timestamp': row['timestamp'],
                        'metric': 'humidity'
                    })

            # Precipitation alerts
            if pd.notna(row.get('total_rain')) and row['total_rain'] > 50:  # Heavy rain
                record_alerts.append({
                    'type': 'heavy_rain',
                    'severity': 'medium',
                    'message': f"Heavy rainfall {row['total_rain']:.1f}mm may cause flooding or lodging",
                    'timestamp': row['timestamp'],
                    'metric': 'precipitation'
                })

            if pd.notna(row.get('wind_speed')) and row['wind_speed'] > 20:
                record_alerts.append({
                    'type': 'high_wind',
                    'severity': 'medium',
                    'message': f"High wind speeds {row['wind_speed']:.1f} km/h may cause physical damage",
                    'timestamp': row['timestamp'],
                    'metric': 'wind'
                })

            alerts.extend(record_alerts)

        return alerts


def test_weather_client():
    """Test OpenWeather client functionality"""
    print("🌤️  Testing OpenWeather Client...")

    client = OpenWeatherClient()

    # Test with sample location (Bhopal)
    lat, lon = 23.25, 77.42

    try:
        # Test current weather
        print(f"📍 Testing current weather for Bhopal ({lat}, {lon})")
        current_weather = client.get_current_weather(lat, lon)
        print("✅ Current weather retrieved successfully")
        print(".2f")

    except Exception as e:
        print(".2f")
        return

    try:
        # Test forecast
        forecast_weather = client.get_weather_forecast(lat, lon)
        if forecast_weather and 'list' in forecast_weather:
            print(f"✅ Forecast retrieved: {len(forecast_weather['list'])} records")

        # Test combined current + forecast
        combined_data = client.get_current_and_forecast_weather(lat, lon)
        if not combined_data.empty:
            print(f"✅ Combined weather data: {len(combined_data)} records")
            print("\nSample combined data:")
            print(combined_data.head()[['timestamp', 'temp', 'humidity', 'wind_speed', 'total_rain']].to_string())

    except Exception as e:
        print(f"❌ Weather client test failed: {e}")


if __name__ == "__main__":
    test_weather_client()
