# Running Error Handling Tests

This guide explains how to run the error handling test suite for the Crop Yield Prediction API.

## Overview

The error handling test suite (`test_error_handling.py`) validates that the API properly handles various error scenarios including:

- API errors (400, 404, 422, 500, 503)
- External service failures (GEE, OpenWeather, database, models)
- Variety selection errors
- Timeout and malformed request handling

## Test Coverage

### Task 9.1: API Error Tests ✓
- 400 Bad Request scenarios (invalid crop type, missing fields)
- 404 Not Found (invalid endpoints, wrong HTTP methods)
- 422 Unprocessable Entity (validation errors for coordinates, dates, formats)
- Error message clarity and actionability
- No sensitive data exposure in errors

### Task 9.2: External Service Failure Tests ⧗
- GEE unavailability handling (requires mock service)
- OpenWeather API failure handling (requires mock service)
- Database connection failure handling (requires test database)
- Model loading failure handling (requires test environment)
- 503 Service Unavailable response format

**Note:** Most external service failure tests are marked as `skip` because they require mock service infrastructure. These will be implemented when mock services are available.

### Task 9.3: Variety Selection Error Tests ✓
- Invalid variety name errors
- Variety not available for crop type errors
- Error messages suggesting manual variety specification
- NoVarietiesAvailable scenario (requires test database - marked as skip)
- Variety database query failures (requires test database - marked as skip)

### Task 9.4: Timeout and Malformed Request Tests ✓
- Invalid JSON handling
- Malformed JSON (missing quotes, syntax errors)
- Empty request body
- Null values in required fields
- Wrong data types
- Extra unexpected fields
- Appropriate error codes for malformed requests
- Request timeout handling (requires slow endpoint simulation - marked as skip)

## Prerequisites

1. **API Server Running:**
   ```bash
   # Start the API server
   python run_api.py
   ```

2. **Test Environment:**
   ```bash
   # Ensure you're in the test directory
   cd test_api_intensive
   
   # Activate virtual environment if using one
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```

3. **Configuration:**
   - Ensure `config/test_config.json` has correct API base URL
   - Default: `http://localhost:8000`

## Running Tests

### Run All Error Handling Tests

```bash
pytest suites/test_error_handling.py -v
```

### Run Specific Test Classes

```bash
# API error tests only
pytest suites/test_error_handling.py::TestAPIErrors -v

# Variety selection error tests only
pytest suites/test_error_handling.py::TestVarietySelectionErrors -v

# Timeout and malformed request tests only
pytest suites/test_error_handling.py::TestTimeoutAndMalformedRequests -v
```

### Run Specific Tests

```bash
# Test 400 Bad Request handling
pytest suites/test_error_handling.py::TestAPIErrors::test_400_bad_request_invalid_crop_type -v

# Test invalid variety name error
pytest suites/test_error_handling.py::TestVarietySelectionErrors::test_invalid_variety_name_error -v

# Test malformed JSON handling
pytest suites/test_error_handling.py::TestTimeoutAndMalformedRequests::test_invalid_json_handling -v
```

### Run Only Implemented Tests (Skip Pending)

```bash
# Skip tests that require mock infrastructure
pytest suites/test_error_handling.py -v --ignore-skip
```

### Run with Markers

```bash
# Run only error_handling tests
pytest suites/test_error_handling.py -m error_handling -v

# Run only critical error handling tests
pytest suites/test_error_handling.py -m "error_handling and critical" -v

# Run fast error handling tests (exclude slow tests)
pytest suites/test_error_handling.py -m "error_handling and not slow" -v
```

### Generate HTML Report

```bash
pytest suites/test_error_handling.py --html=reports/error_handling_report.html --self-contained-html
```

## Test Results Interpretation

### Successful Test Output

```
test_error_handling.py::TestAPIErrors::test_400_bad_request_invalid_crop_type PASSED
test_error_handling.py::TestAPIErrors::test_404_not_found_invalid_endpoint PASSED
test_error_handling.py::TestVarietySelectionErrors::test_invalid_variety_name_error PASSED
```

### Skipped Tests

