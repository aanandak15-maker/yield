# Test Utilities Quick Reference Guide

## Overview

This guide provides quick reference for using the core test utilities in the API intensive testing framework.

## Import Statements

```python
# Import all utilities
from utils import (
    CropYieldAPIClient,
    APIResponse,
    TestDataGenerator,
    PerformanceMetrics,
    assert_valid_prediction_response,
    assert_variety_selection_metadata,
    assert_response_time_within,
    assert_yield_in_range,
    assert_error_response
)
```

## API Client

### Basic Usage

```python
# Create client
client = CropYieldAPIClient("http://localhost:8000", timeout=30)

# Make prediction request
response = client.predict_yield(
    crop_type="Rice",
    latitude=23.2599,
    longitude=77.4126,
    sowing_date="2024-06-15",
    variety_name="IR-64"  # Optional
)

# Check response
if response.is_success():
    print("Success!")
else:
    print(f"Error: {response.get_error_message()}")
```

### Context Manager

```python
with CropYieldAPIClient("http://localhost:8000") as client:
    response = client.predict_yield(...)
    # Client automatically closed
```

### Response Methods

```python
# Status checks
response.is_success()        # 2xx
response.is_client_error()   # 4xx
response.is_server_error()   # 5xx

# Field access
response.has_field('prediction.yield_tons_per_hectare')
response.get_field('prediction.yield_tons_per_hectare', default=0)

# Error handling
response.get_error_message()
```

## Test Data Generator

### Generate Valid Requests

```python
generator = TestDataGenerator(seed=42)  # Seed for reproducibility

# Basic valid request
request = generator.generate_valid_request()

# Specific crop
request = generator.generate_valid_request(crop_type="Rice")

# Without variety (for auto-selection testing)
request = generator.generate_valid_request(include_variety=False)
```

### Generate Invalid Requests

```python
# Invalid crop type
request = generator.generate_invalid_request('invalid_crop')

# Invalid coordinates
request = generator.generate_invalid_request('invalid_coordinates')

# Invalid date
request = generator.generate_invalid_request('invalid_date')

# Future date
request = generator.generate_invalid_request('future_date')

# Missing required field
request = generator.generate_invalid_request('missing_required')
```

### Generate Edge Cases

```python
# Null variety
request = generator.generate_edge_case_request('null_variety')

# Empty variety
request = generator.generate_edge_case_request('empty_variety')

# Boundary coordinates
request = generator.generate_edge_case_request('boundary_coordinates')

# Special characters
request = generator.generate_edge_case_request('special_characters')

# Long strings
request = generator.generate_edge_case_request('long_strings')
```

### Load Test Data

```python
# Generate 100 requests
requests = generator.generate_load_test_requests(100)

# With custom distribution
requests = generator.generate_load_test_requests(
    count=100,
    variety_distribution={
        'with_variety': 0.5,      # 50% with variety
        'without_variety': 0.3,   # 30% without
        'null_variety': 0.2       # 20% null
    }
)
```

### Access Test Data

```python
# Get all test locations
locations = generator.get_test_locations()

# Get varieties for crop
varieties = generator.get_test_varieties('Rice')

# Get random location
location = generator.get_random_location()

# Get random variety
variety = generator.get_random_variety('Wheat')
```

## Custom Assertions

### Prediction Response Validation

```python
# Validate basic prediction response
assert_valid_prediction_response(response)

# Validate with variety metadata check
assert_valid_prediction_response(response, check_variety_metadata=True)
```

### Variety Selection Validation

```python
# Assert variety was auto-selected
assert_variety_selection_metadata(response, expected_assumed=True)

# Assert variety was user-specified
assert_variety_selection_metadata(response, expected_assumed=False)

# Skip metadata field checks
assert_variety_selection_metadata(
    response, 
    expected_assumed=True,
    check_metadata_fields=False
)
```

### Performance Validation

```python
# Assert response time
assert_response_time_within(response, max_ms=5000)

# With custom message
assert_response_time_within(
    response, 
    max_ms=5000,
    message="Response too slow for production"
)
```

### Data Range Validation

```python
# Assert yield in range
assert_yield_in_range(response, min_yield=1.0, max_yield=10.0)

# With crop type context
assert_yield_in_range(
    response, 
    min_yield=3.0, 
    max_yield=8.0,
    crop_type="Rice"
)
```

### Error Response Validation

```python
# Assert error status code
assert_error_response(response, expected_status_code=400)

# With expected error field
assert_error_response(
    response,
    expected_status_code=422,
    expected_error_field='detail'
)
```

### Field Validation

```python
# Assert field exists
assert_field_exists(response, 'prediction.yield_tons_per_hectare')

# Assert field value
assert_field_equals(response, 'status', 'success')

# Assert field type
assert_field_type(response, 'prediction.yield_tons_per_hectare', float)
```

### Data Quality Validation

```python
# Validate satellite data ranges
assert_satellite_data_valid(response)

# Validate weather data ranges
assert_weather_data_valid(response)

# Validate confidence score
assert_confidence_score_valid(response, min_confidence=0.7)
```

