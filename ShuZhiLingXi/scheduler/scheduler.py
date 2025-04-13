from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging
from datetime import datetime, timedelta
from models.chat_history import ChatHistoryDetail
from models.notes import Note
from models.user import User
from llm.qwen import textgen_chain
from utils.exts import db

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.INFO)

scheduler = BackgroundScheduler()

def init_scheduler(app):
    """初始化调度器配置"""
    jobstores = {
        'default': SQLAlchemyJobStore(url=app.config['SQLALCHEMY_DATABASE_URI'])
    }
    executors = {
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(5)
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }
    
    scheduler.configure(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults
    )

def job_listener(event):
    if event.exception:
        print(f"Job {event.job_id} raised an exception: {event.exception}")
        logging.error(f"Job {event.job_id} failed: {str(event.exception)}")
    else:
        print(f"Job {event.job_id} executed successfully")
        logging.info(f"Job {event.job_id} executed successfully")

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

def update_user_profiles():
    try:
        users = User.query.filter_by(is_active=True).all()

        for user in users:
            try:
                now = datetime.utcnow()
                one_day_ago = now - timedelta(days=1)
                chat_records = ChatHistoryDetail.query.filter(
                    ChatHistoryDetail.user_id == user.user_id,
                    ChatHistoryDetail.created_at >= one_day_ago
                ).all()

                notes = Note.query.filter(
                    Note.user_id == user.user_id,
                    Note.created_at >= one_day_ago
                ).all()

                profile = user.profile or "无"
                chat_content = "\n".join([record.words for record in chat_records if record.words])
                note_content = "\n".join([note.words for note in notes if note.words])

                # 构建消息
                messages = [
                    {"role": "system", "content": "你是一个智能助手，根据用户提供的信息更新其人物画像(120字左右)。"},
                    {"role": "user", "content": f"当前用户画像：{profile}"},
                    {"role": "user", "content": f"最近24小时聊天记录：{chat_content}"},
                    {"role": "user", "content": f"最近24小时笔记：{note_content}"},
                    {"role": "user", "content": "请根据以上信息更新用户画像，总结出用户的特点，例如：用户擅长数学，喜欢历史等。"}
                ]

                # 调用大模型
                response = textgen_chain.invoke({'messages': messages})
                new_profile = response['output']['text']

                # 更新用户画像
                user.profile = new_profile
                db.session.commit()

                logging.info(f"Updated profile for user {user.user_id}: {new_profile}")

            except Exception as e:
                logging.error(f"Error updating profile for user {user.user_id}: {str(e)}")
                db.session.rollback()
                continue

    except Exception as e:
        logging.error(f"Error in update_user_profiles: {str(e)}")
        db.session.rollback()

def add_periodic_tasks():
    try:
        # 每天凌晨更新用户画像
        scheduler.add_job(
            update_user_profiles,
            'cron',
            hour=0,
            minute=0,
            id='update_user_profiles',
            replace_existing=True
        )
        logging.info("Successfully added periodic tasks")
    except Exception as e:
        logging.error(f"Error adding periodic tasks: {str(e)}")

def start_scheduler(app):
    """启动调度器"""
    with app.app_context():
        try:
            init_scheduler(app)
            scheduler.start()
            add_periodic_tasks()
            logging.info("Scheduler started successfully")
        except Exception as e:
            logging.error(f"Error starting scheduler: {str(e)}")
            raise

def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logging.info("Scheduler shutdown successfully")
