import json
from bson import ObjectId
import redis

# ✅ Connect to Redis
redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

async def get_redis_cache(cache_key):
    return redis_client.get(cache_key)


async def set_redis_cache(cache_key, data):
    json_data = json.dumps(serialize_mongo_data(data))
    return redis_client.setex(cache_key, 600, json_data)

# 🔹 Helper Function: Convert ObjectId to string
def serialize_mongo_data(data):
    """Recursively convert MongoDB ObjectId to string for JSON serialization."""
    if isinstance(data, list):
        return [serialize_mongo_data(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_mongo_data(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)  # ✅ Convert ObjectId to string
    else:
        return data