"""
Redis Functions Module

This module provides direct function access to Redis operations,
replacing the need for Redis endpoints in the API.
"""

import json
from typing import Optional, Any, Dict, List, Union
from src.core.redis_client import RedisClient, get_redis_client
from src.core.logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)


# =============================================================================
# Basic Key-Value Operations
# =============================================================================

def set_cache_data(
    key: str,
    value: Any,
    expiration: Optional[int] = 3600,  # Default 1 hour
    nx: bool = False,
    xx: bool = False
) -> Dict[str, Any]:
    """
    Set data in Redis cache.
    
    Args:
        key: Cache key
        value: Value to cache
        expiration: Expiration time in seconds (default: 3600)
        nx: Only set if key doesn't exist
        xx: Only set if key exists
        
    Returns:
        Dict: Operation result
    """
    try:
        redis = get_redis_client()
        success = redis.set(key, value, ex=expiration, nx=nx, xx=xx)
        
        return {
            "success": success,
            "key": key,
            "expiration": expiration
        }
    except Exception as e:
        logger.error(f"Error setting cache data for key {key}: {e}")
        return {
            "success": False,
            "key": key,
            "error": str(e)
        }


def get_cache_data(key: str, default: Any = None) -> Dict[str, Any]:
    """
    Get data from Redis cache.
    
    Args:
        key: Cache key
        default: Default value if key doesn't exist
        
    Returns:
        Dict: Cache data result
    """
    try:
        redis = get_redis_client()
        value = redis.get(key, default=default)
        
        return {
            "key": key,
            "value": value,
            "exists": value is not None
        }
    except Exception as e:
        logger.error(f"Error getting cache data for key {key}: {e}")
        return {
            "key": key,
            "value": default,
            "exists": False,
            "error": str(e)
        }


