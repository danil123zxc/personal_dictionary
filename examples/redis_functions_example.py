#!/usr/bin/env python3
"""
Redis Functions Example

This script demonstrates how to use Redis functions directly
instead of making HTTP requests to Redis endpoints.
"""

import sys
import os
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


def print_result(operation: str, result: Dict[str, Any]):
    """Print operation result in a formatted way."""
    print(f"\n{'='*50}")
    print(f"Operation: {operation}")
    print(f"{'='*50}")
    for key, value in result.items():
        print(f"{key}: {value}")


def demo_basic_operations():
    """Demonstrate basic Redis operations."""
    print("\n🔧 Basic Redis Operations")
    print("=" * 50)
    
    # Set cache data
    result = set_cache_data("user:123", {"name": "John Doe", "email": "john@example.com"}, expiration=3600)
    print_result("Set Cache Data", result)
    
    # Get cache data
    result = get_cache_data("user:123")
    print_result("Get Cache Data", result)
    
    # Check if key exists
    result = check_cache_exists("user:123", "user:456")
    print_result("Check Cache Exists", result)
    
    # Get TTL
    result = get_ttl("user:123")
    print_result("Get TTL", result)
    
    # Set expiration
    result = set_expiration("user:123", 7200)  # 2 hours
    print_result("Set Expiration", result)
    
    # Delete cache data
    result = delete_cache_data("user:123")
    print_result("Delete Cache Data", result)


def demo_hash_operations():
    """Demonstrate Redis hash operations."""
    print("\n📋 Hash Operations")
    print("=" * 50)
    
    # Set hash data
    user_data = {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "age": 30,
        "city": "New York"
    }
    result = set_hash_data("user:456", user_data)
    print_result("Set Hash Data", result)
    
    # Get all hash data
    result = get_hash_data("user:456")
    print_result("Get All Hash Data", result)
    
    # Get specific field
    result = get_hash_data("user:456", field="name")
    print_result("Get Hash Field", result)
    
    # Delete hash fields
    result = delete_hash_fields("user:456", "age", "city")
    print_result("Delete Hash Fields", result)
    
    # Get remaining data
    result = get_hash_data("user:456")
    print_result("Get Remaining Hash Data", result)


def demo_list_operations():
    """Demonstrate Redis list operations."""
    print("\n📝 List Operations")
    print("=" * 50)
    
    # Push to list
    result = push_to_list("tasks", ["Buy groceries", "Call mom", "Write code"], side="left")
    print_result("Push to List (Left)", result)
    
    # Push more items
    result = push_to_list("tasks", ["Read book", "Exercise"], side="right")
    print_result("Push to List (Right)", result)
    
    # Get list data
    result = get_list_data("tasks")
    print_result("Get List Data", result)
    
    # Get range
    result = get_list_data("tasks", start=1, end=3)
    print_result("Get List Range", result)
    
    # Pop from list
    result = pop_from_list("tasks", side="right")
    print_result("Pop from List (Right)", result)
    
    # Get updated list
    result = get_list_data("tasks")
    print_result("Get Updated List", result)


def demo_set_operations():
    """Demonstrate Redis set operations."""
    print("\n🔢 Set Operations")
    print("=" * 50)
    
    # Add to set
    result = add_to_set("tags", ["python", "redis", "fastapi", "docker"])
    print_result("Add to Set", result)
    
    # Add more items
    result = add_to_set("tags", ["python", "api", "cache"])  # "python" already exists
    print_result("Add More to Set", result)
    
    # Get set data
    result = get_set_data("tags")
    print_result("Get Set Data", result)
    
    # Check membership
    result = is_set_member("tags", "python")
    print_result("Check Set Membership", result)
    
    result = is_set_member("tags", "javascript")
    print_result("Check Set Membership (Not Found)", result)
    
    # Remove from set
    result = remove_from_set("tags", ["docker", "api"])
    print_result("Remove from Set", result)
    
    # Get updated set
    result = get_set_data("tags")
    print_result("Get Updated Set", result)


def demo_utility_functions():
    """Demonstrate utility functions."""
    print("\n🛠️ Utility Functions")
    print("=" * 50)
    
    # Health check
    result = redis_health_check()
    print_result("Health Check", result)
    
    # Get Redis info
    result = get_redis_info()
    print_result("Redis Info", result)
    
    # Get cache stats
    result = get_cache_stats()
    print_result("Cache Stats", result)


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n⚠️ Error Handling")
    print("=" * 50)
    
    # Try to get non-existent key
    result = get_cache_data("non_existent_key", default="default_value")
    print_result("Get Non-existent Key", result)
    
    # Try to delete non-existent key
    result = delete_cache_data("non_existent_key")
    print_result("Delete Non-existent Key", result)
    
    # Try to get hash field from non-existent hash
    result = get_hash_data("non_existent_hash", field="field")
    print_result("Get Non-existent Hash Field", result)


def main():
    """Run all demonstrations."""
    print("🚀 Redis Functions Demo")
    print("This demonstrates using Redis functions instead of HTTP endpoints")
    
    try:
        # Run all demos
        demo_basic_operations()
        demo_hash_operations()
        demo_list_operations()
        demo_set_operations()
        demo_utility_functions()
        demo_error_handling()
        
        print("\n✅ All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        print("Make sure Redis is running and accessible.")


if __name__ == "__main__":
    main()
