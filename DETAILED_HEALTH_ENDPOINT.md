# Detailed Health Check Endpoint

## Overview

The `/health/detailed` endpoint provides comprehensive health and status information about the Crop Yield Prediction API, including environment versions, model loading status, and service health indicators.

## Endpoint Details

**URL:** `/health/detailed`  
**Method:** `GET`  
**Authentication:** None required

## Response Structure

```json
{
  "status": "healthy" | "degraded" | "error",
  "timestamp": "2025-10-18T12:34:56.789012",
  "version": "6.0.0",
  "environment": {
    "numpy_version": "2.3.3",
    "sklearn_version": "1.7.2",
    "joblib_version": "1.5.2"
  },
  "models": {
    "total_loaded": 15,
    "locations": 5,
    "by_location": {
      "bhopal_training": {
        "algorithms": ["ridge", "gradient_boosting", "random_forest"],
        "count": 3
      },
      "lucknow_training": {
        "algorithms": ["ridge", "gradient_boosting", "random_forest"],
        "count": 3
      },
      "chandigarh_training": {
        "algorithms": ["ridge", "gradient_boosting", "random_forest"],
        "count": 3
      },
      "patna_training": {
        "algorithms": ["ridge", "gradient_boosting", "random_forest"],
        "count": 3
      },
      "north_india_regional": {
        "algorithms": ["ridge", "gradient_boosting", "random_forest"],
        "count": 3
      }
    },
    "fallback_mode": false
  },
  "components": {
    "api_manager": "ready",
    "gee_client": "ready",
    "weather_client": "ready",
    "variety_db": "ready",
    "sowing_intelligence": "ready"
  }
}
```

## Response Fields

### Top-Level Fields

- **status** (string): Overall service health status
  - `"healthy"`: All models loaded successfully, not in fallback mode
  - `"degraded"`: Running with fallback models or limited model coverage
  - `"error"`: Health check encountered an error

- **timestamp** (string): ISO 8601 timestamp of the health check

- **version** (string): API version number

### Environment Section

Contains version information for critical dependencies:

- **numpy_version**: NumPy library version (should be 2.x for compatibility)
- **sklearn_version**: scikit-learn library version (should be 1.7.x for compatibility)
- **joblib_version**: joblib library version (should be 1.5.x for compatibility)

### Models Section

Provides detailed information about loaded ML models:

- **total_loaded** (integer): Total number of models successfully loaded
- **locations** (integer): Number of locations with loaded models
- **by_location** (object): Breakdown of models by location
  - Each location contains:
    - **algorithms** (array): List of algorithm types available
    - **count** (integer): Number of models for this location
- **fallback_mode** (boolean): Whether the service is using fallback models
  - `true`: Using simple fallback models (degraded performance)
  - `false`: Using trained ML models (optimal performance)

### Components Section

Status of various service components:

- **api_manager**: API credentials manager status
- **gee_client**: Google Earth Engine client status
- **weather_client**: Weather data client status
- **variety_db**: Crop variety database status
- **sowing_intelligence**: Sowing date intelligence module status

## Usage Examples

### cURL

```bash
curl -X GET http://localhost:8000/health/detailed
```

### Python (requests)

```python
import requests

response = requests.get("http://localhost:8000/health/detailed")
health_data = response.json()

print(f"Service Status: {health_data['status']}")
print(f"Models Loaded: {health_data['models']['total_loaded']}")
print(f"Fallback Mode: {health_data['models']['fallback_mode']}")
print(f"NumPy Version: {health_data['environment']['numpy_version']}")
```

### JavaScript (fetch)

```javascript
fetch('http://localhost:8000/health/detailed')
  .then(response => response.json())
  .then(data => {
    console.log('Service Status:', data.status);
    console.log('Models Loaded:', data.models.total_loaded);
    console.log('Fallback Mode:', data.models.fallback_mode);
  });
```

## Status Interpretation

### Healthy Status

A `"healthy"` status indicates:
- All expected models (15 total: 5 locations × 3 algorithms) are loaded
- Not running in fallback mode
- All components are operational
- Environment versions are compatible

**Action:** No action required. Service is operating optimally.

### Degraded Status

A `"degraded"` status indicates one of:
- Running in fallback mode (using simple regression models)
- Some models failed to load
- Partial model coverage

**Action:** 
1. Check logs for model loading errors
2. Verify NumPy and scikit-learn versions match model requirements
3. Consider retraining models with current environment versions
4. Service will continue to operate but predictions may be less accurate

### Error Status

An `"error"` status indicates:
- Health check itself encountered an error
- Critical service failure

**Action:**
1. Check API logs for detailed error information
2. Verify service is running correctly
3. Restart service if necessary

## Monitoring and Alerting

### Recommended Monitoring

Monitor these key metrics:

1. **Service Status**: Alert if status is not "healthy"
2. **Model Count**: Alert if `total_loaded < 15`
3. **Fallback Mode**: Alert if `fallback_mode = true`
4. **Environment Versions**: Alert if versions don't match requirements

### Example Monitoring Script

```python
import requests
import time

def monitor_health():
    response = requests.get("http://localhost:8000/health/detailed")
    data = response.json()
    
    # Check status
    if data['status'] != 'healthy':
        alert(f"Service status is {data['status']}")
    
    # Check model count
    if data['models']['total_loaded'] < 15:
        alert(f"Only {data['models']['total_loaded']} models loaded (expected 15)")
    
    # Check fallback mode
    if data['models']['fallback_mode']:
        alert("Service running in fallback mode")
    
    return data

# Run every 5 minutes
while True:
    monitor_health()
    time.sleep(300)
```

## Comparison with Basic Health Endpoint

The basic `/health` endpoint provides minimal information:
- Simple status check
- Component availability
- Model count only

The `/health/detailed` endpoint provides:
- Environment version information
- Detailed model breakdown by location
- Fallback mode indicator
- More granular status information

Use `/health` for simple uptime checks and `/health/detailed` for comprehensive diagnostics and monitoring.

## Testing

A test script is provided to verify the endpoint functionality:

```bash
python test_detailed_health_endpoint.py
```

This script will:
1. Test the `/health/detailed` endpoint
2. Validate response structure
3. Compare with basic `/health` endpoint
4. Display detailed results

## Requirements Satisfied

This endpoint satisfies **Requirement 3.4** from the model compatibility fix specification:

> WHEN the API health check is called THEN it SHALL report the number of successfully loaded models and any compatibility issues

The endpoint provides:
- ✅ Environment versions (NumPy, scikit-learn, joblib)
- ✅ Model loading status (total loaded, by location)
- ✅ Fallback mode indicator
- ✅ Overall service status ('healthy' or 'degraded')
