from flask import Flask, jsonify
from flask_migrate import Migrate
from config.config import Config
from utils.exts import db
from routes.router import register_routes
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import logging
from scheduler.scheduler import start_scheduler, shutdown_scheduler

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# JWT错误处理
@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"Invalid token error: {error}")
    return jsonify({
        'message': 'Token验证失败',
        'error': str(error)
    }), 422

@jwt.unauthorized_loader
def unauthorized_callback(error):
    print(f"Unauthorized error: {error}")
    return jsonify({
        'message': '缺少Authorization头部',
        'error': str(error)
    }), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    print(f"Token expired - Header: {jwt_header}, Data: {jwt_data}")
    return jsonify({
        'message': 'Token已过期',
        'error': 'token_expired'
    }), 401

register_routes(app)

start_scheduler(app)

@app.teardown_appcontext
def shutdown_scheduler_handler(exception=None):
    shutdown_scheduler()

if __name__ == '__main__':
    app.run(debug=True)