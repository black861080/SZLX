from datetime import timedelta


class Config:
    # 数据库配置
    DB_USERNAME = "root"
    DB_PASSWORD = "123456"
    DB_HOST = "127.0.0.1"
    DB_PORT = "3306"
    DB_NAME = "ai_assistant"
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = "SZLX"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # 大模型API配置
    class LLMConfig:
        # 通义千问配置
        DASHSCOPE_API_KEY = "your_api_key"
        QWEN_MODEL_NAME = "qwen2.5-math-72b-instruct"
        QWEN_VL_MODEL = "qwen-vl-max-0809"

        # Moonshot AI配置
        MOONSHOT_API_KEY = "your_api_key"
        MOONSHOT_BASE_URL = "https://api.moonshot.cn/v1"
        MOONSHOT_MODEL_NAME = "moonshot-v1-8k"

        # LangChain配置
        LANGCHAIN_TRACING_V2 = "ture"
        LANGCHAIN_API_KEY = your_api_key

    class COSConfig:
        REGION = your_region
        BUCKET = your_buket
        APPID = your_id
