from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from werkzeug.security import check_password_hash
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request,
    get_jwt
)
from datetime import datetime, timezone, timedelta

from utils.exts import db
from models.user import User
from models.token_usage import TokenUsage
from llm.qwen import textgen_stream_chain


auth_bp = Blueprint('auth', __name__)

# 添加CORS配置
CORS(auth_bp, resources={
    r"/auth/*": {
        "origins": ["http://localhost:5173"],
        "supports_credentials": True,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }
})


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        remember = data.get('remember', False)
        
        if not username or not password:
            return jsonify({
                'message': '用户名和密码不能为空'
            }), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            if not user.is_active:
                return jsonify({
                    'message': '账户已被禁用'
                }), 401

            print(f"User authenticated: {user.user_id}")
            
            access_expires = timedelta(days=7) if remember else timedelta(hours=2)
            refresh_expires = timedelta(days=14) if remember else timedelta(days=1)
            
            access_token = create_access_token(
                identity=str(user.user_id),
                fresh=True,
                expires_delta=access_expires
            )
            refresh_token = create_refresh_token(
                identity=str(user.user_id),
                expires_delta=refresh_expires
            )
            
            return jsonify({
                'message': '登录成功',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_id': user.user_id,
                'username': user.username,
                'token_balance': user.token_balance,
                'profile_picture': user.profile_picture
            }), 200
        else:
            return jsonify({
                'message': '用户名或密码错误'
            }), 401
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            'message': f'登录失败: {str(e)}'
        }), 500


@auth_bp.route('/verify-token', methods=['GET'])
def verify_token():
    try:
        verify_jwt_in_request()
        jwt = get_jwt()
        exp_timestamp = jwt["exp"]
        current_timestamp = datetime.now(timezone.utc).timestamp()
        
        return jsonify({
            'valid': exp_timestamp > current_timestamp
        }), 200
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': str(e)
        }), 401


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    remember = request.args.get('remember', 'false') == 'true'
    
    access_expires = timedelta(days=7) if remember else timedelta(hours=2)
    access_token = create_access_token(
        identity=current_user_id,
        expires_delta=access_expires
    )
    
    return jsonify({
        'access_token': access_token
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """登出用户"""
    return jsonify({
        'message': '成功登出'
    }), 200


@auth_bp.route('/test-protected', methods=['GET'])
@jwt_required()
def test_protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    return jsonify({
        'message': f'受保护的API访问成功！当前用户: {user.username}',
        'user_id': current_user_id
    }), 200
