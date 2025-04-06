import os

from dotenv import load_dotenv
from openai import OpenAI

from src.definition.const.location import ENV_FILE

# 加载 .env 文件
load_dotenv(ENV_FILE)

# 从环境变量中获取密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("环境变量 OPENAI_API_KEY 未设置")

# 初始化 OpenAI 客户端
CLIENT = OpenAI(api_key=OPENAI_API_KEY)