```
test_error_handling.py::TestExternalServiceFailures::test_gee_unavailability_handling SKIPPED
```

Skipped tests are documented and will be implemented when the required infrastructure (mock services, test database) is available.

### Failed Tests

If tests fail, check:
1. Is the API server running?
2. Is the API returning expected error codes?
3. Are error messages properly formatted?
4. Check the detailed error output for specifics

## Expected Behavior

### API Error Tests
- **400 Bad Request:** Invalid input (wrong crop type, missing fields)
- **404 Not Found:** Invalid endpoints or wrong HTTP methods
- **422 Unprocessable Entity:** Validation errors (invalid coordinates, future dates, wrong formats)
- **Error Messages:** Clear, actionable, no sensitive data

### Variety Selection Error Tests
- Invalid variety names should return 4xx error
- Error messages should suggest alternatives (auto-selection or valid varieties)
- Variety-crop mismatches should be caught

### Malformed Request Tests
- Invalid JSON should return 400 error
- Missing required fields should return 4xx error
- Wrong data types should return 4xx error
- Extra fields should be handled gracefully (accept and ignore, or reject with clear error)

## Troubleshooting

### API Not Responding

```bash
# Check if API is running
curl http://localhost:8000/health

# If not, start it
python run_api.py
```

### Import Errors

```bash
# Ensure you're in the test directory
cd test_api_intensive

# Install dependencies
pip install -r requirements.txt
```

### Configuration Issues

```bash
# Verify configuration
python verify_config.py

# Check API base URL
cat config/test_config.json | grep base_url
```

### Tests Timing Out

```bash
# Increase timeout in pytest.ini or use command line
pytest suites/test_error_handling.py --timeout=60
```

## Test Statistics

- **Total Tests:** 27
- **Implemented:** 18
- **Skipped (Pending Infrastructure):** 9
- **Test Classes:** 4
- **Requirements Covered:** 5.1, 5.2, 5.3, 5.4, 5.6, 5.7, 5.8, 5.9

## Next Steps

To complete the error handling test suite:

1. **Implement Mock Services:**
   - Mock Google Earth Engine service
   - Mock OpenWeather API service
   - Enable testing of external service failures

2. **Set Up Test Database:**
   - Create test database that can be manipulated
   - Enable testing of database failures
   - Enable testing of NoVarietiesAvailable scenario

3. **Implement Slow Endpoint Simulation:**
   - Add network delay simulation
   - Enable testing of timeout scenarios

4. **Add Integration Tests:**
   - Test actual external service integration
   - Test graceful degradation and fallback behavior

## Related Documentation

- [Test Suite Overview](README.md)
- [Running Functional Tests](RUNNING_FUNCTIONAL_TESTS.md)
- [Running Validation Tests](RUNNING_VALIDATION_TESTS.md)
- [Test Configuration](config/test_config.json)

## Requirements Mapping

| Requirement | Test Coverage | Status |
|-------------|---------------|--------|
| 5.1 - External API unavailability | TestExternalServiceFailures | Partial (needs mocks) |
| 5.2 - Database connection failures | TestExternalServiceFailures | Partial (needs test DB) |
| 5.3 - Model loading failures | TestExternalServiceFailures | Partial (needs test env) |
| 5.4 - Invalid JSON/malformed requests | TestTimeoutAndMalformedRequests | ✓ Complete |
| 5.6 - Variety selection failures | TestVarietySelectionErrors | ✓ Complete |
| 5.7 - Graceful degradation | TestExternalServiceFailures | Partial (needs mocks) |
| 5.8 - Clear error messages | TestAPIErrors | ✓ Complete |
| 5.9 - Timeout handling | TestTimeoutAndMalformedRequests | Partial (needs simulation) |

## Summary

The error handling test suite provides comprehensive coverage of API error scenarios that can be tested without additional infrastructure. Tests requiring mock services or test databases are documented and marked as skipped, ready to be implemented when the infrastructure is available.

All implemented tests verify:
- Correct HTTP status codes
- Clear and actionable error messages
- No sensitive data exposure
- Proper error response structure
