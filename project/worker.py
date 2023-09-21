import os
import time

from celery import Celery
import oscar_emr_docs_with_pin_login

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")


@celery.task(name="create_task")
def create_task(task_type, oscar_login_details: dict):
    print("create_task task_type received inside worker=======", task_type)
    print("create_task oscar_login_details received inside worker=======", oscar_login_details)
    
    process_emr_documents(oscar_login_details=oscar_login_details)

    print("oscar emr success returned back to worker file======")
    time.sleep(int(task_type) * 3)
    return True


def process_emr_documents(oscar_login_details: dict):
    oscar_emr_docs_with_pin_login.start_emr_process(oscar_login_details=oscar_login_details)
