#!/usr/bin/env python3
"""
Variety Selection Service for Crop Yield Prediction API

Provides intelligent variety selection based on location and crop type,
leveraging regional prevalence data from the variety database.
"""

import logging
import time
from typing import Dict, Any, List, Optional
import pandas as pd
from crop_variety_database import CropVarietyDatabase


class VarietySelectionService:
    """Service for intelligent variety selection based on location and crop type"""

    # Location to region mapping for North India
    LOCATION_REGION_MAPPING = {
        # Cities to States
        'bhopal': 'Madhya Pradesh',
        'lucknow': 'Uttar Pradesh',
        'chandigarh': 'Punjab',
        'patna': 'Bihar',
        'delhi': 'Delhi',
        'jaipur': 'Rajasthan',
        'amritsar': 'Punjab',
        'ludhiana': 'Punjab',
        'kanpur': 'Uttar Pradesh',
        'agra': 'Uttar Pradesh',
        'varanasi': 'Uttar Pradesh',
        'allahabad': 'Uttar Pradesh',
        'prayagraj': 'Uttar Pradesh',
        'gwalior': 'Madhya Pradesh',
        'indore': 'Madhya Pradesh',
        'jabalpur': 'Madhya Pradesh',
        
        # Regional identifiers
        'north india regional': 'All North India',
        'north india': 'All North India',
        
        # States (pass-through)
        'punjab': 'Punjab',
        'haryana': 'Haryana',
        'uttar pradesh': 'Uttar Pradesh',
        'up': 'Uttar Pradesh',
        'madhya pradesh': 'Madhya Pradesh',
        'mp': 'Madhya Pradesh',
        'bihar': 'Bihar',
        'rajasthan': 'Rajasthan',
        'delhi': 'Delhi'
    }

    # Fallback region for unmapped locations
    DEFAULT_REGION = 'All North India'

    # Global default variety rankings by crop type
    GLOBAL_DEFAULT_VARIETIES = {
        'Rice': ['IR-64', 'Basmati 370', 'Swarna'],
        'Wheat': ['HD 3086', 'PBW 725', 'C 306'],
        'Maize': ['DHM 117', 'HQPM 1', 'Baby Corn Hybrid']
    }

    def __init__(self, variety_db: CropVarietyDatabase):
        """
        Initialize variety selection service
        
        Args:
            variety_db: Instance of CropVarietyDatabase
        """
        self.variety_db = variety_db
        self.logger = logging.getLogger(__name__)
        self._location_region_cache = {}
        self._initialize_location_mappings()

    def _initialize_location_mappings(self):
        """Initialize location-to-region mapping cache"""
        # Pre-populate cache with known mappings
        self._location_region_cache = {
            location.lower(): region 
            for location, region in self.LOCATION_REGION_MAPPING.items()
        }
        self.logger.info(f"✅ Initialized location mappings for {len(self._location_region_cache)} locations")

    def map_location_to_region(self, location_name: str) -> str:
        """
        Map location name to state/region with case-insensitive matching
        
        Args:
            location_name: Location name (e.g., "Bhopal", "Lucknow")
        
        Returns:
            State/region name (e.g., "Punjab", "Uttar Pradesh")
        """
        # Input sanitization: remove special characters and extra whitespace
        if not location_name or not isinstance(location_name, str):
            self.logger.warning(f"⚠️  Invalid location_name: {location_name}, using fallback region")
            return self.DEFAULT_REGION
        
        # Sanitize: remove special characters, keep only alphanumeric and spaces
        import re
        sanitized_location = re.sub(r'[^a-zA-Z0-9\s]', '', location_name)
        
        # Normalize location name (lowercase, strip whitespace)
        normalized_location = sanitized_location.lower().strip()
        
        # Additional validation: check for empty string after sanitization
        if not normalized_location:
            self.logger.warning(f"⚠️  Empty location after sanitization, using fallback region")
            return self.DEFAULT_REGION
        
        # Check cache first
        if normalized_location in self._location_region_cache:
            region = self._location_region_cache[normalized_location]
            self.logger.debug(f"📍 Mapped location '{location_name}' to region '{region}'")
            return region
        
        # If not found, use default fallback region
        self.logger.warning(
            f"⚠️  Unknown location '{location_name}', using fallback region '{self.DEFAULT_REGION}'"
        )
        return self.DEFAULT_REGION

    def get_regional_varieties(self, crop_type: str, region: str) -> pd.DataFrame:
        """
        Get varieties for specific crop type and region, sorted by yield potential
        
        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
            region: Region/state name
        
        Returns:
            DataFrame of matching varieties sorted by yield_potential (descending)
        """
        try:
            # Input validation
            if not crop_type or not isinstance(crop_type, str):
                self.logger.error(f"❌ Invalid crop_type: {crop_type}")
                return pd.DataFrame()
            
            if not region or not isinstance(region, str):
                self.logger.error(f"❌ Invalid region: {region}")
                return pd.DataFrame()
            
            # Query database for varieties matching crop type and region
            varieties_df = self.variety_db.get_crop_varieties(crop_type=crop_type, region=region)
            
            # Sort by yield potential (descending) if available
            if not varieties_df.empty and 'yield_potential' in varieties_df.columns:
                varieties_df = varieties_df.sort_values('yield_potential', ascending=False)
            
            self.logger.debug(
                f"🔍 Found {len(varieties_df)} varieties for {crop_type} in {region}"
            )
            
            return varieties_df
            
        except Exception as e:
            self.logger.error(
                f"❌ Database query failed for {crop_type} in {region}: {str(e)}"
            )
            return pd.DataFrame()

    def get_global_default(self, crop_type: str) -> str:
        """
        Get global default variety for crop type from priority list
        
        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
        
        Returns:
            Default variety name
        
        Raises:
            ValueError: If crop type is invalid or no varieties found in database
        """
        if crop_type not in self.GLOBAL_DEFAULT_VARIETIES:
            raise ValueError(f"Invalid crop type: {crop_type}")
        
        defaults = self.GLOBAL_DEFAULT_VARIETIES[crop_type]
        
        # Try each default in order, verify it exists in database
        for variety_name in defaults:
            variety_info = self.variety_db.get_variety_by_name(crop_type, variety_name)
            if variety_info:
                self.logger.info(
                    f"✅ Using global default '{variety_name}' for {crop_type}"
                )
                return variety_name
        
        # If none found, raise error
        raise ValueError(
            f"No default varieties found in database for {crop_type}. "
            f"Attempted: {', '.join(defaults)}"
        )

    def select_default_variety(
        self, 
        crop_type: str, 
        location_name: str
    ) -> Dict[str, Any]:
        """
        Select appropriate default variety based on crop type and location
        
        This method implements a fallback chain:
        1. Try regional varieties (highest yield potential)
        2. Try "All North India" varieties
        3. Use global defaults
        4. Raise error if all attempts fail
        
        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
            location_name: Location name (e.g., "Bhopal", "Lucknow")
        
        Returns:
            Dictionary containing:
            - variety_name: Selected variety name
            - variety_assumed: Always True for this method
            - selection_metadata: Details about selection process
        
        Raises:
            ValueError: If no appropriate variety can be determined
        """
        # Start performance timing
        start_time = time.time()
        
        # Track attempted varieties for error logging
        attempted_varieties = []
        
        try:
            # Input validation
            if not crop_type or not isinstance(crop_type, str):
                raise ValueError(f"Invalid crop_type: {crop_type}")
            
            if not location_name or not isinstance(location_name, str):
                raise ValueError(f"Invalid location_name: {location_name}")
            
            # Step 1: Map location to region (with input sanitization)
            region = self.map_location_to_region(location_name)
            
            # Step 2: Query regional varieties
            try:
                regional_varieties = self.get_regional_varieties(crop_type, region)
            except Exception as db_error:
                self.logger.error(
                    f"❌ Database query failed for {crop_type} in {region}: {str(db_error)}"
                )
                regional_varieties = pd.DataFrame()
            
            # Step 3: Select highest yield potential variety from region
            if not regional_varieties.empty:
                selected = regional_varieties.iloc[0]  # Already sorted by yield_potential DESC
                selected_variety_name = selected['variety_name']
                
                # Validate that selected variety exists in database
                try:
                    variety_info = self.variety_db.get_variety_by_name(crop_type, selected_variety_name)
                    if not variety_info:
                        self.logger.warning(
                            f"⚠️  Selected variety '{selected_variety_name}' not found in database, trying next"
                        )
                        attempted_varieties.append(selected_variety_name)
                    else:
                        # Get alternatives (top 3 other varieties)
                        alternatives = regional_varieties['variety_name'].tolist()[1:4] if len(regional_varieties) > 1 else []
                        
                        # Calculate selection time
                        selection_time_ms = (time.time() - start_time) * 1000
                        
                        # INFO-level logging for successful variety selection with full metadata
                        self.logger.info(
                            f"✅ Variety selection successful | "
                            f"crop_type={crop_type} | "
                            f"location={location_name} | "
                            f"region={region} | "
                            f"selected_variety={selected_variety_name} | "
                            f"reason=regional_highest_yield | "
                            f"yield_potential={selected['yield_potential']:.2f} t/ha | "
                            f"alternatives={len(alternatives)} | "
                            f"selection_time={selection_time_ms:.2f}ms"
                        )
                        
                        return {
                            'variety_name': selected_variety_name,
                            'variety_assumed': True,
                            'selection_metadata': {
                                'region': region,
                                'reason': 'regional_highest_yield',
                                'yield_potential': float(selected['yield_potential']),
                                'alternatives': alternatives,
                                'selection_time_ms': round(selection_time_ms, 2)
                            }
                        }
                except Exception as validation_error:
                    self.logger.error(
                        f"❌ Failed to validate variety '{selected_variety_name}': {str(validation_error)}"
                    )
                    attempted_varieties.append(selected_variety_name)
            
            # Step 4: Try "All North India" fallback if not already tried
            if region != 'All North India':
                # WARNING-level logging for fallback scenario (regional → North India)
                self.logger.warning(
                    f"⚠️  Fallback to regional default | "
                    f"crop_type={crop_type} | "
                    f"location={location_name} | "
                    f"original_region={region} | "
                    f"fallback_region=All North India | "
                    f"reason=no_regional_varieties_found"
                )
                
                try:
                    fallback_varieties = self.get_regional_varieties(crop_type, 'All North India')
                except Exception as db_error:
                    self.logger.error(
                        f"❌ Database query failed for {crop_type} in All North India: {str(db_error)}"
                    )
                    fallback_varieties = pd.DataFrame()
                
                if not fallback_varieties.empty:
                    selected = fallback_varieties.iloc[0]
                    selected_variety_name = selected['variety_name']
                    
                    # Validate that selected variety exists in database
                    try:
                        variety_info = self.variety_db.get_variety_by_name(crop_type, selected_variety_name)
                        if not variety_info:
                            self.logger.warning(
                                f"⚠️  Fallback variety '{selected_variety_name}' not found in database"
                            )
                            attempted_varieties.append(selected_variety_name)
                        else:
                            # Calculate selection time
                            selection_time_ms = (time.time() - start_time) * 1000
                            
                            # INFO-level logging for successful fallback selection with full metadata
                            self.logger.info(
                                f"✅ Variety selection successful (fallback) | "
                                f"crop_type={crop_type} | "
                                f"location={location_name} | "
                                f"original_region={region} | "
                                f"fallback_region=All North India | "
                                f"selected_variety={selected_variety_name} | "
                                f"reason=regional_fallback | "
                                f"yield_potential={selected['yield_potential']:.2f} t/ha | "
                                f"selection_time={selection_time_ms:.2f}ms"
                            )
                            
                            return {
                                'variety_name': selected_variety_name,
                                'variety_assumed': True,
                                'selection_metadata': {
                                    'region': 'All North India',
                                    'reason': 'regional_fallback',
                                    'original_region': region,
                                    'yield_potential': float(selected['yield_potential']),
                                    'selection_time_ms': round(selection_time_ms, 2)
                                }
                            }
                    except Exception as validation_error:
                        self.logger.error(
                            f"❌ Failed to validate fallback variety '{selected_variety_name}': {str(validation_error)}"
                        )
                        attempted_varieties.append(selected_variety_name)
            
            # Step 5: Use global defaults as last resort
            # WARNING-level logging for global default usage
            self.logger.warning(
                f"⚠️  Using global default | "
                f"crop_type={crop_type} | "
                f"location={location_name} | "
                f"region={region} | "
                f"reason=no_regional_varieties_found"
            )
            
            try:
                default_variety = self.get_global_default(crop_type)
                
                # Validate that global default exists in database
                variety_info = self.variety_db.get_variety_by_name(crop_type, default_variety)
                if not variety_info:
                    self.logger.error(
                        f"❌ Global default variety '{default_variety}' not found in database"
                    )
                    attempted_varieties.append(default_variety)
                    raise ValueError(f"Global default variety '{default_variety}' not found in database")
                
                # Calculate selection time
                selection_time_ms = (time.time() - start_time) * 1000
                
                # INFO-level logging for successful global default selection with full metadata
                self.logger.info(
                    f"✅ Variety selection successful (global default) | "
                    f"crop_type={crop_type} | "
                    f"location={location_name} | "
                    f"region={region} | "
                    f"selected_variety={default_variety} | "
                    f"reason=global_default | "
                    f"selection_time={selection_time_ms:.2f}ms"
                )
                
                return {
                    'variety_name': default_variety,
                    'variety_assumed': True,
                    'selection_metadata': {
                        'region': region,
                        'reason': 'global_default',
                        'note': 'No regional varieties found',
                        'selection_time_ms': round(selection_time_ms, 2)
                    }
                }
            except ValueError as global_error:
                # Calculate selection time even for failures
                selection_time_ms = (time.time() - start_time) * 1000
                
                # ERROR-level logging for variety selection failure with full details
                self.logger.error(
                    f"❌ Variety selection failed | "
                    f"crop_type={crop_type} | "
                    f"location={location_name} | "
                    f"region={region} | "
                    f"attempted_varieties={', '.join(attempted_varieties) if attempted_varieties else 'None'} | "
                    f"error={str(global_error)} | "
                    f"selection_time={selection_time_ms:.2f}ms"
                )
                raise ValueError(
                    f"Unable to determine appropriate variety for crop type '{crop_type}' in location '{location_name}'. "
                    f"No varieties available in database for region '{region}' or global defaults."
                )
            
        except ValueError as ve:
            # Re-raise ValueError with context (already logged above)
            raise ve
        except Exception as e:
            # Calculate selection time even for unexpected failures
            selection_time_ms = (time.time() - start_time) * 1000
            
            # ERROR-level logging for unexpected variety selection failure
            self.logger.error(
                f"❌ Variety selection failed (unexpected error) | "
                f"crop_type={crop_type} | "
                f"location={location_name} | "
                f"attempted_varieties={', '.join(attempted_varieties) if attempted_varieties else 'None'} | "
                f"error_type={type(e).__name__} | "
                f"error={str(e)} | "
                f"selection_time={selection_time_ms:.2f}ms"
            )
            error_msg = (
                f"Failed to select variety for {crop_type} in {location_name}: {str(e)}"
            )
            raise ValueError(error_msg)


