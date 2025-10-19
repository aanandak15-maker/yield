# 🌾 Crop Yield Prediction API Documentation

## Overview

The Crop Yield Prediction API is a comprehensive agricultural technology platform that provides automated crop yield forecasting using real satellite imagery and weather data. Built for North India agriculture, the system leverages Google Earth Engine and OpenWeather APIs to deliver high-accuracy predictions for rice, wheat, and maize crops.

**Base URL**: `http://localhost:8000` (production deployments will have custom URLs)
**Version**: 6.1.0
**Authentication**: None required (for this version)
**Data Sources**: Real GEE satellite data + OpenWeather forecasts (no synthetic/mock data)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip package manager
- Valid Google Earth Engine credentials
- Valid OpenWeather API key

### Installation & Setup

1. **Clone and Install Dependencies**:
```bash
git clone <repository-url>
cd crop-yield-prediction
pip install -r requirements.txt
```

2. **Configure API Credentials**:
Edit `config/api_config.json` with your API keys:
```json
{
  "earth_engine": {
    "service_account": "your-gee-service-account@project.iam.gserviceaccount.com",
    "private_key_path": "path/to/private-key.json",
    "project_id": "your-gee-project-id"
  },
  "openweather": {
    "api_key": "your-openweather-api-key"
  }
}
```

3. **Start the API Server**:
```bash
python3 run_api.py
```

4. **Verify Installation**:
```bash
python3 test_api.py
```

## 🌱 Automatic Variety Selection (New in v6.1.0)

The API now supports **optional variety specification**. When you don't provide a variety name, the system intelligently selects the most appropriate variety based on your location and crop type.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                  Variety Selection Flow                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Location → Region      │
              │  (e.g., Bhopal → MP)    │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Query Regional         │
              │  Varieties by Crop      │
              └─────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌──────────────┐        ┌──────────────┐
        │ Found?       │   No   │ Try "All     │
        │ Select Best  │───────▶│ North India" │
        └──────────────┘        └──────────────┘
                │                       │
                │ Yes                   │
                │                       ▼
                │               ┌──────────────┐
                │               │ Found?       │
                │               │ Select Best  │
                │               └──────────────┘
                │                       │
                │                       │ No
                │                       ▼
                │               ┌──────────────┐
                │               │ Use Global   │
                │               │ Defaults     │
                │               └──────────────┘
                │                       │
                └───────────┬───────────┘
                            ▼
                  ┌──────────────────┐
                  │ Return Variety + │
                  │ Selection Meta   │
                  └──────────────────┘
```

### Selection Criteria

1. **Regional Prevalence**: Varieties commonly grown in your location's region
2. **Yield Potential**: Highest-yielding varieties prioritized
3. **Database Validation**: Selected variety must exist in variety database

### Global Default Rankings

If no regional varieties are found, the system uses these defaults:

| Crop Type | Priority Order |
|-----------|----------------|
| **Rice** | IR-64 → Basmati 370 → Swarna |
| **Wheat** | HD 3086 → PBW 725 → C 306 |
| **Maize** | DHM 117 → HQPM 1 → Baby Corn Hybrid |

### Response Transparency

When variety is auto-selected, the response includes:

- **variety_used**: The actual variety used for prediction
- **variety_assumed**: `true` (indicates auto-selection)
- **default_variety_selection**: Object with selection details
  - `region`: Region used for selection
  - `reason`: Selection reason ("regional_highest_yield", "regional_fallback", "global_default")
  - `yield_potential`: Yield potential of selected variety
  - `alternatives`: Other varieties considered

### Example Comparison

**Traditional Request (with variety)**:
```json
{
  "crop_type": "Rice",
  "variety_name": "Basmati 370",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "sowing_date": "2024-07-21"
}
```

**New Request (auto-select variety)**:
```json
{
  "crop_type": "Rice",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "sowing_date": "2024-07-21"
}
```

Both requests work! The second one will automatically select the best variety for Delhi's region.

## 📋 Input Requirements & Validation

### Required Inputs for Yield Prediction

#### ✅ **Minimum Required Parameters**:
```json
{
  "crop_type": "Rice|Wheat|Maize",
  "latitude": -90.0_to_90.0,
  "longitude": -180.0_to_180.0,
  "sowing_date": "YYYY-MM-DD"
}
```

#### 🌱 **Optional Parameters**:
```json
{
  "variety_name": "exact_variety_name",  // Optional - system auto-selects based on location
  "location_name": "field_identifier",
  "use_real_time_data": true
}
```

**Note**: When `variety_name` is not provided, the system automatically selects the most appropriate variety based on:
1. **Regional prevalence**: Varieties commonly grown in your location
2. **Yield potential**: Highest-yielding varieties for the region
3. **Fallback logic**: Regional → All North India → Global defaults

The response will include `variety_assumed: true` and detailed selection metadata when automatic selection is used.

#### 🗺️ **Location Options** (Choose ONE):

**Option 1: GPS Coordinates** (Recommended)
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "location_name": "Optional field identifier"
}
```

