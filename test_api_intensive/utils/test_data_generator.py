"""
Test Data Generator for Crop Yield API Testing

This module provides utilities for generating valid, invalid, and edge-case
test data for comprehensive API testing.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from faker import Faker


fake = Faker()


class TestDataGenerator:
    """Generate test data for API testing"""
    
    # Predefined test locations across North India
    TEST_LOCATIONS = [
        {
            "name": "Bhopal",
            "latitude": 23.2599,
            "longitude": 77.4126,
            "region": "Madhya Pradesh",
            "state": "Madhya Pradesh"
        },
        {
            "name": "Lucknow",
            "latitude": 26.8467,
            "longitude": 80.9462,
            "region": "Uttar Pradesh",
            "state": "Uttar Pradesh"
        },
        {
            "name": "Chandigarh",
            "latitude": 30.7333,
            "longitude": 76.7794,
            "region": "Punjab",
            "state": "Punjab"
        },
        {
            "name": "Patna",
            "latitude": 25.5941,
            "longitude": 85.1376,
            "region": "Bihar",
            "state": "Bihar"
        },
        {
            "name": "Jaipur",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "region": "Rajasthan",
            "state": "Rajasthan"
        },
        {
            "name": "Amritsar",
            "latitude": 31.6340,
            "longitude": 74.8723,
            "region": "Punjab",
            "state": "Punjab"
        },
        {
            "name": "Hisar",
            "latitude": 29.1492,
            "longitude": 75.7217,
            "region": "Haryana",
            "state": "Haryana"
        },
        {
            "name": "Varanasi",
            "latitude": 25.3176,
            "longitude": 82.9739,
            "region": "Uttar Pradesh",
            "state": "Uttar Pradesh"
        }
    ]
    
    # Test varieties for each crop type
    TEST_VARIETIES = {
        "Rice": [
            "IR-64",
            "Pusa Basmati 1121",
            "Swarna",
            "MTU 1010",
            "Samba Mahsuri",
            "PR 126",
            "Pusa 44"
        ],
        "Wheat": [
            "HD 3086",
            "PBW 343",
            "DBW 17",
            "HD 2967",
            "WH 1105",
            "Lok 1",
            "UP 2338"
        ],
        "Maize": [
            "DHM 117",
            "PMH 1",
            "Vivek Hybrid 27",
            "HQPM 1",
            "Bio 9681",
            "Kaveri 50",
            "DKC 9144"
        ]
    }
    
    # Typical sowing dates for each crop
    SOWING_DATES = {
        "Rice": {
            "kharif": ["2024-06-15", "2024-07-01", "2024-07-15"],
            "months": [6, 7]
        },
        "Wheat": {
            "rabi": ["2024-11-01", "2024-11-15", "2024-12-01"],
            "months": [11, 12]
        },
        "Maize": {
            "kharif": ["2024-06-01", "2024-06-15", "2024-07-01"],
            "rabi": ["2024-10-15", "2024-11-01"],
            "months": [6, 7, 10, 11]
        }
    }
    
    VALID_CROPS = ["Rice", "Wheat", "Maize"]
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize test data generator
        
        Args:
            seed: Random seed for reproducible data generation
        """
        if seed is not None:
            random.seed(seed)
            Faker.seed(seed)
    
    def generate_valid_request(
        self,
        crop_type: Optional[str] = None,
        include_variety: bool = True,
        include_location_name: bool = True
    ) -> Dict[str, Any]:
        """
        Generate valid prediction request
        
        Args:
            crop_type: Specific crop type or random if None
            include_variety: Whether to include variety_name
            include_location_name: Whether to include location_name (always included as it's required)
        
        Returns:
            Valid request dictionary
        """
        crop = crop_type or random.choice(self.VALID_CROPS)
        location = random.choice(self.TEST_LOCATIONS)
        
        # Generate sowing date (between 30 and 180 days ago)
        days_ago = random.randint(30, 180)
        sowing_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        request = {
            "crop_type": crop,
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "sowing_date": sowing_date,
            "location_name": location["name"]  # Always include as it's required by API
        }
        
        if include_variety:
            request["variety_name"] = random.choice(self.TEST_VARIETIES[crop])
        
        return request
    
    def generate_invalid_request(self, error_type: str) -> Dict[str, Any]:
        """
        Generate invalid request for specific error scenario
        
        Args:
            error_type: Type of error to generate
                - 'invalid_crop': Invalid crop type
                - 'invalid_coordinates': Out of range coordinates
                - 'invalid_date': Invalid date format
                - 'future_date': Future sowing date
                - 'missing_required': Missing required fields
                - 'invalid_variety': Invalid variety name
                - 'out_of_range_lat': Latitude out of range
                - 'out_of_range_lon': Longitude out of range
        
        Returns:
            Invalid request dictionary
        """
        base_request = self.generate_valid_request(include_variety=False)
        
        if error_type == 'invalid_crop':
            base_request['crop_type'] = random.choice(['rice', 'RICE', 'Ric', 'Corn', 'Barley'])
        
        elif error_type == 'invalid_coordinates':
            base_request['latitude'] = random.choice([999.0, -999.0, 'invalid'])
            base_request['longitude'] = random.choice([999.0, -999.0, 'invalid'])
        
        elif error_type == 'invalid_date':
            base_request['sowing_date'] = random.choice([
                '2024/06/15',  # Wrong format
                '15-06-2024',  # Wrong format
                '2024-13-01',  # Invalid month
                '2024-06-32',  # Invalid day
                'invalid-date'
            ])
        
        elif error_type == 'future_date':
            future_date = datetime.now() + timedelta(days=random.randint(1, 365))
            base_request['sowing_date'] = future_date.strftime("%Y-%m-%d")
        
        elif error_type == 'missing_required':
            # Remove a random required field
            required_fields = ['crop_type', 'latitude', 'longitude', 'sowing_date']
            field_to_remove = random.choice(required_fields)
            del base_request[field_to_remove]
        
        elif error_type == 'invalid_variety':
            base_request['variety_name'] = fake.word() + " " + fake.word()
        
        elif error_type == 'out_of_range_lat':
            base_request['latitude'] = random.choice([-91.0, 91.0, -100.0, 100.0])
        
        elif error_type == 'out_of_range_lon':
            base_request['longitude'] = random.choice([-181.0, 181.0, -200.0, 200.0])
        
        return base_request
    
    def generate_edge_case_request(self, case_type: str) -> Dict[str, Any]:
        """
        Generate edge case request
        
        Args:
            case_type: Type of edge case
                - 'boundary_coordinates': Min/max valid coordinates
                - 'recent_sowing': Very recent sowing date
                - 'old_sowing': Old sowing date (2 years)
                - 'special_characters': Special characters in strings
                - 'long_strings': Extremely long strings
                - 'null_variety': Explicit null variety
                - 'empty_variety': Empty string variety
        
        Returns:
            Edge case request dictionary
        """
        base_request = self.generate_valid_request(include_variety=False)
        
        if case_type == 'boundary_coordinates':
            # Use boundary values for North India
            base_request['latitude'] = random.choice([8.0, 37.0])  # India boundaries
            base_request['longitude'] = random.choice([68.0, 97.0])
        
        elif case_type == 'recent_sowing':
            # Sowing date 15 days ago
            base_request['sowing_date'] = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
        
        elif case_type == 'old_sowing':
            # Sowing date 2 years ago
            base_request['sowing_date'] = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        
        elif case_type == 'special_characters':
            base_request['location_name'] = "Test'; DROP TABLE--"
            base_request['variety_name'] = "<script>alert('xss')</script>"
        
        elif case_type == 'long_strings':
            base_request['location_name'] = "A" * 10000
            base_request['variety_name'] = "B" * 10000
        
        elif case_type == 'null_variety':
            base_request['variety_name'] = None
        
        elif case_type == 'empty_variety':
            base_request['variety_name'] = ""
        
        return base_request
    
    def generate_field_coordinates(
        self,
        num_points: int = 4,
        center_lat: Optional[float] = None,
        center_lon: Optional[float] = None
    ) -> str:
        """
        Generate field polygon coordinates
        
        Args:
            num_points: Number of polygon points (minimum 3)
            center_lat: Center latitude (random if None)
            center_lon: Center longitude (random if None)
        
        Returns:
            Polygon coordinates as string
        """
        if center_lat is None or center_lon is None:
            location = random.choice(self.TEST_LOCATIONS)
            center_lat = location["latitude"]
            center_lon = location["longitude"]
        
        # Generate points around center (roughly 0.01 degree radius)
        points = []
        for i in range(num_points):
            angle = (2 * 3.14159 * i) / num_points
            offset_lat = 0.01 * (1 + random.uniform(-0.2, 0.2)) * (1 if i % 2 == 0 else -1)
            offset_lon = 0.01 * (1 + random.uniform(-0.2, 0.2)) * (1 if i < num_points/2 else -1)
            
            lat = center_lat + offset_lat
            lon = center_lon + offset_lon
            points.append(f"{lon},{lat}")
        
        # Close the polygon
        points.append(points[0])
        
        return ";".join(points)
    
    def generate_load_test_requests(
        self,
        count: int,
        variety_distribution: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple requests for load testing
        
        Args:
            count: Number of requests to generate
            variety_distribution: Distribution of variety inclusion
                Example: {'with_variety': 0.5, 'without_variety': 0.3, 'null_variety': 0.2}
        
        Returns:
            List of request dictionaries
        """
        if variety_distribution is None:
            variety_distribution = {
                'with_variety': 0.6,
                'without_variety': 0.3,
                'null_variety': 0.1
            }
        
        requests = []
        
        for _ in range(count):
            # Determine variety inclusion based on distribution
            rand = random.random()
            cumulative = 0
            include_variety = True
            variety_value = None
            
            for variety_type, prob in variety_distribution.items():
                cumulative += prob
                if rand < cumulative:
                    if variety_type == 'with_variety':
                        include_variety = True
                        variety_value = None  # Will be set by generate_valid_request
                    elif variety_type == 'without_variety':
                        include_variety = False
                    elif variety_type == 'null_variety':
                        include_variety = True
                        variety_value = None
                    break
            
            request = self.generate_valid_request(include_variety=include_variety)
            
            if variety_value is not None:
                request['variety_name'] = variety_value
            
            requests.append(request)
        
        return requests
    
    def get_test_locations(self) -> List[Dict[str, Any]]:
        """
        Get predefined test locations
        
        Returns:
            List of location dictionaries
        """
        return self.TEST_LOCATIONS.copy()
    
    def get_test_varieties(self, crop_type: str) -> List[str]:
        """
        Get test varieties for crop type
        
        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
        
        Returns:
            List of variety names
        """
        return self.TEST_VARIETIES.get(crop_type, []).copy()
    
    def get_random_location(self) -> Dict[str, Any]:
        """Get random test location"""
        return random.choice(self.TEST_LOCATIONS)
    
    def get_random_variety(self, crop_type: str) -> str:
        """Get random variety for crop type"""
        varieties = self.TEST_VARIETIES.get(crop_type, [])
        return random.choice(varieties) if varieties else ""
    
    def get_sowing_date_for_crop(
        self,
        crop_type: str,
        days_ago: Optional[int] = None
    ) -> str:
        """
        Get appropriate sowing date for crop type
        
        Args:
            crop_type: Crop type
            days_ago: Days ago (random if None)
        
        Returns:
            Sowing date in YYYY-MM-DD format
        """
        if days_ago is None:
            days_ago = random.randint(30, 180)
        
        sowing_date = datetime.now() - timedelta(days=days_ago)
        return sowing_date.strftime("%Y-%m-%d")
