"""
API Client Wrapper for Crop Yield Prediction API Testing

This module provides a wrapper around the Crop Yield API with built-in
retry logic, timeout handling, request timing, and logging functionality.
"""

import time
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Wrapper for API response with helper methods"""
    
    status_code: int
    json_data: Optional[Dict[str, Any]]
    headers: Dict[str, str]
    response_time_ms: float
    raw_text: str = ""
    error: Optional[str] = None
    
    def is_success(self) -> bool:
        """Check if response is successful (2xx)"""
        return 200 <= self.status_code < 300
    
    def is_client_error(self) -> bool:
        """Check if response is client error (4xx)"""
        return 400 <= self.status_code < 500
    
    def is_server_error(self) -> bool:
        """Check if response is server error (5xx)"""
        return 500 <= self.status_code < 600
    
    def has_field(self, field_path: str) -> bool:
        """
        Check if response has nested field
        
        Args:
            field_path: Dot-separated path (e.g., 'prediction.yield_tons_per_hectare')
        
        Returns:
            True if field exists, False otherwise
        """
        if not self.json_data:
            return False
        
        try:
            value = self.json_data
            for key in field_path.split('.'):
                if isinstance(value, dict):
                    if key not in value:
                        return False
                    value = value[key]
                elif isinstance(value, list):
                    try:
                        value = value[int(key)]
                    except (ValueError, IndexError):
                        return False
                else:
                    return False
            return True
        except (KeyError, TypeError, IndexError):
            return False
    
    def get_field(self, field_path: str, default: Any = None) -> Any:
        """
        Get nested field value
        
        Args:
            field_path: Dot-separated path (e.g., 'prediction.yield_tons_per_hectare')
            default: Default value if field not found
        
        Returns:
            Field value or default
        """
        if not self.json_data:
            return default
        
        try:
            value = self.json_data
            for key in field_path.split('.'):
                if isinstance(value, dict):
                    value = value[key]
                elif isinstance(value, list):
                    value = value[int(key)]
                else:
                    return default
            return value
        except (KeyError, TypeError, IndexError, ValueError):
            return default
    
    def get_error_message(self) -> Optional[str]:
        """Get error message from response"""
        if self.error:
            return self.error
        
        if self.json_data:
            # Try common error message fields
            for field in ['error', 'message', 'detail', 'error_message']:
                if field in self.json_data:
                    return str(self.json_data[field])
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for logging/reporting"""
        return {
            'status_code': self.status_code,
            'response_time_ms': self.response_time_ms,
            'is_success': self.is_success(),
            'json_data': self.json_data,
            'error': self.error
        }


class CropYieldAPIClient:
    """
    Wrapper for Crop Yield API with testing utilities
    
    Provides methods for all API endpoints with built-in:
    - Request timing
    - Retry logic
    - Timeout handling
    - Logging
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
        retry_on_status: Optional[List[int]] = None
    ):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the API (e.g., 'http://localhost:8000')
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
            retry_on_status: HTTP status codes to retry on (default: [500, 502, 503, 504])
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Configure session with retry logic
        self.session = requests.Session()
        
        retry_on_status = retry_on_status or [500, 502, 503, 504]
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=retry_on_status,
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"Initialized API client for {base_url}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """
        Make HTTP request with timing and error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON request body
            headers: Request headers
        
        Returns:
            APIResponse object
        """
        url = f"{self.base_url}{endpoint}"
        
        logger.debug(f"{method} {url}")
        if json_data:
            logger.debug(f"Request body: {json_data}")
        
        start_time = time.time()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
                timeout=self.timeout
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Try to parse JSON response
            try:
                json_response = response.json()
            except ValueError:
                json_response = None
            
            api_response = APIResponse(
                status_code=response.status_code,
                json_data=json_response,
                headers=dict(response.headers),
                response_time_ms=response_time_ms,
                raw_text=response.text
            )
            
            logger.info(
                f"{method} {url} - Status: {response.status_code}, "
                f"Time: {response_time_ms:.2f}ms"
            )
            
            return api_response
            
        except requests.exceptions.Timeout as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Request timeout after {response_time_ms:.2f}ms: {e}")
            
            return APIResponse(
                status_code=504,
                json_data=None,
                headers={},
                response_time_ms=response_time_ms,
                error=f"Request timeout: {str(e)}"
            )
            
        except requests.exceptions.ConnectionError as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Connection error: {e}")
            
            return APIResponse(
                status_code=503,
                json_data=None,
                headers={},
                response_time_ms=response_time_ms,
                error=f"Connection error: {str(e)}"
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error: {e}")
            
            return APIResponse(
                status_code=0,
                json_data=None,
                headers={},
                response_time_ms=response_time_ms,
                error=f"Unexpected error: {str(e)}"
            )
    
    def predict_yield(
        self,
        crop_type: str,
        latitude: float,
        longitude: float,
        sowing_date: str,
        variety_name: Optional[str] = None,
        location_name: Optional[str] = None
    ) -> APIResponse:
        """
        Make yield prediction request
        
        Args:
            crop_type: Type of crop (Rice, Wheat, Maize)
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            sowing_date: Sowing date in YYYY-MM-DD format
            variety_name: Optional variety name (if omitted, auto-selected)
            location_name: Optional location name
        
        Returns:
            APIResponse object
        """
        payload = {
            "crop_type": crop_type,
            "latitude": latitude,
            "longitude": longitude,
            "sowing_date": sowing_date
        }
        
        if variety_name is not None:
            payload["variety_name"] = variety_name
        
        if location_name is not None:
            payload["location_name"] = location_name
        
        return self._make_request("POST", "/predict/yield", json_data=payload)
    
    def predict_field_analysis(
        self,
        crop_type: str,
        sowing_date: str,
        field_coordinates: str,
        variety_name: Optional[str] = None
    ) -> APIResponse:
        """
        Make field analysis request
        
        Args:
            crop_type: Type of crop (Rice, Wheat, Maize)
            sowing_date: Sowing date in YYYY-MM-DD format
            field_coordinates: Polygon coordinates as string
            variety_name: Optional variety name (if omitted, auto-selected)
        
        Returns:
            APIResponse object
        """
        payload = {
            "crop_type": crop_type,
            "sowing_date": sowing_date,
            "field_coordinates": field_coordinates
        }
        
        if variety_name is not None:
            payload["variety_name"] = variety_name
        
        return self._make_request("POST", "/predict/field-analysis", json_data=payload)
    
    def get_health(self) -> APIResponse:
        """
        Get API health status
        
        Returns:
            APIResponse object
        """
        return self._make_request("GET", "/health")
    
    def get_supported_crops(self) -> APIResponse:
        """
        Get supported crops and varieties
        
        Returns:
            APIResponse object
        """
        return self._make_request("GET", "/crops/supported")
    
    def measure_response_time(
        self,
        request_func: Callable[[], APIResponse]
    ) -> Tuple[APIResponse, float]:
        """
        Execute request and measure response time
        
        Args:
            request_func: Function that makes the API request
        
        Returns:
            Tuple of (APIResponse, response_time_ms)
        """
        start_time = time.time()
        response = request_func()
        response_time_ms = (time.time() - start_time) * 1000
        
        return response, response_time_ms
    
    def close(self):
        """Close the session"""
        self.session.close()
        logger.info("API client session closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