def test_variety_selection_service():
    """Test the variety selection service functionality"""
    print("🌾 Testing Variety Selection Service...")
    
    # Initialize database and service
    variety_db = CropVarietyDatabase()
    service = VarietySelectionService(variety_db)
    
    # Test location mapping
    print("\n📍 Testing location-to-region mapping:")
    test_locations = ['Bhopal', 'LUCKNOW', 'chandigarh', 'Unknown City']
    for location in test_locations:
        region = service.map_location_to_region(location)
        print(f"   {location} → {region}")
    
    # Test regional variety selection
    print("\n🔍 Testing regional variety selection:")
    test_cases = [
        ('Rice', 'Bhopal'),
        ('Wheat', 'Chandigarh'),
        ('Maize', 'Lucknow')
    ]
    
    for crop_type, location in test_cases:
        try:
            result = service.select_default_variety(crop_type, location)
            print(f"   {crop_type} in {location}:")
            print(f"      Selected: {result['variety_name']}")
            print(f"      Reason: {result['selection_metadata']['reason']}")
            print(f"      Region: {result['selection_metadata']['region']}")
        except Exception as e:
            print(f"   ❌ Failed for {crop_type} in {location}: {e}")
    
    # Test global defaults
    print("\n🌍 Testing global defaults:")
    for crop_type in ['Rice', 'Wheat', 'Maize']:
        try:
            default = service.get_global_default(crop_type)
            print(f"   {crop_type}: {default}")
        except Exception as e:
            print(f"   ❌ Failed for {crop_type}: {e}")
    
    print("\n🎉 Variety selection service test completed")


if __name__ == "__main__":
    test_variety_selection_service()
