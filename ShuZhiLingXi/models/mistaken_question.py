from utils.exts import db
from datetime import datetime

class MistakenQuestionList(db.Model):
    __tablename__ = 'mistaken_question_list'
    question_list_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    count = db.Column(db.Integer, default=0)
    is_deleted = db.Column(db.Boolean, default=False)

    mistaken_question = db.relationship('MistakenQuestion', backref='mistaken_question_list', lazy=True)

class MistakenQuestion(db.Model):
    __tablename__ = 'mistaken_question'
    question_id = db.Column(db.Integer, primary_key=True)
    question_list_id = db.Column(db.Integer, db.ForeignKey('mistaken_question_list.question_list_id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    answer = db.Column(db.Text, nullable=True)
    is_image = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(255), nullable=True)
    image_describe = db.Column(db.Text, nullable=True)
    similar_question = db.Column(db.Text, nullable=True)
    similar_answer = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    is_favorite = db.Column(db.Boolean, default=False)
    error_type = db.Column(db.String(20), nullable=True)