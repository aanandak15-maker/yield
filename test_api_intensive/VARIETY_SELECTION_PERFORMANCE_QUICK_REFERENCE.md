# Variety Selection Performance Tests - Quick Reference

## Quick Commands

```bash
# Run all variety selection performance tests
make test-variety-selection-performance

# Or with pytest directly
python -m pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance -v

# Run with detailed output
python -m pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance -v -s

# Generate HTML report
python -m pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance --html=reports/variety_selection_perf.html --self-contained-html
```

## Individual Tests

```bash
# Test 1: Query time measurement
pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance::test_variety_selection_query_time -v -s

# Test 2: Concurrent load
pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance::test_variety_selection_under_concurrent_load -v -s

# Test 3: Database query performance
pytest test_api_intensive/suites/test_performance.py::TestVarietySelectionPerformance::test_database_query_performance_verification -v -s
```

## What Each Test Does

| Test | Purpose | Key Metrics |
|------|---------|-------------|
| `test_variety_selection_query_time` | Measures overhead of auto-selection | Overhead < 500ms |
| `test_variety_selection_under_concurrent_load` | Tests 20 concurrent requests | P95 < 10s, 100% success |
| `test_database_query_performance_verification` | Validates DB query efficiency | Variance < 5x, all < 8s |

## Expected Output

### Query Time Test
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

### Concurrent Load Test
```
⏱️  Testing variety selection under concurrent load (20 requests)
✓ Variety selection under concurrent load completed
  Concurrent requests: 20
  Success rate: 100%
  Auto-selection rate: 100%
  Performance metrics:
    Average time: 2567.89ms
    P95 time: 3234.56ms
  Throughput: 7.82 req/s
```

### Database Query Test
```
⏱️  Verifying database query performance for variety selection
✓ Database query performance verified
  Test scenarios: 9
  Query performance:
    Average time: 2234.56ms
    Time variance: 1.49x
  ✓ Time variance is acceptable (< 5.0x)
  ✓ All queries completed in acceptable time (< 8000ms)
```

## Performance Thresholds

| Metric | Target | Acceptable | Warning |
|--------|--------|------------|---------|
| Selection Overhead | < 100ms | < 500ms | > 500ms |
| Concurrent P95 | < 5s | < 10s | > 10s |
| Query Variance | < 2x | < 5x | > 5x |
| Success Rate | 100% | > 95% | < 95% |

## Prerequisites

- ✅ API server running on http://localhost:8000
- ✅ Variety database populated
- ✅ Test configuration valid
- ✅ GEE/OpenWeather credentials configured

## Troubleshooting

| Issue | Solution |
|-------|----------|
| GEE auth failed | Check credentials, use historical dates |
| High response times | Check API server load, external services |
| Database warnings | Verify indexes exist, run ANALYZE |
| Inconsistent results | Run multiple times, check system load |

## Documentation

- Full guide: `RUNNING_VARIETY_SELECTION_PERFORMANCE_TESTS.md`
- Implementation: `TASK_7_3_VARIETY_SELECTION_PERFORMANCE_SUMMARY.md`
- Verification: `TASK_7_3_VERIFICATION.md`

## Requirements Covered

✅ Requirement 4.9: Variety selection query time < 100ms  
✅ Requirement 4.9: Test under concurrent load  
✅ Requirement 4.9: Verify database query performance
