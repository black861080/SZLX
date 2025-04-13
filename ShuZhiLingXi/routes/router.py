from service.login import auth_bp
from service.register import register_bp
from service.information_management import info_bp
from service.normal_answer_question import kimi_chat_bp
from service.math_answer_question import qwen_chat_bp
from service.chat_history_management import history_bp
from service.plan_management import plan_bp
from service.notes_management import notes_bp
from service.search_history_management import search_history_bp
from service.notes_summary_management import knowledge_graph_bp
from service.mistaken_question_management import mistaken_question_bp

def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(register_bp, url_prefix='/register_service')
    app.register_blueprint(info_bp, url_prefix='/auth')
    app.register_blueprint(kimi_chat_bp, url_prefix='/chat_service')
    app.register_blueprint(qwen_chat_bp, url_prefix='/math_service')
    app.register_blueprint(history_bp, url_prefix='/history_service')
    app.register_blueprint(plan_bp, url_prefix='/plan_service')
    app.register_blueprint(notes_bp, url_prefix='/notes_service')
    app.register_blueprint(search_history_bp, url_prefix='/search_history_service')
    app.register_blueprint(knowledge_graph_bp, url_prefix='/notes_summary_service')
    app.register_blueprint(mistaken_question_bp, url_prefix='/mistaken_question_service')
