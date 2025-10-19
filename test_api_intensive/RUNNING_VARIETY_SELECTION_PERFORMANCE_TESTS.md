# Running Variety Selection Performance Tests

## Overview

The variety selection performance test suite (`TestVarietySelectionPerformance`) measures the performance of automatic variety selection functionality, including query times, concurrent load handling, and database query efficiency.

## Requirements Covered

- **Requirement 4.9**: Variety selection query time SHALL be < 100ms
- **Requirement 4.9**: Test variety selection under concurrent load
- **Requirement 4.9**: Verify database query performance

## Test Suite Contents

### 1. test_variety_selection_query_time
Measures the time taken for automatic variety selection by making requests without specifying variety_name.

**What it tests:**
- Variety selection query time overhead
- Comparison between auto-selection and specified variety
- Verification that auto-selection doesn't add significant latency

**Expected behavior:**
- All requests should succeed with variety_assumed=true
- Selection metadata should be present and complete
- Overhead should be minimal (< 500ms compared to specified variety)

### 2. test_variety_selection_under_concurrent_load
Tests variety selection performance when multiple requests are made concurrently.

**What it tests:**
- Concurrent variety selection queries (20 simultaneous requests)
- Database query efficiency under load
- System stability with concurrent auto-selection

**Expected behavior:**
- All concurrent requests should succeed
- All should have variety auto-selected
- P95 response time should be < 10 seconds
- No database bottlenecks

### 3. test_database_query_performance_verification
Verifies database query performance across different crops and regions.

**What it tests:**
- Query performance for different crop/region combinations
- Database index efficiency
- Query time consistency

**Expected behavior:**
- All queries should complete successfully
- Query times should be consistent (low variance)
- Time variance should be < 5x (indicates good indexing)
- All queries should complete in < 8 seconds



## Running the Tests

### Prerequisites

1. **API Server Running**: Ensure the Crop Yield Prediction API is running on `http://localhost:8000`
   ```bash
   python run_api.py
   ```

2. **Valid Configuration**: Ensure `test_api_intensive/config/test_config.json` is properly configured

3. **Database Available**: The variety database should be accessible and populated

### Run All Variety Selection Performance Tests

```bash
# From project root
python -m pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance -v

# With detailed output
python -m pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance -v -s

# Generate HTML report
python -m pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance -v --html=test_api_intensive/reports/variety_selection_performance.html --self-contained-html
```

### Run Individual Tests

```bash
# Test variety selection query time
python -m pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance::test_variety_selection_query_time -v -s

# Test concurrent load
python -m pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance::test_variety_selection_under_concurrent_load -v -s

# Test database query performance
python -m pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance::test_database_query_performance_verification -v -s
```

### Using Make Commands

```bash
# Run variety selection performance tests
make test-variety-selection-performance

# Run all performance tests (includes variety selection)
make test-performance
```

## Understanding Test Output

### Query Time Test Output

```
⏱️  Measuring variety selection performance (20 samples)

✓ Variety selection performance measured
  Auto-selection requests:
    Average time: 2345.67ms
    Min time: 1876.23ms
    Max time: 3012.45ms
    Median time: 2298.34ms
  Specified variety request:
    Time: 2123.45ms
  Estimated overhead: 222.22ms
  ✓ Overhead is acceptable (< 500ms)
```

### Concurrent Load Test Output

```
⏱️  Testing variety selection under concurrent load (20 requests)

✓ Variety selection under concurrent load completed
  Concurrent requests: 20
  Success rate: 100%
  Auto-selection rate: 100%
  Performance metrics:
    Average time: 2567.89ms
    Min time: 1923.45ms
    Max time: 3456.78ms
    Median time: 2489.12ms
    P95 time: 3234.56ms
    P99 time: 3401.23ms
  Throughput: 7.82 req/s
```

### Database Query Performance Output

```
⏱️  Verifying database query performance for variety selection

✓ Database query performance verified
  Test scenarios: 9
  Query performance:
    Average time: 2234.56ms
    Min time: 1876.34ms
    Max time: 2789.12ms
    Time variance: 1.49x

  Query results by scenario:
    ✓ Rice   | Bhopal       | Madhya Pradesh       | IR-64           | 2123.45ms
    ✓ Rice   | Lucknow      | Uttar Pradesh        | Pusa Basmati 1  | 2234.56ms
    ✓ Rice   | Chandigarh   | Punjab               | PR 126          | 2345.67ms
    ...

  ✓ Time variance is acceptable (< 5.0x)
      Database queries appear to be well-indexed
  ✓ All queries completed in acceptable time (< 8000ms)
```

## Troubleshooting

### Issue: Tests fail with "GEE authentication failed"

**Cause**: The API cannot authenticate with Google Earth Engine

**Solutions**:
1. Ensure GEE credentials are properly configured
2. Check that the service account key file exists
3. Verify network connectivity to GEE services
4. Use historical dates that don't require real-time data collection

### Issue: High response times or timeouts

**Cause**: API server may be under load or external services are slow

**Solutions**:
1. Ensure no other heavy processes are running
2. Check API server logs for errors
3. Verify external API (GEE, OpenWeather) availability
4. Increase timeout in test configuration if needed

### Issue: Database query performance warnings

**Cause**: Database indexes may be missing or inefficient

**Solutions**:
1. Check that database indexes are created (see `test_database_indexes.py`)
2. Run `ANALYZE` on the variety database
3. Verify database file is not corrupted
4. Check disk I/O performance

### Issue: Inconsistent test results

**Cause**: External factors affecting performance

**Solutions**:
1. Run tests multiple times to establish baseline
2. Ensure API server is warmed up before testing
3. Close other applications to reduce system load
4. Use dedicated test environment if possible

## Performance Benchmarks

### Expected Performance Metrics

| Metric | Target | Acceptable | Warning |
|--------|--------|------------|---------|
| Variety Selection Overhead | < 100ms | < 500ms | > 500ms |
| Concurrent Load P95 | < 5s | < 10s | > 10s |
| Database Query Time Variance | < 2x | < 5x | > 5x |
| Success Rate | 100% | > 95% | < 95% |

### Interpreting Results

- **Green (✓)**: Performance meets or exceeds targets
- **Yellow (⚠️)**: Performance is acceptable but could be improved
- **Red (✗)**: Performance is below acceptable thresholds

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Variety Selection Performance Tests
  run: |
    python -m pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance \
      --html=reports/variety_selection_performance.html \
      --self-contained-html \
      --junit-xml=reports/variety_selection_performance.xml
```

## Related Documentation

- [Performance Tests Overview](RUNNING_PERFORMANCE_TESTS.md)
- [Test Configuration](config/test_config.json)
- [API Documentation](../CROP_YIELD_API_DOCUMENTATION.md)
- [Database Indexes](../TASK_6_DATABASE_INDEXES_SUMMARY.md)
