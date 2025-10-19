#!/usr/bin/env python3
"""
Verification script for load and stress test suite implementation.

This script verifies that all components of the load testing framework
are properly implemented and can be imported.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def verify_imports():
    """Verify all required modules can be imported"""
    print("Verifying imports...")
    
    try:
        # Core test module
        from suites import test_load
        print("  ✓ test_load module imported")
        
        # Check for key classes
        assert hasattr(test_load, 'ResourceMonitor'), "ResourceMonitor class not found"
        print("  ✓ ResourceMonitor class found")
        
        assert hasattr(test_load, 'LoadTestRunner'), "LoadTestRunner class not found"
        print("  ✓ LoadTestRunner class found")
        
        assert hasattr(test_load, 'TestLoadAndStress'), "TestLoadAndStress class not found"
        print("  ✓ TestLoadAndStress class found")
        
        # Check for test methods
        test_class = test_load.TestLoadAndStress
        test_methods = [
            'test_gradual_ramp_up',
            'test_sustained_high_load',
            'test_spike_load',
            'test_stress_beyond_capacity',
            'test_system_recovery'
        ]
        
        for method in test_methods:
            assert hasattr(test_class, method), f"Test method {method} not found"
            print(f"  ✓ {method} test method found")
        
        # Check for Locust user (optional)
        if hasattr(test_load, 'CropYieldUser'):
            print("  ✓ CropYieldUser (Locust) class found")
        else:
            print("  ⚠ CropYieldUser (Locust) class not found (Locust may not be installed)")
        
        return True
        
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"  ✗ Assertion error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False


def verify_dependencies():
    """Verify required dependencies are installed"""
    print("\nVerifying dependencies...")
    
    dependencies = {
        'pytest': 'pytest',
        'psutil': 'psutil',
        'requests': 'requests',
        'locust': 'locust (optional)'
    }
    
    all_installed = True
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"  ✓ {name} installed")
        except ImportError:
            if 'optional' in name:
                print(f"  ⚠ {name} not installed (optional)")
            else:
                print(f"  ✗ {name} not installed")
                all_installed = False
    
    return all_installed


def verify_files():
    """Verify all required files exist"""
    print("\nVerifying files...")
    
    base_dir = Path(__file__).parent
    
    required_files = [
        'suites/test_load.py',
        'RUNNING_LOAD_TESTS.md',
        'LOAD_TESTS_QUICK_REFERENCE.md',
        'TASK_8_LOAD_STRESS_TESTS_SUMMARY.md',
        'requirements.txt'
    ]
    
    all_exist = True
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✓ {file_path} exists")
        else:
            print(f"  ✗ {file_path} not found")
            all_exist = False
    
    return all_exist


def verify_configuration():
    """Verify test configuration includes load test settings"""
    print("\nVerifying configuration...")
    
    try:
        import json
        config_path = Path(__file__).parent / 'config' / 'test_config.json'
        
        if not config_path.exists():
            print("  ✗ test_config.json not found")
            return False
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for performance settings
        if 'performance' not in config:
            print("  ✗ 'performance' section not found in config")
            return False
        
        perf_config = config['performance']
        
        required_settings = [
            'load_test_duration_seconds',
            'ramp_up_time_seconds',
            'stress_test_max_users',
            'spike_test_users'
        ]
        
        for setting in required_settings:
            if setting in perf_config:
                print(f"  ✓ {setting}: {perf_config[setting]}")
            else:
                print(f"  ✗ {setting} not found in config")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error reading configuration: {e}")
        return False


def verify_test_structure():
    """Verify test structure and markers"""
    print("\nVerifying test structure...")
    
    try:
        from suites import test_load
        import inspect
        
        test_class = test_load.TestLoadAndStress
        
        # Check class has pytest marker
        if hasattr(test_class, 'pytestmark'):
            markers = [m.name for m in test_class.pytestmark]
            if 'load' in markers:
                print("  ✓ Class has 'load' marker")
            else:
                print("  ⚠ Class missing 'load' marker")
            
            if 'slow' in markers:
                print("  ✓ Class has 'slow' marker")
            else:
                print("  ⚠ Class missing 'slow' marker")
        else:
            print("  ⚠ Class has no pytest markers")
        
        # Check test methods have docstrings
        test_methods = [
            method for method in dir(test_class)
            if method.startswith('test_') and callable(getattr(test_class, method))
        ]
        
        for method_name in test_methods:
            method = getattr(test_class, method_name)
            if method.__doc__:
                print(f"  ✓ {method_name} has docstring")
            else:
                print(f"  ⚠ {method_name} missing docstring")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error verifying test structure: {e}")
        return False


def main():
    """Run all verification checks"""
    print("="*80)
    print("Load and Stress Test Suite Verification")
    print("="*80)
    
    results = {
        'imports': verify_imports(),
        'dependencies': verify_dependencies(),
        'files': verify_files(),
        'configuration': verify_configuration(),
        'structure': verify_test_structure()
    }
    
    print("\n" + "="*80)
    print("Verification Summary")
    print("="*80)
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check.capitalize():20s}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ All verification checks passed!")
        print("\nYou can now run the load tests:")
        print("  pytest suites/test_load.py -v -s")
        print("  locust -f suites/test_load.py --host=http://localhost:8000")
        return 0
    else:
        print("❌ Some verification checks failed")
        print("\nPlease review the errors above and fix any issues.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