**Option 2: Field Polygon** (Most Accurate)
```json
{
  "field_coordinates": "lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4",
  "state": "Optional state name"
}
```

### 📊 Input Validation Rules

#### Crop & Variety Requirements
```json
// ✅ VALID FORMATS
"crop_type": ["Rice", "Wheat", "Maize"],
"variety_name": ["PR 126", "IR-64", "C 306", "HD 3086", "HQPM 1"],  // Optional
"variety_name": null,    // System auto-selects variety
// Omit variety_name entirely for automatic selection

// ❌ INVALID - Will Return Error
"crop_type": "rice",     // Wrong case
"variety_name": "C-70",  // Invalid variety name (if provided)
```

#### Location Requirements
```json
// ✅ VALID FORMATS
"latitude": 28.6139,      // Decimal degrees
"longitude": 77.2090,     // Decimal degrees (East positive)
"field_coordinates": "28.368704,77.540929,28.368928,77.540854,..."

// ❌ INVALID FORMATS
"latitude": "28°N",       // Must be numeric
"longitude": "77°W",      // Must be decimal degrees
"field_coordinates": "28.368704 77.540929"  // Wrong separator
```

#### Date Requirements
```json
// ✅ VALID FORMATS
"sowing_date": "2024-07-21",  // YYYY-MM-DD
"sowing_date": "2024-01-15"   // Past or current dates only

// ❌ INVALID FORMATS
"sowing_date": "21-07-2024",  // Wrong format (MM-DD-YYYY)
"sowing_date": "2025-12-31"   // Future dates not allowed
```

#### Coverage Validation
The API validates geographic coverage automatically:
- **Supported Region**: Only North India (26-32°N, 75-85°E)
- **Coverage Check**: Auto-validates against Indo-Gangetic plain
- **Error Response**: `"Location not supported"` for unsupported areas

### 📤 Request Formatting Examples

#### 📍 **Standard GPS Request (with variety)**:
```bash
curl -X POST http://localhost:8000/predict/yield \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Rice",
    "variety_name": "C 306",
    "location_name": "Delhi NCR Field",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "sowing_date": "2024-07-21"
  }'
```

#### 🌾 **Request WITHOUT Variety (Auto-Selection)**:
```bash
curl -X POST http://localhost:8000/predict/yield \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Rice",
    "location_name": "Bhopal Field",
    "latitude": 23.2599,
    "longitude": 77.4126,
    "sowing_date": "2024-06-15"
  }'
```
**Note**: When variety is omitted, the system automatically selects the most appropriate variety based on location and crop type.

#### 🏞️ **Field Polygon Request**:
```bash
curl -X POST http://localhost:8000/predict/field-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Rice",
    "variety_name": "PR 126",
    "sowing_date": "2024-07-21",
    "field_coordinates": "28.368704,77.540929,28.368928,77.540854,28.368978,77.541109,28.368766,77.541182",
    "location_name": "Haryana Rice Field",
    "state": "HARYANA"
  }'
```

### ⚠️ What We DON'T Require

| ❌ **NOT Required** | 💡 **Why Not Needed** |
|---------------------|----------------------|
| Crop variety name | System auto-selects based on location (optional parameter) |
| Historical yield data | We use government statistics & satellite data |
| Soil test results | We use NDVI + terrain analysis |
| Irrigation records | We calculate optimal irrigation using weather + growth stages |
| Manual weather monitoring | We use OpenWeather API |
| Farm management details | We focus on crop-specific intelligence |

### 📏 Supported Parameter Ranges

