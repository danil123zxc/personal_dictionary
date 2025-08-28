#!/usr/bin/env python3
"""
Migration script to update import statements to the new project structure.

This script helps migrate import statements from the old 'app' structure
to the new 'src' structure.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Mapping of old imports to new imports
IMPORT_MAPPINGS = {
    # Models and schemas
    'from app.models import': 'from src.models.models import',
    'from app.schemas import': 'from src.models.schemas import',
    'from app.crud_schemas import': 'from src.models.crud_schemas import',
    
    # Services
    'from app.crud import': 'from src.services.crud import',
    'from app.auth import': 'from src.services.auth import',
    'from app.generate import': 'from src.services.generate import',
    'from app import crud': 'from src.services import crud',
    'from app import auth': 'from src.services import auth',
    'from app import generate': 'from src.services import generate',
    
    # Core functionality
    'from app.database import': 'from src.core.database import',
    'from app.redis_client import': 'from src.core.redis_client import',
    'from app.redis_dependency import': 'from src.core.redis_dependency import',
    
    # API
    'from app.prompts import': 'from src.api.prompts import',
    'from app.nodes import': 'from src.api.nodes import',
    
    # Configuration
    'import os': 'from src.config.settings import settings',
}

def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in the given directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def update_imports_in_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Update import statements in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Apply import mappings
        for old_import, new_import in IMPORT_MAPPINGS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes.append(f"  {old_import} → {new_import}")
        
        # Update specific import patterns
        patterns = [
            (r'from app\.(\w+) import', r'from src.\1 import'),
            (r'import app\.(\w+)', r'import src.\1'),
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes.append(f"  Updated import pattern: {pattern}")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        
        return False, []
        
    except Exception as e:
        return False, [f"Error processing {file_path}: {e}"]

def main():
    """Main migration function."""
    print("🔄 Starting import migration...")
    print("=" * 50)
    
    # Find all Python files
    python_files = find_python_files('.')
    
    print(f"Found {len(python_files)} Python files")
    
    # Process each file
    updated_files = 0
    total_changes = 0
    
    for file_path in python_files:
        # Skip files in the old app directory
        if 'app/' in str(file_path) and file_path.parent.name == 'app':
            continue
            
        print(f"\nProcessing: {file_path}")
        
        updated, changes = update_imports_in_file(file_path)
        
        if updated:
            updated_files += 1
            total_changes += len(changes)
            print(f"✅ Updated {file_path}")
            for change in changes:
                print(change)
        else:
            print(f"⏭️  No changes needed for {file_path}")
    
    print("\n" + "=" * 50)
    print(f"Migration completed!")
    print(f"📊 Summary:")
    print(f"  - Files processed: {len(python_files)}")
    print(f"  - Files updated: {updated_files}")
    print(f"  - Total changes: {total_changes}")
    
    if updated_files > 0:
        print(f"\n⚠️  Important notes:")
        print(f"  1. Review the changes manually")
        print(f"  2. Test the application thoroughly")
        print(f"  3. Update any remaining import statements")
        print(f"  4. Consider removing the old 'app' directory")

if __name__ == "__main__":
    main()
