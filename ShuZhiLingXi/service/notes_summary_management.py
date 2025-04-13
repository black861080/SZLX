from flask import Blueprint, jsonify, Response
from flask_cors import CORS

from flask_jwt_extended import jwt_required, get_jwt_identity
from models.notes import KnowledgeGraph, KnowledgeItem, KnowledgeRelation, Note, NotesChapter, NoteSummary
from models.token_usage import TokenUsage
from models.user import User
from utils.exts import db
from llm.qwen import textgen_chain, textgen_stream_chain
from flask import stream_with_context
from time import sleep
from functools import wraps
from datetime import datetime
from utils.redis_utils import RedisUtils

knowledge_graph_bp = Blueprint('knowledge_graph', __name__)

CORS(knowledge_graph_bp, resources={
    r"/*": {
        "origins": ["http://localhost:5173"],
        "supports_credentials": True,
        "methods": ["POST", "GET", "OPTIONS"]
    }
})


@knowledge_graph_bp.route('/knowledge_graph/generate/<int:chapter_id>', methods=['POST'])
@jwt_required()
def generate_knowledge_graph(chapter_id):
    try:
        current_user_id = get_jwt_identity()

        # 检查用户token余额
        user = User.query.get(current_user_id)
        if not user or user.token_balance <= 0:
            return jsonify({"code": 0, "msg": "Token余额不足"}), 403

        # 检查章节是否存在且属于当前用户
        chapter = NotesChapter.query.filter_by(
            chapter_id=chapter_id,
            user_id=current_user_id,
            is_deleted=False
        ).first()

        if not chapter:
            return jsonify({
                'msg': '章节不存在或无权访问'
            }), 404

        # 删除已存在的知识图谱及其相关数据
        existing_graph = KnowledgeGraph.query.filter_by(
            chapter_id=chapter_id,
            is_deleted=False
        ).first()

        if existing_graph:
            # 删除相关的关系
            KnowledgeRelation.query.filter_by(
                knowledge_graph_id=existing_graph.knowledge_graph_id
            ).update({'is_deleted': True})

            # 删除相关的节点
            KnowledgeItem.query.filter_by(
                knowledge_graph_id=existing_graph.knowledge_graph_id
            ).update({'is_deleted': True})

            # 删除知识图谱
            existing_graph.is_deleted = True
            db.session.flush()

        notes = Note.query.filter_by(
            chapter_id=chapter_id,
            is_deleted=False
        ).all()

        if not notes:
            return jsonify({
                'msg': '该章节没有笔记内容'
            }), 400

        # 构建笔记内容列表
        notes_content = []
        for note in notes:
            content = []
            if note.words:
                content.append(note.words)
            if note.image_describe:
                content.append(f"图片描述: {note.image_describe}")
            if note.audio_describe:
                content.append(f"音频描述: {note.audio_describe}")
            notes_content.append(" ".join(content))

        # 原提示词部分修改为：
        messages = [
            {"role": "system", "content": f"你是一个专业的知识图谱构建助手。请根据用户提供的笔记内容，提取"
                                          f"关键概念和进行一定并构建知识图谱。输出格式应为JSON，包含items(节点)和relations(关系)两个数组。"},
            {"role": "user", "content": f"""
                                        请根据以下笔记内容构建知识图谱(你要找到item之间的关系，如果这两个item的关系是"无关"，你不必要输出他们的关系，避免存储的浪费):
                                        {' '.join(notes_content)}

                                        请以如下JSON格式返回（不得输出"根据您提供的笔记内容"等多余废话，否则会导致后端解析失败）:
                                        {{
                                            "items": [
                                                {{"name": "概念名称", "description": "概念描述"}}
                                            ],
                                            "relations": [
                                                {{"item_a": "概念A", "item_b": "概念B", "relation_type": "关系类型"}}
                                            ]
                                        }}
                                        "请严格确保：\n"
                                        "1. JSON格式合法，无重复键\n"
                                        "2. relations中的item_a/item_b必须在items中存在\n"
                                        "3. 描述字段用双引号包裹"
                                        """}
        ]

        response = textgen_chain.invoke({'messages': messages})

        try:
            graph_data = response['output']['text']
        except KeyError as e:
            raise Exception(f"API返回格式异常: {str(e)}")

        # 记录token使用情况
        total_tokens = response.get('usage', {}).get('total_tokens', 0)
        try:
            # 获取今天的token使用记录
            today = datetime.utcnow().date()
            token_usage = TokenUsage.query.filter(
                TokenUsage.user_id == current_user_id,
                db.func.date(TokenUsage.created_at) == today
            ).first()

            if token_usage:
                token_usage.spand += total_tokens
            else:
                token_usage = TokenUsage(
                    user_id=current_user_id,
                    spand=total_tokens
                )
                db.session.add(token_usage)

            # 更新用户token余额
            user.token_balance -= total_tokens

        except Exception as e:
            print(f"保存token使用记录到数据库时出错: {str(e)}")
            db.session.rollback()

        # 解析返回的JSON数据
        graph_data = eval(graph_data)

        # 创建知识图谱
        try:
            # 创建知识图谱
            knowledge_graph = KnowledgeGraph(chapter_id=chapter_id)
            db.session.add(knowledge_graph)
            db.session.flush()

            # 创建节点
            items_map = {}  # 用于存储节点名称到ID的映射
            for item in graph_data['items']:
                knowledge_item = KnowledgeItem(
                    knowledge_graph_id=knowledge_graph.knowledge_graph_id,
                    name=item['name'],
                    description=item['description']
                )
                db.session.add(knowledge_item)
                db.session.flush()
                items_map[item['name']] = knowledge_item.knowledge_item_id

            # 创建关系
            for relation in graph_data['relations']:
                knowledge_relation = KnowledgeRelation(
                    knowledge_graph_id=knowledge_graph.knowledge_graph_id,
                    item_a_id=items_map[relation['item_a']],
                    item_b_id=items_map[relation['item_b']],
                    relation_type=relation['relation_type']
                )
                db.session.add(knowledge_relation)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"数据库操作失败: {str(e)}")
            return jsonify({'msg': '知识图谱生成失败: 数据库操作错误'}), 500

        items = KnowledgeItem.query.filter_by(
            knowledge_graph_id=knowledge_graph.knowledge_graph_id
        ).all()
        relations = KnowledgeRelation.query.filter_by(
            knowledge_graph_id=knowledge_graph.knowledge_graph_id
        ).all()

        # 构建返回数据
        items_data = [{
            'id': item.knowledge_item_id,
            'name': item.name,
            'description': item.description
        } for item in items]

        relations_data = [{
            'id': relation.knowledge_relation_id,
            'source': relation.item_a_id,
            'target': relation.item_b_id,
            'relation_type': relation.relation_type
        } for relation in relations]

        return jsonify({
            'msg': '知识图谱生成成功',
            'data': {
                'knowledge_graph_id': knowledge_graph.knowledge_graph_id,
                'items': items_data,
                'relations': relations_data,
                'created_at': knowledge_graph.created_at.isoformat()
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'msg': f'知识图谱生成失败: {str(e)}'
        }), 500


def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise e
                    sleep(delay * retries)  # 指数退避
            return None

        return wrapper

    return decorator


@knowledge_graph_bp.route('/notes/summary/generate/<int:chapter_id>', methods=['POST'])
@jwt_required()
def generate_notes_summary(chapter_id):
    """生成笔记总结"""
    try:
        current_user_id = get_jwt_identity()

        # 检查用户token余额
        user = User.query.get(current_user_id)
        if not user or user.token_balance <= 0:
            return jsonify({"code": 0, "msg": "Token余额不足"}), 403

        notes = Note.query.filter_by(
            chapter_id=chapter_id,
            is_deleted=False
        ).all()

        if not notes:
            return jsonify({'message': '该章节没有笔记内容'}), 400

        # 构建笔记内容列表
        notes_content = []
        for note in notes:
            content = []
            if note.words:
                content.append(note.words)
            if note.image_describe:
                content.append(f"图片描述: {note.image_describe}")
            if note.audio_describe:
                content.append(f"音频描述: {note.audio_describe}")
            notes_content.append(" ".join(content))

        # 构建消息
        messages = [
            {"role": "system", "content": "你是一个专业的笔记总结助手。请帮助用户总结笔记要点，并保持逻辑清晰。"},
            {"role": "user", "content": f"这是我的笔记内容：\n" + "\n".join(
                notes_content) + "\n请帮我总结这些笔记的主要内容，要点和关键信息。"}
        ]

        @retry_on_failure(max_retries=3)
        def generate():
            summary_content = ""
            total_tokens = 0
            try:
                for chunk in textgen_stream_chain.invoke({'messages': messages}):
                    if chunk and 'output' in chunk:
                        content = chunk['output']['choices'][0].get('delta', {}).get('content', '')
                        if content:
                            summary_content += content
                            yield f"data: {content}\n\n"
                        # 从最后一个chunk获取token使用量
                        if 'usage' in chunk:
                            total_tokens = chunk['usage'].get('total_tokens', 0)

                try:
                    # 只在获取到token使用量时更新数据库
                    if total_tokens > 0:
                        today = datetime.utcnow().date()
                        token_usage = TokenUsage.query.filter(
                            TokenUsage.user_id == current_user_id,
                            db.func.date(TokenUsage.created_at) == today
                        ).first()

                        if token_usage:
                            token_usage.spand += total_tokens
                        else:
                            token_usage = TokenUsage(
                                user_id=current_user_id,
                                spand=total_tokens
                            )
                            db.session.add(token_usage)

                        user.token_balance -= total_tokens
                        
                        # 保存总结到数据库
                        note_summary = NoteSummary(
                            chapter_id=chapter_id,
                            summary=summary_content
                        )
                        db.session.add(note_summary)
                        
                        # 提交事务
                        db.session.commit()

                    yield f"data: [TOKENS:{total_tokens}]\n\n"
                    yield "data: [DONE]\n\n"

                except Exception as e:
                    print(f"保存数据到数据库时出错: {str(e)}")
                    db.session.rollback()
                    yield f"data: 保存token使用记录失败: {str(e)}\n\n"
                    yield "data: [DONE]\n\n"

            except Exception as e:
                print(f"生成总结时出错: {str(e)}")
                db.session.rollback()
                yield f"data: 生成失败: {str(e)}\n\n"
                yield "data: [DONE]\n\n"

        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true'
            }
        )

    except Exception as e:
        print(f"生成笔记总结失败: {str(e)}")
        return jsonify({'message': f'生成笔记总结失败: {str(e)}'}), 500