| Parameter | Valid Range | Notes |
|-----------|-------------|-------|
| `latitude` | [-90, 90] | Decimal degrees |
| `longitude` | [-180, 180] | Decimal degrees (East positive) |
| `sowing_date` | Past dates only | YYYY-MM-DD format |
| `field_coordinates` | 3-50 points | Comma-separated lat,lon pairs |
 touristique| North India only | Indo-Gangetic plain coverage |

### 🔍 Pre-Flight Validation

The API automatically validates requests before processing:

1. **Crop Variety Check**: Validates against our database
2. **Location Coverage**: Confirms North India coverage
3. **Date Sanity**: Ensures sowing date is not in future
4. **Coordinate Format**: Validates GPS format and ranges
5. **Region Context**: Uses appropriate ML model for location

## 📋 API Endpoints

### 1. Yield Prediction

**Endpoint**: `POST /predict/yield`

Predict crop yield based on location, crop type, variety (optional), and sowing date.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `crop_type` | string | ✅ Yes | Crop type: "Rice", "Wheat", or "Maize" |
| `variety_name` | string | ⭕ Optional | Specific variety name. If omitted, system auto-selects based on location |
| `location_name` | string | ⭕ Optional | Field identifier or location name |
| `latitude` | float | ✅ Yes | Latitude in decimal degrees (-90 to 90) |
| `longitude` | float | ✅ Yes | Longitude in decimal degrees (-180 to 180) |
| `sowing_date` | string | ✅ Yes | Sowing date in YYYY-MM-DD format |
| `use_real_time_data` | boolean | ⭕ Optional | Use real-time satellite/weather data (default: true) |

#### Automatic Variety Selection

When `variety_name` is not provided (or is `null` or empty string), the system automatically selects the most appropriate variety using this logic:

1. **Regional Selection**: Query varieties prevalent in the location's region (e.g., Madhya Pradesh, Punjab)
2. **Yield Optimization**: Select variety with highest yield potential for the region
3. **Fallback to North India**: If no regional varieties found, use "All North India" varieties
4. **Global Defaults**: Final fallback to crop-specific defaults:
   - **Rice**: IR-64 → Basmati 370 → Swarna
   - **Wheat**: HD 3086 → PBW 725 → C 306
   - **Maize**: DHM 117 → HQPM 1 → Baby Corn Hybrid

#### Example Request (With Variety):
```json
{
  "crop_type": "Rice",
  "variety_name": "C 306",
  "location_name": "Delhi NCR Field",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "sowing_date": "2024-07-21",
  "use_real_time_data": true
}
```

#### Example Request (Without Variety - Auto-Selection):
```json
{
  "crop_type": "Rice",
  "location_name": "Bhopal Field",
  "latitude": 23.2599,
  "longitude": 77.4126,
  "sowing_date": "2024-06-15",
  "use_real_time_data": true
}
```

#### Response (With User-Specified Variety):
```json
{
  "prediction_id": "pred_20241013_143500",
  "timestamp": "2024-10-13T14:35:00Z",
  "prediction": {
    "yield_tons_per_hectare": 4.67,
    "variety_used": "C 306",
    "variety_assumed": false,
    "confidence_score": 0.87,
    "location": "Delhi NCR Field"
  },
  "model": {
    "algorithm": "Gradient Boosting",
    "location_used": "North India Regional",
    "feature_count": 25
  },
  "factors": {
    "variety_characteristics": {
      "maturity_days": 150,
      "yield_potential": "5.0-6.0 t/ha",
      "drought_tolerance": "Medium"
    },
    "environmental_adjustments": {
      "soil_moisture_effect": 1.05,
      "temperature_stress": 0.98,
      "rainfall_impact": 1.02
    }
  },
  "data_sources": {
    "satellite_data_points": 45,
    "weather_data_points": 30,
    "data_freshness_hours": 6
  },
  "processing_time_seconds": 2.34
}
```

