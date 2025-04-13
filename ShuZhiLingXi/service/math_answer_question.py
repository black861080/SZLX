from flask_cors import CORS
from flask_jwt_extended import jwt_required, get_jwt_identity

from config.config import Config
from flask import request, jsonify, Blueprint, Response, stream_with_context
from utils.exts import db
from models.user import User
from models.chat_history import ChatHistoryList, ChatHistoryDetail
from llm.qwen import vl_chain, mathgen_stream_chain
from utils.cos_utils import COSClient
from datetime import datetime
from models.token_usage import TokenUsage
import dashscope

qwen_chat_bp = Blueprint('qwen_chat', __name__)

CORS(qwen_chat_bp, resources={
    r"/math_service/*": {
        "origins": ["http://localhost:5173"],
        "supports_credentials": True,
        "methods": ["POST", "OPTIONS"]
    }
})

dashscope.api_key = Config.LLMConfig.DASHSCOPE_API_KEY


@qwen_chat_bp.route('/math_chat', methods=['POST'])
@jwt_required()
def math_chat():
    try:
        # 获取用户ID从JWT中获取
        current_user_id = get_jwt_identity()

        # 检查用户token余额
        user = User.query.get(current_user_id)
        if not user or user.token_balance <= 0:
            return jsonify({"code": 0, "msg": "Token余额不足"}), 403

        data = request.get_json()
        chat_history_list_id = data.get('chat_history_list_id')
        chat_history_detail = data.get('chat_history_detail', [])
        image = data.get('image')
        question = data.get('question')

        # 使用JWT中获取的用户ID
        user = User.query.get(current_user_id)

        # 验证用户和聊天列表
        chat_list = ChatHistoryList.query.get(chat_history_list_id)
        if not user or not chat_list:
            return jsonify({"code": 0, "msg": "用户或聊天不存在"}), 404

        # 处理图片（如果有）
        image_text = ""
        image_url = None
        if image:
            try:
                # 需要确保 image 是 base64 格式的字符串
                if isinstance(image, str) and image.startswith('data:image'):
                    # 移除 base64 头部信息
                    image = image.split(',')[1] if ',' in image else image

                cos_client = COSClient()
                image_url = cos_client.upload_base64_image(image)

                # 使用图片URL进行识别
                image_text = vl_chain.invoke(image_url)

                # 保存图片URL和识别结果到聊天记录
                chat_detail = ChatHistoryDetail(
                    chat_history_list_id=chat_history_list_id,
                    is_image=True,
                    image_url=image_url,
                    image_describe=image_text,
                    words=question,
                    role='user'
                )
                db.session.add(chat_detail)

            except Exception as e:
                return jsonify({"code": 0, "msg": f"图片处理失败: {str(e)}"}), 500

        # 准备聊天消息
        messages = []

        # 添加系统提示
        system_content = "你是一个智能问答系统"
        if user.profile:
            system_content += f"，请参考用户画像：{user.profile}"
        messages.append({"role": "system", "content": system_content})

        # 添加历史对话记录
        if isinstance(chat_history_detail, list):
            # 限制历史记录最多4条
            recent_history = chat_history_detail[-4:] if len(chat_history_detail) > 4 else chat_history_detail
            for msg in recent_history:
                if isinstance(msg, dict):
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    if role and content:
                        messages.append({
                            "role": role,
                            "content": content
                        })

        # 构建用户当前消息
        user_message = question
        if image_text:
            user_message = (f"图片内容：{image_text}\n用户问题：{question}")
        if user.profile:
            user_message = f"{user_message}\n用户画像：{user.profile}"  # 修正用户画像的添加方式

        messages.append({"role": "user", "content": user_message})

        # 保存用户消息到数据库（非图片消息）
        if not image:
            user_chat_detail = ChatHistoryDetail(
                chat_history_list_id=chat_history_list_id,
                words=question,
                role='user'
            )
            db.session.add(user_chat_detail)
            db.session.commit()

        def generate():
            assistant_message = ""
            total_tokens = 0

            # 使用流式输出
            for chunk in mathgen_stream_chain.invoke({'messages': messages}):
                if chunk and 'output' in chunk:  # 检查output字段
                    content = chunk['output']['choices'][0].get('delta', {}).get('content', '')
                    if content:
                        assistant_message += content
                        yield f"data: {content}\n\n"

                # 统计token使用量
                if chunk and 'usage' in chunk:
                    total_tokens += chunk['usage'].get('total_tokens', 0)

            # 保存完整的对话记录到数据库
            try:
                bot_response = ChatHistoryDetail(
                    chat_history_list_id=chat_history_list_id,
                    words=assistant_message,
                    role='system'
                )
                db.session.add(bot_response)
                chat_list.chat_count += 2

                # 获取今天的token使用记录
                today = datetime.utcnow().date()
                token_usage = TokenUsage.query.filter(
                    TokenUsage.user_id == current_user_id,
                    db.func.date(TokenUsage.created_at) == today
                ).first()

                if token_usage:
                    # 如果今天已有记录，更新spand值
                    token_usage.spand += total_tokens
                else:
                    # 如果今天没有记录，创建新记录
                    token_usage = TokenUsage(
                        user_id=current_user_id,
                        spand=total_tokens
                    )
                    db.session.add(token_usage)

                # 更新用户token余额
                user.token_balance -= total_tokens

                db.session.commit()
            except Exception as e:
                print(f"保存对话记录失败: {str(e)}")
                db.session.rollback()

            # yield f"data: [TOKENS:{total_tokens}]\n\n"
            yield "data: [DONE]\n\n"

        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true'
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "msg": f"处理失败: {str(e)}"
        }), 500