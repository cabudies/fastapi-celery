import os
import time

from celery import Celery


celery = Celery(__name__)
# celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
# celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")


@celery.task(name="create_task")
def create_task(task_type):
    # time.sleep(int(task_type) * 10)
    print("create_task task_type=======", task_type)
    time.sleep(int(task_type) * 3)
    return True
