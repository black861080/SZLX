from flask import Blueprint, request, jsonify, Response, stream_with_context
from models.plan import Plan, PlanAdvice
from utils.exts import db
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from llm.qwen import textgen_stream_chain
from flask_cors import CORS
from models.token_usage import TokenUsage
from utils.redis_utils import RedisUtils

plan_bp = Blueprint('plan', __name__)

# 在创建 Blueprint 后添加 CORS 配置
CORS(plan_bp,
     resources={r"/*": {
         "origins": "http://localhost:5173",
         "supports_credentials": True,
         "allow_headers": ["Content-Type", "Authorization"],
         "expose_headers": ["Content-Type"],
         "max_age": 3600
     }})

# 创建新计划
# 创建新计划
@plan_bp.route('/plans', methods=['POST'])
@jwt_required()
def create_plan():
    """创建新计划"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # 验证必要字段
        if not all(key in data for key in ['todo', 'deadline', 'level']):
            return jsonify({'message': '缺少必要字段'}), 400

        # 验证并转换deadline格式
        try:
            deadline = datetime.fromisoformat(data['deadline'])
        except ValueError:
            return jsonify({'message': '日期格式无效'}), 400

        # 验证level值
        if data['level'] not in ['紧急', '非紧急']:
            return jsonify({'message': '无效的优先级值'}), 400

        new_plan = Plan(
            todo=data['todo'],
            deadline=deadline,
            level=data['level'],
            user_id=current_user_id
        )

        db.session.add(new_plan)
        db.session.commit()

        return jsonify({
            'message': '计划创建成功',
            'plan_id': new_plan.plan_id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'创建计划失败: {str(e)}'}), 500


# 获取某用户的所有计划
@plan_bp.route('/plans', methods=['GET'])
@jwt_required()
def get_plans():
    """获取当前用户的所有计划"""
    try:
        current_user_id = get_jwt_identity()
        plans = Plan.query.filter_by(
            user_id=current_user_id,
            is_deleted=False
        ).order_by(Plan.deadline).all()

        return jsonify({
            'plans': [{
                'plan_id': plan.plan_id,
                'todo': plan.todo,
                'deadline': plan.deadline.isoformat(),
                'level': plan.level,
                'created_at': plan.created_at.isoformat()
            } for plan in plans]
        }), 200
    except Exception as e:
        return jsonify({'message': f'获取计划失败: {str(e)}'}), 500


# 获取用户的紧急计划
# @plan_bp.route('/plans/urgent', methods=['GET'])
# @jwt_required()
# def get_urgent_plans():
#     user_id = get_jwt_identity()
#     urgent_plans = Plan.query.filter_by(
#         user_id=user_id,
#         is_deleted=False,
#         level='紧急'
#     ).all()
#
#     return jsonify({
#         'urgent_plans': [{
#             'plan_id': plan.plan_id,
#             'todo': plan.todo,
#             'deadline': plan.deadline.strftime('%Y-%m-%d %H:%M'),
#             'created_at': plan.created_at.strftime('%Y-%m-%d %H:%M')
#         } for plan in urgent_plans]
#     }), 200

# 更新计划
@plan_bp.route('/plans/<int:plan_id>', methods=['PUT'])
@jwt_required()
def update_plan(plan_id):
    """更新计划"""
    try:
        current_user_id = get_jwt_identity()
        plan = Plan.query.filter_by(
            plan_id=plan_id,
            user_id=current_user_id,
            is_deleted=False
        ).first()

        if not plan:
            return jsonify({'message': '计划不存在或无权限修改'}), 404

        data = request.get_json()

        if 'todo' in data:
            plan.todo = data['todo']
        if 'deadline' in data:
            try:
                plan.deadline = datetime.fromisoformat(data['deadline'])
            except ValueError:
                return jsonify({'message': '日期格式无效'}), 400
        if 'level' in data:
            if data['level'] not in ['紧急', '非紧急']:
                return jsonify({'message': '无效的优先级值'}), 400
            plan.level = data['level']

        db.session.commit()

        return jsonify({
            'message': '计划更新成功',
            'plan_id': plan.plan_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'更新计划失败: {str(e)}'}), 500


# 删除计划（软删除）
@plan_bp.route('/plans/<int:plan_id>', methods=['DELETE'])
@jwt_required()
def delete_plan(plan_id):
    """删除计划(软删除)"""
    try:
        current_user_id = get_jwt_identity()
        plan = Plan.query.filter_by(
            plan_id=plan_id,
            user_id=current_user_id,
            is_deleted=False
        ).first()

        if not plan:
            return jsonify({'message': '计划不存在或无权限删除'}), 404

        plan.is_deleted = True
        db.session.commit()

        return jsonify({
            'message': '计划删除成功',
            'plan_id': plan.plan_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'删除计划失败: {str(e)}'}), 500


@plan_bp.route('/plans/statistics', methods=['GET'])
@jwt_required()
def get_plan_statistics():
    """获取计划统计信息"""
    try:
        current_user_id = get_jwt_identity()

        # 尝试从Redis缓存获取统计信息
        redis_utils = RedisUtils()
        cached_statistics = redis_utils.get_plan_statistics_cache(current_user_id)
        if cached_statistics:
            return jsonify(cached_statistics), 200

        # 获取未删除的计划总数
        total_plans = Plan.query.filter_by(
            user_id=current_user_id,
            is_deleted=False
        ).count()

        # 获取紧急计划数量
        urgent_plans = Plan.query.filter_by(
            user_id=current_user_id,
            is_deleted=False,
            level='紧急'
        ).count()

        # 获取已过期未完成的计划数量
        overdue_plans = Plan.query.filter(
            Plan.user_id == current_user_id,
            Plan.is_deleted == False,
            Plan.deadline < datetime.utcnow()
        ).count()

        statistics = {
            'total_plans': total_plans,
            'urgent_plans': urgent_plans,
            'overdue_plans': overdue_plans
        }

        # 缓存统计信息
        redis_utils.set_plan_statistics_cache(current_user_id, statistics)

        return jsonify(statistics), 200
    except Exception as e:
        return jsonify({'message': f'获取统计信息失败: {str(e)}'}), 500


@plan_bp.route('/plans/ai_advice', methods=['POST'])
@jwt_required()
def get_ai_advice():
    """获取AI定制化建议"""
    try:
        current_user_id = get_jwt_identity()

        # 检查用户token余额
        user = User.query.get(current_user_id)
        if not user or user.token_balance <= 0:
            return jsonify({"code": 0, "msg": "Token余额不足"}), 403

        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'message': '用户不存在'}), 404

        # 获取用户的所有计划
        plans = Plan.query.filter_by(user_id=current_user_id, is_deleted=0).all()
        if not plans:
            return jsonify({'message': '没有找到任何计划'}), 404

        # 构建计划描述
        plan_descriptions = []
        for plan in plans:
            deadline = plan.deadline.strftime('%Y-%m-%d %H:%M') if plan.deadline else '无截止日期'
            plan_descriptions.append(f"计划：{plan.todo}，截止时间：{deadline}，优先级：{plan.level}")

        if user.profile:
            plan_descriptions.append(f"用户画像:{user.profile}")

        # 构建消息
        messages = [
            {"role": "system", "content": "你是一个专业的时间管理顾问。"},
            {"role": "user", "content": f"这是我的计划列表：\n" + "\n".join(
                plan_descriptions) + "\n请根据我的计划和截止时间给出时间管理建议。"}
        ]

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

            # 只在获取到token使用量时更新数据库
            try:
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

                    # 保存建议到数据库
                    advice = PlanAdvice.query.filter_by(user_id=current_user_id).first()
                    if advice:
                        advice.content = advice_content
                        advice.updated_at = datetime.utcnow()
                    else:
                        advice = PlanAdvice(user_id=current_user_id, content=advice_content)
                        db.session.add(advice)
                    db.session.commit()
            except Exception as e:
                print(f"保存AI建议到数据库时出错: {str(e)}")
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
        return jsonify({'message': f'获取AI建议失败: {str(e)}'}), 500


@plan_bp.route('/plans/ai_advice/get', methods=['GET'])
@jwt_required()
def get_existing_advice():
    """获取用户已存在的AI建议"""
    try:
        current_user_id = get_jwt_identity()
        advice = PlanAdvice.query.filter_by(user_id=current_user_id).first()

        if not advice:
            return jsonify({
                'content': '',
                'updated_at': ''
            }), 200

        return jsonify({
            'content': advice.content,
            'updated_at': advice.updated_at.isoformat()
        }), 200

    except Exception as e:
        return jsonify({'message': f'获取建议失败: {str(e)}'}), 500
