# Running Validation Tests

## Overview
This guide explains how to run the validation test suite for the Crop Yield API. The validation tests ensure the API properly validates inputs, handles errors, and rejects invalid data.

## Test Suite Structure

The validation test suite is organized into two main categories:

### Task 6.1: Invalid Input Tests
Tests for invalid inputs that should be rejected:
- Invalid crop types (lowercase, typos, unsupported)
- Invalid coordinates (out of range, non-numeric)
- Invalid dates (future, wrong format, too old)
- Missing required fields
- Error response quality

### Task 6.2: Edge Case Tests
Tests for boundary values and edge cases:
- Boundary coordinate values (min/max lat/lon)
- Boundary dates (very recent, 2 years old)
- Field polygon edge cases (minimum points, large polygons)
- Special characters in strings
- Extremely long strings
- Null and empty values
- Combined edge cases

## Prerequisites

1. **API Server Running**
   ```bash
   # Start the API server in a separate terminal
   python run_api.py
   ```

2. **Test Environment Setup**
   ```bash
   cd test_api_intensive
   pip install -r requirements.txt
   ```

3. **Configuration**
   - Ensure `config/test_config.json` has correct API URL
   - Default: `http://localhost:8000`

## Running Tests

### Run All Validation Tests
```bash
cd test_api_intensive
python -m pytest suites/test_validation.py -v
```

### Run by Category

#### Invalid Input Tests (Task 6.1)
```bash
python -m pytest suites/test_validation.py -m validation -v
```

#### Edge Case Tests (Task 6.2)
```bash
python -m pytest suites/test_validation.py -m edge_case -v
```

#### Critical Tests Only
```bash
python -m pytest suites/test_validation.py -m critical -v
```

### Run Specific Test Classes

#### Invalid Crop Types
```bash
python -m pytest suites/test_validation.py::TestInvalidCropTypes -v
```

#### Invalid Coordinates
```bash
python -m pytest suites/test_validation.py::TestInvalidCoordinates -v
```

#### Invalid Dates
```bash
python -m pytest suites/test_validation.py::TestInvalidDates -v
```

#### Missing Required Fields
```bash
python -m pytest suites/test_validation.py::TestMissingRequiredFields -v
```

#### Boundary Coordinates
```bash
python -m pytest suites/test_validation.py::TestBoundaryCoordinates -v
```

#### Boundary Dates
```bash
python -m pytest suites/test_validation.py::TestBoundaryDates -v
```

#### Field Polygon Edge Cases
```bash
python -m pytest suites/test_validation.py::TestFieldPolygonEdgeCases -v
```

#### Special Characters
```bash
python -m pytest suites/test_validation.py::TestSpecialCharacters -v
```

#### Extremely Long Strings
```bash
python -m pytest suites/test_validation.py::TestExtremelyLongStrings -v
```

#### Null and Empty Values
```bash
python -m pytest suites/test_validation.py::TestNullAndEmptyValues -v
```

#### Combined Edge Cases
```bash
python -m pytest suites/test_validation.py::TestCombinedEdgeCases -v
```

### Run Individual Tests
```bash
# Run a specific test
python -m pytest suites/test_validation.py::TestInvalidCropTypes::test_lowercase_crop_type -v

# Run multiple specific tests
python -m pytest suites/test_validation.py::TestInvalidCropTypes::test_lowercase_crop_type \
                 suites/test_validation.py::TestInvalidCoordinates::test_latitude_out_of_range_positive -v
```

## Output Options

### Verbose Output
```bash
python -m pytest suites/test_validation.py -v
```

### Show Test Details
```bash
python -m pytest suites/test_validation.py -vv
```

### Show Print Statements
```bash
python -m pytest suites/test_validation.py -v -s
```

### Generate HTML Report
```bash
python -m pytest suites/test_validation.py -v --html=reports/validation_report.html
```

### Show Only Failures
```bash
python -m pytest suites/test_validation.py -v --tb=short
```

### Show Full Traceback
```bash
python -m pytest suites/test_validation.py -v --tb=long
```

## Test Statistics

### Task 6.1: Invalid Input Tests
- **Test Classes:** 5
- **Total Tests:** 28
- **Status:** ✅ All 28 passing (100%)

### Task 6.2: Edge Case Tests
- **Test Classes:** 7
- **Total Tests:** 32
- **Status:** ⚠️ 29 passing, 3 failing (90.6% - failures due to API bugs)

