#!/usr/bin/env python3
"""
Verification script to check if the test framework setup is complete and correct.
Run this script to verify all components are in place.
"""

import sys
import json
from pathlib import Path
from typing import List, Tuple


def check_file_exists(filepath: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    if filepath.exists():
        return True, f"✓ {description}: {filepath}"
    else:
        return False, f"✗ {description}: {filepath} (MISSING)"


def check_directory_exists(dirpath: Path, description: str) -> Tuple[bool, str]:
    """Check if a directory exists."""
    if dirpath.is_dir():
        return True, f"✓ {description}: {dirpath}/"
    else:
        return False, f"✗ {description}: {dirpath}/ (MISSING)"


def verify_setup() -> bool:
    """Verify the test framework setup."""
    
    print("=" * 70)
    print("API Intensive Testing Framework - Setup Verification")
    print("=" * 70)
    print()
    
    base_dir = Path(__file__).parent
    all_checks_passed = True
    
    # Check directories
    print("Checking Directory Structure:")
    print("-" * 70)
    
    directories = [
        (base_dir / "config", "Configuration directory"),
        (base_dir / "suites", "Test suites directory"),
        (base_dir / "utils", "Utilities directory"),
        (base_dir / "reports", "Reports directory"),
    ]
    
    for dirpath, description in directories:
        passed, message = check_directory_exists(dirpath, description)
        print(message)
        all_checks_passed = all_checks_passed and passed
    
    print()
    
    # Check core files
    print("Checking Core Files:")
    print("-" * 70)
    
    core_files = [
        (base_dir / "__init__.py", "Package init"),
        (base_dir / "conftest.py", "Pytest fixtures"),
        (base_dir / "pytest.ini", "Pytest configuration"),
        (base_dir / "requirements.txt", "Dependencies"),
        (base_dir / "setup.py", "Package setup"),
        (base_dir / "Makefile", "Make commands"),
        (base_dir / ".gitignore", "Git ignore"),
    ]
    
    for filepath, description in core_files:
        passed, message = check_file_exists(filepath, description)
        print(message)
        all_checks_passed = all_checks_passed and passed
    
    print()
    
    # Check documentation
    print("Checking Documentation:")
    print("-" * 70)
    
    doc_files = [
        (base_dir / "README.md", "Main documentation"),
        (base_dir / "QUICKSTART.md", "Quick start guide"),
        (base_dir / "SETUP_SUMMARY.md", "Setup summary"),
        (base_dir / ".env.example", "Environment template"),
    ]
    
    for filepath, description in doc_files:
        passed, message = check_file_exists(filepath, description)
        print(message)
        all_checks_passed = all_checks_passed and passed
    
    print()
    
    # Check configuration
    print("Checking Configuration:")
    print("-" * 70)
    
    config_files = [
        (base_dir / "config" / "__init__.py", "Config package init"),
        (base_dir / "config" / "test_config.json", "Test configuration"),
    ]
    
    for filepath, description in config_files:
        passed, message = check_file_exists(filepath, description)
        print(message)
        all_checks_passed = all_checks_passed and passed
    
    # Validate JSON configuration
    config_file = base_dir / "config" / "test_config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check required sections
            required_sections = ['api', 'test_data', 'performance', 'thresholds']
            for section in required_sections:
                if section in config:
                    print(f"✓ Config section '{section}' present")
                else:
                    print(f"✗ Config section '{section}' MISSING")
                    all_checks_passed = False
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in test_config.json: {e}")
            all_checks_passed = False
    
    print()
    
    # Check subdirectory init files
    print("Checking Subdirectory Init Files:")
    print("-" * 70)
    
    init_files = [
        (base_dir / "suites" / "__init__.py", "Suites package init"),
        (base_dir / "utils" / "__init__.py", "Utils package init"),
    ]
    
    for filepath, description in init_files:
        passed, message = check_file_exists(filepath, description)
        print(message)
        all_checks_passed = all_checks_passed and passed
    
    print()
    
    # Check Python version
    print("Checking Python Environment:")
    print("-" * 70)
    
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✓ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"✗ Python version: {python_version.major}.{python_version.minor}.{python_version.micro} (3.8+ required)")
        all_checks_passed = False
    
    print()
    
    # Summary
    print("=" * 70)
    if all_checks_passed:
        print("✓ ALL CHECKS PASSED - Setup is complete!")
        print()
        print("Next steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Review configuration: config/test_config.json")
        print("  3. Read documentation: README.md or QUICKSTART.md")
        print("  4. Start implementing test utilities (Task 2)")
    else:
        print("✗ SOME CHECKS FAILED - Please review the output above")
        print()
        print("Fix any missing files or directories before proceeding.")
    print("=" * 70)
    
    return all_checks_passed


if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)
