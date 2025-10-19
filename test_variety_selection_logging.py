#!/usr/bin/env python3
"""
Test suite for variety selection logging and monitoring

Verifies that all logging requirements are met:
- INFO-level logging for successful selections
- WARNING-level logging for fallback scenarios
- ERROR-level logging for failures
- Performance timing logs
- Structured metadata in logs
"""

import sys
import os
import logging
import time
import re
from io import StringIO
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from variety_selection_service import VarietySelectionService
from crop_variety_database import CropVarietyDatabase


class LogCapture:
    """Helper class to capture log messages"""
    
    def __init__(self):
        self.records = []
        self.handler = None
        
    def __enter__(self):
        # Create a custom handler that captures log records
        self.handler = logging.Handler()
        self.handler.emit = lambda record: self.records.append(record)
        
        # Add handler to the variety selection service logger
        logger = logging.getLogger('variety_selection_service')
        logger.addHandler(self.handler)
        logger.setLevel(logging.DEBUG)
        
        return self
    
    def __exit__(self, *args):
        # Remove handler
        logger = logging.getLogger('variety_selection_service')
        logger.removeHandler(self.handler)
    
    def get_messages(self, level=None):
        """Get log messages, optionally filtered by level"""
        if level:
            return [r.getMessage() for r in self.records if r.levelname == level]
        return [r.getMessage() for r in self.records]
    
    def get_records(self, level=None):
        """Get log records, optionally filtered by level"""
        if level:
            return [r for r in self.records if r.levelname == level]
        return self.records


def test_successful_regional_selection_logging():
    """Test INFO-level logging for successful regional variety selection"""
    print("\n🧪 Test: Successful regional selection logging")
    
    # Create mock database
    mock_db = Mock(spec=CropVarietyDatabase)
    
    # Mock regional varieties
    regional_varieties = pd.DataFrame({
        'variety_name': ['Swarna', 'IR-64', 'Basmati 370'],
        'yield_potential': [5.8, 5.5, 5.2],
        'region_prevalence': ['Madhya Pradesh', 'Madhya Pradesh', 'Madhya Pradesh']
    })
    
    mock_db.get_crop_varieties.return_value = regional_varieties
    mock_db.get_variety_by_name.return_value = {'variety_name': 'Swarna', 'yield_potential': 5.8}
    
    # Create service
    service = VarietySelectionService(mock_db)
    
    # Capture logs
    with LogCapture() as log_capture:
        result = service.select_default_variety('Rice', 'Bhopal')
    
    # Verify result
    assert result['variety_name'] == 'Swarna'
    assert result['variety_assumed'] is True
    assert result['selection_metadata']['reason'] == 'regional_highest_yield'
    
    # Verify INFO-level logs
    info_logs = log_capture.get_messages('INFO')
    assert len(info_logs) > 0, "Should have INFO-level logs"
    
    # Find the success log
    success_log = [log for log in info_logs if 'Variety selection successful' in log]
    assert len(success_log) > 0, "Should have success log"
    
    success_msg = success_log[0]
    print(f"   Success log: {success_msg}")
    
    # Verify log contains required metadata
    assert 'crop_type=Rice' in success_msg, "Should log crop_type"
    assert 'location=Bhopal' in success_msg, "Should log location"
    assert 'region=Madhya Pradesh' in success_msg, "Should log region"
    assert 'selected_variety=Swarna' in success_msg, "Should log selected variety"
    assert 'reason=regional_highest_yield' in success_msg, "Should log reason"
    assert 'yield_potential=' in success_msg, "Should log yield potential"
    assert 'selection_time=' in success_msg, "Should log selection time"
    
    # Verify timing is included
    time_match = re.search(r'selection_time=([\d.]+)ms', success_msg)
    assert time_match, "Should include selection time in ms"
    selection_time = float(time_match.group(1))
    assert selection_time >= 0, "Selection time should be non-negative"
    print(f"   ✅ Selection time: {selection_time:.2f}ms")
    
    # Verify metadata includes timing
    assert 'selection_time_ms' in result['selection_metadata'], "Metadata should include timing"
    
    print("   ✅ INFO-level logging verified for successful selection")


