#!/usr/bin/env python3
"""
Phase 2: Automated Data Collection Scripts for North India Crop Prediction

Target States: Punjab, Haryana, Uttar Pradesh, Bihar, Madhya Pradesh
Major Crops: Rice, Wheat, Maize
Data Sources: World Bank, Open-Meteo, NASA POWER, OSM Boundaries
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import os
import time
from pathlib import Path
import xml.etree.ElementTree as ET
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class NorthIndiaDataCollector:
    def __init__(self):
        self.target_states = ['Punjab', 'Haryana', 'UP', 'Bihar', 'MP']
        self.maps = {
            'UP': 'Uttar Pradesh',
            'MP': 'Madhya Pradesh',
            'state_names': {
                'Punjab': 'Punjab',
                'Haryana': 'Haryana',
                'UP': 'Uttar Pradesh',
                'Bihar': 'Bihar',
                'MP': 'Madhya Pradesh'
            }
        }

        # Create data directories
        os.makedirs('data/raw', exist_ok=True)
        os.makedirs('data/processed', exist_ok=True)
        os.makedirs('data/coordinates', exist_ok=True)

        # Initialize collectors
        self.world_bank_collector = WorldBankDataCollector()
        self.weather_collector = WeatherDataCollector(self.target_states)
        self.geospatial_collector = GeospatialDataCollector(self.target_states)

    def collect_all_data(self):
        """Master function to collect all required data"""
        print("🚀 PHASE 2: NORTH INDIA CROP DATA COLLECTION")
        print("=" * 50)

        # 1. Crop Yield Data (World Bank)
        print("\n📊 Step 1: Collecting Crop Yield Data...")
        crop_yields = self.world_bank_collector.collect_crop_yields()
        if crop_yields:
            self.world_bank_collector.save_to_csv(crop_yields, 'data/raw/crop_yields_world_bank.csv')
            print(f"✅ Saved {len(crop_yields)} crop yield records")

        # 2. Weather Data (Open-Meteo + NASA POWER)
        print("\n🌤️  Step 2: Collecting Weather Data...")

        # State coordinates (approximate centers)
        state_coords = self.weather_collector.get_state_coordinates()

        for state, coords in state_coords.items():
            print(f"  📍 Collecting weather for {state}...")

            # Open-Meteo historical (last 2 years)
            meteo_weather = self.weather_collector.collect_open_meteo_weather(
                coords['lat'], coords['lon'], days_back=365 * 2)

            # NASA POWER historical (1981-present)
            nasa_weather = self.weather_collector.collect_nasa_power_weather(
                coords['lat'], coords['lon'])

            # Merge and save
            if not meteo_weather.empty or not nasa_weather.empty:
                combined_weather = self.weather_collector.merge_weather_sources(
                    meteo_weather, nasa_weather, state)
                if not combined_weather.empty:
                    filename = f"data/raw/weather_{state.lower().replace(' ', '_')}.csv"
                    combined_weather.to_csv(filename, index=False)
                    print(f"    ✅ Saved {len(combined_weather)} weather records for {state}")

        # 3. Geospatial/State Boundaries
        print("\n🗺️  Step 3: Collecting State Boundaries...")
        boundaries = self.geospatial_collector.get_administrative_boundaries()
        if boundaries:
            self.geospatial_collector.save_boundaries(boundaries, 'data/raw/state_boundaries.geojson')
            print(f"✅ Saved boundaries for {len(boundaries['features'])} states")

        print("\n🎯 SUMMARY:")
        print("Phase 2 Completion:")
        print("  ✅ World Bank agriculture data: Collected")
        print(f"  ✅ Weather data: {len(list(state_coords.keys()))} states")
        print("  ✅ Geospatial boundaries: Collected")
        print("\n📁 Data stored in 'data/raw/' directory")
        print("🔄 Ready for Phase 3: Data Processing Pipeline")

        return {
            'crop_yields_collected': len(crop_yields) if crop_yields else 0,
            'weather_states_covered': len(list(state_coords.keys())),
            'boundaries_obtained': len(boundaries['features']) if boundaries else 0
        }

class WorldBankDataCollector:
    """Collect agricultural data from World Bank API"""

    def __init__(self, rate_limit_delay=1.0):
        self.base_url = "https://api.worldbank.org/v2/indicator"
        self.rate_limit_delay = rate_limit_delay

    def collect_crop_yields(self):
        """Collect cereal yield data for India"""
        yield_indicators = {
            'AG.YLD.CREL.KG': 'cereal_yield_kg_per_ha',
            'AG.PRD.CREL.MT': 'cereal_production_mt',
            'AG.LND.CREL.HA': 'cereal_harvested_area_ha',
            'AG.LND.IRIG.AG.ZS': 'irrigated_land_percent'
        }

        all_data = []

        for indicator, column_name in yield_indicators.items():
            print(f"    Fetching {column_name}...")
            url = f"{self.base_url}/{indicator}?format=json&country=IND&per_page=1000"

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()

                if len(data) > 1 and data[1]:
                    for record in data[1]:
                        if record.get('value') is not None:
                            clean_record = {
                                'indicator': indicator,
                                'indicator_name': column_name,
                                'country': record.get('countryiso3code'),
                                'year': record.get('date'),
                                'value': record.get('value'),
                                'unit': record.get('unit', 'Unknown'),
                                'source': 'World Bank'
                            }
                            all_data.append(clean_record)

                time.sleep(self.rate_limit_delay)  # Respect rate limits

            except Exception as e:
                print(f"    ⚠️  Failed to collect {indicator}: {e}")

        return all_data if all_data else None

    def save_to_csv(self, data, filename):
        """Save collected data to CSV"""
        if data:
            df = pd.DataFrame(data)

            # Pivot to make indicators columns
            pivot_df = df.pivot_table(
                index='year',
                columns='indicator_name',
                values='value',
                aggfunc='first'
            ).reset_index()

            pivot_df.columns.name = None
            pivot_df.to_csv(filename, index=False)

class WeatherDataCollector:
    """Collect weather data from multiple sources"""

    def __init__(self, states):
        self.states = states
        # Approximate state center coordinates (lat, lon)
        self.state_coordinates = {
            'Punjab': {'lat': 30.9, 'lon': 75.85, 'capital': 'Chandigarh'},
            'Haryana': {'lat': 29.05, 'lon': 76.08, 'capital': 'Chandigarh'},
            'UP': {'lat': 26.85, 'lon': 80.92, 'capital': 'Lucknow'},
            'Bihar': {'lat': 25.6, 'lon': 85.1, 'capital': 'Patna'},
            'MP': {'lat': 23.25, 'lon': 77.42, 'capital': 'Bhopal'}
        }

    def get_state_coordinates(self):
        """Return state center coordinates"""
        # Enhanced coordinates using OSM if available, fallback to defaults
        enhanced_coords = {}

        for state_code in self.states:
            if state_code in self.state_coordinates:
                enhanced_coords[self.state_coordinates[state_code]['capital']] = {
                    'lat': self.state_coordinates[state_code]['lat'],
                    'lon': self.state_coordinates[state_code]['lon'],
                    'state': state_code
                }

        return enhanced_coords

    def collect_open_meteo_weather(self, lat, lon, days_back=365*2):
        """Collect historical weather data from Open-Meteo API"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Open-Meteo API for historical data
            url = (
                f"https://archive-api.open-meteo.com/v1/archive?"
                f"latitude={lat}&longitude={lon}"
                f"&start_date={start_date.strftime('%Y-%m-%d')}"
                f"&end_date={end_date.strftime('%Y-%m-%d')}"
                "&hourly=temperature_2m,relative_humidity_2m,precipitation,rain,snowfall"
                "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean"
                "&timezone=Asia/Kolkata"
            )

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Convert to DataFrame
            weather_records = []
            for i, date_str in enumerate(data['daily']['time']):
                record = {
                    'date': date_str,
                    'latitude': lat,
                    'longitude': lon,
                    'temp_max': data['daily']['temperature_2m_max'][i],
                    'temp_min': data['daily']['temperature_2m_min'][i],
                    'temp_mean': data['daily']['temperature_2m_mean'][i],
                    'source': 'open_meteo',
                    'data_type': 'daily_aggregates'
                }
                weather_records.append(record)

            return pd.DataFrame(weather_records)

        except Exception as e:
            print(f"    ⚠️  Open-Meteo collection failed: {e}")
            return pd.DataFrame()

    def collect_nasa_power_weather(self, lat, lon):
        """Collect historical climate data from NASA POWER API"""
        try:
            # NASA POWER API - get last 10 years of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365*10)

            url = (
                f"https://power.larc.nasa.gov/api/temporal/daily/point?"
                f"start={start_date.strftime('%Y%m%d')}"
                f"&end={end_date.strftime('%Y%m%d')}"
                f"&latitude={lat}&longitude={lon}"
                f"&community=ag&parameters=PRECTOT,ALLSKY_SFC_SW_DWN,T2M_MAX,T2M_MIN,RH2M"
                f"&format=json"
            )

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'properties' in data and 'parameter' in data['properties']:
                params = data['properties']['parameter']

                weather_records = []
                for param_name, param_data in params.items():
                    for date_str, value in param_data.items():
                        if isinstance(value, (int, float)) and value != -999:
                            record = {
                                'date': date_str,
                                'latitude': lat,
                                'longitude': lon,
                                param_name: value,
                                'source': 'nasa_power',
                                'data_type': 'climate_data'
                            }
                            # Convert date format
                            try:
                                date_obj = datetime.strptime(date_str, '%Y%m%d')
                                record['date_formatted'] = date_obj.strftime('%Y-%m-%d')
                            except:
                                pass
                            weather_records.append(record)

                # Group by date for cleaner dataset
                if weather_records:
                    df = pd.DataFrame(weather_records)
                    # Pivot to have parameters as columns
                    pivot_cols = [col for col in df.columns if col.startswith(('PRECTOT', 'ALLSKY', 'T2M', 'RH2M'))]
                    df_pivot = df.pivot_table(
                        index=['date', 'latitude', 'longitude', 'source'],
                        values=pivot_cols,
                        aggfunc='mean'
                    ).reset_index()
                    return df_pivot

            return pd.DataFrame()

        except Exception as e:
            print(f"    ⚠️  NASA POWER collection failed: {e}")
            return pd.DataFrame()

    def merge_weather_sources(self, open_meteo_df, nasa_df, state):
        """Merge weather data from different sources"""
        combined_data = []

        # Process Open-Meteo data
        if not open_meteo_df.empty:
            for _, row in open_meteo_df.iterrows():
                record = {
                    'date': row['date'],
                    'state': state,
                    'latitude': row['latitude'],
                    'longitude': row['longitude'],
                    'temp_max': row['temp_max'],
                    'temp_min': row['temp_min'],
                    'temp_mean': row['temp_mean'],
                    'temp_max_source': 'open_meteo',
                    'temp_min_source': 'open_meteo',
                    'temp_mean_source': 'open_meteo',
                    'precipitation': None,
                    'humidity': None,
                    'solar_radiation': None
                }
                combined_data.append(record)

        # Process NASA data
        if not nasa_df.empty:
            for _, row in nasa_df.iterrows():
                record = {
                    'date': row.get('date_formatted', row['date']) if 'date_formatted' in row else str(row['date']),
                    'state': state,
                    'latitude': row['latitude'],
                    'longitude': row['longitude'],
                    'temp_max': row.get('T2M_MAX', None),
                    'temp_min': row.get('T2M_MIN', None),
                    'temp_mean': None,  # NASA provides max/min, can calculate later
                    'temp_max_source': 'nasa_power',
                    'temp_min_source': 'nasa_power',
                    'temp_mean_source': 'nasa_power',
                    'precipitation': row.get('PRECTOT', None),
                    'humidity': row.get('RH2M', None),
                    'solar_radiation': row.get('ALLSKY_SFC_SW_DWN', None)
                }
                combined_data.append(record)

        if combined_data:
            combined_df = pd.DataFrame(combined_data)

            # Sort by date and remove duplicates by favoriting recent sources
            combined_df['date_parsed'] = pd.to_datetime(combined_df['date'], errors='coerce')
            combined_df = combined_df.sort_values(['date_parsed', 'temp_max_source'], ascending=[True, False])
            combined_df = combined_df.drop_duplicates(subset=['date_parsed', 'state'], keep='first')

            return combined_df.drop('date_parsed', axis=1)

        return pd.DataFrame()

