from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.search_history import SearchHistory
from utils.exts import db

search_history_bp = Blueprint('search_history', __name__)


@search_history_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent_history():
    try:
        current_user_id = get_jwt_identity()

        histories = SearchHistory.query.filter_by(
            user_id=current_user_id,
            is_deleted=False
        ).order_by(
            SearchHistory.created_at.desc()
        ).limit(6).all()

        result = [{
            'history_id': history.history_id,
            'keyword': history.keyword,
            'created_at': history.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for history in histories]

        return jsonify({
            'msg': '获取成功',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'msg': f'获取失败: {str(e)}'
        }), 500


@search_history_bp.route('/delete/<int:history_id>', methods=['DELETE'])
@jwt_required()
def delete_history(history_id):
    try:
        current_user_id = get_jwt_identity()

        history = SearchHistory.query.filter_by(
            history_id=history_id,
            user_id=current_user_id
        ).first()

        if not history:
            return jsonify({
                'msg': '记录不存在或无权限删除'
            }), 404

        # 软删除
        history.is_deleted = True
        db.session.commit()

        return jsonify({
            'msg': '删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'msg': f'删除失败: {str(e)}'
        }), 500
