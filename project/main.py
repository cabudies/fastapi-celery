from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
import os
import time
from js_scripts import JS_SCRIPT


from celery import Celery

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")


@celery.task(name="create_task")
def create_task(task_type):
    print("create_task task_type======", task_type)
    time.sleep(int(task_type) * 10)
    return True


app = FastAPI()


@app.get("/")
def index():
    return "hello world"


@app.post("/tasks", status_code=201)
def run_task(payload = Body(...)):
    print("payload=========", payload)
    task_type = payload["type"]
    task = create_task.delay(int(task_type))
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