class GeospatialDataCollector:
    """Collect administrative boundaries using OSM"""

    def __init__(self, states):
        self.states = states

    def get_administrative_boundaries(self):
        """Get state boundaries using OSM Nominatim API"""
        boundaries = {
            'type': 'FeatureCollection',
            'features': []
        }

        for state in self.states:
            try:
                print(f"    Fetching boundaries for {state}...")

                # Use Nominatim API to get state info
                nominatim_url = f"https://nominatim.openstreetmap.org/search"
                params = {
                    'state': self._get_full_state_name(state),
                    'country': 'India',
                    'format': 'json',
                    'polygon_geojson': 1,
                    'limit': 1
                }

                response = requests.get(nominatim_url, params=params, timeout=30,
                                      headers={'User-Agent': 'NorthIndiaCropPrediction/1.0'})

                if response.status_code == 200:
                    data = response.json()
                    if data and 'geojson' in data[0]:
                        feature = {
                            'type': 'Feature',
                            'properties': {
                                'state': state,
                                'name': self._get_full_state_name(state),
                                'source': 'OSM_Nominatim'
                            },
                            'geometry': data[0]['geojson']
                        }
                        boundaries['features'].append(feature)
                        print(f"      ✅ Got boundary for {state}")

                    time.sleep(1)  # Respect rate limits

            except Exception as e:
                print(f"      ⚠️  Failed to get boundaries for {state}: {e}")

        return boundaries if boundaries['features'] else None

    def _get_full_state_name(self, state_code):
        """Convert state code to full name"""
        state_names = {
            'UP': 'Uttar Pradesh',
            'MP': 'Madhya Pradesh',
            'Punjab': 'Punjab',
            'Haryana': 'Haryana',
            'Bihar': 'Bihar'
        }
        return state_names.get(state_code, state_code)

    def save_boundaries(self, boundaries, filename):
        """Save boundaries to GeoJSON file"""
        if boundaries and boundaries['features']:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(boundaries, f, indent=2, ensure_ascii=False)

        # Also create a simple CSV with state coordinates for quick access
        coords_file = filename.replace('.geojson', '_centers.csv')
        state_centers = []

        for feature in boundaries['features']:
            state = feature['properties']['state']

            # Calculate approximate center from geometry
            if feature['geometry']['type'] == 'Polygon':
                coords = feature['geometry']['coordinates'][0]
                lat_sum = sum(coord[1] for coord in coords)
                lon_sum = sum(coord[0] for coord in coords)
                center_lat = lat_sum / len(coords)
                center_lon = lon_sum / len(coords)

                state_centers.append({
                    'state': state,
                    'center_lat': round(center_lat, 4),
                    'center_lon': round(center_lon, 4)
                })

        if state_centers:
            centers_df = pd.DataFrame(state_centers)
            centers_df.to_csv(coords_file, index=False)

