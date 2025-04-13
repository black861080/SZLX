from utils.exts import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chapter_count = db.Column(db.Integer, default=0)
    notes_count = db.Column(db.Integer, default=0)
    clear_notes_count = db.Column(db.Integer, default=0)
    vague_notes_count = db.Column(db.Integer, default=0)
    unclear_notes_count = db.Column(db.Integer, default=0)
    profile = db.Column(db.String(255), nullable=True)
    token_balance = db.Column(db.Integer, default=100000)
    profile_picture = db.Column(db.String(255), default='https://blackmagic-1329109058.cos.ap-guangzhou.myqcloud.com/chat_images%2F1742457603321.jpg')