import redis
from config.settings import REDIS_CONFIG

class RedisClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.redis_client = redis.Redis(
                host=REDIS_CONFIG['host'],
                port=REDIS_CONFIG['port'],
                db=REDIS_CONFIG['db'],
                password=REDIS_CONFIG.get('password'),
                decode_responses=True
            )
        return cls._instance
    
    def get_client(self):
        return self.redis_client
    
    def set(self, key, value, expire=None):
        """设置键值对"""
        self.redis_client.set(key, value)
        if expire:
            self.redis_client.expire(key, expire)
    
    def get(self, key):
        """获取键值"""
        return self.redis_client.get(key)
    
    def delete(self, key):
        """删除键"""
        return self.redis_client.delete(key)
    
    def exists(self, key):
        """检查键是否存在"""
        return self.redis_client.exists(key) 