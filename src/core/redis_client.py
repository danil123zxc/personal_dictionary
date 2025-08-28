import json
from typing import Optional, Any, Dict, List
from redis import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError
from src.config.settings import settings
from src.core.logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)

class RedisClient:
    """
    Redis client wrapper with connection management and utility methods.
    
    This class provides a high-level interface for Redis operations including:
    - Connection management with connection pooling
    - Automatic reconnection handling
    - JSON serialization/deserialization
    - Error handling and logging
    """
    
    def __init__(self, url: Optional[str] = None, **kwargs):
        """
        Initialize Redis client.
        
        Args:
            url: Redis connection URL (defaults to REDIS_URL from settings)
            **kwargs: Additional Redis connection parameters
        """
        self.url = url or settings.REDIS_URL
        self.redis: Optional[Redis] = None
        self.connection_pool: Optional[ConnectionPool] = None
        self._connect(**kwargs)
    
    def _connect(self, **kwargs):
        """Establish Redis connection with connection pooling."""
        try:
            # Create connection pool
            self.connection_pool = ConnectionPool.from_url(
                self.url,
                decode_responses=True,  # Automatically decode responses to strings
                **kwargs
            )
            
            # Create Redis client
            self.redis = Redis(connection_pool=self.connection_pool)
            
            # Test connection
            self.redis.ping()
            logger.info(f"Successfully connected to Redis at {self.url}")
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _ensure_connection(self):
        """Ensure Redis connection is available."""
        if not self.redis:
            self._connect()
        try:
            self.redis.ping()
        except (RedisError, ConnectionError):
            logger.warning("Redis connection lost, attempting to reconnect...")
            self._connect()
    
    def set(self, key: str, value: Any, ex: Optional[int] = None, nx: bool = False, xx: bool = False) -> bool:
        """
        Set a key-value pair in Redis.
        
        Args:
            key: Redis key
            value: Value to store (will be JSON serialized)
            ex: Expiration time in seconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists
            
        Returns:
            bool: True if operation was successful
        """
        try:
            self._ensure_connection()
            
            # Serialize value to JSON if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            return self.redis.set(key, value, ex=ex, nx=nx, xx=xx)
            
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key
            default: Default value if key doesn't exist
            
        Returns:
            Deserialized value or default
        """
        try:
            self._ensure_connection()
            value = self.redis.get(key)
            
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return default
    
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from Redis.
        
        Args:
            *keys: Keys to delete
            
        Returns:
            int: Number of keys deleted
        """
        try:
            self._ensure_connection()
            return self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting keys {keys}: {e}")
            return 0
    
    def exists(self, *keys: str) -> int:
        """
        Check if keys exist in Redis.
        
        Args:
            *keys: Keys to check
            
        Returns:
            int: Number of existing keys
        """
        try:
            self._ensure_connection()
            return self.redis.exists(*keys)
        except Exception as e:
            logger.error(f"Error checking existence of keys {keys}: {e}")
            return 0
    
    def expire(self, key: str, time: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Redis key
            time: Expiration time in seconds
            
        Returns:
            bool: True if operation was successful
        """
        try:
            self._ensure_connection()
            return self.redis.expire(key, time)
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get time to live for a key.
        
        Args:
            key: Redis key
            
        Returns:
            int: TTL in seconds (-1 if no expiration, -2 if key doesn't exist)
        """
        try:
            self._ensure_connection()
            return self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -2
    
    def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """
        Set hash fields.
        
        Args:
            name: Hash name
            mapping: Dictionary of field-value pairs
            
        Returns:
            int: Number of fields set
        """
        try:
            self._ensure_connection()
            
            # Serialize values to JSON
            serialized_mapping = {}
            for field, value in mapping.items():
                if not isinstance(value, str):
                    serialized_mapping[field] = json.dumps(value, default=str)
                else:
                    serialized_mapping[field] = value
            
            return self.redis.hset(name, mapping=serialized_mapping)
            
        except Exception as e:
            logger.error(f"Error setting hash {name}: {e}")
            return 0
    
    def hget(self, name: str, key: str, default: Any = None) -> Any:
        """
        Get hash field value.
        
        Args:
            name: Hash name
            key: Field key
            default: Default value if field doesn't exist
            
        Returns:
            Deserialized value or default
        """
        try:
            self._ensure_connection()
            value = self.redis.hget(name, key)
            
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Error getting hash field {name}:{key}: {e}")
            return default
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """
        Get all hash fields.
        
        Args:
            name: Hash name
            
        Returns:
            Dict of field-value pairs
        """
        try:
            self._ensure_connection()
            hash_data = self.redis.hgetall(name)
            
            # Deserialize values
            result = {}
            for field, value in hash_data.items():
                try:
                    result[field] = json.loads(value)
                except json.JSONDecodeError:
                    result[field] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting hash {name}: {e}")
            return {}
    
    def lpush(self, name: str, *values: Any) -> int:
        """
        Push values to the left of a list.
        
        Args:
            name: List name
            *values: Values to push
            
        Returns:
            int: Length of list after push
        """
        try:
            self._ensure_connection()
            
            # Serialize values
            serialized_values = []
            for value in values:
                if not isinstance(value, str):
                    serialized_values.append(json.dumps(value, default=str))
                else:
                    serialized_values.append(value)
            
            return self.redis.lpush(name, *serialized_values)
            
        except Exception as e:
            logger.error(f"Error pushing to list {name}: {e}")
            return 0
    
    def rpop(self, name: str, default: Any = None) -> Any:
        """
        Pop value from the right of a list.
        
        Args:
            name: List name
            default: Default value if list is empty
            
        Returns:
            Deserialized value or default
        """
        try:
            self._ensure_connection()
            value = self.redis.rpop(name)
            
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Error popping from list {name}: {e}")
            return default
    
    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        Get range of values from a list.
        
        Args:
            name: List name
            start: Start index
            end: End index
            
        Returns:
            List of deserialized values
        """
        try:
            self._ensure_connection()
            values = self.redis.lrange(name, start, end)
            
            # Deserialize values
            result = []
            for value in values:
                try:
                    result.append(json.loads(value))
                except json.JSONDecodeError:
                    result.append(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting range from list {name}: {e}")
            return []
    
    def sadd(self, name: str, *values: Any) -> int:
        """
        Add values to a set.
        
        Args:
            name: Set name
            *values: Values to add
            
        Returns:
            int: Number of values added
        """
        try:
            self._ensure_connection()
            
            # Serialize values
            serialized_values = []
            for value in values:
                if not isinstance(value, str):
                    serialized_values.append(json.dumps(value, default=str))
                else:
                    serialized_values.append(value)
            
            return self.redis.sadd(name, *serialized_values)
            
        except Exception as e:
            logger.error(f"Error adding to set {name}: {e}")
            return 0
    
    def smembers(self, name: str) -> set:
        """
        Get all members of a set.
        
        Args:
            name: Set name
            
        Returns:
            Set of deserialized values
        """
        try:
            self._ensure_connection()
            members = self.redis.smembers(name)
            
            # Deserialize values
            result = set()
            for member in members:
                try:
                    result.add(json.loads(member))
                except json.JSONDecodeError:
                    result.add(member)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting set {name}: {e}")
            return set()
    
    def close(self):
        """Close Redis connection."""
        if self.redis:
            self.redis.close()
        if self.connection_pool:
            self.connection_pool.disconnect()
        logger.info("Redis connection closed")

# Global Redis client instance
redis_client: Optional[RedisClient] = None

def get_redis_client() -> RedisClient:
    """
    Get or create Redis client instance.
    
    Returns:
        RedisClient: Redis client instance
    """
    global redis_client
    if redis_client is None:
        redis_client = RedisClient()
    return redis_client

def close_redis_client():
    """Close the global Redis client."""
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None