### Overall Validation Suite
- **Total Test Classes:** 12
- **Total Tests:** 60
- **Passing:** 57 (95%)
- **Failing:** 3 (5% - API bugs, not test issues)

## Expected Results

### Successful Test Run
```
============================ test session starts ============================
collected 60 items

suites/test_validation.py::TestInvalidCropTypes::test_lowercase_crop_type PASSED
suites/test_validation.py::TestInvalidCropTypes::test_uppercase_crop_type PASSED
...
suites/test_validation.py::TestCombinedEdgeCases::test_all_optional_fields_omitted PASSED

======================== 57 passed, 3 failed in 7.60s ======================
```

### Known Failures
The following tests are expected to fail due to API bugs:
1. `TestFieldPolygonEdgeCases::test_polygon_with_2_points_rejected`
2. `TestFieldPolygonEdgeCases::test_polygon_with_1_point_rejected`
3. `TestFieldPolygonEdgeCases::test_large_polygon_many_points`

These failures are due to the API returning 500 errors instead of proper validation errors (400/422).

## Troubleshooting

### API Not Running
**Error:** `Connection refused` or `Max retries exceeded`

**Solution:**
```bash
# Start the API server
python run_api.py
```

### Wrong API URL
**Error:** Tests fail to connect

**Solution:**
Edit `config/test_config.json`:
```json
{
  "api": {
    "base_url": "http://localhost:8000"
  }
}
```

### Import Errors
**Error:** `ModuleNotFoundError`

**Solution:**
```bash
cd test_api_intensive
pip install -r requirements.txt
```

### Timeout Errors
**Error:** Tests timeout

**Solution:**
Increase timeout in `config/test_config.json`:
```json
{
  "api": {
    "timeout_seconds": 60
  }
}
```

## Test Markers

The validation tests use the following pytest markers:

- `@pytest.mark.validation` - All validation tests
- `@pytest.mark.edge_case` - Edge case tests
- `@pytest.mark.critical` - Critical validation tests
- `@pytest.mark.slow` - Slow-running tests (long strings)

### Run by Marker
```bash
# Run all validation tests
python -m pytest suites/test_validation.py -m validation -v

# Run edge case tests
python -m pytest suites/test_validation.py -m edge_case -v

# Run critical tests
python -m pytest suites/test_validation.py -m critical -v

# Run non-slow tests
python -m pytest suites/test_validation.py -m "not slow" -v
```

## Continuous Integration

### Run in CI/CD Pipeline
```bash
# Run with JUnit XML output for CI
python -m pytest suites/test_validation.py -v --junitxml=reports/validation_junit.xml

# Run with coverage
python -m pytest suites/test_validation.py -v --cov=utils --cov-report=html
```

### Exit Codes
- `0` - All tests passed
- `1` - Some tests failed
- `2` - Test execution interrupted
- `3` - Internal error
- `4` - Command line usage error
- `5` - No tests collected

## Performance

### Typical Execution Times
- **Invalid Input Tests:** ~2-3 seconds
- **Edge Case Tests:** ~6-8 seconds
- **Full Validation Suite:** ~8-10 seconds

### Parallel Execution
```bash
# Run tests in parallel (4 workers)
python -m pytest suites/test_validation.py -v -n 4
```

## Best Practices

1. **Run Before Commits**
   ```bash
   python -m pytest suites/test_validation.py -v
   ```

2. **Run After API Changes**
   ```bash
   python -m pytest suites/test_validation.py -v --tb=short
   ```

3. **Generate Reports**
   ```bash
   python -m pytest suites/test_validation.py -v --html=reports/validation_report.html
   ```

4. **Check Coverage**
   ```bash
   python -m pytest suites/test_validation.py -v --cov=utils
   ```

## Next Steps

After validation tests pass:
1. Review test report
2. Fix any API bugs identified
3. Move to performance testing (Task 7)
4. Continue with load testing (Task 8)

## Related Documentation

- [Task 6.1 Summary](TASK_6_VALIDATION_TESTS_SUMMARY.md)
- [Task 6.2 Summary](TASK_6_2_EDGE_CASE_TESTS_SUMMARY.md)
- [Test Framework README](README.md)
- [Quick Start Guide](QUICKSTART.md)

## Support

For issues or questions:
1. Check test logs in `reports/test_execution.log`
2. Review HTML report in `reports/test_report.html`
3. Check API logs for server-side errors
4. Verify test configuration in `config/test_config.json`
