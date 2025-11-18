"""
Celery worker for payment and subscription expiration checking
"""
import datetime
from typing import List
from celery import Celery
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from eApp.config import CONFIG
from eApp.database import connection_string
from eApp.models import Subscription, User
from asgiref.sync import async_to_sync

# Celery app for payment tasks
celery_app_payment = Celery(
    "payment_email",
    broker=CONFIG.REDIS_URL,  # Database 0: Celery Tasks (Queue)
    backend=CONFIG.REDIS_CACHE_URL  # Database 2: Celery Results + App Cache
)

# Data serializer ip/op
celery_app_payment.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Additional parameter for production
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
    # for sending email we don't need to cache, delete cache after 5 mins:
    result_expires=300,
    result_backend_always_retry=True
)


@celery_app_payment.task(name="send_email_task", ignore_result=True)
def send_email_task(recip: List[str], sub: str, html: str):
    """Send email task"""
    from eApp.email_verification import send_html_email
    async_to_sync(send_html_email)(recip, sub, html)


# <--------------Celery Beats---------------->
# Celery Worker only do the work
# Celery beats is a scheduler that can assign a work after a fix interval of time:
celery_app_payment.conf.beat_schedule = {
    'check_expire_subscriptions': {
        'task': 'check_expired_subscriptions',
        'schedule': 30.0,  # After 30 seconds: scheduling after 30sec
    },
}

# For celery we need synchronous database
# Convert SQLite URL to work with sync engine
sync_engine = create_engine(CONFIG.DATABASE_URL.replace("asyncpg", "psycopg2"))
SyncSession = sessionmaker(bind=sync_engine)


@celery_app_payment.task(name="check_expired_subscriptions")
def check_expired_subscriptions():
    """Check and handle expired subscriptions"""
    def _check_expired():
        with SyncSession() as session:
            try:
                current_time = func.now()
                batch_size = 100
                page = 0
                print(f"checking subcription at: {current_time}")
                
                #use database index and find those person subcriptions is active:
                expire_subs = session.execute(
                              text(""" 
                                   SELECT s.id, s.user_id, u.email, u.username
                                   FROM chatbot.subcriptions s
                                   JOIN chatbot.user u ON s.user_id = u.id
                                   WHERE s.status = 'active' 
                                   AND s.subscription_expires_at < NOW()
                                   LIMIT 100
                            """)
                        ).fetchall()
                
                # If we have no data:
                if not expire_subs:
                    print("<------------------------->")
                    print("no subscriptions has expired")
                    print("<------------------------->")
                    return
                
                print(f"expire_subscriptions_total_user: {len(expire_subs)}")
                
                # Process each subscription:
                for sub_id, user_id, user_email, username in expire_subs:
                    handle_single_subscription(session, sub_id, user_id, user_email, username)
                
                session.commit()
                print(f"successfully process expire_subscriptions_total_user: {len(expire_subs)}")
            except Exception as e:
                print(f"couldn't check subscriptions status: {str(e)}")
                session.rollback()
    
    _check_expired()


def handle_single_subscription(session, sub_id, user_id, user_email, username):
    """
    Handle single expired subscription:
    - Database update
    - Email Sent
    """
    try:
        print(f"Processing subscription id:{sub_id} user id: {user_id}")
        
        # Update subscription status
        session.execute(text("""
            UPDATE subscriptions 
            SET status = 'expired' 
            WHERE id = :sub_id
        """), {'sub_id': sub_id})
        
        # Update user paid_status
        session.execute(text("""
            UPDATE users 
            SET paid_status = false 
            WHERE id = :user_id
        """), {'user_id': user_id})
        
        # Send email
        from eApp.internal.html_templates import payment_subscription_expired
        html = payment_subscription_expired(
            subscription_expires_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            username=username
        )
        
        sub = "Your Subscription has Expired"
        res = send_email_task.delay([user_email], sub, html)
        print(f"Email task id: {res.id}, state: {res.state}")
        
    except Exception as e:
        print(f"Error processing subscription: {sub_id} error in {str(e)}")


"""
Run separately for production:
# Worker: concurrency-1 would be best i think.
celery -A eApp.worker.celery_task_payment.celery_app_payment worker --loglevel=info --concurrency=1
# Beat
celery -A eApp.worker.celery_task_payment.celery_app_payment beat --loglevel=info
"""