#### Response (With Auto-Selected Variety):
```json
{
  "prediction_id": "Rice_Bhopal_20251019_143022",
  "timestamp": "2025-10-19T14:30:22Z",
  "input": {
    "crop_type": "Rice",
    "variety_name": null,
    "location": {
      "name": "Bhopal",
      "latitude": 23.2599,
      "longitude": 77.4126
    },
    "sowing_date": "2024-06-15",
    "growth_days": 127,
    "use_real_time_data": true
  },
  "prediction": {
    "yield_tons_per_hectare": 5.8,
    "variety_used": "Swarna",
    "variety_assumed": true,
    "lower_bound": 5.2,
    "upper_bound": 6.4,
    "confidence_score": 0.85,
    "variety_adjusted_yield": 5.9
  },
  "model": {
    "location_used": "bhopal_training",
    "algorithm": "gradient_boosting",
    "model_timestamp": "20251019_120000",
    "feature_count": 15
  },
  "factors": {
    "variety_characteristics": {
      "maturity_days": 140,
      "yield_potential": 5.8,
      "drought_tolerance": "Medium"
    },
    "default_variety_selection": {
      "region": "Madhya Pradesh",
      "reason": "regional_highest_yield",
      "yield_potential": 5.8,
      "alternatives": ["IR-64", "Basmati 370"]
    },
    "environmental_adjustments": {
      "heat_stress_penalty": 0.05,
      "drought_penalty": 0.02,
      "cold_stress_penalty": 0.0,
      "optimal_temp_bonus": 0.15
    },
    "data_quality": 0.92
  },
  "data_sources": {
    "satellite_data_points": 30,
    "weather_data_points": 56,
    "data_freshness_hours": 24
  },
  "processing_time_seconds": 2.34,
  "api_version": "6.1.0"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `prediction.variety_used` | string | The actual variety used for prediction (specified or auto-selected) |
| `prediction.variety_assumed` | boolean | `true` if variety was auto-selected, `false` if user-specified |
| `factors.default_variety_selection` | object | Present only when `variety_assumed=true`. Contains selection metadata |
| `factors.default_variety_selection.region` | string | Region used for variety selection |
| `factors.default_variety_selection.reason` | string | Selection reason: "regional_highest_yield", "regional_fallback", or "global_default" |
| `factors.default_variety_selection.yield_potential` | float | Yield potential of selected variety (t/ha) |
| `factors.default_variety_selection.alternatives` | array | Other varieties considered (top 3) |

### 2. Field Analysis with Area Calculation

**Endpoint**: `POST /predict/field-analysis`

Calculate field area from polygon coordinates and provide yield prediction.

**Request Body**:
```json
{
  "crop_type": "Rice",
  "variety_name": "C 306",
  "sowing_date": "2024-07-21",
  "field_coordinates": "28.368704,77.540929,28.368928,77.540854,28.368978,77.541109,28.368766,77.541182",
  "location_name": "Gurugram Rice Field",
  "state": "HARYANA"
}
```

**Response**:
```json
{
  "field_analysis": {
    "area_hectares": 0.069,
    "area_sqm": 690,
    "centroid": [28.3689, 77.5410],
    "field_class": "Small Farm (Marginal holding)"
  },
  "yield_prediction": {
    "tons_per_hectare": 4.67,
    "confidence_score": 0.86,
    "economic_value_rs": 32340
  },
  "ground_truth": {
    "district_average": 4.2,
    "region_range": "3.8-4.8",
    "crop_condition": "Good irrigation"
  }
}
```

### 3. Historical Weather Analysis

**Endpoint**: `GET /weather/historical/{lat}/{lon}/{days}`

**Parameters**:
- `lat`: Latitude (float)
- `lon`: Longitude (float)
- `days`: Number of historical days (int, max 30)

**Response**:
```json
{
  "location": {
    "latitude": 28.6139,
    "longitude": 77.2090
  },
  "weather_summary": {
    "total_rainfall_mm": 45.2,
    "avg_temperature_c": 28.5,
    "avg_humidity_percent": 65,
    "dominant_weather": "Partly cloudy"
  },
  "daily_data": [
    {
      "date": "2024-10-13",
      "temperature_max": 32.1,
      "temperature_min": 24.8,
      "humidity": 62,
      "rainfall_mm": 0.5,
      "wind_speed_kmh": 12.5,
      "description": "Clear sky"
    }
  ]
}
```

### 4. API Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-10-13T14:35:00Z",
  "services": {
    "google_earth_engine": "operational",
    "openweather_api": "operational",
    "machine_learning_models": "loaded",
    "database": "connected"
  },
  "version": "6.1.0"
}
```

### 5. Supported Crops & Varieties

**Endpoint**: `GET /crops/supported`