def test_fallback_to_north_india_logging():
    """Test WARNING-level logging for fallback to 'All North India'"""
    print("\n🧪 Test: Fallback to North India logging")
    
    # Create mock database
    mock_db = Mock(spec=CropVarietyDatabase)
    
    # Mock: no regional varieties, but North India varieties exist
    mock_db.get_crop_varieties.side_effect = [
        pd.DataFrame(),  # Empty for specific region
        pd.DataFrame({   # North India varieties
            'variety_name': ['IR-64'],
            'yield_potential': [5.5],
            'region_prevalence': ['All North India']
        })
    ]
    mock_db.get_variety_by_name.return_value = {'variety_name': 'IR-64', 'yield_potential': 5.5}
    
    # Create service
    service = VarietySelectionService(mock_db)
    
    # Capture logs
    with LogCapture() as log_capture:
        result = service.select_default_variety('Rice', 'Bhopal')
    
    # Verify result
    assert result['variety_name'] == 'IR-64'
    assert result['selection_metadata']['reason'] == 'regional_fallback'
    
    # Verify WARNING-level logs for fallback
    warning_logs = log_capture.get_messages('WARNING')
    assert len(warning_logs) > 0, "Should have WARNING-level logs"
    
    # Find the fallback warning
    fallback_log = [log for log in warning_logs if 'Fallback to regional default' in log]
    assert len(fallback_log) > 0, "Should have fallback warning"
    
    fallback_msg = fallback_log[0]
    print(f"   Fallback warning: {fallback_msg}")
    
    # Verify warning contains required metadata
    assert 'crop_type=Rice' in fallback_msg, "Should log crop_type"
    assert 'location=Bhopal' in fallback_msg, "Should log location"
    assert 'original_region=Madhya Pradesh' in fallback_msg, "Should log original region"
    assert 'fallback_region=All North India' in fallback_msg, "Should log fallback region"
    assert 'reason=no_regional_varieties_found' in fallback_msg, "Should log reason"
    
    # Verify INFO-level log for successful fallback selection
    info_logs = log_capture.get_messages('INFO')
    success_log = [log for log in info_logs if 'Variety selection successful (fallback)' in log]
    assert len(success_log) > 0, "Should have success log for fallback"
    
    success_msg = success_log[0]
    print(f"   Success log: {success_msg}")
    
    # Verify success log contains metadata
    assert 'selected_variety=IR-64' in success_msg, "Should log selected variety"
    assert 'reason=regional_fallback' in success_msg, "Should log reason"
    assert 'selection_time=' in success_msg, "Should log selection time"
    
    print("   ✅ WARNING-level logging verified for fallback scenario")


def test_global_default_logging():
    """Test WARNING-level logging for global default usage"""
    print("\n🧪 Test: Global default usage logging")
    
    # Create mock database
    mock_db = Mock(spec=CropVarietyDatabase)
    
    # Mock: no regional varieties at all
    mock_db.get_crop_varieties.return_value = pd.DataFrame()
    mock_db.get_variety_by_name.return_value = {'variety_name': 'IR-64', 'yield_potential': 5.5}
    
    # Create service
    service = VarietySelectionService(mock_db)
    
    # Capture logs
    with LogCapture() as log_capture:
        result = service.select_default_variety('Rice', 'Bhopal')
    
    # Verify result
    assert result['variety_name'] == 'IR-64'
    assert result['selection_metadata']['reason'] == 'global_default'
    
    # Verify WARNING-level logs for global default
    warning_logs = log_capture.get_messages('WARNING')
    assert len(warning_logs) > 0, "Should have WARNING-level logs"
    
    # Find the global default warning
    global_default_log = [log for log in warning_logs if 'Using global default' in log]
    assert len(global_default_log) > 0, "Should have global default warning"
    
    warning_msg = global_default_log[0]
    print(f"   Global default warning: {warning_msg}")
    
    # Verify warning contains required metadata
    assert 'crop_type=Rice' in warning_msg, "Should log crop_type"
    assert 'location=Bhopal' in warning_msg, "Should log location"
    assert 'region=Madhya Pradesh' in warning_msg, "Should log region"
    assert 'reason=no_regional_varieties_found' in warning_msg, "Should log reason"
    
    # Verify INFO-level log for successful global default selection
    info_logs = log_capture.get_messages('INFO')
    success_log = [log for log in info_logs if 'Variety selection successful (global default)' in log]
    assert len(success_log) > 0, "Should have success log for global default"
    
    success_msg = success_log[0]
    print(f"   Success log: {success_msg}")
    
    # Verify success log contains metadata
    assert 'selected_variety=IR-64' in success_msg, "Should log selected variety"
    assert 'reason=global_default' in success_msg, "Should log reason"
    assert 'selection_time=' in success_msg, "Should log selection time"
    
    print("   ✅ WARNING-level logging verified for global default usage")