@knowledge_graph_bp.route('/notes/summary/get/<int:chapter_id>', methods=['GET'])
@jwt_required()
def get_notes_summary(chapter_id):
    """获取已存在的笔记总结"""
    try:
        current_user_id = get_jwt_identity()

        # 尝试从Redis缓存获取笔记总结
        redis_utils = RedisUtils()
        cached_summary = redis_utils.get_notes_summary_cache(chapter_id)
        if cached_summary:
            return jsonify({
                'msg': '获取成功',
                'summary': cached_summary['summary'],
                'created_at': cached_summary['created_at']
            }), 200

        # 先检查章节是否存在且属于当前用户
        chapter = NotesChapter.query.filter_by(
            chapter_id=chapter_id,
            user_id=current_user_id,
            is_deleted=False
        ).first()

        if not chapter:
            return jsonify({
                'msg': '章节不存在或无权访问',
                'summary': '',
                'created_at': ''
            }), 404

        summary = NoteSummary.query.filter_by(
            chapter_id=chapter_id,
            is_deleted=False
        ).first()

        if not summary:
            return jsonify({
                'msg': '暂无笔记总结',
                'summary': '',
                'created_at': ''
            }), 200

        summary_data = {
            'summary': summary.summary,
            'created_at': summary.created_at.isoformat() if summary.created_at else ''
        }

        # 缓存笔记总结
        redis_utils.set_notes_summary_cache(chapter_id, summary_data)

        return jsonify({
            'msg': '获取成功',
            'summary': summary_data['summary'],
            'created_at': summary_data['created_at']
        }), 200

    except Exception as e:
        print(f"获取笔记总结时出错: {str(e)}")
        return jsonify({
            'msg': f'获取笔记总结失败: {str(e)}',
            'summary': '',
            'created_at': ''
        }), 500


