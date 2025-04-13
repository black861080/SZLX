import json
import time
from redis import Redis, ConnectionError
from config.settings import REDIS_CONFIG, CACHE_CONFIG

class RedisUtils:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisUtils, cls).__new__(cls)
            try:
                cls._instance.redis_client = Redis(**REDIS_CONFIG)
                # 测试连接
                cls._instance.redis_client.ping()
            except ConnectionError as e:
                print(f"Redis连接失败: {str(e)}")
                # 如果连接失败，设置redis_client为None
                cls._instance.redis_client = None
        return cls._instance
    
    def get_client(self):
        if self.redis_client is None:
            try:
                self.redis_client = Redis(**REDIS_CONFIG)
                self.redis_client.ping()
            except ConnectionError as e:
                print(f"Redis重连失败: {str(e)}")
                return None
        return self.redis_client
    
    def get_cache(self, key):
        """获取缓存"""
        try:
            client = self.get_client()
            if client is None:
                return None
            value = client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"获取缓存失败: {str(e)}")
            return None
    
    def set_cache(self, key, value, ttl=None):
        """设置缓存"""
        try:
            client = self.get_client()
            if client is None:
                return False
            client.set(key, json.dumps(value), ex=ttl)
            return True
        except Exception as e:
            print(f"设置缓存失败: {str(e)}")
            return False
    
    def delete_cache(self, key):
        """删除缓存"""
        try:
            client = self.get_client()
            if client is None:
                return False
            client.delete(key)
            return True
        except Exception as e:
            print(f"删除缓存失败: {str(e)}")
            return False
    
    def check_rate_limit(self, key, window=None, max_requests=None):
        """检查API调用频率限制"""
        try:
            client = self.get_client()
            if client is None:
                return True  # 如果Redis不可用，默认允许请求
            
            if window is None:
                window = CACHE_CONFIG['api_rate_limit']['window']
            if max_requests is None:
                max_requests = CACHE_CONFIG['api_rate_limit']['max_requests']
                
            current = client.get(key)
            if current is None:
                client.setex(key, window, 1)
                return True
                
            if int(current) >= max_requests:
                return False
                
            client.incr(key)
            return True
        except Exception as e:
            print(f"检查限流失败: {str(e)}")
            return True  # 如果Redis不可用，默认允许请求
    
    def get_user_info_cache(self, user_id):
        """获取用户信息缓存"""
        try:
            key = f"user:info:{user_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"获取用户信息缓存失败: {str(e)}")
            return None
    
    def set_user_info_cache(self, user_id, data, expire_time=None):
        """设置用户信息缓存"""
        try:
            key = f"user:info:{user_id}"
            if expire_time is None:
                expire_time = CACHE_CONFIG['user_info_ttl']  # 默认30分钟
            self.redis_client.setex(key, expire_time, json.dumps(data))
        except Exception as e:
            print(f"设置用户信息缓存失败: {str(e)}")
    
    def delete_user_info_cache(self, user_id):
        """删除用户信息缓存"""
        try:
            key = f"user:info:{user_id}"
            self.redis_client.delete(key)
        except Exception as e:
            print(f"删除用户信息缓存失败: {str(e)}")
    
    def get_search_history_cache(self, user_id):
        """获取搜索历史缓存"""
        return self.get_cache(f"search:history:{user_id}")
    
    def set_search_history_cache(self, user_id, history):
        """设置搜索历史缓存"""
        self.set_cache(
            f"search:history:{user_id}",
            history,
            CACHE_CONFIG['search_history_ttl']
        )
    
    def get_plan_statistics_cache(self, user_id):
        """获取计划统计缓存"""
        return self.get_cache(f"plan:statistics:{user_id}")
    
    def set_plan_statistics_cache(self, user_id, statistics):
        """设置计划统计缓存"""
        self.set_cache(
            f"plan:statistics:{user_id}",
            statistics,
            CACHE_CONFIG['plan_statistics_ttl']
        )
    
    def get_notes_summary_cache(self, chapter_id):
        """获取笔记总结缓存"""
        return self.get_cache(f"notes:summary:{chapter_id}")
    
    def set_notes_summary_cache(self, chapter_id, summary):
        """设置笔记总结缓存"""
        self.set_cache(
            f"notes:summary:{chapter_id}",
            summary,
            CACHE_CONFIG['notes_summary_ttl']
        ) 