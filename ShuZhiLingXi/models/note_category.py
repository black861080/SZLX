from utils.exts import db
from datetime import datetime

class NoteCategory(db.Model):
    __tablename__ = 'note_category'
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)  # 分类名称
    description = db.Column(db.Text, nullable=True)   # 分类描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
