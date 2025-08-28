#!/usr/bin/env python3
"""
Test script for Redis functionality.

This script demonstrates how to use Redis with your application.
Run this script to test Redis connection and basic operations.
"""

import os
import sys
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.redis_client import RedisClient, get_redis_client

def test_basic_operations():
    """Test basic Redis operations."""
    print("🧪 Testing Basic Redis Operations")
    print("=" * 40)
    
    try:
        # Get Redis client
        redis = get_redis_client()
        print(f"✅ Connected to Redis at: {redis.url}")
        
        # Test 1: Set and Get
        print("\n1. Testing Set/Get operations...")
        test_data = {
            "message": "Hello Redis!",
            "timestamp": datetime.now().isoformat(),
            "numbers": [1, 2, 3, 4, 5],
            "nested": {"key": "value", "list": ["a", "b", "c"]}
        }
        
        success = redis.set("test:basic", test_data, ex=300)  # 5 minutes expiration
        print(f"   Set operation: {'✅ Success' if success else '❌ Failed'}")
        
        retrieved_data = redis.get("test:basic")
        print(f"   Get operation: {'✅ Success' if retrieved_data == test_data else '❌ Failed'}")
        print(f"   Retrieved data: {json.dumps(retrieved_data, indent=2)}")
        
        # Test 2: Hash operations
        print("\n2. Testing Hash operations...")
        hash_data = {
            "user_id": "12345",
            "username": "testuser",
            "email": "test@example.com",
            "preferences": {"theme": "dark", "language": "en"}
        }
        
        fields_set = redis.hset("user:12345", hash_data)
        print(f"   Hash set: {fields_set} fields set")
        
        retrieved_hash = redis.hgetall("user:12345")
        print(f"   Hash get all: {json.dumps(retrieved_hash, indent=2)}")
        
        # Test 3: List operations
        print("\n3. Testing List operations...")
        list_items = ["item1", "item2", "item3", {"complex": "item"}]
        
        pushed_count = redis.lpush("test:list", *list_items)
        print(f"   List push: {pushed_count} items pushed")
        
        list_data = redis.lrange("test:list", 0, -1)
        print(f"   List range: {json.dumps(list_data, indent=2)}")
        
        # Test 4: Set operations
        print("\n4. Testing Set operations...")
        set_items = ["apple", "banana", "cherry", "apple"]  # Note: duplicate
        
        added_count = redis.sadd("test:set", *set_items)
        print(f"   Set add: {added_count} items added (duplicates ignored)")
        
        set_data = redis.smembers("test:set")
        print(f"   Set members: {list(set_data)}")
        
        # Test 5: Existence and TTL
        print("\n5. Testing Existence and TTL...")
        exists = redis.exists("test:basic")
        print(f"   Key exists: {exists > 0}")
        
        ttl = redis.ttl("test:basic")
        print(f"   TTL: {ttl} seconds")
        
        # Test 6: Delete operations
        print("\n6. Testing Delete operations...")
        deleted_count = redis.delete("test:basic", "user:12345", "test:list", "test:set")
        print(f"   Deleted {deleted_count} keys")
        
        # Verify deletion
        exists_after = redis.exists("test:basic", "user:12345", "test:list", "test:set")
        print(f"   Keys exist after deletion: {exists_after}")
        
        print("\n✅ All basic operations completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during basic operations: {e}")
        return False
    
    return True

