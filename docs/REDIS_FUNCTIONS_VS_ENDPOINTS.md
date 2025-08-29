# Redis Functions vs Redis Endpoints

This document compares using Redis functions directly vs making HTTP requests to Redis endpoints.

## Overview

Instead of making HTTP requests to Redis endpoints like `/cache/set`, `/cache/get`, etc., you can now use direct function calls that provide the same functionality with better performance and easier integration.

## Benefits of Using Redis Functions

### 1. **Better Performance**
- **No HTTP overhead**: Direct function calls are faster than HTTP requests
- **No serialization overhead**: No need to serialize/deserialize HTTP requests/responses
- **Connection reuse**: Uses existing Redis connection pool

### 2. **Easier Integration**
- **Direct imports**: Simple `from src.core.redis_functions import set_cache_data`
- **Type safety**: Full type hints and IDE support
- **Error handling**: Consistent error handling with detailed error messages

### 3. **Better Developer Experience**
- **IDE autocomplete**: Full autocomplete support
- **Documentation**: Inline docstrings with examples
- **Debugging**: Easier to debug and trace function calls

### 4. **Reduced Complexity**
- **No HTTP client needed**: No need to manage HTTP sessions
- **No URL construction**: Direct function parameters
- **No response parsing**: Direct return values

## Comparison Examples

### Setting Cache Data

#### Using Redis Endpoints (HTTP)
```python
import requests

# Make HTTP request
response = requests.post("http://localhost:8000/cache/set", json={
    "key": "user:123",
    "value": {"name": "John Doe", "email": "john@example.com"},
    "expiration": 3600
})

# Parse response
result = response.json()
if result["success"]:
    print("Cache set successfully")
else:
    print("Failed to set cache")
```

#### Using Redis Functions (Direct)
```python
from src.core.redis_functions import set_cache_data

# Direct function call
result = set_cache_data(
    key="user:123",
    value={"name": "John Doe", "email": "john@example.com"},
    expiration=3600
)

if result["success"]:
    print("Cache set successfully")
else:
    print("Failed to set cache")
```

### Getting Cache Data

#### Using Redis Endpoints (HTTP)
```python
import requests

# Make HTTP request
response = requests.get("http://localhost:8000/cache/get/user:123")

# Parse response
result = response.json()
if result["exists"]:
    user_data = result["value"]
    print(f"User: {user_data}")
else:
    print("User not found in cache")
```

#### Using Redis Functions (Direct)
```python
from src.core.redis_functions import get_cache_data

# Direct function call
result = get_cache_data("user:123")

if result["exists"]:
    user_data = result["value"]
    print(f"User: {user_data}")
else:
    print("User not found in cache")
```

### Hash Operations

#### Using Redis Endpoints (HTTP)
```python
import requests

# Set hash data
response = requests.post("http://localhost:8000/cache/hash/set", json={
    "hash_name": "user:456",
    "data": {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "age": 30
    }
})

# Get hash data
response = requests.get("http://localhost:8000/cache/hash/get/user:456")
result = response.json()
user_data = result["data"]
```

#### Using Redis Functions (Direct)
```python
from src.core.redis_functions import set_hash_data, get_hash_data

# Set hash data
set_hash_data("user:456", {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "age": 30
})

# Get hash data
result = get_hash_data("user:456")
user_data = result["data"]
```

## Function Reference

### Basic Operations

| Operation | Function | Description |
|-----------|----------|-------------|
| Set | `set_cache_data(key, value, expiration=3600)` | Set key-value pair with optional expiration |
| Get | `get_cache_data(key, default=None)` | Get value by key with optional default |
| Delete | `delete_cache_data(*keys)` | Delete one or more keys |
| Exists | `check_cache_exists(*keys)` | Check if keys exist |
| TTL | `get_ttl(key)` | Get time to live for key |
| Expire | `set_expiration(key, time)` | Set expiration time |

### Hash Operations

| Operation | Function | Description |
|-----------|----------|-------------|
| Set Hash | `set_hash_data(hash_name, data)` | Set hash fields |
| Get Hash | `get_hash_data(hash_name, field=None)` | Get hash data or specific field |
| Delete Fields | `delete_hash_fields(hash_name, *fields)` | Delete hash fields |

