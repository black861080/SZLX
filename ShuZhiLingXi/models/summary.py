from utils.exts import db
from datetime import datetime

class Summary(db.Model):
    __tablename__ = 'summary'
    summary_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    summary_content = db.Column(db.Text, nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('notes_chapter.chapter_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    chapter = db.relationship('NotesChapter', backref='summaries', lazy=True)

class Advice(db.Model):
    __tablename__ = 'advice'
    advice_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    advice_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chapter_id = db.Column(db.Integer, db.ForeignKey('notes_chapter.chapter_id'), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)

    chapter = db.relationship('NotesChapter', backref='advices', lazy=True)
