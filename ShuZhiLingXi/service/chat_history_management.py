from flask import Blueprint, request, jsonify
from flask_cors import CORS

from llm.qwen import vl_chain
from models.chat_history import ChatHistoryList, ChatHistoryDetail
from utils.cos_utils import COSClient
from utils.exts import db
from flask_jwt_extended import jwt_required, get_jwt_identity

history_bp = Blueprint('history', __name__)

# 修改CORS配置
CORS(history_bp, resources={
    r"/history_service/*": {  # 修改路由匹配模式
        "origins": ["http://localhost:5173"],
        "supports_credentials": True,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }
})


@history_bp.route('/list/delete/<int:list_id>', methods=['DELETE'])
@jwt_required()
def delete_chat_list(list_id):
    try:
        current_user_id = get_jwt_identity()
        chat_list = ChatHistoryList.query.filter_by(
            chat_history_list_id=list_id,
            user_id=current_user_id
        ).first()

        if not chat_list:
            return jsonify({
                'code': 0,
                'msg': '聊天列表不存在或无权限删除'
            }), 404

        chat_list.is_deleted = True
        for detail in chat_list.chat_details:
            detail.is_deleted = True
        db.session.commit()
        return jsonify({
            'code': 1,
            'msg': '聊天列表删除成功'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 0,
            'msg': f'删除失败: {str(e)}'
        }), 500


