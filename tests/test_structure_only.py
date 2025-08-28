#!/usr/bin/env python3
"""
Simple test script to verify the new project structure.
This script only checks file structure and import syntax without requiring dependencies.
"""

import os
import ast
import sys
from pathlib import Path

def test_directory_structure():
    """Test that all required directories and files exist."""
    print("📁 Testing directory structure...")
    
    required_dirs = [
        '../src',
        '../src/api',
        '../src/core', 
        '../src/config',
        '../src/models',
        '../src/services',
        '../src/utils',
        '../scripts',
        '../examples',
        '../docs'
    ]
    
    required_files = [
        '../src/__init__.py',
        '../src/api/__init__.py',
        '../src/core/__init__.py',
        '../src/config/__init__.py',
        '../src/models/__init__.py',
        '../src/services/__init__.py',
        '../src/utils/__init__.py',
        '../src/api/main.py',
        '../src/core/database.py',
        '../src/config/settings.py',
        '../src/models/models.py',
        '../src/services/crud.py',
        '../main.py'
    ]
    
    missing_dirs = []
    missing_files = []
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ Directory structure is correct!")
    return True

def test_import_syntax():
    """Test that import statements are syntactically correct."""
    print("\n🔍 Testing import syntax...")
    
    python_files = []
    for root, dirs, files in os.walk('../src'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    syntax_errors = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the Python code to check syntax
            ast.parse(content)
            
        except SyntaxError as e:
            syntax_errors.append(f"{file_path}: {e}")
        except Exception as e:
            syntax_errors.append(f"{file_path}: {e}")
    
    if syntax_errors:
        print(f"❌ Syntax errors found:")
        for error in syntax_errors:
            print(f"  {error}")
        return False
    
    print(f"✅ All {len(python_files)} Python files have correct syntax!")
    return True

def test_no_old_imports():
    """Test that no files contain old 'app.' imports."""
    print("\n🔍 Checking for old import statements...")
    
    python_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    old_imports = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for old import patterns (but ignore relative imports)
            if 'from app.' in content or 'import app' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if ('from app.' in line or 'import app' in line) and not line.strip().startswith('from .'):
                        old_imports.append(f"{file_path}:{i}: {line.strip()}")
                        
        except Exception as e:
            old_imports.append(f"{file_path}: Error reading file: {e}")
    
    if old_imports:
        print(f"❌ Found old import statements:")
        for imp in old_imports:
            print(f"  {imp}")
        return False
    
    print("✅ No old import statements found!")
    return True

def test_new_imports_exist():
    """Test that new import statements exist."""
    print("\n🔍 Checking for new import statements...")
    
    required_imports = [
        'from src.core.database import',
        'from src.models.models import',
        'from src.services.crud import',
        'from src.config.settings import',
    ]
    
    missing_imports = []
    
    for required_import in required_imports:
        found = False
        for root, dirs, files in os.walk('../src'):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if required_import in content:
                            found = True
                            break
                    except:
                        pass
            if found:
                break
        
        if not found:
            missing_imports.append(required_import)
    
    if missing_imports:
        print(f"❌ Missing new import statements:")
        for imp in missing_imports:
            print(f"  {imp}")
        return False
    
    print("✅ New import statements are present!")
    return True

def main():
    """Main test function."""
    print("🚀 Testing New Project Structure")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Import Syntax", test_import_syntax),
        ("No Old Imports", test_no_old_imports),
        ("New Imports Exist", test_new_imports_exist),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All structure tests passed!")
        print("\n✅ You can safely delete the app directory.")
        print("\nTo delete the app directory:")
        print("  cp -r app/ app_backup/  # Backup first")
        print("  rm -rf app/             # Delete old directory")
        print("\nNote: You'll need to install dependencies to run the application:")
        print("  pip install -r requirements.txt")
    else:
        print("⚠️  Some tests failed. Please fix the issues before deleting the app directory.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
