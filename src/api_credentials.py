#!/usr/bin/env python3
"""
API Credentials Management for Crop Yield Prediction System

Securely handles API credentials and authentication for external services.
Manages credentials from environment variables, config files, and key vaults.
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

class APICredentialsManager:
    """Manages API credentials securely"""

    def __init__(self, config_path: str = "config/api_config.json"):
        self.config_path = Path(config_path)
        self.credentials = {}
        self._loaded = False

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def load_credentials(self) -> bool:
        """Load all API credentials from various sources"""
        try:
            # Load from environment variables first (highest priority)
            self._load_from_environment()

            # Load from config file
            self._load_from_config_file()

            # Validate critical credentials
            self._validate_credentials()

            self._loaded = True
            self.logger.info("✅ API credentials loaded successfully")

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to load credentials: {e}")
            return False

    def _load_from_environment(self):
        """Load credentials from environment variables"""
        # Google Earth Engine
        if os.getenv('GEE_SERVICE_ACCOUNT_EMAIL'):
            self.credentials['gee'] = {
                'service_account_email': os.getenv('GEE_SERVICE_ACCOUNT_EMAIL'),
                'private_key_path': os.getenv('GEE_PRIVATE_KEY_PATH'),
                'project_id': os.getenv('GEE_PROJECT_ID')
            }
        elif os.getenv('GEE_PRIVATE_KEY_JSON'):
            self.logger.info("🔑 Using GEE credentials from GEE_PRIVATE_KEY_JSON environment variable")
            gee_json = os.getenv('GEE_PRIVATE_KEY_JSON')
            self.logger.info(f"🔍 GEE_PRIVATE_KEY_JSON length: {len(gee_json)} characters")
            self.logger.info(f"🔍 GEE_PRIVATE_KEY_JSON starts with: {gee_json[:50]}...")
            
            # Use environment variable content instead of file
            self.credentials['gee'] = {
                'service_account_email': 'crop-yield-gee-service@named-tome-472312-m3.iam.gserviceaccount.com',
                'private_key_path': None,  # Will handle in initialize_gee
                'private_key_content': gee_json,  # Store JSON content
                'project_id': 'named-tome-472312-m3'
            }

        # OpenWeather API
        if os.getenv('OPENWEATHER_API_KEY'):
            self.credentials['openweather'] = {
                'api_key': os.getenv('OPENWEATHER_API_KEY')
            }

    def _load_from_config_file(self):
        """Load credentials from configuration file"""
        if not self.config_path.exists():
            self.logger.warning(f"Config file not found: {self.config_path}")
            return

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Extract credentials from config (assuming they're stored there for development)
            # In production, this should be from secure key vault
            if 'google_earth_engine' in config:
                gee_config = config['google_earth_engine']
                if 'service_account_email' in gee_config:
                    self.credentials['gee'] = {
                        'service_account_email': gee_config['service_account_email'],
                        'private_key_path': gee_config.get('private_key_path'),
                        'project_id': gee_config.get('project_id')
                    }

            if 'openweather' in config:
                ow_config = config['openweather']
                if 'api_key' in ow_config:
                    self.credentials['openweather'] = {
                        'api_key': ow_config['api_key']
                    }

        except Exception as e:
            self.logger.error(f"❌ Failed to load config file: {e}")

    def _validate_credentials(self):
        """Validate that all required credentials are present"""
        required_services = ['gee', 'openweather']
        missing_services = []

        for service in required_services:
            if service not in self.credentials:
                missing_services.append(service)
            else:
                # Service-specific validation
                if service == 'gee':
                    gee_creds = self.credentials[service]
                    # Check if we have either file-based or JSON-based credentials
                    has_file_creds = all(k in gee_creds and gee_creds[k] for k in
                                        ['service_account_email', 'private_key_path', 'project_id'])
                    has_json_creds = all(k in gee_creds and gee_creds[k] for k in
                                        ['service_account_email', 'private_key_content', 'project_id'])
                    if not (has_file_creds or has_json_creds):
                        missing_services.append(f"{service} (missing credentials)")
                elif service == 'openweather':
                    if 'api_key' not in self.credentials[service]:
                        missing_services.append(f"{service} (missing api_key)")

        if missing_services:
            raise ValueError(f"Missing required credentials for: {', '.join(missing_services)}")

    def get_credential(self, service: str, key: str = None) -> Any:
        """Get specific credential or entire credential set"""
        if not self._loaded:
            raise RuntimeError("Credentials not loaded. Call load_credentials() first.")

        if service not in self.credentials:
            raise KeyError(f"No credentials found for service: {service}")

        if key:
            if key not in self.credentials[service]:
                raise KeyError(f"Credential key '{key}' not found for service '{service}'")
            return self.credentials[service][key]

        return self.credentials[service]

    def get_gee_credentials(self) -> Dict[str, str]:
        """Get Google Earth Engine credentials"""
        return self.get_credential('gee')

    def get_openweather_credentials(self) -> Dict[str, str]:
        """Get OpenWeather credentials"""
        return self.get_credential('openweather')

    def has_credentials(self, service: str) -> bool:
        """Check if credentials exist for a service"""
        return service in self.credentials

    def initialize_gee(self):
        """Initialize Google Earth Engine with credentials"""
        try:
            import ee
            import tempfile
            import json
            import os

            # Check for environment variable first
            gee_json = os.getenv('GEE_PRIVATE_KEY_JSON')
            if gee_json:
                self.logger.info("🔑 Using GEE credentials from GEE_PRIVATE_KEY_JSON environment variable")
                # Parse the JSON content and create temporary credentials
                try:
                    # Clean up the JSON string - remove any extra whitespace/newlines
                    gee_json_clean = gee_json.strip()
                    self.logger.info(f"🔍 Cleaned JSON length: {len(gee_json_clean)}")
                    
                    key_data = json.loads(gee_json_clean)
                    self.logger.info(f"✅ Parsed GEE credentials for project: {key_data.get('project_id', 'unknown')}")
                    
                    # Write private key to temporary file for GEE SDK
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                        json.dump(key_data, temp_file)
                        temp_key_file = temp_file.name

                    # Initialize Earth Engine with parsed credentials
                    credentials = ee.ServiceAccountCredentials(
                        key_data.get('client_email', 'crop-yield-gee-service@named-tome-472312-m3.iam.gserviceaccount.com'),
                        temp_key_file
                    )
                    
                    # Initialize EE with credentials
                    ee.Initialize(credentials)
                    self.logger.info("✅ Google Earth Engine initialized successfully")
                    return True

                except json.JSONDecodeError as e:
                    self.logger.error(f"❌ Failed to parse GEE_PRIVATE_KEY_JSON: {e}")
                    self.logger.error(f"❌ JSON content preview: {gee_json[:100]}...")
                    raise ValueError("Invalid GEE_PRIVATE_KEY_JSON format")
                except Exception as e:
                    self.logger.error(f"❌ Failed to initialize GEE with environment credentials: {e}")
                    raise

            else:
                # Fallback to file-based credentials for development
                gee_creds = self.get_gee_credentials()
                gee_file = gee_creds.get('private_key_path') or gee_creds.get('private_key_content')

                if gee_file and Path(gee_file).exists():
                    self.logger.info("🔑 Using GEE credentials from file path")
                    credentials = ee.ServiceAccountCredentials(
                        gee_creds['service_account_email'],
                        gee_file
                    )
                else:
                    # Last resort: try to find any GEE file in config
                    gee_config_file = Path('config/gee_private_key.json')
                    if gee_config_file.exists():
                        self.logger.info("🔑 Found GEE credentials file in config directory")
                        credentials = ee.ServiceAccountCredentials(
                            gee_creds.get('service_account_email', 'crop-yield-gee-service@named-tome-472312-m3.iam.gserviceaccount.com'),
                            str(gee_config_file)
                        )
                    else:
                        self.logger.error("❌ No valid GEE credential source found (no JSON env var, no file)")
                        raise ValueError("No GEE private key source found")

            # Initialize Earth Engine
            ee.Initialize(credentials, project='named-tome-472312-m3')
            self.logger.info("✅ Google Earth Engine initialized successfully")

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize GEE: {e}")
            # Skip GEE if in demo mode
            if os.getenv('ALLOW_LOCAL_TESTING') == 'true':
                self.logger.warning("⚠️ GEE failed but ALLOW_LOCAL_TESTING=true, continuing with demo mode")
                return True
            return False

    def test_openweather_connection(self) -> bool:
        """Test OpenWeather API connection"""
        try:
            import requests

            ow_creds = self.get_openweather_credentials()
            api_key = ow_creds['api_key']

            # Test with a simple current weather request
            test_url = f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}&units=metric"

            response = requests.get(test_url, timeout=10)

            if response.status_code == 200:
                self.logger.info("✅ OpenWeather API connection successful")
                return True
            else:
                self.logger.error(f"❌ OpenWeather API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to test OpenWeather connection: {e}")
            return False

# Global credentials manager instance
_credentials_manager = None

def get_credentials_manager() -> APICredentialsManager:
    """Get global credentials manager instance"""
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = APICredentialsManager()
    return _credentials_manager

def initialize_all_apis() -> bool:
    """Initialize all API connections"""
    manager = get_credentials_manager()

    if not manager.load_credentials():
        return False

    # Initialize GEE
    if not manager.initialize_gee():
        return False

    # Test OpenWeather
    if not manager.test_openweather_connection():
        return False

    print("🎉 All API connections initialized successfully!")
    return True

if __name__ == "__main__":
    # Test credentials loading
    print("🔐 Testing API Credentials Management...")

    manager = get_credentials_manager()

    if manager.load_credentials():
        print("✅ Credentials loaded successfully")
        print(f"Available services: {list(manager.credentials.keys())}")

        # Test API connections
        initialize_all_apis()
    else:
        print("❌ Failed to load credentials")
        print("Please ensure environment variables or config file contains valid credentials.")