@history_bp.route('/list/edit/<int:list_id>', methods=['PUT'])
@jwt_required()
def edit_chat_list(list_id):
    try:
        current_user_id = get_jwt_identity()
        chat_list = ChatHistoryList.query.filter_by(
            chat_history_list_id=list_id,
            user_id=current_user_id
        ).first()

        if not chat_list:
            return jsonify({'message': '聊天列表不存在或无权限编辑'}), 404

        data = request.get_json()
        if 'name' in data:
            chat_list.name = data['name']

        db.session.commit()
        return jsonify({'message': '聊天列表更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@history_bp.route('/detail/delete/<int:detail_id>', methods=['DELETE'])
@jwt_required()
def delete_chat_detail(detail_id):
    try:
        current_user_id = get_jwt_identity()

        # 获取要删除的消息
        chat_detail = ChatHistoryDetail.query.get(detail_id)
        if not chat_detail:
            return jsonify({
                'code': 0,
                'msg': '聊天记录不存在'
            }), 404

        # 获取聊天列表并验证权限
        chat_list = ChatHistoryList.query.filter_by(
            chat_history_list_id=chat_detail.chat_history_list_id,
            user_id=current_user_id,
            is_deleted=False
        ).first()

        if not chat_list:
            return jsonify({
                'code': 0,
                'msg': '无权限删除此聊天记录'
            }), 403

        chat_detail.is_deleted = True

        # 更新聊天数量
        if chat_list and chat_list.chat_count > 0:
            chat_list.chat_count -= 1

        db.session.commit()
        return jsonify({
            'code': 1,
            'msg': '聊天记录删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 0,
            'msg': f'删除失败: {str(e)}'
        }), 500


@history_bp.route('/detail/edit/<int:detail_id>', methods=['PUT'])
@jwt_required()
def edit_chat_detail(detail_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        words = data.get('words')
        chat_history_list_id = data.get('chat_history_list_id')

        if not words:
            return jsonify({"code": 0, "msg": "消息内容不能为空"}), 400

        # 获取要编辑的消息和对应的聊天列表
        chat_detail = ChatHistoryDetail.query.get(detail_id)
        if not chat_detail:
            return jsonify({"code": 0, "msg": "消息不存在"}), 404

        # 获取聊天列表并验证权限
        chat_list = ChatHistoryList.query.filter_by(
            chat_history_list_id=chat_history_list_id,
            user_id=current_user_id,
            is_deleted=False
        ).first()

        if not chat_list:
            return jsonify({"code": 0, "msg": "无权限编辑此消息"}), 403

        # 更新消息内容
        chat_detail.words = words

        # 删除该消息之后的所有消息
        ChatHistoryDetail.query.filter(
            ChatHistoryDetail.chat_history_list_id == chat_history_list_id,
            ChatHistoryDetail.chat_history_detail_id > detail_id,
            ChatHistoryDetail.is_deleted == False
        ).update({"is_deleted": True})

        # 更新聊天数量
        if chat_list:
            # 重新计算未删除的消息数量
            chat_count = ChatHistoryDetail.query.filter_by(
                chat_history_list_id=chat_history_list_id,
                is_deleted=False
            ).count()
            chat_list.chat_count = chat_count

        db.session.commit()

        return jsonify({
            "code": 1,
            "msg": "更新成功",
            "data": {
                "chat_history_detail_id": chat_detail.chat_history_detail_id,
                "words": chat_detail.words
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 0, "msg": f"更新失败: {str(e)}"}), 500


@history_bp.route('/list', methods=['GET'])
@jwt_required()
def get_chat_lists():
    try:
        current_user_id = get_jwt_identity()
        chat_lists = ChatHistoryList.query.filter_by(
            user_id=current_user_id,
            is_deleted=False
        ).all()

        result = [{
            'chat_history_list_id': list_element.chat_history_list_id,
            'name': list_element.name,
            'chat_count': list_element.chat_count,
            'created_at': list_element.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for list_element in chat_lists]

        return jsonify({
            'code': 1,
            'msg': '获取成功',
            'data': result
        }), 200
    except Exception as e:
        return jsonify({
            'code': 0,
            'msg': f'获取失败: {str(e)}'
        }), 500


@history_bp.route('/detail/<int:list_id>', methods=['GET'])
@jwt_required()
def get_chat_details(list_id):
    try:
        current_user_id = get_jwt_identity()

        # 首先验证聊天列表的所有权
        chat_list = ChatHistoryList.query.filter_by(
            chat_history_list_id=list_id,
            user_id=current_user_id,
            is_deleted=False
        ).first()

        if not chat_list:
            return jsonify({
                'code': 0,
                'msg': '无权限访问此聊天记录或聊天记录不存在'
            }), 403

        # 获取聊天详情
        chat_details = ChatHistoryDetail.query.filter_by(
            chat_history_list_id=list_id,
            is_deleted=False
        ).order_by(ChatHistoryDetail.created_at).all()

        result = [{
            'chat_history_detail_id': detail.chat_history_detail_id,
            'is_image': detail.is_image,
            'image_url': detail.image_url,
            'image_describe': detail.image_describe,
            'words': detail.words,
            'role': detail.role,
            'created_at': detail.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for detail in chat_details]

        return jsonify({
            'code': 1,
            'msg': '获取成功',
            'data': result
        }), 200
    except Exception as e:
        return jsonify({
            'code': 0,
            'msg': f'获取失败: {str(e)}'
        }), 500


@history_bp.route('/list/create', methods=['POST'])
@jwt_required()
def create_chat_list():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # 创建新的聊天列表
        new_chat_list = ChatHistoryList(
            name=data.get('name', '新对话'),
            user_id=current_user_id,
            chat_count=1  # 初始计数为1，因为会添加一条系统消息
        )
        db.session.add(new_chat_list)
        db.session.flush()  # 获取新创建的chat_history_list_id

        # 创建系统欢迎消息
        welcome_message = ChatHistoryDetail(
            chat_history_list_id=new_chat_list.chat_history_list_id,
            is_image=False,
            image_url=None,
            image_describe=None,
            words="您好，请问有什么可以帮你的吗",
            role="system"
        )
        db.session.add(welcome_message)

        db.session.commit()
        return jsonify({
            'code': 1,
            'msg': '创建成功',
            'data': {
                'chat_history_list_id': new_chat_list.chat_history_list_id,
                'name': new_chat_list.name
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 0,
            'msg': f'创建失败: {str(e)}'
        }), 500
