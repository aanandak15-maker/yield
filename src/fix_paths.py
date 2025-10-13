#!/usr/bin/env python3
"""
Fix database paths in all Phase 5 modules to use project root paths
"""

import os
import re

def fix_database_paths():
    """Fix database path issues in all modules"""

    # Files to fix
    files_to_fix = [
        'crop_variety_database.py',
        'sowing_date_intelligence.py',
        'unified_data_pipeline.py'
    ]

    # Pattern to fix: database_path from self.db_config.get('database_path', 'data/database/...')
    # Replace with: os.path.join(os.path.dirname(__file__), '..', self.db_config.get('database_path', 'data/database/...')

    for filename in files_to_fix:
        filepath = os.path.join(os.path.dirname(__file__), filename)

        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Pattern 1: db_path = Path(self.db_config.get('database_path', 'data/database/crop_prediction.db'))
            pattern1 = r'(db_path = Path\(self\.db_config\.get\(\'database_path\', \'data/database/crop_prediction\.db\'\))'
            replacement1 = r'\1\n        # Ensure path is relative to project root\n        if not db_path.is_absolute():\n            db_path = Path(os.path.join(os.path.dirname(__file__), "..", str(db_path)))'

            # Pattern 2: self.db_path = Path(self.db_config.get('database_path', 'data/database/...'))
            pattern2 = r'(self\.db_path = Path\(self\.db_config\.get\(\'database_path\''
            replacement2 = r'\1)\n        # Ensure path is relative to project root\n        if not self.db_path.is_absolute():\n            self.db_path = Path(os.path.join(os.path.dirname(__file__), "..", str(self.db_path)))'

            # Apply fixes
            content = re.sub(pattern1, replacement1, content)
            content = re.sub(pattern2, replacement2, content)

            with open(filepath, 'w') as f:
                f.write(content)

            print(f"✅ Fixed database paths in {filename}")

        except Exception as e:
            print(f"❌ Failed to fix {filename}: {e}")

if __name__ == "__main__":
    fix_database_paths()