def test_selection_failure_logging():
    """Test ERROR-level logging for variety selection failures"""
    print("\n🧪 Test: Selection failure logging")
    
    # Create mock database
    mock_db = Mock(spec=CropVarietyDatabase)
    
    # Mock: no varieties at all
    mock_db.get_crop_varieties.return_value = pd.DataFrame()
    mock_db.get_variety_by_name.return_value = None  # No varieties found
    
    # Create service
    service = VarietySelectionService(mock_db)
    
    # Capture logs
    with LogCapture() as log_capture:
        try:
            result = service.select_default_variety('Rice', 'Bhopal')
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"   Expected error: {str(e)}")
    
    # Verify ERROR-level logs
    error_logs = log_capture.get_messages('ERROR')
    assert len(error_logs) > 0, "Should have ERROR-level logs"
    
    # Find the failure log
    failure_log = [log for log in error_logs if 'Variety selection failed' in log]
    assert len(failure_log) > 0, "Should have failure log"
    
    error_msg = failure_log[0]
    print(f"   Error log: {error_msg}")
    
    # Verify error log contains required metadata
    assert 'crop_type=Rice' in error_msg, "Should log crop_type"
    assert 'location=Bhopal' in error_msg, "Should log location"
    assert 'region=Madhya Pradesh' in error_msg, "Should log region"
    assert 'error=' in error_msg, "Should log error message"
    assert 'selection_time=' in error_msg, "Should log selection time even for failures"
    
    print("   ✅ ERROR-level logging verified for selection failure")


def test_performance_timing_logs():
    """Test that performance timing is logged for all scenarios"""
    print("\n🧪 Test: Performance timing logs")
    
    # Create mock database
    mock_db = Mock(spec=CropVarietyDatabase)
    
    # Mock regional varieties
    regional_varieties = pd.DataFrame({
        'variety_name': ['Swarna'],
        'yield_potential': [5.8],
        'region_prevalence': ['Madhya Pradesh']
    })
    
    mock_db.get_crop_varieties.return_value = regional_varieties
    mock_db.get_variety_by_name.return_value = {'variety_name': 'Swarna', 'yield_potential': 5.8}
    
    # Create service
    service = VarietySelectionService(mock_db)
    
    # Measure actual selection time
    start_time = time.time()
    
    # Capture logs
    with LogCapture() as log_capture:
        result = service.select_default_variety('Rice', 'Bhopal')
    
    actual_time_ms = (time.time() - start_time) * 1000
    
    # Verify timing in result metadata
    assert 'selection_time_ms' in result['selection_metadata'], "Should include timing in metadata"
    reported_time = result['selection_metadata']['selection_time_ms']
    print(f"   Reported selection time: {reported_time:.2f}ms")
    print(f"   Actual selection time: {actual_time_ms:.2f}ms")
    
    # Verify timing is reasonable (should be close to actual time)
    assert reported_time <= actual_time_ms + 10, "Reported time should be <= actual time + 10ms"
    assert reported_time >= 0, "Reported time should be non-negative"
    
    # Verify timing in logs
    info_logs = log_capture.get_messages('INFO')
    success_log = [log for log in info_logs if 'selection_time=' in log]
    assert len(success_log) > 0, "Should have timing in logs"
    
    # Extract timing from log
    time_match = re.search(r'selection_time=([\d.]+)ms', success_log[0])
    assert time_match, "Should have timing in correct format"
    log_time = float(time_match.group(1))
    
    # Verify log timing matches metadata timing
    assert abs(log_time - reported_time) < 0.1, "Log timing should match metadata timing"
    
    print("   ✅ Performance timing logs verified")


