from redis_client import REDIS_CLIENT
from uuid import uuid4
from datetime import datetime

class Database:
  client = REDIS_CLIENT
  
  class Utils:
    def to_dict(redis_hash_data: dict) -> dict:
      return {key.decode('utf-8'): value.decode('utf-8') for key, value in redis_hash_data.items()}

    def gen_uuid():
      return str(uuid4())

    def gen_timestamp():
      return datetime.now()
    
  @classmethod
  def get(cls, key):
    return cls.client.get(key)
  
  @classmethod
  def set(cls, key, value):
    return cls.client.set(key, value)
  
  @classmethod
  def hget(cls, key, field):
    return cls.client.hget(key, field)
  
  @classmethod
  def hmset(cls, key, mapping):
    return cls.client.hmset(key, mapping)
  
  @classmethod
  def hgetall(cls, key):
    return cls.client.hgetall(key)
  
  @classmethod
  def hset(cls, key, field, value):
    return cls.client.hset(key, field, value)
  
  @classmethod
  def hdel(cls, key, field):
    return cls.client.hdel(key, field)
  
  @classmethod
  def exists(cls, key):
    return cls.client.exists(key)
  
  @classmethod
  def keys(cls, pattern):
    return cls.client.keys(pattern)
  