from utils.exts import db
from datetime import datetime

class ChatHistoryList(db.Model):
    __tablename__ = 'chat_history_list'
    chat_history_list_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    chat_count = db.Column(db.Integer, default=0)

    chat_details = db.relationship('ChatHistoryDetail', backref='chat_list', lazy=True)

class ChatHistoryDetail(db.Model):
    __tablename__ = 'chat_history_detail'
    chat_history_detail_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chat_history_list_id = db.Column(db.Integer, db.ForeignKey('chat_history_list.chat_history_list_id'), nullable=False)
    is_image = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(255), nullable=True)
    image_describe = db.Column(db.Text, nullable=True)
    words = db.Column(db.Text, nullable=True)
    role = db.Column(db.Enum('system', 'user'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
