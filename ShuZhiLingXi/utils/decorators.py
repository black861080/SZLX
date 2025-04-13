from functools import wraps
from flask import jsonify
from utils.redis_utils import RedisUtils

def rate_limit(key_prefix='api', window=None, max_requests=None):
    """API限流装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            redis_utils = RedisUtils()
            key = f"{key_prefix}:{kwargs.get('user_id', 'global')}"
            
            if not redis_utils.check_rate_limit(key, window, max_requests):
                return jsonify({
                    'message': '请求过于频繁，请稍后再试'
                }), 429
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator 