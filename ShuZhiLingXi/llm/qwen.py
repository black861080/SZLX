# qwen.py
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda
from config.config import Config
import dashscope
from openai import OpenAI
from typing import List, Dict, Generator


dashscope.api_key = Config.LLMConfig.DASHSCOPE_API_KEY


class QwenTools:
    @tool
    def qwen_vl_recognize(image_url: str) -> str:
        """图像文字识别工具"""
        try:
            client = OpenAI(
                api_key=Config.LLMConfig.DASHSCOPE_API_KEY,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )

            completion = client.chat.completions.create(
                model="qwen-vl-plus-latest",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text",
                         "text": "请识别并提取这张图片中的所有文字内容，以文本形式输出，只需要输出图片中的内容，不需要告诉我你的想法等多余的东西"},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }]
            )
            return completion.choices[0].message.content

        except Exception as e:
            raise Exception(f"通义千问图像识别接口调用失败: {str(e)}")

    @tool
    def qwen_audio_recognize(audio_url: str) -> str:
        """语音识别工具"""
        try:
            messages = [{
                "role": "user",
                "content": [{"audio": audio_url}]
            }]

            response = dashscope.MultiModalConversation.call(
                model="qwen-audio-asr-1204",
                messages=messages,
                result_format="message"
            )

            return response.output.choices[0].message.content[0]["text"]

        except Exception as e:
            raise Exception(f"通义千问语音识别接口调用失败: {str(e)}")

    # qwen.py 修改后的工具函数
    @tool
    def qwen_text_generation_stream(messages: List[Dict[str, str]]) -> Generator:
        """Qwen流式文本生成工具"""
        try:
            from dashscope import Generation
            response = Generation.call(
                model="qwen-max",
                messages=messages,
                stream=True,
                result_format='message'
            )

            prev_content = ""
            for chunk in response:
                if chunk.status_code == 200:
                    current_content = chunk.output.choices[0].message.content
                    delta_content = current_content[len(prev_content):]
                    prev_content = current_content
                    
                    output = {
                        'output': {
                            'choices': [{
                                'delta': {
                                    'content': delta_content
                                }
                            }]
                        }
                    }
                    
                    # 在最后一个chunk中添加usage信息
                    if hasattr(chunk, 'usage') and chunk.usage:
                        output['usage'] = {
                            'total_tokens': chunk.usage.total_tokens
                        }
                    
                    yield output
                else:
                    raise Exception(f"API请求失败，状态码: {chunk.code}")

        except Exception as e:
            raise Exception(f"Qwen流式对话失败: {str(e)}")

    @tool
    def qwen_math_generation_stream(messages: List[Dict[str, str]]) -> Generator:
        """Qwen数学模型流式文本生成工具"""
        try:
            from dashscope import Generation
            response = Generation.call(
                model="qwen2.5-math-72b-instruct",
                messages=messages,
                stream=True,
                result_format='message'
            )

            prev_content = ""
            for chunk in response:
                if chunk.status_code == 200:
                    current_content = chunk.output.choices[0].message.content
                    delta_content = current_content[len(prev_content):]
                    prev_content = current_content
                    
                    output = {
                        'output': {
                            'choices': [{
                                'delta': {
                                    'content': delta_content
                                }
                            }]
                        }
                    }
                    
                    # 在最后一个chunk中添加usage信息
                    if hasattr(chunk, 'usage') and chunk.usage:
                        output['usage'] = {
                            'total_tokens': chunk.usage.total_tokens
                        }
                    
                    yield output
                else:
                    raise Exception(f"API请求失败，状态码: {chunk.code}")

        except Exception as e:
            raise Exception(f"Qwen数学模型流式对话失败: {str(e)}")

    @tool
    def qwen_text_generation(messages: List[Dict[str, str]]) -> Dict:
        """Qwen非流式文本生成工具"""
        try:
            from dashscope import Generation
            response = Generation.call(
                model="qwen-max",
                messages=messages,
                result_format='message'
            )

            if response.status_code != 200:
                raise Exception(f"API请求失败，状态码: {response.status_code}")

            return {
                'output': {
                    'text': response.output.choices[0].message.content,  # 直接提取text字段
                    'usage': response.usage.total_tokens
                }
            }

        except Exception as e:
            raise Exception(f"Qwen非流式对话失败: {str(e)}")


qwen_tools = QwenTools()
vl_chain = RunnableLambda(qwen_tools.qwen_vl_recognize)
audio_chain = RunnableLambda(qwen_tools.qwen_audio_recognize)
textgen_chain = RunnableLambda(qwen_tools.qwen_text_generation)
textgen_stream_chain = RunnableLambda(qwen_tools.qwen_text_generation_stream)
mathgen_stream_chain = RunnableLambda(qwen_tools.qwen_math_generation_stream)