from flask import Blueprint, jsonify, Response, stream_with_context, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from utils.cos_utils import COSClient
from utils.redis_utils import RedisUtils
from utils.exts import db
from models.token_usage import TokenUsage
from models.user import User
from flask_cors import CORS
from llm.qwen import textgen_stream_chain
from models.mistaken_question import MistakenQuestion, MistakenQuestionList

info_bp = Blueprint('info', __name__)

# 添加CORS配置
CORS(info_bp, resources={
    r"/auth/*": {
        "origins": ["http://localhost:5173"],
        "supports_credentials": True,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }
})

@info_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_info(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        print(f"Current user from token: {current_user_id}, type: {type(current_user_id)}")
        print(f"Requested user_id: {user_id}, type: {type(user_id)}")
        
        if current_user_id != user_id:
            return jsonify({
                'message': '无权访问此用户信息'
            }), 403
            
        # 尝试从Redis缓存获取用户信息
        redis_utils = RedisUtils()
        cached_user_info = redis_utils.get_user_info_cache(user_id)
        if cached_user_info:
            return jsonify(cached_user_info), 200
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'message': '用户不存在'
            }), 404
            
        # 查询用户的错题数量
        mistaken_question_count = db.session.query(MistakenQuestion).join(
            MistakenQuestionList,
            MistakenQuestion.question_list_id == MistakenQuestionList.question_list_id
        ).filter(
            MistakenQuestionList.user_id == user_id,
            MistakenQuestion.is_deleted == False
        ).count()
            
        user_info = {
            'user_id': user.user_id,
            'username': user.username,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'chapter_count': user.chapter_count,
            'notes_count': user.notes_count,
            'clear_notes_count': user.clear_notes_count,
            'vague_notes_count': user.vague_notes_count,
            'unclear_notes_count': user.unclear_notes_count,
            'profile': user.profile,
            'token_balance': user.token_balance,
            'profile_picture': user.profile_picture,
            'mistaken_question_count': mistaken_question_count
        }

        # 缓存用户信息
        redis_utils.set_user_info_cache(user_id, user_info)
        
        return jsonify(user_info), 200
        
    except Exception as e:
        print(f"Error in get_user_info: {str(e)}")
        return jsonify({
            'message': f'获取用户信息失败: {str(e)}'
        }), 500

@info_bp.route('/user/advice', methods=['GET'])
@jwt_required()
def get_user_advice():
    """获取基于用户画像的个性化建议"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': '用户不存在'}), 404

        if not user or user.token_balance <= 0:
            return jsonify({"code": 0, "msg": "Token余额不足"}), 403

        # 尝试从Redis缓存获取用户建议
        redis_utils = RedisUtils()
        cached_advice = redis_utils.get_cache(f"user:advice:{current_user_id}")
        if cached_advice:
            return jsonify(cached_advice), 200

        # 构建消息
        messages = [
            {"role": "system", "content": "你是一个贴心的生活助手，请给出简短的建议，字数200字左右。"}
        ]

        if user.profile:
            messages.append({
                "role": "user", 
                "content": f"这是我的个人画像：{user.profile}，请根据我的特点给出一条建议，200字左右。"
            })
        else:
            messages.append({
                "role": "user", 
                "content": "请给我一个实用的生活小妙招。"
            })

        def generate():
            advice_content = ""
            total_tokens = 0

            for chunk in textgen_stream_chain.invoke({'messages': messages}):
                if chunk and 'output' in chunk:
                    content = chunk['output']['choices'][0].get('delta', {}).get('content', '')
                    if content:
                        advice_content += content
                        yield f"data: {content}\n\n"
                    # 从最后一个chunk获取token使用量
                    if 'usage' in chunk:
                        total_tokens = chunk['usage'].get('total_tokens', 0)
            
            try:
                # 只在获取到token使用量时更新数据库
                if total_tokens > 0:
                    today = datetime.utcnow().date()
                    token_usage = TokenUsage.query.filter(
                        TokenUsage.user_id == current_user_id,
                        db.func.date(TokenUsage.created_at) == today
                    ).first()

                    if token_usage:
                        token_usage.spand += total_tokens
                    else:
                        token_usage = TokenUsage(
                            user_id=current_user_id,
                            spand=total_tokens
                        )
                        db.session.add(token_usage)

                    user.token_balance -= total_tokens
                    db.session.commit()

                    # 缓存用户建议
                    advice_data = {
                        'advice': advice_content,
                        'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    redis_utils.set_cache(f"user:advice:{current_user_id}", advice_data, 3600)  # 缓存1小时

            except Exception as e:
                print(f"保存token使用记录失败: {str(e)}")
                db.session.rollback()

            yield f"data: [TOKENS:{total_tokens}]\n\n"
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
        return jsonify({'message': f'获取建议失败: {str(e)}'}), 500


@info_bp.route('/token_usage/biweekly', methods=['GET'])
@jwt_required()
def get_biweekly_token_usage():
    try:
        current_user_id = get_jwt_identity()

        # 尝试从Redis缓存获取token使用记录
        redis_utils = RedisUtils()
        cached_usage = redis_utils.get_cache(f"token:usage:biweekly:{current_user_id}")
        if cached_usage:
            return jsonify(cached_usage), 200

        # 获取最近7天的日期范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=13)

        # 查询最近7天的token使用记录
        token_usage = TokenUsage.query.filter(
            TokenUsage.user_id == current_user_id,
            TokenUsage.created_at >= start_date,
            TokenUsage.created_at <= end_date
        ).all()

        # 格式化数据
        token_data = [{
            'created_at': usage.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'spand': usage.spand
        } for usage in token_usage]

        # 缓存token使用记录
        redis_utils.set_cache(f"token:usage:biweekly:{current_user_id}", token_data, 1800)  # 缓存30分钟

        return jsonify(token_data), 200

    except Exception as e:
        return jsonify({'message': f'获取Token使用记录失败: {str(e)}'}), 500

@info_bp.route('/user/edit/profile_picture', methods=['POST'])
@jwt_required()
def edit_user_profile_picture():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        cos_client = COSClient()
        profile_picture = cos_client.upload_base64_image(data['profile_picture'])
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                "code": 0,
                "msg": "用户不存在！"
            }),404
        user.profile_picture = profile_picture
        db.session.commit()

        # 清除用户信息缓存
        redis_utils = RedisUtils()
        redis_utils.delete_user_info_cache(current_user_id)

        return jsonify({
            "code": 1,
            "profile_picture": profile_picture
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "msg": f"处理失败: {str(e)}"
        }), 500
