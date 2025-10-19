# Load Tests Quick Reference

## Quick Start

```bash
# 1. Start API
python run_api.py

# 2. Run all load tests
cd test_api_intensive
pytest suites/test_load.py -v -s

# 3. Check results
ls -lh reports/load_test_*.json
```

## Individual Tests

```bash
# Ramp-up (1 → 100 users)
pytest suites/test_load.py::TestLoadAndStress::test_gradual_ramp_up -v -s

# Sustained (100 users, 5 min)
pytest suites/test_load.py::TestLoadAndStress::test_sustained_high_load -v -s

# Spike (10 → 150 users)
pytest suites/test_load.py::TestLoadAndStress::test_spike_load -v -s

# Stress (200 users)
pytest suites/test_load.py::TestLoadAndStress::test_stress_beyond_capacity -v -s

# Recovery
pytest suites/test_load.py::TestLoadAndStress::test_system_recovery -v -s
```

## Locust (Interactive)

```bash
# Start web UI
locust -f suites/test_load.py --host=http://localhost:8000
# Open http://localhost:8089

# Headless mode
locust -f suites/test_load.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --html reports/locust_report.html
```

## Test Patterns

| Test | Users | Duration | Purpose |
|------|-------|----------|---------|
| Ramp-up | 1→100 | 60s | Gradual increase |
| Sustained | 100 | 5min | Stability |
| Spike | 10→150→10 | 70s | Sudden load |
| Stress | 200 | 60s | Beyond capacity |
| Recovery | 150→10 | 90s | Recovery time |

## Success Criteria

- ✅ Error rate < 5%
- ✅ P95 < 10s
- ✅ P99 < 15s
- ✅ Memory < 2GB
- ✅ System stable

## Results Location

```
test_api_intensive/reports/
├── load_test_ramp_up_*.json
├── load_test_sustained_*.json
├── load_test_spike_*.json
├── load_test_stress_*.json
├── load_test_recovery_*.json
└── locust_report.html
```

## Configuration

Edit `config/test_config.json`:

```json
{
  "performance": {
    "load_test_duration_seconds": 300,
    "ramp_up_time_seconds": 60,
    "stress_test_max_users": 200,
    "spike_test_users": 150
  },
  "thresholds": {
    "max_error_rate_percent": 5.0,
    "max_p95_response_time_ms": 10000
  }
}
```

## Monitoring

```bash
# Watch API logs
tail -f logs/api.log

# Monitor resources
top -p $(pgrep -f run_api.py)

# Check API health
curl http://localhost:8000/health
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check API is running |
| High error rate | Check API logs, reduce load |
| Timeout | Increase timeout in config |
| Out of memory | Reduce concurrent users |

## Quick Adjustments

For faster testing during development:

```json
{
  "performance": {
    "load_test_duration_seconds": 60,
    "ramp_up_time_seconds": 30,
    "stress_test_max_users": 50
  }
}
```

## Example Output

```
✅ Sustained load test completed:
   Duration: 300.5s
   Total requests: 3000
   Success rate: 98.50%
   Throughput: 9.98 RPS
   Avg response time: 2345.67ms
   P95 response time: 4567.89ms
   CPU usage: 45.2% avg, 78.5% max
   Memory usage: 512.3MB avg, 678.9MB max
```

## More Info

See `RUNNING_LOAD_TESTS.md` for detailed documentation.
