"""
Redis connection and queue management
"""

import logging
import redis.asyncio as redis
from typing import Optional
from .config import get_settings

logger = logging.getLogger(__name__)

# Global Redis client
redis_client: Optional[redis.Redis] = None

async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    
    settings = get_settings()
    
    try:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            retry_on_timeout=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection initialized")
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

def get_redis() -> redis.Redis:
    """Get Redis client"""
    return redis_client

async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")