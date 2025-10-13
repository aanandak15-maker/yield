# Phase 5: API Infrastructure & Crop Intelligence
# Core modules for automated crop yield prediction system

# Version and metadata
__version__ = "5.0.0"
__phase__ = "API Infrastructure & Crop Intelligence"

from .api_credentials import APICredentialsManager, get_credentials_manager, initialize_all_apis
from .gee_client import GEEClient
from .weather_client import OpenWeatherClient
from .unified_data_pipeline import UnifiedDataPipeline, DataCacheManager
from .crop_variety_database import CropVarietyDatabase
from .sowing_date_intelligence import SowingDateIntelligence

__all__ = [
    # API Infrastructure
    'APICredentialsManager',
    'get_credentials_manager',
    'initialize_all_apis',
    'GEEClient',
    'OpenWeatherClient',
    'UnifiedDataPipeline',
    'DataCacheManager',

    # Crop Intelligence
    'CropVarietyDatabase',
    'SowingDateIntelligence',

    # Metadata
    '__version__',
    '__phase__'
]

# Quick setup function for easy initialization
def initialize_phase5_system(config_path: str = "../config/api_config.json") -> dict:
    """
    Initialize all Phase 5 components with a single call

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary with initialization results
    """
    results = {
        'apis_connected': False,
        'database_ready': False,
        'variety_db_ready': False,
        'sowing_intelligence_ready': False,
        'errors': []
    }

    try:
        # Initialize API connections
        if initialize_all_apis():
            results['apis_connected'] = True
    except Exception as e:
        results['errors'].append(f"API init failed: {e}")

    try:
        # Initialize crop variety database
        variety_db = CropVarietyDatabase(config_path)
        rice_varieties = variety_db.get_crop_varieties('Rice')
        if len(rice_varieties) > 0:
            results['variety_db_ready'] = True
    except Exception as e:
        results['errors'].append(f"Variety DB init failed: {e}")

    try:
        # Initialize sowing date intelligence
        sdi = SowingDateIntelligence(config_path)
        current_season = sdi.detect_current_season()
        if current_season:
            results['sowing_intelligence_ready'] = True
    except Exception as e:
        results['errors'].append(f"Sowing intelligence init failed: {e}")

    try:
        # Initialize unified pipeline
        pipeline = UnifiedDataPipeline(config_path)
        quality_report = pipeline.get_data_quality_report()
        if 'error' not in quality_report:
            results['database_ready'] = True
    except Exception as e:
        results['errors'].append(f"Database init failed: {e}")

    results['success_rate'] = (sum([
        results['apis_connected'],
        results['database_ready'],
        results['variety_db_ready'],
        results['sowing_intelligence_ready']
    ]) / 4) * 100

    return results
