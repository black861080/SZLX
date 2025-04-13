from openai import OpenAI
import json
import requests
from typing import List, Dict, Generator
from config.config import Config
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda

kimi_client = OpenAI(
    api_key=Config.LLMConfig.MOONSHOT_API_KEY,
    base_url=Config.LLMConfig.MOONSHOT_BASE_URL,
)


class KimiTools:
    @tool
    def kimi_chat_stream(model: str, messages: List[Dict[str, str]]) -> Generator:
        """Kimi流式对话工具"""
        try:
            url = "https://api.moonshot.cn/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {Config.LLMConfig.MOONSHOT_API_KEY}"
            }

            data = {
                "model": model,
                "messages": messages,
                "stream": True
            }

            response = requests.post(url, headers=headers, json=data, stream=True)

            if response.status_code != 200:
                raise Exception(f"API请求失败，状态码: {response.status_code}")

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]

                    if line == '[DONE]':
                        break

                    try:
                        chunk_data = json.loads(line)
                        if 'usage' not in chunk_data and 'choices' in chunk_data:
                            content = chunk_data['choices'][0].get('delta', {}).get('content', '')
                            chunk_data['usage'] = {'total_tokens': len(content.split())}
                        yield chunk_data
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            raise Exception(f"Kimi流式对话失败: {str(e)}")

    @tool
    def kimi_chat(model: str, messages: List[Dict[str, str]]) -> Dict:
        """Kimi非流式对话工具"""
        try:
            url = "https://api.moonshot.cn/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {Config.LLMConfig.MOONSHOT_API_KEY}"
            }

            data = {
                "model": model,
                "messages": messages,
                "stream": False
            }

            response = requests.post(url, headers=headers, json=data)

            if response.status_code != 200:
                raise Exception(f"API请求失败，状态码: {response.status_code}")

            return response.json()

        except Exception as e:
            raise Exception(f"Kimi非流式对话失败: {str(e)}")


kimi_tools = KimiTools()
stream_chain = RunnableLambda(kimi_tools.kimi_chat_stream)
chat_chain = RunnableLambda(kimi_tools.kimi_chat)