### List Operations

| Operation | Function | Description |
|-----------|----------|-------------|
| Push | `push_to_list(list_name, values, side="left")` | Push values to list |
| Get | `get_list_data(list_name, start=0, end=-1)` | Get list data with range |
| Pop | `pop_from_list(list_name, side="right")` | Pop value from list |

### Set Operations

| Operation | Function | Description |
|-----------|----------|-------------|
| Add | `add_to_set(set_name, values)` | Add values to set |
| Get | `get_set_data(set_name)` | Get all set members |
| Remove | `remove_from_set(set_name, values)` | Remove values from set |
| Check | `is_set_member(set_name, value)` | Check if value is member |

### Utility Functions

| Operation | Function | Description |
|-----------|----------|-------------|
| Health Check | `redis_health_check()` | Check Redis connection health |
| Info | `get_redis_info()` | Get Redis server information |
| Clear | `clear_cache(pattern="*")` | Clear cache by pattern |
| Stats | `get_cache_stats()` | Get cache statistics |

## Migration Guide

### Step 1: Import Functions
```python
# Replace HTTP client imports
# import requests

# With Redis function imports
from src.core.redis_functions import (
    set_cache_data,
    get_cache_data,
    delete_cache_data,
    # ... other functions as needed
)
```

### Step 2: Replace HTTP Calls
```python
# Before: HTTP request
response = requests.post("http://localhost:8000/cache/set", json={
    "key": "my_key",
    "value": "my_value"
})

# After: Direct function call
result = set_cache_data("my_key", "my_value")
```

### Step 3: Update Error Handling
```python
# Before: HTTP error handling
try:
    response = requests.post("http://localhost:8000/cache/set", json=data)
    response.raise_for_status()
    result = response.json()
except requests.RequestException as e:
    print(f"HTTP error: {e}")

# After: Function error handling
result = set_cache_data("my_key", "my_value")
if not result["success"]:
    print(f"Redis error: {result.get('error', 'Unknown error')}")
```

## Performance Comparison

### Latency Comparison
- **HTTP Endpoints**: ~5-15ms per request (including HTTP overhead)
- **Redis Functions**: ~1-3ms per request (direct Redis calls)

### Throughput Comparison
- **HTTP Endpoints**: ~100-500 requests/second (limited by HTTP server)
- **Redis Functions**: ~1000-5000 requests/second (limited by Redis)

### Memory Usage
- **HTTP Endpoints**: Higher memory usage due to HTTP client overhead
- **Redis Functions**: Lower memory usage with connection pooling

## Best Practices

### 1. **Use Functions for Internal Operations**
```python
# Good: Use functions for internal caching
def get_user_profile(user_id: int):
    # Try cache first
    cached = get_cache_data(f"user:{user_id}")
    if cached["exists"]:
        return cached["value"]
    
    # Fetch from database
    user = database.get_user(user_id)
    
    # Cache for future requests
    set_cache_data(f"user:{user_id}", user, expiration=3600)
    return user
```

### 2. **Keep Endpoints for External APIs**
```python
# Keep endpoints for external API access
@app.get("/api/cache/{key}")
def get_cache_endpoint(key: str):
    return get_cache_data(key)
```

### 3. **Use Consistent Error Handling**
```python
def safe_cache_operation(operation_func, *args, **kwargs):
    """Wrapper for safe cache operations."""
    try:
        result = operation_func(*args, **kwargs)
        if not result.get("success", True):
            logger.warning(f"Cache operation failed: {result.get('error')}")
        return result
    except Exception as e:
        logger.error(f"Cache operation error: {e}")
        return {"success": False, "error": str(e)}
```

## Conclusion

Using Redis functions instead of HTTP endpoints provides significant benefits in terms of performance, developer experience, and code maintainability. The functions provide the same functionality as the endpoints but with better performance and easier integration.

For new code, prefer using Redis functions directly. For existing code, consider migrating from endpoints to functions gradually, starting with the most performance-critical operations.
