#!/usr/bin/env python3
"""
Test Redis Functions

This script tests the Redis functions to ensure they work correctly.
"""

import sys
import os
import time
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.redis_functions import (
    # Basic operations
    set_cache_data,
    get_cache_data,
    delete_cache_data,
    check_cache_exists,
    set_expiration,
    get_ttl,
    
    # Hash operations
    set_hash_data,
    get_hash_data,
    delete_hash_fields,
    
    # List operations
    push_to_list,
    get_list_data,
    pop_from_list,
    
    # Set operations
    add_to_set,
    get_set_data,
    remove_from_set,
    is_set_member,
    
    # Utility functions
    redis_health_check,
    get_redis_info,
    clear_cache,
    get_cache_stats
)


def test_basic_operations():
    """Test basic Redis operations."""
    print("🧪 Testing Basic Operations...")
    
    # Test set and get
    test_key = "test:basic:key"
    test_value = {"name": "Test User", "id": 123}
    
    # Set data
    result = set_cache_data(test_key, test_value, expiration=60)
    assert result["success"], f"Failed to set cache: {result}"
    print("✅ Set cache data")
    
    # Get data
    result = get_cache_data(test_key)
    assert result["exists"], f"Cache data not found: {result}"
    assert result["value"] == test_value, f"Value mismatch: {result['value']} != {test_value}"
    print("✅ Get cache data")
    
    # Check exists
    result = check_cache_exists(test_key)
    assert result["exists"], f"Key should exist: {result}"
    print("✅ Check cache exists")
    
    # Get TTL
    result = get_ttl(test_key)
    assert result["exists"], f"Key should exist for TTL: {result}"
    assert result["ttl"] > 0, f"TTL should be positive: {result}"
    print("✅ Get TTL")
    
    # Set expiration
    result = set_expiration(test_key, 120)
    assert result["success"], f"Failed to set expiration: {result}"
    print("✅ Set expiration")
    
    # Delete data
    result = delete_cache_data(test_key)
    assert result["success"], f"Failed to delete cache: {result}"
    print("✅ Delete cache data")
    
    # Verify deletion
    result = get_cache_data(test_key)
    assert not result["exists"], f"Key should not exist after deletion: {result}"
    print("✅ Verify deletion")


def test_hash_operations():
    """Test Redis hash operations."""
    print("\n🧪 Testing Hash Operations...")
    
    test_hash = "test:hash:user"
    test_data = {
        "name": "Hash User",
        "email": "hash@example.com",
        "age": 25,
        "city": "Test City"
    }
    
    # Set hash data
    result = set_hash_data(test_hash, test_data)
    assert result["success"], f"Failed to set hash: {result}"
    print("✅ Set hash data")
    
    # Get all hash data
    result = get_hash_data(test_hash)
    assert result["field_count"] == len(test_data), f"Field count mismatch: {result}"
    for key, value in test_data.items():
        assert result["data"][key] == value, f"Hash field mismatch for {key}"
    print("✅ Get all hash data")
    
    # Get specific field
    result = get_hash_data(test_hash, field="name")
    assert result["exists"], f"Hash field should exist: {result}"
    assert result["value"] == test_data["name"], f"Hash field value mismatch: {result}"
    print("✅ Get specific hash field")
    
    # Delete hash fields
    result = delete_hash_fields(test_hash, "age", "city")
    assert result["success"], f"Failed to delete hash fields: {result}"
    print("✅ Delete hash fields")
    
    # Verify remaining data
    result = get_hash_data(test_hash)
    assert "name" in result["data"], "Name field should remain"
    assert "email" in result["data"], "Email field should remain"
    assert "age" not in result["data"], "Age field should be deleted"
    assert "city" not in result["data"], "City field should be deleted"
    print("✅ Verify remaining hash data")


