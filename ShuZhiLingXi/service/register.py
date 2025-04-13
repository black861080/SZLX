from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from models.user import User, db

register_bp = Blueprint('register', __name__)


@register_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # 获取注册信息
        username = data.get('username')
        password = data.get('password')

        # 验证必填字段
        if not all([username, password]):
            return jsonify({
                'code': 400,
                'message': '所有字段都是必填的'
            }), 400

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({
                'code': 400,
                'message': '用户名已存在'
            }), 400

        # 创建新用户
        new_user = User(
            username=username,
            password=generate_password_hash(password),
        )

        # 保存到数据库
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '注册成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'注册失败: {str(e)}'
        }), 500
