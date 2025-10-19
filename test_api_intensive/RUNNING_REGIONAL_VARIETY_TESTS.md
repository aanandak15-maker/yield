# Running Regional Variety Selection Tests

## Quick Start

### Run All Regional Variety Tests
```bash
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection -v
```

### Run Specific Test
```bash
# Test auto-selection for all crops
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_auto_selection_for_each_crop -v

# Test specific region
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_regional_variety_selection -v

# Test fallback mechanism
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_fallback_to_all_north_india -v

# Test metadata validation
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_selection_metadata_region_field -v
```

### Run with Output
```bash
# Show print statements and detailed output
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection -v -s

# Show only test names
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection -v --tb=no

# Show full error traces
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection -v --tb=long
```

## Prerequisites

### 1. Start API Server
```bash
# In a separate terminal
python run_api.py
```

### 2. Verify API is Running
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "api_manager": "ready",
    "gee_client": "ready",
    "weather_client": "ready",
    "variety_db": "ready"
  }
}
```

### 3. Check Environment Variables
```bash
# GEE credentials
echo $GEE_SERVICE_ACCOUNT_KEY

# OpenWeather API key
echo $OPENWEATHER_API_KEY
```

## Test Scenarios

### By Crop Type
```bash
# Test Rice auto-selection
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_auto_selection_for_each_crop[Rice] -v

# Test Wheat auto-selection
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_auto_selection_for_each_crop[Wheat] -v

# Test Maize auto-selection
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_auto_selection_for_each_crop[Maize] -v
```

### By Region
```bash
# Test Punjab region
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_regional_variety_selection[Chandigarh-Punjab] -v
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_regional_variety_selection[Amritsar-Punjab] -v

# Test Haryana region
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_regional_variety_selection[Hisar-Haryana] -v

# Test Uttar Pradesh region
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_regional_variety_selection[Lucknow-Uttar\ Pradesh] -v
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_regional_variety_selection[Varanasi-Uttar\ Pradesh] -v

# Test Bihar region
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_regional_variety_selection[Patna-Bihar] -v

# Test Madhya Pradesh region
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_regional_variety_selection[Bhopal-Madhya\ Pradesh] -v
```

### By Feature
```bash
# Test crop-specific varieties
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_crop_specific_regional_varieties -v

# Test multiple regions
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_multiple_regions_same_crop -v

# Test alternatives list
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_alternatives_list_validity -v

# Test reason field
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection::test_reason_field_descriptiveness -v
```

## Advanced Options

### With Coverage
```bash
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection \
  --cov=utils \
  --cov-report=html \
  --cov-report=term
```

### With HTML Report
```bash
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection \
  --html=reports/regional_variety_tests.html \
  --self-contained-html
```

### With JSON Output
```bash
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection \
  --json-report \
  --json-report-file=reports/regional_variety_tests.json
```

### With Markers
```bash
# Run only variety selection tests
pytest -m variety_selection -v

# Run critical tests only
pytest -m critical -v

# Run fast tests only
pytest -m fast -v
```

### Parallel Execution
```bash
# Run tests in parallel (4 workers)
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection -n 4 -v
```

### With Timeout
```bash
# Set 60 second timeout per test
pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection --timeout=60 -v
```

## Interpreting Results

### Successful Test
```
test_auto_selection_for_each_crop[Rice] PASSED [33%]
```
✅ Test passed - variety selection working correctly

### Failed Test
```
test_auto_selection_for_each_crop[Rice] FAILED [33%]
E   AssertionError: Auto-selection failed for Rice: GEE authentication failed
```
❌ Test failed - check error message for details

### Skipped Test
```
test_regional_variety_selection[Chandigarh-Punjab] SKIPPED [50%]
```
⚠️ Test skipped - API not available or test condition not met

## Troubleshooting

### Issue: All tests fail with "Connection refused"
**Cause**: API server not running  
**Solution**:
```bash
python run_api.py
```

### Issue: Tests fail with "GEE authentication failed"
**Cause**: GEE credentials not configured  
**Solution**:
```bash
export GEE_SERVICE_ACCOUNT_KEY="path/to/credentials.json"
```

### Issue: Tests fail with "OpenWeather API error"
**Cause**: OpenWeather API key not set  
**Solution**:
```bash
export OPENWEATHER_API_KEY="your_api_key"
```

### Issue: Tests fail with "No variety selected"
**Cause**: Variety database not populated  
**Solution**:
```bash
# Check database
python -c "from src.crop_variety_database import CropVarietyDatabase; db = CropVarietyDatabase(); print(db.get_all_varieties('Rice'))"
```

### Issue: Tests are slow
**Cause**: External API calls taking time  
**Solution**:
```bash
# Run with timeout
pytest --timeout=30 -v

# Or run in parallel
pytest -n 4 -v
```

## Test Data

### Locations Tested
- **Punjab**: Chandigarh (30.73°N, 76.78°E), Amritsar (31.63°N, 74.87°E)
- **Haryana**: Hisar (29.15°N, 75.72°E)
- **Uttar Pradesh**: Lucknow (26.85°N, 80.95°E), Varanasi (25.32°N, 82.97°E)
- **Bihar**: Patna (25.59°N, 85.14°E)
- **Madhya Pradesh**: Bhopal (23.26°N, 77.41°E)

### Crops Tested
- **Rice**: Kharif season (June-July sowing)
- **Wheat**: Rabi season (November-December sowing)
- **Maize**: Both seasons (June-July, October-November)

### Expected Varieties
- **Rice**: IR-64, Pusa Basmati 1121, Swarna, MTU 1010, etc.
- **Wheat**: HD 3086, PBW 343, DBW 17, Lok 1, etc.
- **Maize**: DHM 117, Vivek Hybrid 27, HQPM 1, etc.

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Regional Variety Tests
  run: |
    pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection \
      --junitxml=reports/regional-variety-tests.xml \
      --html=reports/regional-variety-tests.html
```

### Jenkins
```groovy
stage('Regional Variety Tests') {
    steps {
        sh 'pytest test_api_intensive/suites/test_variety_selection.py::TestRegionalVarietySelection -v'
    }
}
```

## Performance Expectations

### Response Times
- Single test: < 5 seconds
- Full suite: < 2 minutes
- With parallel execution: < 1 minute

### Success Rate
- Expected: > 95% (when API is healthy)
- Acceptable: > 90%
- Critical: > 80%

## Related Documentation

- [Task 5.2 Summary](TASK_5_2_REGIONAL_VARIETY_TESTS_SUMMARY.md)
- [Task 5.2 Verification](TASK_5_2_VERIFICATION.md)
- [Test Framework README](README.md)
- [API Documentation](../CROP_YIELD_API_DOCUMENTATION.md)

## Support

For issues or questions:
1. Check API health: `curl http://localhost:8000/health`
2. Check API logs: `tail -f api_startup.log`
3. Check test logs: `cat reports/test_execution.log`
4. Review error messages in test output
5. Consult troubleshooting section above