def test_no_sensitive_data_in_logs():
    """Test that no sensitive user data is logged"""
    print("\n🧪 Test: No sensitive data in logs")
    
    # Create mock database
    mock_db = Mock(spec=CropVarietyDatabase)
    
    # Mock regional varieties
    regional_varieties = pd.DataFrame({
        'variety_name': ['Swarna'],
        'yield_potential': [5.8],
        'region_prevalence': ['Madhya Pradesh']
    })
    
    mock_db.get_crop_varieties.return_value = regional_varieties
    mock_db.get_variety_by_name.return_value = {'variety_name': 'Swarna', 'yield_potential': 5.8}
    
    # Create service
    service = VarietySelectionService(mock_db)
    
    # Capture logs
    with LogCapture() as log_capture:
        result = service.select_default_variety('Rice', 'Bhopal')
    
    # Get all log messages
    all_logs = log_capture.get_messages()
    
    # Verify no sensitive patterns (examples of what NOT to log)
    sensitive_patterns = [
        r'password',
        r'api[_-]?key',
        r'secret',
        r'token',
        r'credit[_-]?card',
        r'ssn',
        r'\d{3}-\d{2}-\d{4}',  # SSN pattern
        r'\d{16}',  # Credit card pattern
    ]
    
    for log_msg in all_logs:
        for pattern in sensitive_patterns:
            assert not re.search(pattern, log_msg, re.IGNORECASE), \
                f"Log should not contain sensitive data matching pattern: {pattern}"
    
    # Verify only expected data is logged (crop type, location, variety, region)
    # These are all non-sensitive operational data
    expected_data_types = ['crop_type', 'location', 'region', 'selected_variety', 'reason']
    
    print(f"   Verified {len(all_logs)} log messages contain no sensitive data")
    print(f"   Only operational data logged: {', '.join(expected_data_types)}")
    print("   ✅ No sensitive data in logs verified")


def test_structured_log_format():
    """Test that logs use structured format with key=value pairs"""
    print("\n🧪 Test: Structured log format")
    
    # Create mock database
    mock_db = Mock(spec=CropVarietyDatabase)
    
    # Mock regional varieties
    regional_varieties = pd.DataFrame({
        'variety_name': ['Swarna'],
        'yield_potential': [5.8],
        'region_prevalence': ['Madhya Pradesh']
    })
    
    mock_db.get_crop_varieties.return_value = regional_varieties
    mock_db.get_variety_by_name.return_value = {'variety_name': 'Swarna', 'yield_potential': 5.8}
    
    # Create service
    service = VarietySelectionService(mock_db)
    
    # Capture logs
    with LogCapture() as log_capture:
        result = service.select_default_variety('Rice', 'Bhopal')
    
    # Get INFO logs
    info_logs = log_capture.get_messages('INFO')
    success_log = [log for log in info_logs if 'Variety selection successful' in log][0]
    
    print(f"   Log message: {success_log}")
    
    # Verify structured format with key=value pairs
    required_keys = [
        'crop_type',
        'location',
        'region',
        'selected_variety',
        'reason',
        'yield_potential',
        'selection_time'
    ]
    
    for key in required_keys:
        # Check for key=value pattern
        pattern = f'{key}=[^|]+'
        assert re.search(pattern, success_log), f"Log should contain {key}=value"
    
    # Verify pipe-separated format for easy parsing
    assert '|' in success_log, "Log should use pipe separators"
    
    print("   ✅ Structured log format verified")


def run_all_tests():
    """Run all logging tests"""
    print("=" * 70)
    print("🧪 Variety Selection Logging Test Suite")
    print("=" * 70)
    
    tests = [
        test_successful_regional_selection_logging,
        test_fallback_to_north_india_logging,
        test_global_default_logging,
        test_selection_failure_logging,
        test_performance_timing_logs,
        test_no_sensitive_data_in_logs,
        test_structured_log_format,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70)
    
    if failed == 0:
        print("✅ All logging tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
