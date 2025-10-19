# Running Load and Stress Tests

This guide explains how to run the load and stress tests for the Crop Yield Prediction API.

## Overview

The load test suite includes:
- **Gradual Ramp-Up Test**: Increases load from 1 to 100 users over time
- **Sustained Load Test**: Maintains 100 users for 5 minutes
- **Spike Test**: Sudden increase from 10 to 150 users
- **Stress Test**: Pushes system beyond capacity with 200 users
- **Recovery Test**: Measures system recovery after stress

## Prerequisites

1. **API Server Running**: Ensure the Crop Yield API is running
   ```bash
   python run_api.py
   ```

2. **Dependencies Installed**: Install test dependencies
   ```bash
   cd test_api_intensive
   pip install -r requirements.txt
   ```

3. **Configuration**: Verify test configuration in `config/test_config.json`

## Running Tests with Pytest

### Run All Load Tests

```bash
# From test_api_intensive directory
pytest suites/test_load.py -v -s

# Or with markers
pytest -m load -v -s
```

### Run Individual Tests

```bash
# Gradual ramp-up test
pytest suites/test_load.py::TestLoadAndStress::test_gradual_ramp_up -v -s

# Sustained load test
pytest suites/test_load.py::TestLoadAndStress::test_sustained_high_load -v -s

# Spike test
pytest suites/test_load.py::TestLoadAndStress::test_spike_load -v -s

# Stress test
pytest suites/test_load.py::TestLoadAndStress::test_stress_beyond_capacity -v -s

# Recovery test
pytest suites/test_load.py::TestLoadAndStress::test_system_recovery -v -s
```

### Quick Test (Shorter Duration)

For faster testing during development, you can modify the configuration:

```bash
# Edit config/test_config.json and reduce durations:
# - load_test_duration_seconds: 60 (instead of 300)
# - ramp_up_time_seconds: 30 (instead of 60)
```

## Running Tests with Locust

Locust provides a web-based UI for interactive load testing.

### Start Locust Web UI

```bash
cd test_api_intensive
locust -f suites/test_load.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser.

### Configure Load Test

In the Locust web UI:
1. **Number of users**: Total users to simulate (e.g., 100)
2. **Spawn rate**: Users to add per second (e.g., 10)
3. Click **Start swarming**

### Locust Command Line

Run Locust without the web UI:

```bash
# Run with 100 users, spawn 10 per second, run for 5 minutes
locust -f suites/test_load.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --html reports/locust_report.html
```

### Advanced Locust Scenarios

```bash
# Gradual ramp-up
locust -f suites/test_load.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 2 \
  --run-time 10m \
  --headless

# Spike test (fast spawn)
locust -f suites/test_load.py \
  --host=http://localhost:8000 \
  --users 150 \
  --spawn-rate 50 \
  --run-time 2m \
  --headless

# Stress test
locust -f suites/test_load.py \
  --host=http://localhost:8000 \
  --users 200 \
  --spawn-rate 20 \
  --run-time 5m \
  --headless
```

## Test Configuration

Key configuration parameters in `config/test_config.json`:

```json
{
  "performance": {
    "max_response_time_ms": 5000,
    "max_response_time_under_load_ms": 10000,
    "concurrent_users": [1, 10, 50, 100],
    "load_test_duration_seconds": 300,
    "ramp_up_time_seconds": 60,
    "stress_test_max_users": 200,
    "spike_test_users": 150,
    "spike_duration_seconds": 10
  },
  "thresholds": {
    "max_error_rate_percent": 5.0,
    "max_p95_response_time_ms": 10000,
    "max_p99_response_time_ms": 15000
  }
}
```

## Understanding Test Results

### Pytest Output

Each test displays:
- **Total requests**: Number of requests executed
- **Success rate**: Percentage of successful requests
- **Throughput**: Requests per second (RPS)
- **Response times**: Average, P95, P99 percentiles
- **Resource usage**: CPU and memory consumption

Example output:
```
✅ Sustained load test completed:
   Duration: 300.5s
   Total requests: 3000
   Success rate: 98.50%
   Throughput: 9.98 RPS
   Avg response time: 2345.67ms
   P95 response time: 4567.89ms
   P99 response time: 6789.01ms
   CPU usage: 45.2% avg, 78.5% max
   Memory usage: 512.3MB avg, 678.9MB max
