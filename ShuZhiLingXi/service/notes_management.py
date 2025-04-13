from flask import Blueprint, request, jsonify

from llm.qwen import vl_chain, audio_chain
from models.notes import Note, NotesChapter
from models.note_category import NoteCategory
from utils.cos_utils import COSClient
from utils.exts import db
from datetime import datetime, timedelta
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.search_history import SearchHistory

notes_bp = Blueprint('notes', __name__)


# 创建笔记章节
@notes_bp.route('/chapter/create', methods=['POST'])
@jwt_required()
def create_chapter():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        name = data.get('name')
        category = data.get('category')

        user = User.query.get(current_user_id)
        chapter = NotesChapter(
            name=name,
            user_id=current_user_id,
            category=category
        )
        user.chapter_count += 1
        db.session.add(chapter)
        db.session.commit()

        return jsonify({
            'msg': '创建成功',
            'data': {
                'chapter_id': chapter.chapter_id,
                'name': chapter.name,
                'category': chapter.category,
                'created_at': chapter.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'msg': f'创建失败: {str(e)}'
        }), 500


# 获取用户的所有笔记章节
@notes_bp.route('/chapter/list', methods=['GET'])
@jwt_required()
def get_chapters():
    try:
        current_user_id = get_jwt_identity()
        chapters = NotesChapter.query.filter_by(
            user_id=current_user_id,
            is_deleted=False
        ).all()

        result = [{
            'chapter_id': chapter.chapter_id,
            'name': chapter.name,
            'category': chapter.category,
            'created_at': chapter.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'note_count': len([note for note in chapter.notes if not note.is_deleted])
        } for chapter in chapters]

        return jsonify({
            'msg': '获取成功',
            'data': result
        }), 200

    except Exception as e:
        print(f"Error in get_chapters: {str(e)}")  # 添加日志
        return jsonify({
            'msg': f'获取失败: {str(e)}'
        }), 500


# 编辑笔记章节
@notes_bp.route('/chapter/edit/<int:chapter_id>', methods=['PUT'])
@jwt_required()
def edit_chapter(chapter_id):
    try:
        chapter = NotesChapter.query.get_or_404(chapter_id)
        data = request.get_json()

        if 'name' in data:
            chapter.name = data['name']
        chapter.category = data['category']

        db.session.commit()

        return jsonify({
            'msg': '更新成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'msg': f'更新失败: {str(e)}'
        }), 500


# 删除笔记章节
@notes_bp.route('/chapter/delete/<int:chapter_id>', methods=['PUT'])
@jwt_required()
def delete_chapter(chapter_id):
    try:
        chapter = NotesChapter.query.get_or_404(chapter_id)
        user = User.query.get(chapter.user_id)

        # 获取该章节下所有未删除的笔记
        notes = Note.query.filter_by(chapter_id=chapter_id, is_deleted=False).all()
        
        # 更新用户的各类笔记计数
        for note in notes:
            # 更新总笔记计数
            user.notes_count = max(0, user.notes_count - 1)
            
            # 根据笔记的理解程度更新对应计数
            if note.comprehension_level == '理解':
                user.clear_notes_count = max(0, user.clear_notes_count - 1)
            elif note.comprehension_level == '模糊':
                user.vague_notes_count = max(0, user.vague_notes_count - 1)
            elif note.comprehension_level == '不理解':
                user.unclear_notes_count = max(0, user.unclear_notes_count - 1)
            
            # 标记笔记为已删除
            note.is_deleted = True

        # 更新用户的章节计数
        user.chapter_count = max(0, user.chapter_count - 1)

        # 标记章节为已删除
        chapter.is_deleted = True
        chapter.notes_count = 0

        db.session.commit()
        return jsonify({'msg': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Delete chapter error: {str(e)}")
        return jsonify({'msg': f'删除失败: {str(e)}'}), 500


# 创建笔记
@notes_bp.route('/note/create', methods=['POST'])
def create_note():
    try:
        data = request.get_json()
        chapter_id = data.get('chapter_id')
        is_image = 0
        image_url = ''
        image_describe = ''
        is_audio = 0
        audio_url = ''
        audio_describe = ''
        if data['image']:
            is_image = 1
            cos_client = COSClient()
            image_url = cos_client.upload_base64_image(data['image'])
            # 原调用方式：image_describe = qwen_vl_recognize(image_url)
            image_describe = vl_chain.invoke(image_url)  # 使用LangChain调用

        if data['audio']:
            is_audio = 1
            cos_client = COSClient()
            audio_url = cos_client.upload_base64_audio(data['audio'])
            # 原调用方式：audio_describe = qwen_audio_recognize(audio_url)
            audio_describe = audio_chain.invoke(audio_url)  # 使用LangChain调用

        words = data.get('words')

        # 添加处理 comprehension_level
        comprehension_level = data.get('comprehension_level', '理解')  # 获取理解程度，默认为"理解"

        # 获取章节和用户信息
        chapter = NotesChapter.query.get(chapter_id)
        user = User.query.get(chapter.user_id)

        # 更新用户的笔记计数
        user.notes_count += 1
        
        # 根据理解程度更新对应的计数
        if comprehension_level == '理解':
            user.clear_notes_count += 1
        elif comprehension_level == '模糊':
            user.vague_notes_count += 1
        elif comprehension_level == '不理解':
            user.unclear_notes_count += 1

        # 更新章节的笔记计数
        chapter.notes_count = len([n for n in chapter.notes if not n.is_deleted]) + 1

        note = Note(
            chapter_id=chapter_id,
            is_image=is_image,
            image_url=image_url,
            image_describe=image_describe,
            is_audio=is_audio,
            audio_url=audio_url,
            audio_describe=audio_describe,
            words=words,
            comprehension_level=comprehension_level  # 添加理解程度字段
        )
        db.session.add(note)
        db.session.commit()

        return jsonify({
            'code': 1,
            'msg': '创建成功',
            'data': {
                'note_id': note.note_id,
                'comprehension_level': note.comprehension_level  # 返回理解程度
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 0,
            'msg': f'创建失败: {str(e)}'
        }), 500


# 获取章节下的所有笔记
@notes_bp.route('/note/list/<int:chapter_id>', methods=['GET'])
def get_notes(chapter_id):
    try:
        notes = Note.query.filter_by(
            chapter_id=chapter_id,
            is_deleted=False
        ).order_by(Note.created_at).all()

        result = [{
            'note_id': note.note_id,
            'is_image': note.is_image,
            'image_url': note.image_url,
            'image_describe': note.image_describe,
            'is_audio': note.is_audio,
            'audio_url': note.audio_url,
            'audio_describe': note.audio_describe,
            'words': note.words,
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'comprehension_level': note.comprehension_level  # 添加理解程度
        } for note in notes]

        return jsonify({
            'msg': '获取成功',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'code': 0,
            'msg': f'获取失败: {str(e)}'
        }), 500


# 编辑笔记
@notes_bp.route('/note/edit/<int:note_id>', methods=['PUT'])
def edit_note(note_id):
    try:
        note = Note.query.get_or_404(note_id)
        data = request.get_json()

        # 修改edit_note中的调用
        if data['image']:
            note.is_image = 1
            cos_client = COSClient()
            note.image_url = cos_client.upload_base64_image(data['image'])
            # 原调用方式：note.image_describe = qwen_vl_recognize(note.image_url)
            note.image_describe = vl_chain.invoke(note.image_url)
        if 'is_audio' in data:
            note.is_audio = data['is_audio']
        if 'audio_url' in data:
            note.audio_url = data['audio_url']
        if 'audio_describe' in data:
            note.audio_describe = data['audio_describe']
        if 'words' in data:
            note.words = data['words']

        # 添加处理 comprehension_level
        if 'comprehension_level' in data:
            note.comprehension_level = data['comprehension_level']

        db.session.commit()

        return jsonify({
            'code': 1,
            'msg': '更新成功',
            'data': {
                'comprehension_level': note.comprehension_level  # 返回更新后的理解程度
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 0,
            'msg': f'更新失败: {str(e)}'
        }), 500


# 删除笔记
@notes_bp.route('/note/delete/<int:note_id>', methods=['PUT'])
def delete_note(note_id):
    try:
        note = Note.query.get_or_404(note_id)
        note.is_deleted = True

        # 获取章节和用户信息
        chapter = NotesChapter.query.get(note.chapter_id)
        user = User.query.get(chapter.user_id)

        # 更新用户的笔记计数
        user.notes_count = max(0, user.notes_count - 1)

        # 根据理解程度更新对应的计数
        if note.comprehension_level == '理解':
            user.clear_notes_count = max(0, user.clear_notes_count - 1)
        elif note.comprehension_level == '模糊':
            user.vague_notes_count = max(0, user.vague_notes_count - 1)
        elif note.comprehension_level == '不理解':
            user.unclear_notes_count = max(0, user.unclear_notes_count - 1)

        # 更新章节的笔记计数
        if chapter:
            chapter.notes_count = len([n for n in chapter.notes if not n.is_deleted])

        db.session.commit()

        return jsonify({
            'code': 1,
            'msg': '删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 0,
            'msg': f'删除失败: {str(e)}'
        }), 500


# 获取所有笔记分类
@notes_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    try:
        categories = NoteCategory.query.filter_by(is_deleted=False).all()

        result = [{
            'category_id': category.category_id,
            'name': category.name,
            'description': category.description
        } for category in categories]

        return jsonify({
            'msg': '获取成功',
            'data': result
        }), 200

    except Exception as e:
        print(f"Error in get_categories: {str(e)}")  # 添加日志
        return jsonify({
            'msg': f'获取失败: {str(e)}'
        }), 500


@notes_bp.route('/notes/weekly', methods=['GET'])
@jwt_required()
def get_weekly_notes():
    try:
        user_id = get_jwt_identity()
        # 获取最近7天的时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)

        # 查询该时间范围内的笔记
        notes = Note.query.join(NotesChapter).filter(
            NotesChapter.user_id == user_id,
            Note.is_deleted == False,
            Note.created_at >= start_date,
            Note.created_at <= end_date
        ).all()

        # 转换为JSON格式
        notes_data = [{
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for note in notes]

        return jsonify(notes_data), 200

    except Exception as e:
        return jsonify({
            'msg': f'获取笔记数据失败: {str(e)}'
        }), 500


@notes_bp.route('/note/search', methods=['GET'])
@jwt_required()
def search_notes():
    try:
        current_user_id = get_jwt_identity()
        keyword = request.args.get('keyword', '')

        if not keyword:
            return jsonify({
                'msg': '请输入搜索关键词',
                'data': []
            }), 400

        # 查找是否存在相同的搜索记录
        existing_history = SearchHistory.query.filter_by(
            user_id=current_user_id,
            keyword=keyword,
            is_deleted=False
        ).first()

        if existing_history:
            # 如果存在，更新创建时间
            existing_history.created_at = datetime.utcnow()
        else:
            # 如果不存在，创建新的搜索记录
            search_history = SearchHistory(
                user_id=current_user_id,
                keyword=keyword
            )
            db.session.add(search_history)

        db.session.commit()

        # 查询当前用户的所有章节
        user_chapters = NotesChapter.query.filter_by(
            user_id=current_user_id,
            is_deleted=False
        ).all()

        chapter_ids = [chapter.chapter_id for chapter in user_chapters]

        # 在用户的章节中搜索包含关键词的笔记
        notes = Note.query.filter(
            Note.chapter_id.in_(chapter_ids),
            Note.is_deleted == False,
            db.or_(
                Note.words.like(f'%{keyword}%'),
                Note.image_describe.like(f'%{keyword}%'),
                Note.audio_describe.like(f'%{keyword}%')
            )
        ).all()

        result = []
        for note in notes:
            chapter = NotesChapter.query.get(note.chapter_id)
            match_type = []

            if note.words and keyword in note.words:
                match_type.append('text')

            if note.image_describe and keyword in note.image_describe:
                match_type.append('image')

            if note.audio_describe and keyword in note.audio_describe:
                match_type.append('audio')

            result.append({
                'note_id': note.note_id,
                'chapter_id': note.chapter_id,
                'chapter_name': chapter.name,
                'is_image': note.is_image,
                'image_url': note.image_url,
                'image_describe': note.image_describe,
                'is_audio': note.is_audio,
                'audio_url': note.audio_url,
                'audio_describe': note.audio_describe,
                'words': note.words,
                'match_type': match_type,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify({
            'msg': '搜索成功',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'msg': f'搜索失败: {str(e)}',
            'data': []
        }), 500