def delete_cache_data(*keys: str) -> Dict[str, Any]:
    """
    Delete data from Redis cache.
    
    Args:
        *keys: Keys to delete
        
    Returns:
        Dict: Operation result
    """
    try:
        redis = get_redis_client()
        deleted_count = redis.delete(*keys)
        
        return {
            "success": deleted_count > 0,
            "keys": list(keys),
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error deleting cache data for keys {keys}: {e}")
        return {
            "success": False,
            "keys": list(keys),
            "deleted_count": 0,
            "error": str(e)
        }


def check_cache_exists(*keys: str) -> Dict[str, Any]:
    """
    Check if keys exist in Redis cache.
    
    Args:
        *keys: Keys to check
        
    Returns:
        Dict: Existence check result
    """
    try:
        redis = get_redis_client()
        exists_count = redis.exists(*keys)
        
        # Get TTL for the first key if it exists
        ttl = -2
        if exists_count > 0 and len(keys) == 1:
            ttl = redis.ttl(keys[0])
        
        return {
            "keys": list(keys),
            "exists": exists_count > 0,
            "exists_count": exists_count,
            "ttl": ttl
        }
    except Exception as e:
        logger.error(f"Error checking cache existence for keys {keys}: {e}")
        return {
            "keys": list(keys),
            "exists": False,
            "exists_count": 0,
            "ttl": -2,
            "error": str(e)
        }


def set_expiration(key: str, time: int) -> Dict[str, Any]:
    """
    Set expiration time for a key.
    
    Args:
        key: Redis key
        time: Expiration time in seconds
        
    Returns:
        Dict: Operation result
    """
    try:
        redis = get_redis_client()
        success = redis.expire(key, time)
        
        return {
            "success": success,
            "key": key,
            "expiration": time
        }
    except Exception as e:
        logger.error(f"Error setting expiration for key {key}: {e}")
        return {
            "success": False,
            "key": key,
            "error": str(e)
        }


def get_ttl(key: str) -> Dict[str, Any]:
    """
    Get time to live for a key.
    
    Args:
        key: Redis key
        
    Returns:
        Dict: TTL result
    """
    try:
        redis = get_redis_client()
        ttl = redis.ttl(key)
        
        return {
            "key": key,
            "ttl": ttl,
            "exists": ttl != -2
        }
    except Exception as e:
        logger.error(f"Error getting TTL for key {key}: {e}")
        return {
            "key": key,
            "ttl": -2,
            "exists": False,
            "error": str(e)
        }


# =============================================================================
# Hash Operations
# =============================================================================

def set_hash_data(hash_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set hash data in Redis cache.
    
    Args:
        hash_name: Hash name
        data: Dictionary of field-value pairs
        
    Returns:
        Dict: Operation result
    """
    try:
        redis = get_redis_client()
        fields_set = redis.hset(hash_name, data)
        
        return {
            "success": fields_set > 0,
            "hash_name": hash_name,
            "fields_set": fields_set
        }
    except Exception as e:
        logger.error(f"Error setting hash data for {hash_name}: {e}")
        return {
            "success": False,
            "hash_name": hash_name,
            "error": str(e)
        }


def get_hash_data(
    hash_name: str,
    field: Optional[str] = None,
    default: Any = None
) -> Dict[str, Any]:
    """
    Get hash data from Redis cache.
    
    Args:
        hash_name: Hash name
        field: Specific field to get (optional, gets all if not specified)
        default: Default value if field doesn't exist
        
    Returns:
        Dict: Hash data
    """
    try:
        redis = get_redis_client()
        
        if field:
            value = redis.hget(hash_name, field, default=default)
            return {
                "hash_name": hash_name,
                "field": field,
                "value": value,
                "exists": value is not None
            }
        else:
            data = redis.hgetall(hash_name)
            return {
                "hash_name": hash_name,
                "data": data,
                "field_count": len(data)
            }
    except Exception as e:
        logger.error(f"Error getting hash data for {hash_name}: {e}")
        return {
            "hash_name": hash_name,
            "field": field,
            "error": str(e)
        }


def delete_hash_fields(hash_name: str, *fields: str) -> Dict[str, Any]:
    """
    Delete fields from a hash.
    
    Args:
        hash_name: Hash name
        *fields: Fields to delete
        
    Returns:
        Dict: Operation result
    """
    try:
        redis = get_redis_client()
        deleted_count = redis.redis.hdel(hash_name, *fields)
        
        return {
            "success": deleted_count > 0,
            "hash_name": hash_name,
            "fields": list(fields),
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error deleting hash fields for {hash_name}: {e}")
        return {
            "success": False,
            "hash_name": hash_name,
            "fields": list(fields),
            "error": str(e)
        }


# =============================================================================
# List Operations
# =============================================================================

def push_to_list(
    list_name: str,
    values: List[Any],
    side: str = "left"  # "left" or "right"
) -> Dict[str, Any]:
    """
    Push values to a Redis list.
    
    Args:
        list_name: List name
        values: Values to push
        side: Which side to push to ("left" or "right")
        
    Returns:
        Dict: Operation result
    """
    try:
        redis = get_redis_client()
        
        if side.lower() == "left":
            pushed_count = redis.lpush(list_name, *values)
        else:
            pushed_count = redis.redis.rpush(list_name, *values)
        
        return {
            "success": pushed_count > 0,
            "list_name": list_name,
            "pushed_count": pushed_count,
            "side": side
        }
    except Exception as e:
        logger.error(f"Error pushing to list {list_name}: {e}")
        return {
            "success": False,
            "list_name": list_name,
            "error": str(e)
        }


def get_list_data(
    list_name: str,
    start: int = 0,
    end: int = -1
) -> Dict[str, Any]:
    """
    Get data from a Redis list.
    
    Args:
        list_name: List name
        start: Start index
        end: End index
        
    Returns:
        Dict: List data
    """
    try:
        redis = get_redis_client()
        data = redis.lrange(list_name, start, end)
        
        return {
            "list_name": list_name,
            "data": data,
            "count": len(data),
            "range": f"{start}:{end}"
        }
    except Exception as e:
        logger.error(f"Error getting list data for {list_name}: {e}")
        return {
            "list_name": list_name,
            "data": [],
            "count": 0,
            "error": str(e)
        }


def pop_from_list(
    list_name: str,
    side: str = "right",  # "left" or "right"
    default: Any = None
) -> Dict[str, Any]:
    """
    Pop value from a Redis list.
    
    Args:
        list_name: List name
        side: Which side to pop from ("left" or "right")
        default: Default value if list is empty
        
    Returns:
        Dict: Pop result
    """
    try:
        redis = get_redis_client()
        
        if side.lower() == "left":
            value = redis.redis.lpop(list_name)
        else:
            value = redis.rpop(list_name, default=default)
        
        return {
            "list_name": list_name,
            "value": value,
            "exists": value is not None,
            "side": side
        }
    except Exception as e:
        logger.error(f"Error popping from list {list_name}: {e}")
        return {
            "list_name": list_name,
            "value": default,
            "exists": False,
            "error": str(e)
        }


# =============================================================================
# Set Operations
# =============================================================================

def add_to_set(set_name: str, values: List[Any]) -> Dict[str, Any]:
    """
    Add values to a Redis set.
    
    Args:
        set_name: Set name
        values: Values to add
        
    Returns:
        Dict: Operation result
    """
    try:
        redis = get_redis_client()
        added_count = redis.sadd(set_name, *values)
        
        return {
            "success": added_count > 0,
            "set_name": set_name,
            "added_count": added_count
        }
    except Exception as e:
        logger.error(f"Error adding to set {set_name}: {e}")
        return {
            "success": False,
            "set_name": set_name,
            "error": str(e)
        }


def get_set_data(set_name: str) -> Dict[str, Any]:
    """
    Get data from a Redis set.
    
    Args:
        set_name: Set name
        
    Returns:
        Dict: Set data
    """
    try:
        redis = get_redis_client()
        data = redis.smembers(set_name)
        
        return {
            "set_name": set_name,
            "data": list(data),
            "count": len(data)
        }
    except Exception as e:
        logger.error(f"Error getting set data for {set_name}: {e}")
        return {
            "set_name": set_name,
            "data": [],
            "count": 0,
            "error": str(e)
        }


def remove_from_set(set_name: str, values: List[Any]) -> Dict[str, Any]:
    """
    Remove values from a Redis set.
    
    Args:
        set_name: Set name
        values: Values to remove
        
    Returns:
        Dict: Operation result
    """
    try:
        redis = get_redis_client()
        removed_count = redis.redis.srem(set_name, *values)
        
        return {
            "success": removed_count > 0,
            "set_name": set_name,
            "removed_count": removed_count
        }
    except Exception as e:
        logger.error(f"Error removing from set {set_name}: {e}")
        return {
            "success": False,
            "set_name": set_name,
            "error": str(e)
        }


def is_set_member(set_name: str, value: Any) -> Dict[str, Any]:
    """
    Check if a value is a member of a set.
    
    Args:
        set_name: Set name
        value: Value to check
        
    Returns:
        Dict: Membership check result
    """
    try:
        redis = get_redis_client()
        is_member = redis.redis.sismember(set_name, value)
        
        return {
            "set_name": set_name,
            "value": value,
            "is_member": is_member
        }
    except Exception as e:
        logger.error(f"Error checking set membership for {set_name}: {e}")
        return {
            "set_name": set_name,
            "value": value,
            "is_member": False,
            "error": str(e)
        }


# =============================================================================
# Utility Functions
# =============================================================================

def redis_health_check() -> Dict[str, Any]:
    """
    Health check for Redis connection.
    
    Returns:
        Dict: Health status
    """
    try:
        redis = get_redis_client()
        
        # Test connection by setting and getting a test key
        test_key = "health_check_test"
        test_value = {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
        
        redis.set(test_key, test_value, ex=10)  # Expire in 10 seconds
        retrieved_value = redis.get(test_key)
        redis.delete(test_key)
        
        return {
            "status": "healthy",
            "redis_url": redis.url,
            "test_passed": retrieved_value == test_value
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def get_redis_info() -> Dict[str, Any]:
    """
    Get Redis server information.
    
    Returns:
        Dict: Redis server info
    """
    try:
        redis = get_redis_client()
        info = redis.redis.info()
        
        return {
            "status": "connected",
            "redis_url": redis.url,
            "server_info": {
                "version": info.get("redis_version"),
                "uptime": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed")
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def clear_cache(pattern: str = "*") -> Dict[str, Any]:
    """
    Clear cache by pattern.
    
    Args:
        pattern: Key pattern to match (default: all keys)
        
    Returns:
        Dict: Operation result
    """
    try:
        redis = get_redis_client()
        keys = redis.redis.keys(pattern)
        
        if keys:
            deleted_count = redis.delete(*keys)
        else:
            deleted_count = 0
        
        return {
            "success": True,
            "pattern": pattern,
            "keys_found": len(keys),
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error clearing cache with pattern {pattern}: {e}")
        return {
            "success": False,
            "pattern": pattern,
            "error": str(e)
        }


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dict: Cache statistics
    """
    try:
        redis = get_redis_client()
        info = redis.redis.info()
        
        # Get some basic stats
        total_keys = redis.redis.dbsize()
        
        return {
            "status": "success",
            "total_keys": total_keys,
            "memory_usage": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "uptime_seconds": info.get("uptime_in_seconds")
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