```

### Result Files

Test results are saved to `reports/` directory:
- `load_test_ramp_up_YYYYMMDD_HHMMSS.json`
- `load_test_sustained_YYYYMMDD_HHMMSS.json`
- `load_test_spike_YYYYMMDD_HHMMSS.json`
- `load_test_stress_YYYYMMDD_HHMMSS.json`
- `load_test_recovery_YYYYMMDD_HHMMSS.json`

### Locust Reports

Locust generates HTML reports with:
- Request statistics (RPS, response times, failures)
- Charts showing performance over time
- Distribution of response times
- Failure details

## Interpreting Results

### Success Criteria

✅ **Good Performance**:
- Error rate < 5%
- P95 response time < 10 seconds
- P99 response time < 15 seconds
- System remains stable under load
- Memory usage < 2GB

⚠️ **Warning Signs**:
- Error rate 5-10%
- P95 response time 10-15 seconds
- Increasing error rate over time
- Memory usage 1-2GB

❌ **Performance Issues**:
- Error rate > 10%
- P95 response time > 15 seconds
- System crashes or becomes unresponsive
- Memory usage > 2GB

### Common Issues

**High Error Rate**:
- Check API logs for errors
- Verify external services (GEE, OpenWeather) are available
- Check database connection pool size
- Review rate limits

**Slow Response Times**:
- Check database query performance
- Review model loading/prediction time
- Check external API latency
- Monitor CPU/memory usage

**Memory Growth**:
- Check for memory leaks
- Review connection pooling
- Monitor model caching
- Check for resource cleanup

## Resource Monitoring

### System Resources

Monitor system resources during tests:

```bash
# CPU and memory
top -p $(pgrep -f run_api.py)

# Or use htop
htop -p $(pgrep -f run_api.py)

# Detailed process info
ps aux | grep run_api.py
```

### API Logs

Monitor API logs during load tests:

```bash
tail -f logs/api.log
```

### Database Performance

Monitor database queries:

```bash
# SQLite query log (if enabled)
tail -f logs/database.log
```

## Best Practices

1. **Start Small**: Begin with lower user counts and shorter durations
2. **Monitor Resources**: Watch CPU, memory, and disk I/O during tests
3. **Baseline First**: Establish baseline performance before load testing
4. **Isolate Tests**: Run load tests on dedicated test environment
5. **Clean State**: Reset database and clear caches between tests
6. **Document Results**: Save and compare results over time
7. **Gradual Increase**: Increase load gradually to find breaking points

## Troubleshooting

### Tests Fail to Start

```bash
# Check API is running
curl http://localhost:8000/health

# Check dependencies
pip list | grep -E "pytest|locust|psutil"

# Verify configuration
python verify_config.py
```

### Connection Errors

```bash
# Check API port
netstat -an | grep 8000

# Check firewall
# (platform-specific)

# Test connectivity
curl -v http://localhost:8000/health
```

### Out of Memory

```bash
# Reduce concurrent users
# Edit config/test_config.json:
# - concurrent_users: [1, 5, 10, 25]
# - stress_test_max_users: 50

# Or increase system memory
```

### Timeout Errors

```bash
# Increase timeout in config
# Edit config/test_config.json:
# - timeout_seconds: 60

# Or reduce load
```

## Advanced Usage

### Custom Load Patterns

Create custom load patterns by modifying `LoadTestRunner` class:

```python
# Example: Custom load pattern
runner = LoadTestRunner(api_client, data_generator)

# Your custom pattern
results = runner.ramp_up_test(
    start_users=5,
    end_users=50,
    ramp_time_seconds=120,
    requests_per_user=10
)
```

### Distributed Load Testing

For higher load, use Locust in distributed mode:

```bash
# Start master
locust -f suites/test_load.py --master --host=http://localhost:8000

# Start workers (on same or different machines)
locust -f suites/test_load.py --worker --master-host=localhost
locust -f suites/test_load.py --worker --master-host=localhost
```

### CI/CD Integration

Add load tests to CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run Load Tests
  run: |
    cd test_api_intensive
    pytest suites/test_load.py -v --html=reports/load_test_report.html
```

## Support

For issues or questions:
1. Check API logs: `logs/api.log`
2. Review test configuration: `config/test_config.json`
3. Check test results: `reports/`
4. Consult main README: `README.md`
