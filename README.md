# fastapi-celery
fastapi-celery


## commands to run

### 1. fastapi uvicorn

`uvicorn main:app --reload`

### 2. celery app

`celery -A worker.celery worker --pool=solo -l info --loglevel=info --logfile=logs/celery.log`

### 3. flower

`celery --broker=redis://127.0.0.1:6379/0 flower --port=5555`

