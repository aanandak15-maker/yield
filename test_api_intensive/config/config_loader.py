"""Configuration loader for test framework"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class TestConfig:
    """Test configuration loader and accessor"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/test_config.json relative to this file
            config_dir = Path(__file__).parent
            config_path = config_dir / "test_config.json"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self._config = json.load(f)
    
    def reload(self):
        """Reload configuration from file"""
        self._load_config()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation path
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'api.base_url')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config = TestConfig()
            >>> config.get('api.base_url')
            'http://localhost:8000'
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    @property
    def api_base_url(self) -> str:
        """Get API base URL"""
        return self.get('api.base_url', 'http://localhost:8000')
    
    @property
    def api_timeout(self) -> int:
        """Get API timeout in seconds"""
        return self.get('api.timeout_seconds', 30)
    
    @property
    def retry_attempts(self) -> int:
        """Get number of retry attempts"""
        return self.get('api.retry_attempts', 3)
    
    @property
    def test_locations(self) -> List[Dict[str, Any]]:
        """Get list of test locations"""
        return self.get('test_data.locations', [])
    
    @property
    def test_crops(self) -> List[str]:
        """Get list of test crops"""
        return self.get('test_data.crops', [])
    
    def get_sowing_dates(self, crop_type: str) -> List[str]:
        """
        Get sowing dates for specific crop
        
        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
            
        Returns:
            List of sowing dates
        """
        dates_config = self.get(f'test_data.sowing_dates.{crop_type}', {})
        
        # Flatten all season dates into single list
        all_dates = []
        for key, value in dates_config.items():
            if isinstance(value, list):
                all_dates.extend(value)
        
        return all_dates
    
    def get_test_varieties(self, crop_type: str) -> List[str]:
        """
        Get test varieties for specific crop
        
        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
            
        Returns:
            List of variety names
        """
        return self.get(f'test_data.test_varieties.{crop_type}', [])
    
    @property
    def max_response_time_ms(self) -> int:
        """Get maximum acceptable response time in milliseconds"""
        return self.get('performance.max_response_time_ms', 5000)
    
    @property
    def max_response_time_under_load_ms(self) -> int:
        """Get maximum acceptable response time under load in milliseconds"""
        return self.get('performance.max_response_time_under_load_ms', 10000)
    
    @property
    def concurrent_users(self) -> List[int]:
        """Get list of concurrent user counts for load testing"""
        return self.get('performance.concurrent_users', [1, 10, 50, 100])
    
    @property
    def max_error_rate_percent(self) -> float:
        """Get maximum acceptable error rate percentage"""
        return self.get('thresholds.max_error_rate_percent', 5.0)
    
    @property
    def min_yield(self) -> float:
        """Get minimum reasonable yield in tons per hectare"""
        return self.get('thresholds.min_yield_tons_per_hectare', 1.0)
    
    @property
    def max_yield(self) -> float:
        """Get maximum reasonable yield in tons per hectare"""
        return self.get('thresholds.max_yield_tons_per_hectare', 10.0)
    
    @property
    def parallel_execution(self) -> bool:
        """Check if parallel test execution is enabled"""
        return self.get('test_parameters.parallel_execution', True)
    
    @property
    def max_workers(self) -> int:
        """Get maximum number of parallel workers"""
        return self.get('test_parameters.max_workers', 4)
    
    @property
    def report_output_dir(self) -> str:
        """Get report output directory"""
        return self.get('reporting.output_directory', 'test_api_intensive/reports')
    
    @property
    def report_formats(self) -> List[str]:
        """Get list of report formats to generate"""
        return self.get('reporting.formats', ['html', 'json', 'markdown'])
    
    def get_field_polygon(self, polygon_name: str) -> List[List[float]]:
        """
        Get predefined field polygon coordinates
        
        Args:
            polygon_name: Name of polygon (small_field, medium_field, etc.)
            
        Returns:
            List of [lon, lat] coordinate pairs
        """
        return self.get(f'test_data.field_polygons.{polygon_name}', [])
    
    def get_invalid_crop_types(self) -> List[str]:
        """Get list of invalid crop types for validation testing"""
        return self.get('validation.invalid_crop_types', [])
    
    def get_sql_injection_payloads(self) -> List[str]:
        """Get SQL injection test payloads"""
        return self.get('security.sql_injection_payloads', [])
    
    def get_xss_payloads(self) -> List[str]:
        """Get XSS test payloads"""
        return self.get('security.xss_payloads', [])
    
    def is_suite_enabled(self, suite_name: str) -> bool:
        """
        Check if test suite is enabled
        
        Args:
            suite_name: Name of test suite
            
        Returns:
            True if suite is enabled
        """
        return self.get(f'test_suites.{suite_name}.enabled', True)
    
    def get_suite_priority(self, suite_name: str) -> int:
        """
        Get test suite priority (lower number = higher priority)
        
        Args:
            suite_name: Name of test suite
            
        Returns:
            Priority number
        """
        return self.get(f'test_suites.{suite_name}.priority', 999)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary"""
        return self._config.copy()
    
    def __repr__(self) -> str:
        return f"TestConfig(config_path='{self.config_path}')"


# Global config instance
_config_instance: Optional[TestConfig] = None


def get_config(config_path: Optional[str] = None) -> TestConfig:
    """
    Get global configuration instance (singleton pattern)
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        TestConfig instance
    """
    global _config_instance
    
    if _config_instance is None or config_path is not None:
        _config_instance = TestConfig(config_path)
    
    return _config_instance


def reload_config():
    """Reload global configuration from file"""
    global _config_instance
    if _config_instance is not None:
        _config_instance.reload()