### Security Validation

```python
# Check for sensitive data in errors
assert_no_sensitive_data_in_error(response)
```

## Performance Metrics

### Basic Usage

```python
metrics = PerformanceMetrics()
metrics.start_collection()

# Record requests
metrics.record_request(
    endpoint='/predict/yield',
    response_time_ms=150.0,
    status_code=200,
    request_size=500,
    response_size=1000
)

metrics.stop_collection()
```

### Get Statistics

```python
# All endpoints
stats = metrics.get_statistics()

# Specific endpoint
stats = metrics.get_statistics(endpoint='/predict/yield')

# Access statistics
print(f"Total requests: {stats['total_requests']}")
print(f"Success rate: {stats['successful_requests'] / stats['total_requests'] * 100}%")
print(f"Avg response time: {stats['response_time']['avg_ms']:.2f}ms")
print(f"P95 response time: {stats['response_time']['p95_ms']:.2f}ms")
print(f"P99 response time: {stats['response_time']['p99_ms']:.2f}ms")
```

### Calculate Metrics

```python
# Throughput
throughput = metrics.get_throughput()
print(f"Throughput: {throughput:.2f} req/s")

# Error rate
error_rate = metrics.get_error_rate()
print(f"Error rate: {error_rate * 100:.2f}%")

# Response time distribution
distribution = metrics.get_response_time_distribution(bucket_size_ms=100)
for bucket, count in distribution.items():
    print(f"{bucket}: {count} requests")
```

### Get Summary

```python
summary = metrics.get_summary()
print(f"Duration: {summary['collection_period']['duration_seconds']:.2f}s")
print(f"Total requests: {summary['total_requests']}")
print(f"Throughput: {summary['throughput_rps']:.2f} req/s")
print(f"Avg response time: {summary['response_time_summary']['avg_ms']:.2f}ms")
```

### Export Metrics

```python
# Export to JSON
json_data = metrics.export_metrics('json')

# Export to CSV
csv_data = metrics.export_metrics('csv')

# Export to file
metrics.export_to_file('metrics.json', format='json')
metrics.export_to_file('metrics.csv', format='csv')
```

### Get Errors

```python
errors = metrics.get_errors()
for error in errors:
    print(f"{error['timestamp']}: {error['status_code']} - {error['error_message']}")
```

## Common Patterns

### Test with Metrics Collection

```python
def test_prediction_performance():
    client = CropYieldAPIClient("http://localhost:8000")
    generator = TestDataGenerator()
    metrics = PerformanceMetrics()
    
    metrics.start_collection()
    
    for i in range(100):
        request = generator.generate_valid_request()
        response = client.predict_yield(**request)
        
        metrics.record_request(
            endpoint='/predict/yield',
            response_time_ms=response.response_time_ms,
            status_code=response.status_code,
            request_size=len(str(request)),
            response_size=len(str(response.json_data))
        )
        
        assert_valid_prediction_response(response)
        assert_response_time_within(response, 5000)
    
    metrics.stop_collection()
    
    # Verify performance
    stats = metrics.get_statistics()
    assert stats['response_time']['p95_ms'] < 5000
    assert metrics.get_error_rate() < 0.05  # Less than 5% errors
```

### Test Variety Selection

```python
def test_variety_auto_selection():
    client = CropYieldAPIClient("http://localhost:8000")
    generator = TestDataGenerator()
    
    # Generate request without variety
    request = generator.generate_valid_request(include_variety=False)
    
    response = client.predict_yield(**request)
    
    # Validate auto-selection occurred
    assert_valid_prediction_response(response, check_variety_metadata=True)
    assert_variety_selection_metadata(response, expected_assumed=True)
    
    # Check metadata fields
    assert_field_exists(response, 'prediction.default_variety_selection.selected_variety')
    assert_field_exists(response, 'prediction.default_variety_selection.region')
    assert_field_exists(response, 'prediction.default_variety_selection.reason')
```

### Test Error Handling

```python
def test_invalid_input_handling():
    client = CropYieldAPIClient("http://localhost:8000")
    generator = TestDataGenerator()
    
    # Generate invalid request
    request = generator.generate_invalid_request('invalid_crop')
    
    response = client.predict_yield(**request)
    
    # Validate error response
    assert_error_response(response, expected_status_code=400)
    assert_no_sensitive_data_in_error(response)
```

## Tips

1. **Use seeds for reproducibility**: Always use `TestDataGenerator(seed=42)` in tests
2. **Context managers**: Use `with` statement for automatic cleanup
3. **Batch metrics**: Collect metrics for multiple requests before analyzing
4. **Custom assertions**: Chain assertions for comprehensive validation
5. **Error handling**: Always check `response.is_success()` before accessing data

## Reference

- API Client: `test_api_intensive/utils/api_client.py`
- Test Data Generator: `test_api_intensive/utils/test_data_generator.py`
- Assertions: `test_api_intensive/utils/assertions.py`
- Performance Metrics: `test_api_intensive/utils/performance_metrics.py`
