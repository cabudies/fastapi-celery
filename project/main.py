from fastapi import FastAPI
from fastapi import Body, FastAPI, Form, Request
from fastapi.responses import JSONResponse
from celery.result import AsyncResult
import os
import time
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from js_scripts import JS_SCRIPT

# from worker import create_task


from celery import Celery

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")
# celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
# celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


class OscarEmr:

    user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")

    def __init__(self):
        self.driver = self.get_deriver()

    def get_deriver(self):
        options = ChromeOptions()
        # if self.headless:
        #     options.add_argument("--headless=new")
        options.set_capability('unhandledPromptBehavior', 'accept')
        options.add_argument("--window-size=1920,1080")
        options.add_argument("start-maximized")
        options.add_argument(f'user-agent={self.user_agent}')
        options.add_argument("--disable-blink-features")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)

        options.add_experimental_option("prefs", {
            'download.default_directory': self.download_directory,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True
        })

        CHROME_DRIVER_PATH = "D:\Freelance\Phelix.ai\chromedriver_win32\chromedriver"

        driver = webdriver.Chrome(CHROME_DRIVER_PATH, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 1});")
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        driver.execute_script("Object.defineProperty(navigator.connection, 'rtt', {get: () => 100});")
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {
                "userAgent": driver.execute_script(
                    "return navigator.userAgent"
                ).replace("Headless", "")
            },
        )
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            JS_SCRIPT,
        )
        return driver

    '''
    1. login to the system
    2. click on patient and get demographic information
    3. go to process 2
    '''
    def process(self):
        print("inside process function=======")
        self.driver.get("https://release.blockhealth.co/")
        print("EMR_LOGIN_SUCCESS")
        

@celery.task(name="create_task")
def create_task(task_type):
    print("create_task task_type======", task_type)
    OscarEmr()
    time.sleep(int(task_type) * 10)
    # time.sleep(int(task_type) * 4) ## sleeping the task for 4 seconds and then return true
    return True


app = FastAPI()


@app.get("/")
def index():
    return "hello world"


@app.post("/tasks", status_code=201)
def run_task(payload = Body(...)):
    print("payload=========", payload)
    task_type = payload["type"]
    # task = create_task.delay(int(task_type))
    task = create_task.delay(int(task_type))
    return JSONResponse({"task_id": task.id})


@app.get("/tasks/{task_id}")
def get_status(task_id):
    # task_result = AsyncResult(task_id)
    task_result = celery.AsyncResult(task_id)
    print("task_result======", task_result)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    print("result=======", result)

    return JSONResponse(result)
