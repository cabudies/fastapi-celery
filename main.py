from fastapi import FastAPI
from fastapi import Body, FastAPI, Form, Request
from fastapi.responses import JSONResponse
from celery.result import AsyncResult
import os
import time
# from worker import create_task


from celery import Celery

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379")


@celery.task(name="create_task")
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    # time.sleep(int(task_type) * 4) ## sleeping the task for 4 seconds and then return true
    return True


app = FastAPI()


@app.get("/")
def index():
    return "hello world"


@app.post("/tasks", status_code=201)
def run_task(payload = Body(...)):
    task_type = payload["type"]
    task = create_task.delay(int(task_type))
    return JSONResponse({"task_id": task.id})


@app.get("/tasks/{task_id}")
def get_status(task_id):
    # task_result = AsyncResult(task_id)
    task_result = celery.AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JSONResponse(result)
