def redis_to_dict(redis_hash_data: dict) -> dict:
    return {key.decode('utf-8'): value.decode('utf-8') for key, value in redis_hash_data.items()}