**Response**:
```json
{
  "supported_crops": [
    {
      "name": "Rice",
      "scientific_name": "Oryza sativa",
      "states": ["PUNJAB", "HARYANA", "UP", "BIHAR", "MP"],
      "varieties": [
        {"name": "C 306", "maturity_days": 150, "yield_potential": "5.0-6.0"},
        {"name": "PR 126", "maturity_days": 140, "yield_potential": "4.5-5.5"},
        {"name": "IR-64", "maturity_days": 130, "yield_potential": "4.0-5.0"}
      ]
    },
    {
      "name": "Wheat",
      "scientific_name": "Triticum aestivum",
      "states": ["PUNJAB", "HARYANA", "UP", "BIHAR", "MP"],
      "varieties": [
        {"name": "HD 3086", "maturity_days": 140, "yield_potential": "5.5-6.5"},
        {"name": "PBW 725", "maturity_days": 135, "yield_potential": "5.0-6.0"}
      ]
    },
    {
      "name": "Maize",
      "scientific_name": "Zea mays",
      "states": ["PUNJAB", "HARYANA", "UP"],
      "varieties": [
        {"name": "HQPM 1", "maturity_days": 85, "yield_potential": "6.0-7.0"}
      ]
    }
  ]
}
```

### 6. Sowing Date Recommendations

**Endpoint**: `POST /sowing/recommend`

**Request Body**:
```json
{
  "crop_type": "Rice",
  "variety_name": "C 306",
  "state": "HARYANA",
  "target_sowing_month": 7
}
```

**Response**:
```json
{
  "recommendations": {
    "optimal_sowing_window": {
      "start": "2024-06-15",
      "end": "2024-07-15"
    },
    "recommended_date": "2024-07-10",
    "confidence_score": 0.92,
    "season": "Kharif",
    "risk_assessment": "Low risk - optimal weather conditions expected"
  },
  "variety_requirements": {
    "seed_rate": 20.0,
    "irrigation_schedule": "Weekly during early growth",
    "temperature_optimal": "25-30°C"
  }
}
```

## 📊 Data Models

### Crop Types
- **Rice** (Oryza sativa) - Kharif season, 140-160 days maturity
- **Wheat** (Triticum aestivum) - Rabi season, 130-140 days maturity
- **Maize** (Zea mays) - Kharif season, 80-90 days maturity

### Geographic Coverage
- **States**: Punjab, Haryana, Uttar Pradesh, Bihar, Madhya Pradesh
- **Region**: North India (primarily Indo-Gangetic plain)
- **Coordinates**: Supports field-level precision (polygon boundaries)

### Data Sources
- **Satellite Imagery**: Sentinel-2 (Google Earth Engine)
- **Weather Data**: OpenWeather API (historical + forecast)
- **Soil Data**: Integrated terrain analysis
- **Agricultural Statistics**: Government yield databases (2019-2024)

## 🔧 SDK & Tools

### Python Client Library

```python
import requests
import json

class CropYieldAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def predict_yield(self, crop_type, lat, lon, sowing_date, variety=None, location_name=None):
        """
        Predict crop yield with optional variety specification.
        
        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
            lat: Latitude
            lon: Longitude
            sowing_date: Sowing date (YYYY-MM-DD)
            variety: Optional variety name (auto-selected if not provided)
            location_name: Optional location identifier
        """
        data = {
            "crop_type": crop_type,
            "latitude": lat,
            "longitude": lon,
            "sowing_date": sowing_date,
            "use_real_time_data": True
        }
        
        # Only include variety if specified
        if variety:
            data["variety_name"] = variety
        
        if location_name:
            data["location_name"] = location_name

        response = requests.post(f"{self.base_url}/predict/yield", json=data)
        return response.json()

# Usage Example 1: With specific variety
api = CropYieldAPI()
result = api.predict_yield("Rice", 28.6139, 77.2090, "2024-07-21", variety="C 306")
print(f"Predicted yield: {result['prediction']['yield_tons_per_hectare']} t/ha")
print(f"Variety assumed: {result['prediction']['variety_assumed']}")  # False

# Usage Example 2: Auto-select variety based on location
result = api.predict_yield("Rice", 23.2599, 77.4126, "2024-06-15", location_name="Bhopal")
print(f"Predicted yield: {result['prediction']['yield_tons_per_hectare']} t/ha")
print(f"Variety used: {result['prediction']['variety_used']}")  # Auto-selected
print(f"Variety assumed: {result['prediction']['variety_assumed']}")  # True
if result['prediction']['variety_assumed']:
    selection = result['factors']['default_variety_selection']
    print(f"Selection reason: {selection['reason']}")
    print(f"Region: {selection['region']}")
```

