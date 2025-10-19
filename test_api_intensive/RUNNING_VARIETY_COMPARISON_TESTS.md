# Running Variety Comparison Tests (Task 5.3)

## Quick Start

### Prerequisites
1. **Start the API server**:
   ```bash
   python run_api.py
   ```

2. **Verify API is running**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Ensure GEE authentication is configured** (if using real-time data)

### Run All Variety Comparison Tests

```bash
# From project root
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison -v

# With detailed output
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison -v --tb=short

# With HTML report
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison -v --html=reports/variety_comparison_report.html
```

## Individual Test Execution

### Core Comparison Tests

```bash
# Test auto vs user-specified variety
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_auto_vs_user_specified_variety -v

# Test variety_assumed flag differences
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_variety_assumed_flag_differences -v

# Test response structure consistency
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_response_structure_consistency -v
```

### Invalid Variety Tests

```bash
# Test invalid variety with auto-selection suggestion
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_invalid_variety_with_auto_selection_suggestion -v

# Test invalid variety error details
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_invalid_variety_error_details -v

# Test case sensitivity
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_case_sensitive_variety_names -v
```

### Comprehensive Tests

```bash
# Test multiple crops
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_multiple_crops_auto_vs_user -v

# Test same location consistency
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_same_location_auto_vs_user_consistency -v

# Test yield predictions
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_yield_predictions_reasonable_auto_vs_user -v

# Test metadata presence
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_metadata_not_present_for_user_specified -v

# Test alternatives
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_auto_selection_with_alternatives -v

# Test multiple locations
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison::test_comparison_across_multiple_locations -v
```

## Test Categories

### By Requirement

**Requirement 2.9 Tests** (Comparison and consistency):
```bash
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison \
  -k "auto_vs_user or flag_differences or structure_consistency or multiple_crops or same_location or yield_predictions or metadata_not_present or alternatives or multiple_locations" \
  -v
```

**Requirement 2.10 Tests** (Invalid variety handling):
```bash
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison \
  -k "invalid_variety or case_sensitive" \
  -v
```

## Expected Results

### Successful Test Run
```
test_auto_vs_user_specified_variety PASSED
test_variety_assumed_flag_differences PASSED
test_response_structure_consistency PASSED
test_invalid_variety_with_auto_selection_suggestion PASSED
test_multiple_crops_auto_vs_user PASSED
test_same_location_auto_vs_user_consistency PASSED
test_yield_predictions_reasonable_auto_vs_user PASSED
test_invalid_variety_error_details PASSED
test_case_sensitive_variety_names PASSED
test_metadata_not_present_for_user_specified PASSED
test_auto_selection_with_alternatives PASSED
test_comparison_across_multiple_locations PASSED

12 passed in X.XXs
```

## Troubleshooting

### API Not Running
**Error**: `Connection refused` or `Failed to connect`

**Solution**:
```bash
# Start the API server
python run_api.py

# Verify it's running
curl http://localhost:8000/health
```

### GEE Authentication Failed
**Error**: `Failed to collect real-time data: GEE authentication failed`

**Solution**:
1. Check GEE credentials are configured
2. Verify service account key file exists
3. Check environment variables:
   ```bash
   echo $GEE_SERVICE_ACCOUNT_KEY
   ```

### Database Not Found
**Error**: `Database connection failed` or `Variety not found`

**Solution**:
```bash
# Verify database exists
ls -la data/database/crop_prediction.db

# Check database has variety data
sqlite3 data/database/crop_prediction.db "SELECT COUNT(*) FROM crop_varieties;"
```

### Tests Timing Out
**Error**: `Test timeout after 30s`

**Solution**:
```bash
# Increase timeout
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison \
  --timeout=60 \
  -v
```

## Test Data

### Crops Tested
- Rice (variety: IR-64)
- Wheat (variety: HD 3086)
- Maize (variety: DHM 117)

### Locations Tested
- Lucknow (26.8467, 80.9462)
- Chandigarh (30.7333, 76.7794)
- Bhopal (23.2599, 77.4126)
- Patna (25.5941, 85.1376)

### Test Scenarios
1. Auto-selection (variety omitted)
2. User-specified variety
3. Invalid variety names
4. Case sensitivity
5. Multiple crops and locations

## Performance Expectations

### Response Times
- Single request: < 5 seconds
- Test suite: < 30 seconds (with API running)

### Success Rate
- Expected: 100% pass rate when API is properly configured
- Acceptable: 90%+ pass rate (some tests may skip if API unavailable)

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Variety Comparison Tests
  run: |
    pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison \
      -v \
      --html=reports/variety_comparison_report.html \
      --self-contained-html
```

### Jenkins Example
```groovy
stage('Variety Comparison Tests') {
    steps {
        sh '''
            pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison \
              -v \
              --junitxml=reports/variety_comparison_junit.xml
        '''
    }
}
```

## Additional Options

### Run with Coverage
```bash
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison \
  --cov=src \
  --cov-report=html \
  -v
```

### Run with Markers
```bash
# Run only fast tests
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison \
  -m "not slow" \
  -v

# Run only critical tests
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison \
  -m "critical" \
  -v
```

### Parallel Execution
```bash
# Run tests in parallel (requires pytest-xdist)
pytest test_api_intensive/suites/test_variety_selection.py::TestVarietyComparison \
  -n auto \
  -v
```

## Verification Checklist

Before running tests, verify:
- [ ] API server is running
- [ ] GEE authentication is configured (if needed)
- [ ] Database exists and has variety data
- [ ] Test configuration is correct
- [ ] Network connectivity is available

After running tests, verify:
- [ ] All tests passed or have acceptable skip reasons
- [ ] No unexpected errors in logs
- [ ] Response times are within acceptable range
- [ ] Test report is generated

## Support

For issues or questions:
1. Check the test summary: `TASK_5_3_VARIETY_COMPARISON_TESTS_SUMMARY.md`
2. Review test logs in `reports/test_execution.log`
3. Check API logs for errors
4. Verify test configuration in `config/test_config.json`
