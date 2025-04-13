from utils.exts import db
from datetime import datetime

class Plan(db.Model):
    __tablename__ = 'plan'
    plan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    todo = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    level = db.Column(db.Enum('紧急', '非紧急'), default='非紧急')

class PlanAdvice(db.Model):
    __tablename__ = 'plan_advice'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

