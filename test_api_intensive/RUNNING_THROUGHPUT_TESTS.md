# Running Throughput Tests

## Quick Start

```bash
# Run all throughput tests
pytest test_api_intensive/suites/test_performance.py::TestThroughput -v

# Run with detailed output
pytest test_api_intensive/suites/test_performance.py::TestThroughput -v -s
```

## Individual Tests

### 1. Sustained Load Test (100 requests over 1 minute)
```bash
pytest test_api_intensive/suites/test_performance.py::TestThroughput::test_sustained_load_100_requests_over_1_minute -v -s
```

**What it tests:**
- Distributes 100 requests evenly over 60 seconds
- Measures throughput (requests per second)
- Tracks error rate throughout test
- Validates system stability under sustained load

**Expected duration:** ~60 seconds

**Success criteria:**
- Throughput within 30% of target (1.67 req/s)
- Error rate ≤ 5%
- Success rate ≥ 95%
- Max response time < 10 seconds

### 2. Throughput Calculation Test
```bash
pytest test_api_intensive/suites/test_performance.py::TestThroughput::test_calculate_requests_per_second -v -s
```

**What it tests:**
- Validates throughput calculation accuracy
- Makes 20 requests as fast as possible
- Compares calculated vs expected throughput

**Expected duration:** ~1 second

**Success criteria:**
- Throughput calculation accurate within 1%

### 3. Error Rate Under Load Test
```bash
pytest test_api_intensive/suites/test_performance.py::TestThroughput::test_error_rate_under_load -v -s
```

**What it tests:**
- Measures error rate with 50 concurrent requests
- Tracks errors by status code
- Validates error rate calculation

**Expected duration:** ~5 seconds

**Success criteria:**
- Error rate ≤ 5%
- Error rate calculation matches expected

### 4. System Stability Test
```bash
pytest test_api_intensive/suites/test_performance.py::TestThroughput::test_system_stability_under_load -v -s
```

**What it tests:**
- Distributes 60 requests over 30 seconds
- Analyzes performance across 3 time periods
- Detects performance degradation trends

**Expected duration:** ~30 seconds

**Success criteria:**
- Response time degradation < 50%
- Error rate increase < 10%
- System remains stable throughout

## Prerequisites

1. **API Server Running:**
   ```bash
   python run_api.py
   ```
   Server should be accessible at http://localhost:8000

2. **GEE Authentication Configured:**
   - Service account credentials in place
   - GEE authentication working

3. **Database Populated:**
   - Variety database has required data
   - All crop types and varieties available

## Understanding Test Output

### Sustained Load Test Output
```
⏳ Starting sustained load test: 100 requests over 60s
   Request interval: 0.60s (1.67 req/s target)
   Progress: 10/100 requests (6.0s elapsed)
   Progress: 20/100 requests (12.1s elapsed)
   ...

✓ Sustained load test completed successfully

  Test Duration:
    Target: 60s
    Actual: 60.23s

  Throughput:
    Requests per second: 1.66 req/s
    Target throughput: 1.67 req/s
    Variance: 0.6%

  Request Statistics:
    Total requests: 100
    Successful: 98
    Failed: 2
    Success rate: 98.0%
    Error rate: 2.00%

  Response Times:
    Average: 2345.67ms
    Median: 2123.45ms
    Min: 1234.56ms
    Max: 4567.89ms
    P95: 3456.78ms
    P99: 4123.45ms
    Std Dev: 567.89ms
```

### Stability Test Output
```
⏳ Testing system stability: 60 requests over 30s

✓ System stability verified over 30s

  Period Analysis:
    Period 1:
      Avg response time: 2100.45ms
      Error rate: 0.00%
      Throughput: 2.05 req/s
    Period 2:
      Avg response time: 2234.12ms
      Error rate: 0.00%
      Throughput: 2.01 req/s
    Period 3:
      Avg response time: 2298.78ms
      Error rate: 0.00%
      Throughput: 1.98 req/s

  Stability Metrics:
    Response time ratio (last/first): 1.09x
    Error rate change: 0.00%
    Status: STABLE
```

## Troubleshooting

### High Error Rates

**Problem:** Tests fail with "Error rate 100.00% exceeds threshold 5.00%"

**Possible causes:**
1. API server not running
2. GEE authentication failed
3. Invalid variety names in test data
4. Database not populated

**Solutions:**
```bash
# Check API server status
curl http://localhost:8000/health

# Check API logs
tail -f api_startup.log

# Verify GEE authentication
python -c "from src.gee_client import GEEClient; client = GEEClient(); print('GEE OK')"

# Check database
sqlite3 data/database/crop_prediction.db "SELECT COUNT(*) FROM crop_varieties;"
```

### Throughput Variance Too High

**Problem:** "Throughput 1.20 req/s deviates too much from expected 1.67 req/s"

**Possible causes:**
1. System under other load
2. Network latency
3. API server resource constraints

**Solutions:**
- Close other applications
- Check system resources (CPU, memory)
- Increase API server resources
- Run tests during off-peak hours

### Test Timeouts

**Problem:** "Test exceeded 120 second timeout"

**Possible causes:**
1. API server very slow
2. Network issues
3. External API (GEE, OpenWeather) slow

**Solutions:**
```bash
# Increase timeout in pytest.ini
# Or run with custom timeout
pytest test_api_intensive/suites/test_performance.py::TestThroughput --timeout=300 -v -s
```

### Connection Errors

**Problem:** "Connection error: Connection refused"

**Possible causes:**
1. API server not running
2. Wrong base URL in config
3. Firewall blocking connection

**Solutions:**
```bash
# Start API server
python run_api.py

# Check config
cat test_api_intensive/config/test_config.json | grep base_url

# Test connection
curl http://localhost:8000/health
```

## Configuration

### Adjust Thresholds

Edit `test_api_intensive/config/test_config.json`:

```json
{
  "performance": {
    "max_response_time_under_load_ms": 10000,
    "max_error_rate_percent": 5.0
  }
}
```

### Adjust Test Parameters

Modify test parameters in the test file:

```python
# Sustained load test
num_requests = 100  # Number of requests
duration_seconds = 60  # Duration in seconds

# Error rate test
num_requests = 50  # Number of requests
max_workers = 10  # Concurrent workers

# Stability test
num_requests = 60  # Number of requests
duration_seconds = 30  # Duration in seconds
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Throughput Tests

on: [push, pull_request]

jobs:
  throughput-tests:
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
      
      - name: Start API server
        run: |
          python run_api.py &
          sleep 10
      
      - name: Run throughput tests
        run: |
          pytest test_api_intensive/suites/test_performance.py::TestThroughput -v --html=reports/throughput_report.html
      
      - name: Upload test report
        uses: actions/upload-artifact@v2
        with:
          name: throughput-test-report
          path: reports/throughput_report.html
```

## Best Practices

1. **Run tests during off-peak hours** for consistent results
2. **Monitor system resources** during tests
3. **Review detailed output** to understand performance characteristics
4. **Track metrics over time** to detect performance regressions
5. **Adjust thresholds** based on your performance requirements
6. **Run tests regularly** as part of CI/CD pipeline

## Next Steps

After running throughput tests:

1. Review performance metrics
2. Identify bottlenecks
3. Optimize API if needed
4. Run other performance tests (Task 7.3)
5. Proceed to load and stress tests (Task 8)

## Support

For issues or questions:
1. Check API logs: `api_startup.log`
2. Review test output carefully
3. Verify all prerequisites are met
4. Check configuration settings
5. Consult TASK_7_2_THROUGHPUT_TESTS_SUMMARY.md for detailed information
