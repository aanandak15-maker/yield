# Running Performance Tests

## Quick Start

### 1. Ensure API is Running
```bash
# In the main project directory
python run_api.py
```

The API should be accessible at http://localhost:8000

### 2. Verify API Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-19T...",
  "version": "6.0.0",
  "components": {...}
}
```

### 3. Run Performance Tests

#### Run All Performance Tests
```bash
cd test_api_intensive
pytest suites/test_performance.py -v
```

#### Run Specific Test Classes
```bash
# Response time tests only
pytest suites/test_performance.py::TestResponseTime -v

# Endpoint-specific tests
pytest suites/test_performance.py::TestResponseTimeByEndpoint -v

# Location consistency tests
pytest suites/test_performance.py::TestResponseTimeByLocation -v
```

#### Run Individual Tests
```bash
# Single request test
pytest suites/test_performance.py::TestResponseTime::test_single_request_response_time -v

# 10 concurrent requests
pytest suites/test_performance.py::TestResponseTime::test_10_concurrent_requests -v

# 50 concurrent requests
pytest suites/test_performance.py::TestResponseTime::test_50_concurrent_requests -v

# 100 concurrent requests (slow)
pytest suites/test_performance.py::TestResponseTime::test_100_concurrent_requests -v

# Percentile measurements
pytest suites/test_performance.py::TestResponseTime::test_response_time_percentiles -v
```

#### Run With Options
```bash
# Show detailed output (print statements)
pytest suites/test_performance.py -v -s

# Skip slow tests (100 concurrent)
pytest suites/test_performance.py -v -m "not slow"

# Run only critical tests
pytest suites/test_performance.py -v -m "critical"

# Generate HTML report
pytest suites/test_performance.py -v --html=reports/performance_report.html --self-contained-html

# Run with timeout (30 seconds per test)
pytest suites/test_performance.py -v --timeout=30

# Run in parallel (requires pytest-xdist)
pytest suites/test_performance.py -v -n auto
```

## Understanding Test Output

### Successful Test Output
```
test_api_intensive/suites/test_performance.py::TestResponseTime::test_single_request_response_time PASSED

✓ Single request response time: 2345.67ms
```

### Concurrent Test Output
```
test_api_intensive/suites/test_performance.py::TestResponseTime::test_50_concurrent_requests PASSED

✓ 50 concurrent requests completed
  Success rate: 98.0%
  Average response time: 3245.67ms
  Min: 1234.56ms
  Max: 8765.43ms
  Median: 3012.34ms
  P95: 6543.21ms
  P99: 7890.12ms
  Throughput: 15.42 req/s
```

### Percentile Test Output
```
test_api_intensive/suites/test_performance.py::TestResponseTime::test_response_time_percentiles PASSED

✓ Response time percentiles measured (30 requests)
  P50 (median): 2456.78ms
  P75: 3123.45ms
  P90: 4567.89ms
  P95: 5234.56ms
  P99: 6789.01ms
  Average: 2789.34ms
  Min: 1234.56ms
  Max: 7890.12ms
  Std Dev: 1234.56ms
```

## Test Markers

### Available Markers
- `performance`: All performance tests
- `critical`: Critical tests that must pass
- `slow`: Tests that take longer than 5 seconds

### Using Markers
```bash
# Run only performance tests
pytest -v -m "performance"

# Run critical performance tests
pytest -v -m "performance and critical"

# Skip slow tests
pytest -v -m "performance and not slow"
```

## Configuration

### Test Configuration File
Edit `test_api_intensive/config/test_config.json` to customize:

```json
{
  "api": {
    "base_url": "http://localhost:8000",
    "timeout_seconds": 30
  },
  "performance": {
    "max_response_time_ms": 5000,
    "max_response_time_under_load_ms": 10000,
    "max_p95_response_time_ms": 7000,
    "max_p99_response_time_ms": 10000,
    "concurrent_users": [1, 10, 50, 100]
  }
}
```

### Environment Variables
```bash
# Override API base URL
export API_BASE_URL=http://staging.example.com:8000

