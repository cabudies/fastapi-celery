# fastapi-celery
fastapi-celery


## commands to run

### 1. fastapi uvicorn

`uvicorn main:app --reload`

### 2. celery app

`celery -A main.celery worker --pool=solo --loglevel=info`

### 3. flower

`celery -A main.celery flower --port=5555`

