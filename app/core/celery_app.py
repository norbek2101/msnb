import os
from celery import Celery

celery = Celery(
    "worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    include=["app.tasks"]  
)

# celery.conf.task_routes = {
#     "app.tasks.send_email_task": "main-queue"
# }