# Run tests
pytest suites/test_performance.py -v
```

## Troubleshooting

### Issue: Connection Refused
```
ERROR: Connection error: [Errno 61] Connection refused
```

**Solution**: Start the API server
```bash
python run_api.py
```

### Issue: GEE Authentication Failed
```
AssertionError: Request failed with status 400
detail: "Failed to collect real-time data: GEE authentication failed"
```

**Solution**: This is expected if GEE credentials are not configured. The API should fall back to historical data, but if tests fail, you can:

1. Configure GEE credentials (see main project README)
2. Or modify tests to handle this gracefully
3. Or use mock data for testing

### Issue: Response Times Exceed Thresholds
```
AssertionError: Response time 6234.56ms exceeds threshold 5000ms
```

**Solutions**:
1. Check server resources (CPU, memory)
2. Optimize database queries
3. Add caching
4. Increase thresholds in config (if acceptable)
5. Scale server resources

### Issue: High Error Rates Under Load
```
AssertionError: Success rate 85.0% is below threshold 95.0%
```

**Solutions**:
1. Increase server resources
2. Add connection pooling
3. Optimize slow endpoints
4. Add rate limiting
5. Scale horizontally

### Issue: Tests Timeout
```
ERROR: Test timeout after 30 seconds
```

**Solutions**:
1. Increase timeout: `pytest --timeout=60`
2. Check for deadlocks or infinite loops
3. Optimize slow operations
4. Run fewer concurrent requests

## Performance Benchmarks

### Expected Performance (Local Development)

| Test | Expected Time | Threshold |
|------|--------------|-----------|
| Single request | 2-4 seconds | < 5 seconds |
| 10 concurrent (avg) | 2.5-4.5 seconds | < 5 seconds |
| 50 concurrent (avg) | 3-6 seconds | < 10 seconds |
| 50 concurrent (p95) | 5-7 seconds | < 7 seconds |
| 100 concurrent (avg) | 3.5-7 seconds | < 10 seconds |
| 100 concurrent (p99) | 7-10 seconds | < 10 seconds |

### Expected Performance (Production)

| Test | Expected Time | Threshold |
|------|--------------|-----------|
| Single request | 1-2 seconds | < 3 seconds |
| 10 concurrent (avg) | 1.5-3 seconds | < 3 seconds |
| 50 concurrent (avg) | 2-4 seconds | < 5 seconds |
| 50 concurrent (p95) | 3-5 seconds | < 5 seconds |
| 100 concurrent (avg) | 2.5-5 seconds | < 7 seconds |
| 100 concurrent (p99) | 5-7 seconds | < 8 seconds |

## Continuous Integration

### GitHub Actions Example
```yaml
name: Performance Tests

on: [push, pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r test_api_intensive/requirements.txt
    
    - name: Start API
      run: |
        python run_api.py &
        sleep 10
    
    - name: Run performance tests
      run: |
        cd test_api_intensive
        pytest suites/test_performance.py -v --html=reports/performance_report.html
    
    - name: Upload report
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: performance-report
        path: test_api_intensive/reports/performance_report.html
```

## Analyzing Results

### View HTML Report
```bash
# Generate report
pytest suites/test_performance.py -v --html=reports/performance_report.html --self-contained-html

# Open in browser
open reports/performance_report.html  # macOS
xdg-open reports/performance_report.html  # Linux
start reports/performance_report.html  # Windows
```

### Export Metrics
Performance metrics are automatically collected and can be exported:

```python
# In your test or after test run
metrics_collector.export_to_file("performance_metrics.json", format="json")
metrics_collector.export_to_file("performance_metrics.csv", format="csv")
```

### Compare Runs
```bash
# Run tests and save metrics
pytest suites/test_performance.py -v > results_run1.txt

# Make changes, run again
pytest suites/test_performance.py -v > results_run2.txt

# Compare
diff results_run1.txt results_run2.txt
```

## Best Practices

### 1. Warm Up the API
Run a few requests before performance tests to warm up caches:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/crops/supported
```

### 2. Consistent Environment
- Close other applications
- Disable background processes
- Use consistent hardware
- Run multiple times and average results

### 3. Monitor Resources
```bash
# Monitor CPU and memory during tests
top  # or htop

# Monitor API logs
tail -f logs/api.log
```

### 4. Baseline Performance
Establish baselines and track over time:
```bash
# Run and save baseline
pytest suites/test_performance.py -v | tee baseline_performance.txt

# Compare future runs against baseline
```

## Next Steps

After running performance tests:

1. **Review Results**: Check if all tests pass and thresholds are met
2. **Identify Bottlenecks**: Look for slow endpoints or operations
3. **Optimize**: Improve performance where needed
4. **Re-test**: Verify improvements
5. **Document**: Update baselines and expectations
6. **Automate**: Integrate into CI/CD pipeline

## Related Documentation

- [Task 7.1 Summary](TASK_7_1_RESPONSE_TIME_TESTS_SUMMARY.md) - Implementation details
- [Test Configuration](config/test_config.json) - Configuration options
- [Main README](README.md) - Overall test framework documentation
- [Utilities Reference](UTILITIES_QUICK_REFERENCE.md) - Utility functions
