# Quick Start Guide

Get started with the API Intensive Testing Framework in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- The Crop Yield Prediction API running (default: http://localhost:8000)

## Installation

### Step 1: Navigate to Test Directory

```bash
cd test_api_intensive
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the Makefile:

```bash
make install
```

## Configuration

### Basic Configuration

The default configuration in `config/test_config.json` is ready to use with:
- API URL: http://localhost:8000
- Timeout: 30 seconds
- Test locations: Bhopal, Lucknow, Chandigarh, Patna

### Custom Configuration

Edit `config/test_config.json` to change:

```json
{
  "api": {
    "base_url": "http://your-api-url:8000",
    "timeout_seconds": 30
  }
}
```

Or use environment variable:

```bash
export API_BASE_URL="http://your-api-url:8000"
```

## Running Your First Test

### Run All Tests

```bash
pytest
```

Or using Makefile:

```bash
make test
```

### Run Specific Test Suite

```bash
# Functional tests
make test-functional

# Performance tests
make test-performance

# Security tests
make test-security
```

### Run Tests in Parallel (Faster)

```bash
make test-parallel
```

## Viewing Results

### HTML Report

After running tests, open the HTML report:

```bash
make reports
```

Or manually open: `reports/test_report.html`

### Console Output

Tests display results in the console with:
- ✓ Passed tests in green
- ✗ Failed tests in red
- Summary statistics

### Log Files

Detailed logs are saved in: `reports/test_execution.log`

## Common Commands

```bash
# Install dependencies
make install

# Run all tests
make test

# Run fast tests only
make test-fast

# Run critical tests only
make test-critical

# Run tests in parallel
make test-parallel

# Clean test artifacts
make clean

# View test report
make reports
```

## Test Markers

Filter tests by category:

```bash
# Run only functional tests
pytest -m functional

# Run only performance tests
pytest -m performance

# Run fast tests only
pytest -m fast

# Exclude slow tests
pytest -m "not slow"
```

## Next Steps

1. **Review Configuration**: Check `config/test_config.json` for your environment
2. **Run Tests**: Start with `make test-fast` to run quick tests
3. **Review Reports**: Open `reports/test_report.html` to see results
4. **Add Tests**: Create new test files in `suites/` directory
5. **Read Documentation**: See `README.md` for detailed information

## Troubleshooting

### API Not Running

```
Error: Connection refused
```

**Solution**: Start the Crop Yield Prediction API first:

```bash
# In the main project directory
python run_api.py
```

### Import Errors

```
ModuleNotFoundError: No module named 'pytest'
```

**Solution**: Install dependencies:

```bash
pip install -r requirements.txt
```

### Permission Errors

```
Permission denied: reports/
```

**Solution**: Ensure you have write permissions:

```bash
chmod -R 755 reports/
```

## Getting Help

- Check `README.md` for detailed documentation
- Review test examples in `suites/` directory
- Check logs in `reports/test_execution.log`
- Review design document: `.kiro/specs/api-intensive-testing/design.md`

## Example Test Run

```bash
$ make test-fast

======================== test session starts =========================
platform darwin -- Python 3.11.0, pytest-7.4.0
rootdir: /path/to/test_api_intensive
configfile: pytest.ini
plugins: xdist-3.3.0, timeout-2.1.0, html-3.2.0
collected 45 items

suites/test_functional.py ........                            [ 17%]
suites/test_validation.py .......                             [ 33%]
suites/test_variety_selection.py ..........                   [ 55%]

======================== 45 passed in 12.34s =========================
```

Happy Testing! 🚀
