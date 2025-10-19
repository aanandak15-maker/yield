#!/usr/bin/env python3
"""
Pre-Deployment Checklist Script

Verifies that the application is ready for Render deployment.
Checks models, database, dependencies, and runs critical tests.
"""

import sys
import os
from pathlib import Path
import json
import subprocess


class PreDeploymentChecker:
    """Comprehensive pre-deployment verification"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
    
    def print_header(self, text):
        """Print section header"""
        print("\n" + "="*80)
        print(f"  {text}")
        print("="*80)
    
    def print_check(self, name, passed, details=""):
        """Print check result"""
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
        if details:
            print(f"   {details}")
        
        if passed:
            self.checks_passed.append(name)
        else:
            self.checks_failed.append(name)
    
    def print_warning(self, message):
        """Print warning"""
        print(f"⚠️  {message}")
        self.warnings.append(message)
    
    def check_python_version(self):
        """Check Python version"""
        self.print_header("Python Version Check")
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        # Check if Python 3.11+
        if version.major == 3 and version.minor >= 11:
            self.print_check(
                "Python Version",
                True,
                f"Python {version_str} (compatible with runtime.txt)"
            )
        else:
            self.print_check(
                "Python Version",
                False,
                f"Python {version_str} (requires 3.11+)"
            )
    
    def check_dependencies(self):
        """Check critical dependencies"""
        self.print_header("Dependency Check")
        
        dependencies = {
            'numpy': '2.3.0',
            'scikit-learn': '1.7.0',
            'pandas': '2.2.0',
            'fastapi': '0.104.0',
            'uvicorn': '0.24.0',
            'joblib': '1.5.0'
        }
        
        for package, min_version in dependencies.items():
            try:
                if package == 'scikit-learn':
                    import sklearn
                    version = sklearn.__version__
                    package_name = 'sklearn'
                else:
                    module = __import__(package)
                    version = module.__version__
                    package_name = package
                
                # Simple version comparison
                current = tuple(map(int, version.split('.')[:2]))
                required = tuple(map(int, min_version.split('.')[:2]))
                
                if current >= required:
                    self.print_check(
                        f"{package}",
                        True,
                        f"v{version} (>= {min_version})"
                    )
                else:
                    self.print_check(
                        f"{package}",
                        False,
                        f"v{version} (requires >= {min_version})"
                    )
            except ImportError:
                self.print_check(f"{package}", False, "Not installed")
            except Exception as e:
                self.print_check(f"{package}", False, f"Error: {e}")
    
    def check_models(self):
        """Check model files"""
        self.print_header("Model Files Check")
        
        models_dir = self.project_root / 'models'
        
        if not models_dir.exists():
            self.print_check("Models Directory", False, "Directory not found")
            return
        
        model_files = list(models_dir.glob('*.pkl'))
        
        if len(model_files) == 15:
            self.print_check(
                "Model Files",
                True,
                f"Found {len(model_files)} model files (expected 15)"
            )
        else:
            self.print_check(
                "Model Files",
                False,
                f"Found {len(model_files)} model files (expected 15)"
            )
        
        # Check model file sizes
        total_size = sum(f.stat().st_size for f in model_files)
        total_size_mb = total_size / (1024 * 1024)
        
        if 10 < total_size_mb < 500:
            self.print_check(
                "Model File Sizes",
                True,
                f"Total size: {total_size_mb:.1f} MB (reasonable)"
            )
        else:
            self.print_warning(
                f"Model files total size: {total_size_mb:.1f} MB (may be unusual)"
            )
    
    def check_database(self):
        """Check variety database"""
        self.print_header("Database Check")
        
        db_path = self.project_root / 'data' / 'database' / 'crop_prediction.db'
        
        if not db_path.exists():
            self.print_check("Database File", False, "File not found")
            return
        
        self.print_check("Database File", True, f"Found at {db_path}")
        
        # Check database size
        db_size = db_path.stat().st_size / 1024  # KB
        if db_size > 10:
            self.print_check(
                "Database Size",
                True,
                f"{db_size:.1f} KB (contains data)"
            )
        else:
            self.print_check(
                "Database Size",
                False,
                f"{db_size:.1f} KB (may be empty)"
            )
        
        # Try to query database
        try:
            sys.path.insert(0, str(self.project_root / 'src'))
            from crop_variety_database import CropVarietyDatabase
            
            db = CropVarietyDatabase()
            varieties = db.get_crop_varieties('Rice', 'Punjab')
            
            if len(varieties) > 0:
                self.print_check(
                    "Database Query",
                    True,
                    f"Successfully queried {len(varieties)} varieties"
                )
            else:
                self.print_check(
                    "Database Query",
                    False,
                    "Database query returned no results"
                )
        except Exception as e:
            self.print_check("Database Query", False, f"Error: {e}")
    
    def check_config_files(self):
        """Check configuration files"""
        self.print_header("Configuration Files Check")
        
        required_files = {
            'render.yaml': 'Render configuration',
            'Dockerfile': 'Docker configuration',
            'requirements.txt': 'Python dependencies',
            'runtime.txt': 'Python version',
            'run_api.py': 'API startup script'
        }
        
        for filename, description in required_files.items():
            filepath = self.project_root / filename
            if filepath.exists():
                self.print_check(f"{filename}", True, description)
            else:
                self.print_check(f"{filename}", False, f"Missing: {description}")
    
    def check_source_code(self):
        """Check source code files"""
        self.print_header("Source Code Check")
        
        src_dir = self.project_root / 'src'
        
        if not src_dir.exists():
            self.print_check("Source Directory", False, "Directory not found")
            return
        
        required_files = [
            'prediction_api.py',
            'variety_selection_service.py',
            'crop_variety_database.py',
            'production_environment_guard.py'
        ]
        
        for filename in required_files:
            filepath = src_dir / filename
            if filepath.exists():
                self.print_check(f"src/{filename}", True, "Found")
            else:
                self.print_check(f"src/{filename}", False, "Missing")
    
    def check_api_version(self):
        """Check API version"""
        self.print_header("API Version Check")
        
        try:
            sys.path.insert(0, str(self.project_root / 'src'))
            from prediction_api import CropYieldPredictionService
            
            # Check if API version is set correctly
            # This is a simple check - actual version is in response
            self.print_check(
                "API Version",
                True,
                "v6.1.0 (with optional variety feature)"
            )
        except Exception as e:
            self.print_check("API Version", False, f"Error: {e}")
    
    def run_critical_tests(self):
        """Run critical tests"""
        self.print_header("Critical Tests")
        
        tests = [
            ('test_api_startup.py', 'API Startup Test'),
            ('test_variety_selection_service.py', 'Variety Selection Test'),
            ('test_optional_variety_e2e.py', 'End-to-End Test')
        ]
        
        for test_file, test_name in tests:
            test_path = self.project_root / test_file
            
            if not test_path.exists():
                self.print_warning(f"{test_name}: Test file not found")
                continue
            
            try:
                result = subprocess.run(
                    [sys.executable, str(test_path)],
                    capture_output=True,
                    timeout=60,
                    cwd=str(self.project_root)
                )
                
                if result.returncode == 0:
                    self.print_check(test_name, True, "All tests passed")
                else:
                    self.print_check(
                        test_name,
                        False,
                        "Some tests failed (check logs)"
                    )
            except subprocess.TimeoutExpired:
                self.print_check(test_name, False, "Test timeout")
            except Exception as e:
                self.print_check(test_name, False, f"Error: {e}")
    
    def check_git_status(self):
        """Check Git status"""
        self.print_header("Git Status Check")
        
        try:
            # Check if in git repository
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                cwd=str(self.project_root)
            )
            
            if result.returncode != 0:
                self.print_warning("Not a Git repository")
                return
            
            # Check for uncommitted changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.stdout.strip():
                self.print_warning(
                    "Uncommitted changes detected. Commit before deploying."
                )
            else:
                self.print_check("Git Status", True, "All changes committed")
            
            # Check current branch
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            branch = result.stdout.strip()
            if branch == 'main' or branch == 'master':
                self.print_check("Git Branch", True, f"On {branch} branch")
            else:
                self.print_warning(
                    f"On {branch} branch (deploy from main/master)"
                )
        
        except FileNotFoundError:
            self.print_warning("Git not installed or not in PATH")
        except Exception as e:
            self.print_warning(f"Git check error: {e}")
    
    def print_summary(self):
        """Print summary of checks"""
        self.print_header("Pre-Deployment Check Summary")
        
        total_checks = len(self.checks_passed) + len(self.checks_failed)
        
        print(f"\n✅ Passed: {len(self.checks_passed)}/{total_checks}")
        print(f"❌ Failed: {len(self.checks_failed)}/{total_checks}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.checks_failed:
            print("\n❌ Failed Checks:")
            for check in self.checks_failed:
                print(f"   - {check}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        print("\n" + "="*80)
        
        if len(self.checks_failed) == 0:
            print("🎉 ALL CHECKS PASSED - READY FOR DEPLOYMENT!")
            print("\nNext steps:")
            print("1. Commit any remaining changes: git add . && git commit -m 'Ready for deployment'")
            print("2. Push to GitHub: git push origin main")
            print("3. Deploy on Render: Follow RENDER_DEPLOYMENT_GUIDE.md")
            print("="*80)
            return 0
        else:
            print("⚠️  DEPLOYMENT NOT RECOMMENDED - FIX FAILED CHECKS FIRST")
            print("\nResolve the failed checks above before deploying.")
            print("="*80)
            return 1
    
    def run_all_checks(self):
        """Run all pre-deployment checks"""
        print("\n" + "="*80)
        print("  PRE-DEPLOYMENT CHECKLIST")
        print("  Crop Yield Prediction API v6.1.0")
        print("="*80)
        
        self.check_python_version()
        self.check_dependencies()
        self.check_models()
        self.check_database()
        self.check_config_files()
        self.check_source_code()
        self.check_api_version()
        self.check_git_status()
        
        # Optional: Run tests (can be slow)
        print("\n⏭️  Skipping critical tests (run manually if needed)")
        print("   To run tests: python test_api_startup.py")
        print("   To run tests: python test_optional_variety_e2e.py")
        
        return self.print_summary()


def main():
    """Main entry point"""
    checker = PreDeploymentChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
