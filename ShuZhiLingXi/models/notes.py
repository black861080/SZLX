from utils.exts import db
from datetime import datetime

class NotesChapter(db.Model):
    __tablename__ = 'notes_chapter'
    chapter_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    notes_count = db.Column(db.Integer, default=0)
    clear_notes_count = db.Column(db.Integer, default=0)
    vague_notes_count = db.Column(db.Integer, default=0)
    unclear_notes_count = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), default='未分类')
    
    notes = db.relationship('Note', backref='chapter', lazy=True)

class Note(db.Model):
    __tablename__ = 'note'
    note_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('notes_chapter.chapter_id'), nullable=False)
    is_image = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(255), nullable=True)
    image_describe = db.Column(db.Text, nullable=True)
    is_audio = db.Column(db.Boolean, default=False)
    audio_url = db.Column(db.String(255), nullable=True)
    audio_describe = db.Column(db.Text, nullable=True)
    words = db.Column(db.Text, nullable=True)
    comprehension_level = db.Column(db.Enum('理解', '模糊', '不理解'), default='理解')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

class KnowledgeGraph(db.Model):
    __tablename__ = 'knowledge_graph'
    knowledge_graph_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('notes_chapter.chapter_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    chapter = db.relationship('NotesChapter', backref='knowledge_graph', lazy=True, uselist=False)
    items = db.relationship('KnowledgeItem', backref='knowledge_graph', lazy=True)
    relations = db.relationship('KnowledgeRelation', backref='knowledge_graph', lazy=True)

class KnowledgeItem(db.Model):
    __tablename__ = 'knowledge_item'
    knowledge_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    knowledge_graph_id = db.Column(db.Integer, db.ForeignKey('knowledge_graph.knowledge_graph_id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    relations_as_a = db.relationship('KnowledgeRelation',
                                   backref='item_a',
                                   foreign_keys='KnowledgeRelation.item_a_id',
                                   lazy=True)
    relations_as_b = db.relationship('KnowledgeRelation',
                                   backref='item_b',
                                   foreign_keys='KnowledgeRelation.item_b_id',
                                   lazy=True)

class KnowledgeRelation(db.Model):
    __tablename__ = 'knowledge_relation'
    knowledge_relation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    knowledge_graph_id = db.Column(db.Integer, db.ForeignKey('knowledge_graph.knowledge_graph_id'), nullable=False)
    item_a_id = db.Column(db.Integer, db.ForeignKey('knowledge_item.knowledge_item_id'), nullable=False)
    item_b_id = db.Column(db.Integer, db.ForeignKey('knowledge_item.knowledge_item_id'), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

class NoteSummary(db.Model):
    __tablename__ = 'note_summary'
    note_summary_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('notes_chapter.chapter_id'), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    chapter = db.relationship('NotesChapter', backref='note_summaries', lazy=True)