def test_list_operations():
    """Test Redis list operations."""
    print("\n🧪 Testing List Operations...")
    
    test_list = "test:list:tasks"
    test_items = ["Task 1", "Task 2", "Task 3"]
    
    # Push items to list
    result = push_to_list(test_list, test_items, side="left")
    assert result["success"], f"Failed to push to list: {result}"
    print("✅ Push items to list")
    
    # Get list data
    result = get_list_data(test_list)
    assert result["count"] == len(test_items), f"List count mismatch: {result}"
    # Note: Items are pushed to left, so order is reversed
    assert result["data"] == list(reversed(test_items)), f"List data mismatch: {result}"
    print("✅ Get list data")
    
    # Get list range
    result = get_list_data(test_list, start=0, end=1)
    assert result["count"] == 2, f"List range count mismatch: {result}"
    print("✅ Get list range")
    
    # Pop from list
    result = pop_from_list(test_list, side="right")
    assert result["exists"], f"Should be able to pop from list: {result}"
    print("✅ Pop from list")
    
    # Verify updated list
    result = get_list_data(test_list)
    assert result["count"] == len(test_items) - 1, f"List count after pop mismatch: {result}"
    print("✅ Verify updated list")


def test_set_operations():
    """Test Redis set operations."""
    print("\n🧪 Testing Set Operations...")
    
    test_set = "test:set:tags"
    test_items = ["python", "redis", "fastapi"]
    
    # Add items to set
    result = add_to_set(test_set, test_items)
    assert result["success"], f"Failed to add to set: {result}"
    print("✅ Add items to set")
    
    # Get set data
    result = get_set_data(test_set)
    assert result["count"] == len(test_items), f"Set count mismatch: {result}"
    for item in test_items:
        assert item in result["data"], f"Set item {item} not found"
    print("✅ Get set data")
    
    # Check membership
    result = is_set_member(test_set, "python")
    assert result["is_member"], f"Python should be a member: {result}"
    print("✅ Check membership (exists)")
    
    result = is_set_member(test_set, "javascript")
    assert not result["is_member"], f"JavaScript should not be a member: {result}"
    print("✅ Check membership (not exists)")
    
    # Remove from set
    result = remove_from_set(test_set, ["redis"])
    assert result["success"], f"Failed to remove from set: {result}"
    print("✅ Remove from set")
    
    # Verify updated set
    result = get_set_data(test_set)
    assert "redis" not in result["data"], "Redis should be removed"
    assert "python" in result["data"], "Python should remain"
    assert "fastapi" in result["data"], "FastAPI should remain"
    print("✅ Verify updated set")


def test_utility_functions():
    """Test utility functions."""
    print("\n🧪 Testing Utility Functions...")
    
    # Health check
    result = redis_health_check()
    assert result["status"] == "healthy", f"Redis health check failed: {result}"
    print("✅ Health check")
    
    # Get Redis info
    result = get_redis_info()
    assert result["status"] == "connected", f"Redis info failed: {result}"
    assert "server_info" in result, "Server info should be present"
    print("✅ Get Redis info")
    
    # Get cache stats
    result = get_cache_stats()
    assert result["status"] == "success", f"Cache stats failed: {result}"
    assert "total_keys" in result, "Total keys should be present"
    print("✅ Get cache stats")


def test_error_handling():
    """Test error handling."""
    print("\n🧪 Testing Error Handling...")
    
    # Test non-existent key
    result = get_cache_data("non_existent_key", default="default_value")
    assert not result["exists"], f"Non-existent key should not exist: {result}"
    assert result["value"] == "default_value", f"Default value not returned: {result}"
    print("✅ Handle non-existent key")
    
    # Test delete non-existent key
    result = delete_cache_data("non_existent_key")
    assert not result["success"], f"Delete non-existent should not succeed: {result}"
    assert result["deleted_count"] == 0, f"Deleted count should be 0: {result}"
    print("✅ Handle delete non-existent key")
    
    # Test get non-existent hash field
    result = get_hash_data("non_existent_hash", field="field")
    assert "error" in result, f"Should have error for non-existent hash: {result}"
    print("✅ Handle non-existent hash")


def cleanup():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    # Clear all test keys
    patterns = [
        "test:basic:*",
        "test:hash:*",
        "test:list:*",
        "test:set:*"
    ]
    
    for pattern in patterns:
        result = clear_cache(pattern)
        if result["success"]:
            print(f"✅ Cleared pattern: {pattern}")
        else:
            print(f"⚠️ Failed to clear pattern: {pattern}")


def main():
    """Run all tests."""
    print("🚀 Redis Functions Test Suite")
    print("=" * 50)
    
    try:
        # Run all tests
        test_basic_operations()
        test_hash_operations()
        test_list_operations()
        test_set_operations()
        test_utility_functions()
        test_error_handling()
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        cleanup()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
