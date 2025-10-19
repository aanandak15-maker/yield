# Error Handling Tests - Quick Reference

## Quick Commands

```bash
# Run all error handling tests
pytest suites/test_error_handling.py -v

# Run only implemented tests (skip pending)
pytest suites/test_error_handling.py -v -k "not skip"

# Run specific test class
pytest suites/test_error_handling.py::TestAPIErrors -v
pytest suites/test_error_handling.py::TestVarietySelectionErrors -v
pytest suites/test_error_handling.py::TestTimeoutAndMalformedRequests -v

# Run with HTML report
pytest suites/test_error_handling.py --html=reports/error_handling_report.html --self-contained-html

# Run critical tests only
pytest suites/test_error_handling.py -m "error_handling and critical" -v
```

## Test Classes

| Class | Tests | Focus |
|-------|-------|-------|
| `TestAPIErrors` | 8 | HTTP error codes (400, 404, 422) |
| `TestExternalServiceFailures` | 5 | External service failures (GEE, OpenWeather, DB) |
| `TestVarietySelectionErrors` | 5 | Variety selection error handling |
| `TestTimeoutAndMalformedRequests` | 8 | Malformed requests, timeouts |

## Key Test Scenarios

### API Errors (Task 9.1)
- ✅ Invalid crop type → 400/422
- ✅ Missing required fields → 400/422
- ✅ Invalid coordinates → 422
- ✅ Future sowing date → 422
- ✅ Invalid date format → 422
- ✅ Invalid endpoint → 404
- ✅ Wrong HTTP method → 404/405
- ✅ Error message clarity

### External Service Failures (Task 9.2)
- ⧗ GEE unavailability → 503 (needs mock)
- ⧗ OpenWeather failure → 503 (needs mock)
- ⧗ Database failure → 500 (needs test DB)
- ⧗ Model loading failure → 500 (needs test env)
- ✅ 503 response format

### Variety Selection Errors (Task 9.3)
- ✅ Invalid variety name → 4xx
- ✅ Variety-crop mismatch → 4xx
- ✅ Error suggests alternatives
- ⧗ No varieties available (needs test DB)
- ⧗ Database query failure (needs test DB)

### Malformed Requests (Task 9.4)
- ✅ Invalid JSON → 400
- ✅ Malformed JSON → 400
- ✅ Empty request body → 4xx
- ✅ Null required fields → 4xx
- ✅ Wrong data types → 4xx
- ✅ Extra fields handling
- ⧗ Request timeout → 504 (needs simulation)

## Test Statistics

- **Total:** 27 tests
- **Implemented:** 18 (67%)
- **Pending:** 9 (33%)
- **Requirements:** 5.1, 5.2, 5.3, 5.4, 5.6, 5.7, 5.8, 5.9

## Expected Error Codes

| Scenario | Expected Code | Status |
|----------|---------------|--------|
| Invalid crop type | 400/422 | ✅ |
| Missing required field | 400/422 | ✅ |
| Invalid coordinates | 422 | ✅ |
| Future date | 422 | ✅ |
| Invalid date format | 422 | ✅ |
| Invalid endpoint | 404 | ✅ |
| Wrong HTTP method | 404/405 | ✅ |
| Invalid variety | 400/422 | ✅ |
| Invalid JSON | 400 | ✅ |
| External service down | 503 | ⧗ |
| Database failure | 500 | ⧗ |
| Model failure | 500 | ⧗ |
| Timeout | 504 | ⧗ |

## Verification Checklist

- [ ] API server is running (`http://localhost:8000`)
- [ ] Test configuration is correct (`config/test_config.json`)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Tests collect successfully (`pytest --collect-only`)
- [ ] Implemented tests pass
- [ ] Error messages are clear and actionable
- [ ] No sensitive data in error responses

## Common Issues

### API Not Running
```bash
# Check API health
curl http://localhost:8000/health

# Start API
python run_api.py
```

### Import Errors
```bash
cd test_api_intensive
pip install -r requirements.txt
```

### Configuration Issues
```bash
python verify_config.py
```

## Next Steps

1. **Run Tests:** Execute implemented tests
2. **Verify Behavior:** Check error responses match expectations
3. **Implement Mocks:** Set up mock services for pending tests
4. **Test Database:** Create test database for database failure tests
5. **Timeout Simulation:** Implement slow endpoint for timeout tests

## Related Files

- `suites/test_error_handling.py` - Test implementation
- `RUNNING_ERROR_HANDLING_TESTS.md` - Detailed guide
- `TASK_9_ERROR_HANDLING_SUMMARY.md` - Implementation summary
- `utils/assertions.py` - Custom assertions
- `utils/api_client.py` - API client wrapper

## Legend

- ✅ Implemented and ready to run
- ⧗ Documented but requires infrastructure
- 🔧 Needs implementation
