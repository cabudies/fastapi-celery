from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
import os
import time
from celery import Celery
from worker import create_task


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")


# @celery.task(name="create_task")
# def create_task(task_type):
#     print("create_task task_type======", task_type)
#     time.sleep(int(task_type) * 10)
#     return True


app = FastAPI()


@app.get("/")
def index():
    return "hello world"


@app.post("/tasks", status_code=201)
def run_task(payload = Body(...)):
    task_type = payload["type"]
    oscar_login_partner_id = payload["oscar_login_partner_id"]
    oscar_login_url = payload["oscar_login_url"]
    oscar_login_username = payload["oscar_login_username"]
    oscar_login_password = payload["oscar_login_password"]
    oscar_login_pin = payload["oscar_login_pin"]
    oscar_login_via_pin = payload["oscar_login_via_pin"]
    oscar_files_dump_gcp_bucket_name = payload["oscar_files_dump_gcp_bucket_name"]
    oscar_files_dump_gcp_folder_name = payload["oscar_files_dump_gcp_folder_name"]
    oscar_files_dump_gcp_sub_folder_name = payload["oscar_files_dump_gcp_sub_folder_name"]
    number_of_patients_to_be_processed = payload["number_of_patients_to_be_processed"]

    # task = create_task.delay(int(task_type))

    task = create_task.apply_async(
        kwargs={
            "task_type": task_type,
            "oscar_login_details": {
                "oscar_login_partner_id": oscar_login_partner_id,
                "oscar_login_url": oscar_login_url,
                "oscar_login_username": oscar_login_username,
                "oscar_login_password": oscar_login_password,
                "oscar_login_pin": oscar_login_pin,
                "oscar_login_via_pin": oscar_login_via_pin,
                "oscar_files_dump_gcp_bucket_name": oscar_files_dump_gcp_bucket_name,
                "oscar_files_dump_gcp_folder_name": oscar_files_dump_gcp_folder_name,
                "oscar_files_dump_gcp_sub_folder_name": oscar_files_dump_gcp_sub_folder_name,
                "number_of_patients_to_be_processed": number_of_patients_to_be_processed
            }
        }
    )

    return JSONResponse({"task_id": task.id})


@app.get("/tasks/{task_id}")
def get_status(task_id):
    task_result = celery.AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }

    return JSONResponse(result)
