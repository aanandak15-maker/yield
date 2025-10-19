"""
Shared pytest fixtures and configuration for all test suites.

This file is automatically loaded by pytest and provides common fixtures
that can be used across all test modules.
"""

import pytest
import json
import os
from pathlib import Path
from typing import Dict, Any


# Get the test directory path
TEST_DIR = Path(__file__).parent
CONFIG_DIR = TEST_DIR / "config"
REPORTS_DIR = TEST_DIR / "reports"


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    Load test configuration from config file.
    
    Returns:
        Dictionary containing test configuration
    """
    config_path = CONFIG_DIR / "test_config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    else:
        # Return default configuration if file doesn't exist
        return {
            "api": {
                "base_url": os.getenv("API_BASE_URL", "http://localhost:8000"),
                "timeout_seconds": 30,
                "retry_attempts": 3
            },
            "performance": {
                "max_response_time_ms": 5000,
                "max_response_time_under_load_ms": 10000,
                "concurrent_users": [1, 10, 50, 100],
                "load_test_duration_seconds": 60
            }
        }


@pytest.fixture(scope="session")
def config(test_config) -> Dict[str, Any]:
    """
    Alias for test_config for convenience.
    
    Returns:
        Dictionary containing test configuration
    """
    return test_config


@pytest.fixture(scope="session")
def api_base_url(test_config) -> str:
    """
    Get API base URL from configuration.
    
    Returns:
        API base URL string
    """
    return test_config["api"]["base_url"]


@pytest.fixture(scope="session")
def api_timeout(test_config) -> int:
    """
    Get API timeout from configuration.
    
    Returns:
        Timeout in seconds
    """
    return test_config["api"]["timeout_seconds"]


@pytest.fixture(scope="function")
def test_data_dir() -> Path:
    """
    Get path to test data directory.
    
    Returns:
        Path to test data directory
    """
    return CONFIG_DIR


@pytest.fixture(scope="session")
def reports_dir() -> Path:
    """
    Get path to reports directory.
    
    Returns:
        Path to reports directory
    """
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(exist_ok=True)
    return REPORTS_DIR


@pytest.fixture(scope="function")
def performance_thresholds(test_config) -> Dict[str, Any]:
    """
    Get performance thresholds from configuration.
    
    Returns:
        Dictionary containing performance thresholds
    """
    return test_config.get("performance", {})


def pytest_configure(config):
    """
    Pytest hook for initial configuration.
    Called before test collection.
    """
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # Register custom markers
    config.addinivalue_line(
        "markers", "functional: Functional tests for API endpoints"
    )
    config.addinivalue_line(
        "markers", "variety_selection: Tests for automatic variety selection"
    )
    config.addinivalue_line(
        "markers", "validation: Input validation tests"
    )
    config.addinivalue_line(
        "markers", "edge_case: Edge case and boundary value tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and response time tests"
    )
    config.addinivalue_line(
        "markers", "load: Load and stress tests"
    )
    config.addinivalue_line(
        "markers", "error_handling: Error handling and recovery tests"
    )
    config.addinivalue_line(
        "markers", "security: Security and input sanitization tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with external services"
    )
    config.addinivalue_line(
        "markers", "backward_compat: Backward compatibility tests"
    )
    config.addinivalue_line(
        "markers", "end_to_end: End-to-end scenario tests"
    )
    config.addinivalue_line(
        "markers", "monitoring: Monitoring and logging tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than 5 seconds"
    )
    config.addinivalue_line(
        "markers", "fast: Tests that complete quickly (< 1 second)"
    )
    config.addinivalue_line(
        "markers", "critical: Critical tests that must pass"
    )


def pytest_collection_modifyitems(config, items):
    """
    Pytest hook to modify test items after collection.
    Can be used to add markers based on test characteristics.
    """
    for item in items:
        # Add 'slow' marker to tests with timeout > 5 seconds
        if item.get_closest_marker("timeout"):
            timeout_marker = item.get_closest_marker("timeout")
            if timeout_marker.args and timeout_marker.args[0] > 5:
                item.add_marker(pytest.mark.slow)


def pytest_report_header(config):
    """
    Add custom header to pytest report.
    """
    return [
        "API Intensive Testing Framework v1.0.0",
        f"Test Directory: {TEST_DIR}",
        f"Reports Directory: {REPORTS_DIR}"
    ]