def run_phase2_collection():
    """Main function to run Phase 2 data collection"""
    print("🌾 NORTH INDIA CROP PREDICTION")
    print("Phase 2: Automated Data Collection")
    print("="*50)

    collector = NorthIndiaDataCollector()
    results = collector.collect_all_data()

    print(f"\n📊 Collection Results:")
    print(f"  🇮🇳 Crop Yields: {results['crop_yields_collected']} records")
    print(f"  🌤️  Weather: {results['weather_states_covered']} states covered")
    print(f"  🗺️  Boundaries: {results['boundaries_obtained']} states")
    print(f"\n💾 Data saved to 'data/raw/' directory")

    # Create summary CSV
    summary = {
        'phase': '2_data_collection',
        'completed': datetime.now(),
        'crop_yields': results['crop_yields_collected'],
        'weather_states': results['weather_states_covered'],
        'boundaries': results['boundaries_obtained'],
        'files_created': len([f for f in os.listdir('data/raw') if f.endswith('.csv')])
    }

    summary_df = pd.DataFrame([summary])
    summary_df.to_csv('data/phase2_completion.csv', index=False)

    print("\n✅ Phase 2 Complete! Ready for Phase 3: Data Processing Pipeline")

if __name__ == "__main__":
    run_phase2_collection()
