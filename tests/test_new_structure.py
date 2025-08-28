#!/usr/bin/env python3
"""
Test script to verify the new project structure works correctly.
This script tests imports and basic functionality without the old app directory.
"""

import sys
import os

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    # Add src to Python path
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    try:
        # Test core imports
        print("  Testing core imports...")
        from src.core.database import get_db, Base
        from src.core.redis_client import RedisClient
        from src.core.redis_dependency import get_redis
        print("    ✅ Core imports working")
        
        # Test models imports
        print("  Testing models imports...")
        from src.models.models import User, Word, Dictionary
        from src.models.schemas import State, TranslationResponse
        from src.models.crud_schemas import UserCreate, WordBase
        print("    ✅ Models imports working")
        
        # Test services imports
        print("  Testing services imports...")
        from src.services.crud import register_user, login
        from src.services.auth import verify_password, get_password_hash
        from src.services.generate import generate_translation
        print("    ✅ Services imports working")
        
        # Test config imports
        print("  Testing config imports...")
        from src.config.settings import settings
        print("    ✅ Config imports working")
        
        # Test API imports (without FastAPI dependencies)
        print("  Testing API imports...")
        from src.api.prompts import translation_prompt
        print("    ✅ API imports working")
        
        print("✅ All imports working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_settings():
    """Test that settings are accessible."""
    print("\n🔧 Testing settings...")
    
    # Add src to Python path
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    try:
        from src.config.settings import settings
        
        # Test that settings are accessible
        print(f"  Database URL: {settings.DATABASE_URL}")
        print(f"  Redis URL: {settings.REDIS_URL}")
        print(f"  Project name: {settings.PROJECT_NAME}")
        
        print("✅ Settings working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def test_structure():
    """Test that the directory structure is correct."""
    print("\n📁 Testing directory structure...")
    
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
        'src/core/database.py',
        'src/config/settings.py',
        'src/models/models.py',
        'src/services/crud.py',
        'main.py'
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

def main():
    """Main test function."""
    print("🚀 Testing New Project Structure")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_structure),
        ("Settings", test_settings),
        ("Imports", test_imports),
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
        print("🎉 All tests passed! You can safely delete the app directory.")
        print("\nTo delete the app directory:")
        print("  cp -r app/ app_backup/  # Backup first")
        print("  rm -rf app/             # Delete old directory")
    else:
        print("⚠️  Some tests failed. Please fix the issues before deleting the app directory.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
