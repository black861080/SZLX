from flask import Blueprint, request, jsonify, stream_with_context, Response

from llm.qwen import vl_chain, textgen_stream_chain
from models.mistaken_question import MistakenQuestionList, MistakenQuestion
from models.token_usage import TokenUsage
from models.user import User
from utils.exts import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.cos_utils import COSClient
from functools import wraps
from time import sleep
from datetime import datetime
from models.search_history import SearchHistory

mistaken_question_bp = Blueprint('mistaken_question', __name__)

# 创建错题本
@mistaken_question_bp.route('/list/create', methods=['POST'])
@jwt_required()
def create_question_list():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        name = data.get('name')

        question_list = MistakenQuestionList(
            name=name,
            user_id=current_user_id
        )
        
        db.session.add(question_list)
        db.session.commit()

        return jsonify({
            'msg': '创建成功',
            'data': {
                'question_list_id': question_list.question_list_id,
                'name': question_list.name,
                'created_at': question_list.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'msg': f'创建失败: {str(e)}'
        }), 500

# 获取用户的所有错题本
@mistaken_question_bp.route('/list/all', methods=['GET'])
@jwt_required()
def get_question_lists():
    try:
        current_user_id = get_jwt_identity()
        lists = MistakenQuestionList.query.filter_by(
            user_id=current_user_id,
            is_deleted=False
        ).all()

        result = [{
            'question_list_id': lst.question_list_id,
            'name': lst.name,
            'count': lst.count,
            'created_at': lst.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for lst in lists]

        return jsonify({
            'msg': '获取成功',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'msg': f'获取失败: {str(e)}'
        }), 500

# 创建错题
@mistaken_question_bp.route('/question/create', methods=['POST'])
@jwt_required()
def create_question():
    try:
        data = request.get_json()
        question_list_id = data.get('question_list_id')
        content = data.get('content')
        
        is_image = False
        image_url = None
        image_describe = None

        if data.get('image'):
            is_image = True
            cos_client = COSClient()
            image_url = cos_client.upload_base64_image(data['image'])
            image_describe = vl_chain.invoke(image_url)

        question = MistakenQuestion(
            question_list_id=question_list_id,
            content=content,
            is_image=is_image,
            image_url=image_url,
            image_describe=image_describe,
        )

        question_list = MistakenQuestionList.query.get(question_list_id)
        question_list.count += 1

        db.session.add(question)
        db.session.commit()

        return jsonify({
            'msg': '创建成功',
            'data': {
                'question_id': question.question_id
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'msg': f'创建失败: {str(e)}'
        }), 500

# 获取错题本中的所有错题
@mistaken_question_bp.route('/question/list/<int:question_list_id>', methods=['GET'])
@jwt_required()
def get_questions(question_list_id):
    try:
        questions = MistakenQuestion.query.filter_by(
            question_list_id=question_list_id,
            is_deleted=False
        ).order_by(MistakenQuestion.created_at).all()

        result = [{
            'question_id': q.question_id,
            'content': q.content,
            'answer': q.answer,
            'is_image': q.is_image,
            'image_url': q.image_url,
            'image_describe': q.image_describe,
            'similar_question': q.similar_question,
            'similar_answer': q.similar_answer,
            'created_at': q.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_favorite': q.is_favorite
        } for q in questions]

        return jsonify({
            'msg': '获取成功',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'msg': f'获取失败: {str(e)}'
        }), 500

# 删除错题本
@mistaken_question_bp.route('/list/delete/<int:question_list_id>', methods=['PUT'])
@jwt_required()
def delete_question_list(question_list_id):
    try:
        question_list = MistakenQuestionList.query.get_or_404(question_list_id)
        
        # 标记所有相关的错题为已删除
        questions = MistakenQuestion.query.filter_by(
            question_list_id=question_list_id,
            is_deleted=False
        ).all()
        
        for question in questions:
            question.is_deleted = True
            
        question_list.is_deleted = True
        question_list.count = 0
        
        db.session.commit()
        return jsonify({'msg': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'删除失败: {str(e)}'}), 500

# 删除单个错题
@mistaken_question_bp.route('/question/delete/<int:question_id>', methods=['PUT'])
@jwt_required()
def delete_question(question_id):
    try:
        question = MistakenQuestion.query.get_or_404(question_id)
        question.is_deleted = True

        # 更新错题本的题目数量
        question_list = MistakenQuestionList.query.get(question.question_list_id)
        question_list.count = max(0, question_list.count - 1)

        db.session.commit()
        return jsonify({'msg': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'删除失败: {str(e)}'}), 500

@mistaken_question_bp.route('/question/edit/<int:chapter_id>', methods=['PUT'])
@jwt_required()
def edit_chapter(chapter_id):
    try:
        lst = MistakenQuestionList.query.get_or_404(chapter_id)
        data = request.get_json()

        if 'name' in data:
            lst.name = data['name']

        db.session.commit()

        return jsonify({
            'msg': '更新成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'msg': f'更新失败: {str(e)}'
        }), 500

@mistaken_question_bp.route('/question/edit/<int:question_id>', methods=['PUT'])
@jwt_required()
def edit_question(question_id):
    try:
        question = MistakenQuestion.query.get_or_404(question_id)
        data = request.get_json()

        if data['image']:
            question.is_image = 1
            cos_client = COSClient()
            question.image_url = cos_client.upload_base64_image(data['image'])
            question.image_describe = vl_chain.invoke(question.image_url)
        if data['content']:
            question.words = data['content']

        db.session.commit()

        return jsonify({
            'code': 1,
            'msg': '更新成功',
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 0,
            'msg': f'更新失败: {str(e)}'
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

@mistaken_question_bp.route('/question/update_answer/<int:question_id>', methods=['POST'])
@jwt_required()
def update_answer(question_id):
    try:
        current_user_id = get_jwt_identity()

        user = User.query.get(current_user_id)
        if not user or user.token_balance <= 0:
            return jsonify({"code": 0, "msg": "Token余额不足"}), 403

        question = MistakenQuestion.query.get_or_404(question_id)
        question_content = []
        if question.content:
            question_content.append(question.content)
        if question.image_describe:
            question_content.append(f"图片描述: {question.image_describe}")


        messages = [
            {"role": "system", "content": "你是一个习题助手。请你帮完成我给的习题。"},
            {"role": "user",
             "content": f"这是题目：\n" + "\n".join(question_content) + "\n请你给出这题的答案，尽量简练一点。"}
        ]

        @retry_on_failure(max_retries=3)
        def generate():
            answer_content = ""
            total_tokens = 0
            try:
                for chunk in textgen_stream_chain.invoke({'messages': messages}):
                    if chunk and 'output' in chunk:
                        content = chunk['output']['choices'][0].get('delta', {}).get('content', '')
                        if content:
                            answer_content += content
                            yield f"data: {content}\n\n"
                        if 'usage' in chunk:
                            total_tokens = chunk['usage'].get('total_tokens', 0)

                try:
                    today = datetime.utcnow().date()
                    token_usage = TokenUsage.query.filter(
                        TokenUsage.user_id == current_user_id,
                        db.func.date(TokenUsage.created_at) == today
                    ).first()

                    if total_tokens > 0:
                        if token_usage:
                            token_usage.spand += total_tokens
                        else:
                            token_usage = TokenUsage(
                                user_id=current_user_id,
                                spand=total_tokens
                            )
                            db.session.add(token_usage)

                        user.token_balance -= total_tokens

                    question.answer = answer_content
                    db.session.commit()

                except Exception as e:
                    print(f"保存数据到数据库时出错: {str(e)}")
                    db.session.rollback()

                yield "data: [DONE]\n\n"
            except Exception as e:
                print(f"生成总结时出错: {str(e)}")
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
        print(f"生成答案失败: {str(e)}")
        return jsonify({'message': f'生成答案失败: {str(e)}'}), 500

@mistaken_question_bp.route('/question/update_similar_answer/<int:question_id>', methods=['POST'])
@jwt_required()
def update_similar_answer(question_id):
    try:
        current_user_id = get_jwt_identity()

        user = User.query.get(current_user_id)
        if not user or user.token_balance <= 0:
            return jsonify({"code": 0, "msg": "Token余额不足"}), 403

        question = MistakenQuestion.query.get_or_404(question_id)
        if not question.similar_question:
            return jsonify({"code": 0, "msg": "请先生成题目"}), 404

        question_content = []
        question_content.append(question.similar_question)

        messages = [
            {"role": "system", "content": "你是一个习题助手。请你帮完成我给的习题。"},
            {"role": "user",
             "content": f"这是题目：\n" + "\n".join(question_content) + "\n请你给出这题的答案，尽量简练一点。"}
        ]

        @retry_on_failure(max_retries=3)
        def generate():
            answer_content = ""
            total_tokens = 0
            try:
                for chunk in textgen_stream_chain.invoke({'messages': messages}):
                    if chunk and 'output' in chunk:
                        content = chunk['output']['choices'][0].get('delta', {}).get('content', '')
                        if content:
                            answer_content += content
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
                        question.similar_answer = answer_content
                        db.session.commit()

                    yield f"data: [TOKENS:{total_tokens}]\n\n"
                    yield "data: [DONE]\n\n"

                except Exception as e:
                    print(f"保存数据到数据库时出错: {str(e)}")
                    db.session.rollback()
                    yield f"data: 保存token使用记录失败: {str(e)}\n\n"
                    yield "data: [DONE]\n\n"

            except Exception as e:
                print(f"生成答案时出错: {str(e)}")
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
        print(f"生成答案失败: {str(e)}")
        return jsonify({'message': f'生成答案失败: {str(e)}'}), 500

@mistaken_question_bp.route('/question/update_similar_question/<int:question_id>', methods=['POST'])
@jwt_required()
def update_similar_question(question_id):
    try:
        current_user_id = get_jwt_identity()

        user = User.query.get(current_user_id)
        if not user or user.token_balance <= 0:
            return jsonify({"code": 0, "msg": "Token余额不足"}), 403

        question = MistakenQuestion.query.get_or_404(question_id)
        question_content = []
        if question.content:
            question_content.append(question.content)
        if question.image_describe:
            question_content.append(f"图片描述: {question.image_describe}")

        messages = [
            {"role": "system", "content": "你是一个习题助手。我会给你一个原题，请你帮一道生成相似的题目。"},
            {"role": "user",
             "content": f"这是原题目题目：\n" + "\n".join(question_content) + "\n请你帮一道生成相似的题目，不需要给出答案。"}
        ]

        @retry_on_failure(max_retries=3)
        def generate():
            similar_question_content = ""
            total_tokens = 0
            try:
                for chunk in textgen_stream_chain.invoke({'messages': messages}):
                    if chunk and 'output' in chunk:
                        content = chunk['output']['choices'][0].get('delta', {}).get('content', '')
                        if content:
                            similar_question_content += content
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
                        question.similar_question = similar_question_content
                        db.session.commit()

                    yield f"data: [TOKENS:{total_tokens}]\n\n"
                    yield "data: [DONE]\n\n"

                except Exception as e:
                    print(f"保存数据到数据库时出错: {str(e)}")
                    db.session.rollback()
                    yield f"data: 保存token使用记录失败: {str(e)}\n\n"
                    yield "data: [DONE]\n\n"

            except Exception as e:
                print(f"生成答案时出错: {str(e)}")
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
        print(f"生成答案失败: {str(e)}")
        return jsonify({'message': f'生成答案失败: {str(e)}'}), 500

@mistaken_question_bp.route('/question/toggle_favorite/<int:question_id>', methods=['PUT'])
@jwt_required()
def toggle_favorite(question_id):
    try:
        question = MistakenQuestion.query.get_or_404(question_id)
        question.is_favorite = not question.is_favorite
        db.session.commit()
        
        return jsonify({
            'msg': '更新成功',
            'data': {
                'is_favorite': question.is_favorite
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'msg': f'更新失败: {str(e)}'
        }), 500

@mistaken_question_bp.route('/question/search', methods=['GET'])
@jwt_required()
def search_questions():
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

        # 查询当前用户的所有错题本
        user_question_lists = MistakenQuestionList.query.filter_by(
            user_id=current_user_id,
            is_deleted=False
        ).all()

        question_list_ids = [question_list.question_list_id for question_list in user_question_lists]

        # 在用户的错题本中搜索包含关键词的错题
        questions = MistakenQuestion.query.filter(
            MistakenQuestion.question_list_id.in_(question_list_ids),
            MistakenQuestion.is_deleted == False,
            db.or_(
                MistakenQuestion.content.like(f'%{keyword}%'),
                MistakenQuestion.answer.like(f'%{keyword}%'),
                MistakenQuestion.image_describe.like(f'%{keyword}%'),
                MistakenQuestion.similar_question.like(f'%{keyword}%'),
                MistakenQuestion.similar_answer.like(f'%{keyword}%')
            )
        ).all()

        result = []
        for question in questions:
            question_list = MistakenQuestionList.query.get(question.question_list_id)
            match_type = []

            if question.content and keyword in question.content:
                match_type.append('content')
            if question.answer and keyword in question.answer:
                match_type.append('answer')
            if question.image_describe and keyword in question.image_describe:
                match_type.append('image')
            if question.similar_question and keyword in question.similar_question:
                match_type.append('similar_question')
            if question.similar_answer and keyword in question.similar_answer:
                match_type.append('similar_answer')

            result.append({
                'question_id': question.question_id,
                'question_list_id': question.question_list_id,
                'question_list_name': question_list.name,
                'content': question.content,
                'answer': question.answer,
                'is_image': question.is_image,
                'image_url': question.image_url,
                'image_describe': question.image_describe,
                'similar_question': question.similar_question,
                'similar_answer': question.similar_answer,
                'match_type': match_type,
                'created_at': question.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_favorite': question.is_favorite
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