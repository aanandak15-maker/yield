# Running Functional Tests - Quick Guide

## Prerequisites

### 1. Start the API Server
```bash
# From the project root directory
python run_api.py
```

The API should be running on `http://localhost:8000`

### 2. Verify API is Running
```bash
curl http://localhost:8000/health
```

### 3. Configure GEE Credentials (Optional)
If you want to test with real-time data collection:
```bash
export GEE_SERVICE_ACCOUNT_KEY=/path/to/your/gee-credentials.json
```

## Running Tests

### Run All Functional Tests
```bash
python -m pytest test_api_intensive/suites/test_functional.py -v
```

### Run Only Basic Endpoint Tests
```bash
python -m pytest test_api_intensive/suites/test_functional.py::TestBasicEndpoints -v
```

### Run Only Coverage Tests
```bash
python -m pytest test_api_intensive/suites/test_functional.py::TestCropAndLocationCoverage -v
```

### Run Specific Test
```bash
# Test health endpoint
python -m pytest test_api_intensive/suites/test_functional.py::TestBasicEndpoints::test_health_endpoint -v

# Test all crop types
python -m pytest test_api_intensive/suites/test_functional.py::TestCropAndLocationCoverage::test_all_crop_types -v
```

### Run with HTML Report
```bash
python -m pytest test_api_intensive/suites/test_functional.py -v --html=test_api_intensive/reports/functional_tests.html --self-contained-html
```

### Run with Detailed Output
```bash
python -m pytest test_api_intensive/suites/test_functional.py -vv -s
```

## Test Collection

### List All Tests Without Running
```bash
python -m pytest test_api_intensive/suites/test_functional.py --collect-only
```

### Count Tests
```bash
python -m pytest test_api_intensive/suites/test_functional.py --collect-only -q
```

## Test Markers

### Run Only Fast Tests
```bash
python -m pytest test_api_intensive/suites/test_functional.py -m fast -v
```

### Run Only Functional Tests
```bash
python -m pytest test_api_intensive/suites/test_functional.py -m functional -v
```

## Troubleshooting

### API Not Running
If you see connection errors:
```
Error: Connection error: HTTPConnectionPool(host='localhost', port=8000)
```

**Solution:** Start the API server first:
```bash
python run_api.py
```

### GEE Authentication Failed
If you see:
```
Error: Failed to collect real-time data: GEE authentication failed
```

**Solutions:**
1. Set up GEE credentials:
   ```bash
   export GEE_SERVICE_ACCOUNT_KEY=/path/to/credentials.json
   ```

2. Or run tests that don't require real-time data (health endpoint, etc.)

### Missing location_name Field
If you see:
```
Error: Field required: location_name
```

**Solution:** This is expected - the API requires location_name. The test data generator has been updated to always include it.

### Endpoint Not Found (404)
If you see:
```
Error: Supported crops endpoint should return 2xx, got 404
```

**Solution:** This is expected if the endpoint isn't implemented. The test will automatically skip.

## Test Configuration

### Change API Base URL
Edit `test_api_intensive/config/test_config.json`:
```json
{
  "api": {
    "base_url": "http://your-api-url:port",
    ...
  }
}
```

### Adjust Performance Thresholds
Edit `test_api_intensive/config/test_config.json`:
```json
{
  "performance": {
    "max_response_time_ms": 5000,
    ...
  },
  "thresholds": {
    "min_yield_tons_per_hectare": 1.0,
    "max_yield_tons_per_hectare": 10.0,
    ...
  }
}
```

## Expected Test Results

### With API Running and GEE Configured
- All 17 tests should pass
- Response times should be within configured thresholds
- Predictions should be within reasonable ranges

### With API Running but No GEE
- Health endpoint test: ✅ PASS
- Supported crops test: ⚠️ SKIP (if endpoint not implemented)
- Prediction tests: ❌ FAIL (GEE authentication required)

### Without API Running
- All tests: ❌ FAIL (connection error)

## Test Summary

Total Tests: **17**

### TestBasicEndpoints (6 tests)
1. test_predict_yield_with_valid_inputs
2. test_predict_yield_without_variety
3. test_predict_field_analysis_with_polygon
4. test_health_endpoint
5. test_supported_crops_endpoint
6. test_all_required_response_fields_present

### TestCropAndLocationCoverage (11 tests)
1. test_all_crop_types[Rice]
2. test_all_crop_types[Wheat]
3. test_all_crop_types[Maize]
4. test_all_test_locations[Bhopal]
5. test_all_test_locations[Lucknow]
6. test_all_test_locations[Chandigarh]
7. test_all_test_locations[Patna]
8. test_different_sowing_dates
9. test_predictions_within_reasonable_ranges
10. test_crop_variety_combinations
11. test_regional_predictions

## Next Steps

After functional tests pass:
1. Run variety selection tests (Task 5)
2. Run validation tests (Task 6)
3. Run performance tests (Task 7)
4. Run full test suite

## Support

For issues or questions:
1. Check the test summary document: `TASK_4_FUNCTIONAL_TESTS_SUMMARY.md`
2. Review test configuration: `test_api_intensive/config/test_config.json`
3. Check API documentation: `CROP_YIELD_API_DOCUMENTATION.md`