def test_cache_scenarios():
    """Test common caching scenarios."""
    print("\n🧪 Testing Cache Scenarios")
    print("=" * 40)
    
    try:
        redis = get_redis_client()
        
        # Scenario 1: User session cache
        print("\n1. User Session Cache...")
        session_data = {
            "user_id": "12345",
            "username": "john_doe",
            "last_activity": datetime.now().isoformat(),
            "permissions": ["read", "write", "admin"]
        }
        
        session_key = f"session:{session_data['user_id']}"
        redis.set(session_key, session_data, ex=3600)  # 1 hour
        
        retrieved_session = redis.get(session_key)
        print(f"   Session cached: {'✅' if retrieved_session == session_data else '❌'}")
        
        # Scenario 2: API response cache
        print("\n2. API Response Cache...")
        api_response = {
            "status": "success",
            "data": {
                "words": ["hello", "world"],
                "translations": {"hello": ["hola"], "world": ["mundo"]}
            },
            "cached_at": datetime.now().isoformat()
        }
        
        cache_key = "api:translate:hello_world:en_es"
        redis.set(cache_key, api_response, ex=1800)  # 30 minutes
        
        cached_response = redis.get(cache_key)
        print(f"   API response cached: {'✅' if cached_response == api_response else '❌'}")
        
        # Scenario 3: User preferences
        print("\n3. User Preferences...")
        preferences = {
            "theme": "dark",
            "language": "es",
            "notifications": True,
            "auto_save": True
        }
        
        pref_key = f"preferences:{session_data['user_id']}"
        redis.hset(pref_key, preferences)
        
        retrieved_prefs = redis.hgetall(pref_key)
        print(f"   Preferences cached: {'✅' if retrieved_prefs == preferences else '❌'}")
        
        # Scenario 4: Recent searches
        print("\n4. Recent Searches...")
        searches = ["hello", "world", "example", "test"]
        
        for search in searches:
            redis.lpush("recent_searches:12345", search)
        
        recent_searches = redis.lrange("recent_searches:12345", 0, 9)  # Last 10
        print(f"   Recent searches: {recent_searches}")
        
        # Clean up
        redis.delete(session_key, cache_key, pref_key, "recent_searches:12345")
        
        print("\n✅ All cache scenarios completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during cache scenarios: {e}")
        return False
    
    return True

def test_performance():
    """Test Redis performance with bulk operations."""
    print("\n🧪 Testing Performance")
    print("=" * 40)
    
    try:
        redis = get_redis_client()
        
        # Bulk set operations
        print("\n1. Bulk Set Operations...")
        import time
        
        start_time = time.time()
        for i in range(100):
            key = f"bulk:test:{i}"
            value = {"index": i, "data": f"value_{i}", "timestamp": datetime.now().isoformat()}
            redis.set(key, value, ex=60)
        
        set_time = time.time() - start_time
        print(f"   Set 100 keys in {set_time:.3f} seconds")
        
        # Bulk get operations
        print("\n2. Bulk Get Operations...")
        start_time = time.time()
        retrieved_count = 0
        for i in range(100):
            key = f"bulk:test:{i}"
            value = redis.get(key)
            if value:
                retrieved_count += 1
        
        get_time = time.time() - start_time
        print(f"   Retrieved {retrieved_count}/100 keys in {get_time:.3f} seconds")
        
        # Clean up
        keys_to_delete = [f"bulk:test:{i}" for i in range(100)]
        deleted_count = redis.delete(*keys_to_delete)
        print(f"   Cleaned up {deleted_count} keys")
        
        print("\n✅ Performance test completed!")
        
    except Exception as e:
        print(f"❌ Error during performance test: {e}")
        return False
    
    return True

def main():
    """Main test function."""
    print("🚀 Redis Connection Test")
    print("=" * 50)
    
    # Check if Redis URL is set
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"Redis URL: {redis_url}")
    
    # Run tests
    tests = [
        ("Basic Operations", test_basic_operations),
        ("Cache Scenarios", test_cache_scenarios),
        ("Performance", test_performance)
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
        print("🎉 All tests passed! Redis is working correctly.")
    else:
        print("⚠️  Some tests failed. Check your Redis configuration.")
    
    # Close Redis connection
    try:
        from app.redis_client import close_redis_client
        close_redis_client()
        print("🔌 Redis connection closed.")
    except:
        pass

if __name__ == "__main__":
    main()