@knowledge_graph_bp.route('/knowledge_graph/get/<int:chapter_id>', methods=['GET'])
@jwt_required()
def get_knowledge_graph(chapter_id):
    """获取知识图谱及其相关的节点和关系"""
    try:
        current_user_id = get_jwt_identity()

        # 检查章节是否存在且属于当前用户
        chapter = NotesChapter.query.filter_by(
            chapter_id=chapter_id,
            user_id=current_user_id,
            is_deleted=False
        ).first()

        if not chapter:
            return jsonify({
                'msg': '章节不存在或无权访问'
            }), 404

        # 查询知识图谱
        knowledge_graph = KnowledgeGraph.query.filter_by(
            chapter_id=chapter_id,
            is_deleted=False
        ).first()

        if not knowledge_graph:
            return jsonify({
                'msg': '该章节暂无知识图谱',
                'data': None
            }), 200

        # 查询所有相关的节点和关系
        items = KnowledgeItem.query.filter_by(
            knowledge_graph_id=knowledge_graph.knowledge_graph_id,
            is_deleted=False
        ).all()

        relations = KnowledgeRelation.query.filter_by(
            knowledge_graph_id=knowledge_graph.knowledge_graph_id,
            is_deleted=False
        ).all()

        # 构建返回数据
        items_data = [{
            'id': item.knowledge_item_id,
            'name': item.name,
            'description': item.description
        } for item in items]

        relations_data = [{
            'id': relation.knowledge_relation_id,
            'source': relation.item_a_id,
            'target': relation.item_b_id,
            'relation_type': relation.relation_type
        } for relation in relations]

        return jsonify({
            'msg': '获取成功',
            'data': {
                'knowledge_graph_id': knowledge_graph.knowledge_graph_id,
                'items': items_data,
                'relations': relations_data,
                'created_at': knowledge_graph.created_at.isoformat()
            }
        }), 200

    except Exception as e:
        return jsonify({
            'msg': f'获取知识图谱失败: {str(e)}'
        }), 500

