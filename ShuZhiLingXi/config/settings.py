# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,  # 如果有密码，请设置
    'decode_responses': True,  # 自动解码响应
    'socket_timeout': 5,  # 连接超时时间
    'socket_connect_timeout': 5,  # 连接超时时间
    'retry_on_timeout': True,  # 超时重试
    'max_connections': 10,  # 最大连接数
    'health_check_interval': 30  # 健康检查间隔
}

# Redis缓存配置
CACHE_CONFIG = {
    'user_info_ttl': 300,  # 用户信息缓存时间改为5分钟
    'search_history_ttl': 3600,  # 搜索历史缓存时间（秒）
    'plan_statistics_ttl': 300,  # 计划统计缓存时间（秒）
    'notes_summary_ttl': 3600,  # 笔记总结缓存时间（秒）
    'api_rate_limit': {
        'window': 60,  # 时间窗口（秒）
        'max_requests': 100  # 最大请求数
    }
}