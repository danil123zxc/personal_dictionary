#!/usr/bin/env python3
"""
Simple test script to verify the project structure.
This script only checks file structure without requiring dependencies.
"""

import os
import sys
from pathlib import Path

def test_directory_structure():
    """Test that all required directories and files exist."""
    print("📁 Testing directory structure...")
    
    # Get the project root (parent of tests directory)
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        'src',
        'src/api',
        'src/core', 
        'src/config',
        'src/models',
        'src/services',
        'src/utils',
        'scripts',
        'examples',
        'docs',
        'tests'
    ]
    
    required_files = [
        'src/__init__.py',
        'src/api/__init__.py',
        'src/core/__init__.py',
        'src/config/__init__.py',
        'src/models/__init__.py',
        'src/services/__init__.py',
        'src/utils/__init__.py',
        'src/api/main.py',
        'src/core/database.py',
        'src/config/settings.py',
        'src/models/models.py',
        'src/services/crud.py',
        'main.py',
        'requirements.txt',
        'compose.yaml'
    ]
    
    missing_dirs = []
    missing_files = []
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
    
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ Directory structure is correct!")
    return True

def test_test_files_moved():
    """Test that test files are in the tests directory."""
    print("\n🧪 Testing test file organization...")
    
    project_root = Path(__file__).parent.parent
    
    # Check that test files are in tests directory
    test_files_in_tests = [
        'tests/test_crud.py',
        'tests/conftest.py',
        'tests/test_redis.py',
        'tests/test_structure_only.py',
        'tests/test_new_structure.py'
    ]
    
    # Check that test files are NOT in root directory
    test_files_not_in_root = [
        'test_crud.py',
        'conftest.py',
        'test_redis.py',
        'test_structure_only.py',
        'test_new_structure.py'
    ]
    
    missing_in_tests = []
    still_in_root = []
    
    for test_file in test_files_in_tests:
        if not (project_root / test_file).exists():
            missing_in_tests.append(test_file)
    
    for test_file in test_files_not_in_root:
        if (project_root / test_file).exists():
            still_in_root.append(test_file)
    
    if missing_in_tests:
        print(f"❌ Test files missing from tests directory: {missing_in_tests}")
        return False
    
    if still_in_root:
        print(f"❌ Test files still in root directory: {still_in_root}")
        return False
    
    print("✅ Test files properly organized!")
    return True

def test_example_files_moved():
    """Test that example files are in the examples directory."""
    print("\n📚 Testing example file organization...")
    
    project_root = Path(__file__).parent.parent
    
    # Check that example files are in examples directory
    example_files_in_examples = [
        'examples/simple_logging_demo.py',
        'examples/logging_demo.py',
        'examples/example_usage.py'
    ]
    
    # Check that example files are NOT in root directory
    example_files_not_in_root = [
        'simple_logging_demo.py',
        'logging_demo.py',
        'example_usage.py'
    ]
    
    missing_in_examples = []
    still_in_root = []
    
    for example_file in example_files_in_examples:
        if not (project_root / example_file).exists():
            missing_in_examples.append(example_file)
    
    for example_file in example_files_not_in_root:
        if (project_root / example_file).exists():
            still_in_root.append(example_file)
    
    if missing_in_examples:
        print(f"❌ Example files missing from examples directory: {missing_in_examples}")
        return False
    
    if still_in_root:
        print(f"❌ Example files still in root directory: {still_in_root}")
        return False
    
    print("✅ Example files properly organized!")
    return True

def test_configuration_files():
    """Test that configuration files are in the right place."""
    print("\n⚙️ Testing configuration files...")
    
    project_root = Path(__file__).parent.parent
    
    # Configuration files that should be in root
    root_config_files = [
        'pytest.ini',
        'requirements.txt',
        'requirements-test.txt',
        'compose.yaml',
        'Dockerfile',
        'run_tests.sh'
    ]
    
    missing_config_files = []
    
    for config_file in root_config_files:
        if not (project_root / config_file).exists():
            missing_config_files.append(config_file)
    
    if missing_config_files:
        print(f"❌ Missing configuration files: {missing_config_files}")
        return False
    
    print("✅ Configuration files in place!")
    return True

def main():
    """Main test function."""
    print("🚀 Testing Project Structure Organization")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Test Files Organization", test_test_files_moved),
        ("Example Files Organization", test_example_files_moved),
        ("Configuration Files", test_configuration_files),
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
        print("🎉 All organization tests passed!")
        print("\n✅ Test files have been successfully moved to the tests directory.")
        print("✅ Example files have been successfully moved to the examples directory.")
        print("✅ Configuration files are properly organized.")
    else:
        print("⚠️  Some tests failed. Please check the organization.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
