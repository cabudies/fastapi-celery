import os
import time

from celery import Celery
import oscar_emr_docs_with_pin_login

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")


@celery.task(name="create_task")
def create_task(task_type):
    print("create_task task_type=======", task_type)
    
    process_emr_documents()

    print("oscar emr success returned back to worker file======")
    time.sleep(int(task_type) * 3)
    return True


def process_emr_documents():
    oscar_emr_docs_with_pin_login.start_emr_process()
