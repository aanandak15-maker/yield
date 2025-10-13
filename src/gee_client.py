#!/usr/bin/env python3
"""
Google Earth Engine (GEE) API Client for Crop Yield Prediction

Retrieves satellite data including NDVI, EVI, and other vegetation indices
from MODIS and Landsat datasets for crop monitoring and yield prediction.
"""

import ee
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

class GEEClient:
    """Google Earth Engine client for satellite data retrieval"""

    def __init__(self, config_path: str = "config/api_config.json"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._load_config()
        self._initialized = False

    def _load_config(self):
        """Load GEE configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            self.gee_config = config.get('google_earth_engine', {})
            self.data_refresh = config.get('data_refresh', {})
            self.north_india_bounds = config.get('north_india_region', {})

        except Exception as e:
            self.logger.error(f"Failed to load GEE config: {e}")
            self.gee_config = {}
            self.data_refresh = {}
            self.north_india_bounds = {}

    def initialize(self) -> bool:
        """Initialize Google Earth Engine"""
        try:
            # Import credentials manager and initialize GEE
            from .api_credentials import get_credentials_manager

            credentials_manager = get_credentials_manager()
            if not credentials_manager.load_credentials():
                raise RuntimeError("Failed to load credentials")

            if not credentials_manager.initialize_gee():
                raise RuntimeError("Failed to initialize GEE")

            self._initialized = True
            self.logger.info("✅ GEE client initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize GEE client: {e}")
            return False

    def _ensure_initialized(self):
        """Ensure GEE is initialized before operations"""
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("GEE client not initialized")

    def get_satellite_data_for_location(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        data_types: List[str] = None
    ) -> pd.DataFrame:
        """
        Get satellite data for a specific location and time period

        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            data_types: List of data types to retrieve (e.g., ['ndvi', 'evi', 'lst'])

        Returns:
            DataFrame with satellite data
        """
        self._ensure_initialized()

        if data_types is None:
            data_types = ['ndvi', 'evi']

        # Create point geometry
        point = ee.Geometry.Point([longitude, latitude])

        # Get satellite data
        satellite_data = {}

        for data_type in data_types:
            try:
                if data_type == 'ndvi':
                    data = self._get_modis_ndvi(point, start_date, end_date)
                elif data_type == 'evi':
                    data = self._get_modis_evi(point, start_date, end_date)
                elif data_type == 'lst':
                    data = self._get_landsat_temp(point, start_date, end_date)
                elif data_type == 'precipitation':
                    data = self._get_chirps_precipitation(point, start_date, end_date)
                else:
                    self.logger.warning(f"Unknown data type: {data_type}")
                    continue

                if not data.empty:
                    satellite_data[data_type] = data
                    self.logger.info(f"✅ Retrieved {data_type} data: {len(data)} records")

            except Exception as e:
                self.logger.error(f"❌ Failed to get {data_type} data: {e}")

        # Merge all data types
        if satellite_data:
            result_df = self._merge_satellite_datasets(satellite_data, latitude, longitude)
            return result_df
        else:
            return pd.DataFrame()

    def _get_modis_ndvi(self, point: ee.Geometry, start_date: str, end_date: str) -> pd.DataFrame:
        """Get MODIS NDVI (Normalized Difference Vegetation Index) data"""
        try:
            # MOD13Q1 dataset for 16-day NDVI composites
            collection = ee.ImageCollection('MODIS/061/MOD13Q1') \
                .filterDate(start_date, end_date) \
                .filterBounds(point) \
                .select(['NDVI', 'EVI', 'DetailedQA'])

            # Get data for the point
            ndvi_data = self._extract_time_series(collection, point, 'NDVI')
            evi_data = self._extract_time_series(collection, point, 'EVI')

            # Scale NDVI from integer to float (MODIS NDVI is scaled by 10000)
            if not ndvi_data.empty:
                ndvi_data['ndvi'] = ndvi_data['ndvi'] / 10000.0

            if not evi_data.empty:
                evi_data['evi'] = evi_data['evi'] / 10000.0

            # Merge NDVI and EVI
            if not ndvi_data.empty and not evi_data.empty:
                combined = pd.merge(ndvi_data, evi_data, on='date', how='outer')
            elif not ndvi_data.empty:
                combined = ndvi_data
            else:
                combined = evi_data

            return combined

        except Exception as e:
            self.logger.error(f"Failed to get MODIS NDVI: {e}")
            return pd.DataFrame()

    def _get_modis_evi(self, point: ee.Geometry, start_date: str, end_date: str) -> pd.DataFrame:
        """Get MODIS EVI (Enhanced Vegetation Index) data - included in NDVI function above"""
        # EVI is already retrieved in the NDVI function
        return pd.DataFrame()

    def _get_landsat_temp(self, point: ee.Geometry, start_date: str, end_date: str) -> pd.DataFrame:
        """Get Landsat surface temperature data"""
        try:
            # LANDSAT/LC08/C01/T1_TOA collection
            collection = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA') \
                .filterDate(start_date, end_date) \
                .filterBounds(point) \
                .select(['B10', 'B11'])  # Thermal bands

            # Calculate LST from thermal bands
            def calculate_lst(image):
                # Convert DN to radiance, then to temperature
                thermal_radiance = image.select('B10').multiply(0.0003342).add(0.1)
                lst = thermal_radiance.expression(
                    '(Tb / ((1 + (wavelength/Tb)*log(emissivity))) - 273.15)',
                    {
                        'Tb': thermal_radiance.select('B10'),
                        'wavelength': 10.8,  # Band 10 wavelength in microns
                        'emissivity': 0.97   # Typical vegetation emissivity
                    }
                )
                return image.addBands(lst.rename('LST'))

            lst_collection = collection.map(calculate_lst)
            lst_data = self._extract_time_series(lst_collection, point, 'LST')

            return lst_data.rename(columns={'LST': 'surface_temp'})

        except Exception as e:
            self.logger.error(f"Failed to get Landsat temperature: {e}")
            return pd.DataFrame()

    def _get_chirps_precipitation(self, point: ee.Geometry, start_date: str, end_date: str) -> pd.DataFrame:
        """Get CHIRPS precipitation data"""
        try:
            collection = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
                .filterDate(start_date, end_date) \
                .filterBounds(point) \
                .select('precipitation')

            precip_data = self._extract_time_series(collection, point, 'precipitation')
            return precip_data.rename(columns={'precipitation': 'chirps_precipitation'})

        except Exception as e:
            self.logger.error(f"Failed to get CHIRPS precipitation: {e}")
            return pd.DataFrame()

    def _extract_time_series(
        self,
        collection: ee.ImageCollection,
        point: ee.Geometry,
        band_name: str
    ) -> pd.DataFrame:
        """Extract time series data from Earth Engine collection at a point"""
        try:
            # Convert collection to list for iteration
            collection_list = collection.toList(collection.size())

            # Get dates and values
            data_list = []

            size = collection.size().getInfo()

            for i in range(size):
                try:
                    image = ee.Image(collection_list.get(i))
                    date = ee.Date(image.get('system:time_start')).format('YYYY-MM-DD').getInfo()

                    # Get value at point
                    value = image.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=point,
                        scale=250,  # 250m resolution for MODIS
                        maxPixels=10
                    ).get(band_name).getInfo()

                    if value is not None:
                        data_list.append({
                            'date': date,
                            band_name: float(value)
                        })

                except Exception as e:
                    self.logger.debug(f"Skipping image {i}: {e}")
                    continue

            if data_list:
                df = pd.DataFrame(data_list)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Failed to extract time series for {band_name}: {e}")
            return pd.DataFrame()

    def _merge_satellite_datasets(self, datasets: Dict[str, pd.DataFrame], lat: float, lon: float) -> pd.DataFrame:
        """Merge multiple satellite datasets into a single DataFrame"""
        try:
            base_df = None

            for data_type, df in datasets.items():
                if df.empty:
                    continue

                if base_df is None:
                    base_df = df.copy()
                else:
                    base_df = pd.merge(base_df, df, on='date', how='outer')

            if base_df is not None:
                # Add location information
                base_df['latitude'] = lat
                base_df['longitude'] = lon

                # Sort by date and fill missing values
                base_df = base_df.sort_values('date').reset_index(drop=True)
                base_df = base_df.fillna(method='ffill')  # Forward fill missing values
                base_df = base_df.fillna(method='bfill')  # Backward fill remaining NaNs

                return base_df
            else:
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Failed to merge satellite datasets: {e}")
            return pd.DataFrame()

    def get_regional_average_data(
        self,
        region_bounds: List[float],
        start_date: str,
        end_date: str,
        data_types: List[str] = None
    ) -> pd.DataFrame:
        """
        Get regional average satellite data for a bounding box

        Args:
            region_bounds: [west, south, east, north]
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            data_types: List of data types to retrieve
        """
        self._ensure_initialized()

        if data_types is None:
            data_types = ['ndvi']

        # Create region geometry
        region = ee.Geometry.Rectangle(region_bounds)

        # Similar logic as point data but for regional averages
        satellite_data = {}

        for data_type in data_types:
            try:
                if data_type == 'ndvi':
                    data = self._get_modis_ndvi_regional(region, start_date, end_date)
                else:
                    continue

                if not data.empty:
                    satellite_data[data_type] = data

            except Exception as e:
                self.logger.error(f"Failed to get regional {data_type}: {e}")

        if satellite_data:
            # For regional data, we return the data as-is since we're averaging over the region
            return satellite_data.get('ndvi', pd.DataFrame())
        else:
            return pd.DataFrame()

    def _get_modis_ndvi_regional(self, region: ee.Geometry, start_date: str, end_date: str) -> pd.DataFrame:
        """Get regional MODIS NDVI data"""
        try:
            collection = ee.ImageCollection('MODIS/061/MOD13Q1') \
                .filterDate(start_date, end_date) \
                .filterBounds(region) \
                .select('NDVI')

            # Extract regional averages
            ndvi_data = self._extract_regional_time_series(collection, region, 'NDVI')

            if not ndvi_data.empty:
                ndvi_data['ndvi'] = ndvi_data['ndvi'] / 10000.0  # Scale to 0-1

            return ndvi_data

        except Exception as e:
            self.logger.error(f"Failed to get regional MODIS NDVI: {e}")
            return pd.DataFrame()

    def _extract_regional_time_series(
        self,
        collection: ee.ImageCollection,
        region: ee.Geometry,
        band_name: str
    ) -> pd.DataFrame:
        """Extract regional time series data from Earth Engine collection"""
        try:
            collection_list = collection.toList(collection.size())
            data_list = []

            size = collection.size().getInfo()

            for i in range(size):
                try:
                    image = ee.Image(collection_list.get(i))
                    date = ee.Date(image.get('system:time_start')).format('YYYY-MM-DD').getInfo()

                    # Get regional mean
                    mean_value = image.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=region,
                        scale=1000,  # 1km for regional averages
                        maxPixels=10000
                    ).get(band_name).getInfo()

                    if mean_value is not None:
                        data_list.append({
                            'date': date,
                            band_name.lower(): float(mean_value)
                        })

                except Exception as e:
                    continue

            if data_list:
                df = pd.DataFrame(data_list)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Failed to extract regional time series for {band_name}: {e}")
            return pd.DataFrame()

    def get_north_india_satellite_data(
        self,
        data_types: List[str] = None,
        days_back: int = 30
    ) -> Dict[str, pd.DataFrame]:
        """
        Get satellite data for key North India regions (capitals)

        Args:
            data_types: List of data types to retrieve
            days_back: Number of days to look back from today

        Returns:
            Dictionary with location names as keys and DataFrames as values
        """
        self._ensure_initialized()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        results = {}

        # Get data for each state capital
        for state_info in self.north_india_bounds.get('states', []):
            location_name = state_info['capital']
            lat, lon = state_info['lat'], state_info['lon']

            self.logger.info(f"📡 Getting satellite data for {location_name}...")

            try:
                data = self.get_satellite_data_for_location(
                    latitude=lat,
                    longitude=lon,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    data_types=data_types
                )

                if not data.empty:
                    data['location'] = location_name
                    data['state'] = state_info.get('state', 'Unknown')
                    results[location_name] = data
                    self.logger.info(f"✅ Retrieved {len(data)} records for {location_name}")

            except Exception as e:
                self.logger.error(f"❌ Failed to get data for {location_name}: {e}")

        return results


def test_gee_client():
    """Test GEE client functionality"""
    print("🛰️  Testing GEE Client...")

    client = GEEClient()

    if not client.initialize():
        print("❌ Failed to initialize GEE client")
        return

    # Test data retrieval for a sample location (Bhopal)
    lat, lon = 23.25, 77.42  # Bhopal coordinates
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"📍 Testing data retrieval for Bhopal ({lat}, {lon})")
    print(f"📅 Date range: {start_date} to {end_date}")

    data = client.get_satellite_data_for_location(
        latitude=lat,
        longitude=lon,
        start_date=start_date,
        end_date=end_date,
        data_types=['ndvi', 'evi']
    )

    if not data.empty:
        print("✅ Successfully retrieved satellite data!")
        print(f"Shape: {data.shape}")
        print(f"Columns: {list(data.columns)}")
        print(f"Date range: {data['date'].min()} to {data['date'].max()}")
        print("\nSample data:")
        print(data.head())
    else:
        print("❌ No data retrieved")


if __name__ == "__main__":
    test_gee_client()
