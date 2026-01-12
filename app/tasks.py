from asgiref.sync import async_to_sync
from app.core.email import send_verification_email
from app.core.celery_app import celery

@celery.task(name="app.tasks.send_email_task")
def send_email_task(email: str, code: str):
    async_to_sync(send_verification_email)(email, code, None)
    print("Task created")
    return f"Email sent to {email}"