### Command Line Tools

```bash
# Quick prediction with specific variety
python3 -c "
import requests
data = {'crop_type': 'Rice', 'variety_name': 'PR 126', 'latitude': 28.6, 'longitude': 77.2, 'sowing_date': '2024-07-01', 'use_real_time_data': True}
resp = requests.post('http://localhost:8000/predict/yield', json=data).json()
print(f'Yield: {resp[\"prediction\"][\"yield_tons_per_hectare\"]} t/ha')
print(f'Variety assumed: {resp[\"prediction\"][\"variety_assumed\"]}')
"

# Quick prediction with auto-selected variety
python3 -c "
import requests
data = {'crop_type': 'Rice', 'latitude': 23.26, 'longitude': 77.41, 'sowing_date': '2024-06-15', 'location_name': 'Bhopal'}
resp = requests.post('http://localhost:8000/predict/yield', json=data).json()
print(f'Yield: {resp[\"prediction\"][\"yield_tons_per_hectare\"]} t/ha')
print(f'Variety used: {resp[\"prediction\"][\"variety_used\"]}')
print(f'Selection reason: {resp[\"factors\"][\"default_variety_selection\"][\"reason\"]}')
"

# Health check
curl -X GET http://localhost:8000/health

# Field analysis with coordinates (variety optional)
curl -X POST http://localhost:8000/predict/field-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Rice",
    "sowing_date": "2024-07-21",
    "field_coordinates": "28.368704,77.540929,28.368928,77.540854,28.368978,77.541109,28.368766,77.541182",
    "location_name": "Gurugram Field",
    "state": "HARYANA"
  }'
```

## 📈 Performance & Limits

- **Prediction Speed**: < 3 seconds per request
- **Accuracy**: 85-92% confidence (validated against ground truth)
- **Supported Area**: North India (5 states)
- **Concurrent Users**: Up to 100 simultaneous predictions
- **Data Freshness**: < 6 hours for satellite data
- **QPS Limit**: 10 requests per minute per IP

## 🛠️ Troubleshooting

### Common Error Codes

- **400 Bad Request**: Invalid input parameters
- **503 Service Unavailable**: External API rate limits exceeded
- **500 Internal Server Error**: Model or data processing error

### Error Recovery

```python
try:
    response = requests.post('http://localhost:8000/predict/yield', json=data, timeout=30)
    response.raise_for_status()
    result = response.json()
except requests.exceptions.Timeout:
    print("Request timed out - retry with smaller area or fewer data points")
except requests.exceptions.HTTPError as e:
    if response.status_code == 503:
        print("API rate limit exceeded - wait and retry")
    else:
        print(f"HTTP Error: {e}")
```

## 📞 Support & Licensing

- **Documentation**: This file serves as complete API reference
- **Issue Tracking**: GitHub repository issues
- **License**: MIT License for non-commercial agricultural use
- **Contact**: API support team available for enterprise integrations

## 🔗 Integration Examples

For full working examples, see:
- `test_api.py` - Comprehensive test suite
- `predict_field_yield.py` - Field prediction example
- `field_mapping_and_area.py` - Area calculation example
- `src/dashboard.html` - Interactive web interface

---

**Last Updated**: October 19, 2025  
**API Version**: 6.1.0  
**Environment**: Production Ready

## 🆕 Version 6.1.0 Changes

### Optional Variety Selection
- **variety_name** parameter is now optional
- System automatically selects most appropriate variety based on location when not specified
- Selection uses regional prevalence data and yield potential metrics
- Response includes transparency fields: `variety_used`, `variety_assumed`, and `default_variety_selection`

### Selection Logic
1. **Regional Selection**: Queries varieties prevalent in location's region (e.g., Punjab, Madhya Pradesh)
2. **Yield Optimization**: Selects variety with highest yield potential for the region
3. **Fallback to North India**: Uses "All North India" varieties if no regional match
4. **Global Defaults**: Final fallback to crop-specific defaults (IR-64 for Rice, HD 3086 for Wheat, DHM 117 for Maize)

### Backward Compatibility
- All existing requests with `variety_name` work unchanged
- No breaking changes to API contract
- Response format enhanced but maintains all existing fields
