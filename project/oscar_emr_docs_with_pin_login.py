import json
import os
import json
import copy
import time
import shutil
import string
import datetime
import traceback

from google.cloud import storage
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException
from dotenv import load_dotenv
from js_scripts import JS_SCRIPT
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
# import chromedriver_binary  # Adds chromedriver binary to path


load_dotenv()


CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
DOWNLOAD_PATH = os.path.join(CURRENT_PATH, 'download')
print("download_path==========", DOWNLOAD_PATH)
EMR_LOGIN_URL = os.getenv(
    "RPA_EMR_LOGIN_URL", "https://phelix.kai-oscar.com/oscar/index.jsp"
)
print(f"EMR_LOGIN_URL: {EMR_LOGIN_URL}")
RPA_EMR_PHELIX_ID = os.getenv('RPA_EMR_PHELIX_ID', '192')
print("RPA_EMR_PHELIX_ID=======", RPA_EMR_PHELIX_ID)
# CHROME_DRIVER_PATH = os.getenv(
#     "RPA_CHROME_DRIVER_PATH",
#     os.path.join(CURRENT_PATH, "chromedriver")
# )
CHROME_DRIVER_PATH = os.environ.get("RPA_CHROME_DRIVER_PATH", os.path.join(CURRENT_PATH, "chromedriver"))
print("CHROME_DRIVER_PATH==========", CHROME_DRIVER_PATH)
try:
    DOWNLOAD_LIMIT = int(os.getenv("DOWNLOAD_LIMIT", 25000))
except Exception:
    DOWNLOAD_LIMIT = 25000

try:
    DOCUMENT_DOWNLOAD_LIMIT = int(os.getenv("DOCUMENT_DOWNLOAD_LIMIT", 100))
except Exception:
    DOCUMENT_DOWNLOAD_LIMIT = 100

try:
    EXPECTED_DOCUMENT_TYPES_COUNT = int(os.getenv("EXPECTED_DOCUMENT_TYPES_COUNT", 50))
except Exception:
    EXPECTED_DOCUMENT_TYPES_COUNT = 50

STORAGE_BUCKET_NAME = os.getenv("RPA_STORAGE_BUCKET_NAME", 'scratch-bucket-1')
STORAGE_BUCKET_PATH = os.getenv("RPA_STORAGE_BUCKET_PATH", 'rpa-emr-oscar')
STORAGE_BUCKET_ROOT_PATH = os.getenv("STORAGE_BUCKET_ROOT_PATH", 'files')


# gcs = storage.Client()


class OscarEmr:

    user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")

    def __init__(self,
                 emr_login_url,
                 emr_id,
                 download_directory,
                 processed_patients_stored=None,
                 headless=True,
                 download_limit=10000,
                 file_downloaded=0,
                 download_type_records=None,
                 document_download_limit=100,
                 expected_document_type_count=50,
                 file_processed=0,
                 doc_create_start_date='2018-12-31'):
        """

        :param emr_login_url:
        :param emr_id:
        :param download_directory:
        :param processed_patients_stored:
        :param headless:
        :param download_limit:
        :param file_downloaded:
        """
        # acts as max no of patients to process
        self.counter = -100000
        self.file_downloaded = file_downloaded
        self.file_processed = file_processed
        self.download_time = 0
        self.download_limit = download_limit
        self.document_download_limit = document_download_limit
        self.expected_document_type_count = expected_document_type_count
        self.single_download_time_out = 180
        self.processed_patients_stored = processed_patients_stored or []
        self.download_type_records = download_type_records or {}
        self.processed_patients = []
        self.complete_processed_patients = []
        self.current_patients = []
        self.previous_patient_id = None
        self.previous_patient_relative_pos = None
        self.patient_table_initiated = False
        self.emr_login_url = emr_login_url
        self.emr_id = emr_id
        self.doc_create_start_date = doc_create_start_date
        # to support multiple emr instance of OscarEMR we have to
        # add subdomain part of the login url to download_directory
        self.download_directory = os.path.join(download_directory, self.emr_id)
        self.headless = headless
        self.prepare_download_directory()
        self.driver = self.get_deriver()

    def get_deriver(self):
        options = ChromeOptions()
        # if self.headless:
        #     options.add_argument("--headless=new")
        # options.add_argument("--headless=new")
        options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        options.add_argument("log-path=/app/chromedriver.log")
        options.add_argument('--disable-dev-shm-usage')
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

        # options.binary_location = '/usr/bin/chromium-browser' 

        # driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', options=options)
        # driver = webdriver.Chrome(executable_path='/app/chromedriver', options=options)
        driver = webdriver.Chrome(options=options)
        # driver = webdriver.Chrome(DesiredCapabilities.CHROME, options=options)

        # chrome_executable_path = os.getenv("PATH", "not found")
        # print("chrome_executable_path==========", chrome_executable_path)

        # # driver = webdriver.Chrome(CHROME_DRIVER_PATH, options=options)
        # from selenium.webdriver.chrome.service import Service
        # service = Service()
        # driver = webdriver.Chrome(service=service, options=options)
        # driver = webdriver.Chrome(executable_path='/app/chromedriver', options=options)
        
        # driver = webdriver.Remote(
        #     "http://localhost:4444/wd/hub", 
        #     DesiredCapabilities.CHROME, 
        #     options=options
        # )

        # from selenium.webdriver.remote.remote_connection import RemoteConnection

        # remote_driver = webdriver.Remote(
        #     RemoteConnection(remote_server_addr="http://localhost:4444/wd/hub"), 
        #     DesiredCapabilities.CHROME.copy(), 
        #     # options=options
        # )

        # # Cast the RemoteWebDriver to a ChromeDriver
        # driver = webdriver.Chrome(options=options)  # You can pass additional options if needed
        # # driver.command_executor = remote_driver.command_executor
        # # driver.session_id = remote_driver.session_id

        # # from selenium.webdriver.chrome.service import Service

        # # ser = Service()

        # from selenium.webdriver.chrome.service import Service
        # from webdriver_manager.chrome import ChromeDriverManager

        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # # driver.get("https://www.google.com")

        # # driver = webdriver.Chrome(options=options)
        # # import selenium.webdriver
        # # driver = selenium.webdriver.Chrome(options=options)

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
        search = self.emr_login()
        if search is None:
            print("EMR_LOGIN_FAILED=====")
            return
        print("EMR_LOGIN_SUCCESS========")
        return
        try:
            search.click()
        except ElementClickInterceptedException as err:
            print(f"ERROR: {type(err)}")
            try:
                # initial_pop_up = self.driver.find_element(
                #     By.XPATH, "//div/div/button[text()[contains(., 'Got it!')]]"
                # )
                initial_pop_up = self.driver.find_element(
                    By.XPATH, "//a[@title='Search for patient records']"
                )
                initial_pop_up.click()
                time.sleep(1)
                search.click()
            except Exception as err:
                print(f"error: {type(err)}")
        
        initial_pop_up = self.driver.find_element(
            By.XPATH, "//a[@title='Search for patient records']"
        )
        initial_pop_up.click()
        time.sleep(2)
        processed_patients_count = 0

        while True:
            if processed_patients_count > 5:
                break
            if self.download_limit and self.file_downloaded and self.file_processed > self.download_limit:
                print(f"file download limit {self.download_limit} "
                      f"crossed: {self.file_processed} - downloaded: {self.file_downloaded}")
                break
            if self.is_doc_type_limit_processed():
                print(f"doc_type_limit_processed: file_processed: downloaded: {self.file_downloaded}")
                break

            clicked_patient, demographic_info = self.click_on_patient()
            if self.previous_patient_relative_pos >= 9:
                print(f"counter: {self.counter}; previous_patient_id: {self.previous_patient_id}; "
                      f"previous_patient_relative_pos: {self.previous_patient_relative_pos}; "
                      f"current_patients: {len(self.current_patients)}")
            if not clicked_patient:
                break
            if self.previous_patient_id in self.processed_patients_stored:
                self.complete_processed_patients.append(self.previous_patient_id)
                continue

            if demographic_info:
                demographic_info.click()

            try:
                time.sleep(0.1)
                WebDriverWait(self.driver, 1).until(
                    EC.alert_is_present(),
                    'Timed out waiting demographic_info_click alert'
                )
                alert = self.driver.switch_to.alert
                alert.accept()
                time.sleep(0.5)
                print("####--------alert accepted------####")
            except TimeoutException as err:
                print(f"no_alert_is_ok: {err}")

            try:
                self.process_pop_up2()
            except Exception as err:
                print(f"process_pop_up2_error: {err}: {type(err)}")
                time.sleep(0.5)
                continue
            self.complete_processed_patients.append(self.previous_patient_id)
            time.sleep(0.2)
            processed_patients_count += 1
            # break

        time.sleep(1.5)
        self.driver.close()
        self.driver.quit()

    def click_on_patient(self):
        print("len(self.driver.window_handles)========", len(self.driver.window_handles))
        if len(self.driver.window_handles) < 2:
            print("POP-UP 1 not found")
            return None, None
        self.driver.switch_to.window(self.driver.window_handles[1])
        if not self.patient_table_initiated:
            print(f"patient_table_initiation ")
            pop_up_01_search = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='SUBMIT'][value='Search']"))
            )
            # print(pop_up_01_search.get_attribute("type"), pop_up_01_search.get_attribute("class"))
            pop_up_01_search.click()
            time.sleep(0.5)
            pop_up_01_search_results = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "searchResults"))
            )
            pop_up_01_demographic_td = pop_up_01_search_results.find_element(By.CSS_SELECTOR, "td[class='demoIdSearch']")
            pop_up_01_demographic_td.click()
            time.sleep(0.5)
            pop_up_01_search_results = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "searchResults"))
            )
            self.patient_table_initiated = True
            self.current_patients = pop_up_01_search_results.find_elements(By.TAG_NAME, "tr")[1:]
        elif (self.previous_patient_relative_pos + 1) >= len(self.current_patients):
            print(f"click_next->")
            pop_up_01_search_results = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "searchResults"))
            )
            # TODO: handle no next page for patients table
            # no such element: Unable to locate element:
            # {"method":"xpath","selector":"a[text()[contains(., "Next Page")]]"
            pop_up_01_search_results.find_element(By.XPATH, 'a[text()[contains(., "Next Page")]]').click()
            time.sleep(0.5)
            pop_up_01_search_results = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "searchResults"))
            )
            self.current_patients = pop_up_01_search_results.find_elements(By.TAG_NAME, "tr")[1:]

        current_patient, demographic_info = None, None
        if self.previous_patient_id is None and self.current_patients:
            current_patient = self.current_patients[0]
            self.previous_patient_relative_pos = 0
        elif self.previous_patient_id is not None and self.current_patients:
            if (self.previous_patient_relative_pos + 1) >= len(self.current_patients):
                print(f"previous_patient_relative_pos_check_counter: {self.counter}")
                if self.counter <= 0:
                    current_patient = self.current_patients[0]
                    self.counter += 1
                self.previous_patient_relative_pos = 0
            else:
                current_patient = self.current_patients[self.previous_patient_relative_pos + 1]
                self.previous_patient_relative_pos += 1
        if current_patient:
            try:
                demographic_info = current_patient.find_element(
                    By.CSS_SELECTOR, "td[class='demoIdSearch']"
                ).find_element(By.TAG_NAME, "a")
                self.previous_patient_id = demographic_info.text
                if self.previous_patient_id in self.processed_patients:
                    return None, None
                self.processed_patients.append(self.previous_patient_id)
                print(f"previous_patient_id: {self.previous_patient_id}")
            except:
                return None, None

        return current_patient, demographic_info

    '''
    1. find - MainTableLeftColumn
    2. click on documents from MainTableLeftColumn
    3. go to process 3
    '''
    def process_pop_up2(self):
        # selecting pop-up-2
        self.driver.switch_to.window(self.driver.window_handles[2])
        try:
            pop_up_02_main_left_column = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "td[class='MainTableLeftColumn']"))
            )
        except Exception as err:
            print(f"pop-up-2-availability-error: {err}: {type(err)}")
            if isinstance(err, UnexpectedAlertPresentException):
                try:
                    time.sleep(1.1)
                    print(f"sleep before alert handle")
                    alert = self.driver.switch_to.alert
                    alert.accept()
                    time.sleep(0.6)
                    print(f"<<<<--------alert accepted------>>>>*********")
                    pop_up_02_main_left_column = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "td[class='MainTableLeftColumn']"))
                    )
                except Exception as err:
                    print(f"error: {err}")
                    self.close_pop_up(2)
                    time.sleep(0.6)
                    return
            else:
                self.close_pop_up(2)
                time.sleep(0.5)
                return
        documents = pop_up_02_main_left_column.find_element(By.XPATH, '//a[text()[contains(., "Documents")]]')
        documents.click()
        time.sleep(0.6)
        self.process_pop_up3()
        # closing pop-up-2
        self.close_pop_up(2)
        time.sleep(0.1)

    '''
    1. find - privateDocs
    2. start getting documents from that tag
    3. make directory if not there
    4. iterate through documents:
        a. use process pop up 4 (for downloading the file)
        b. keep on updating the download time
    '''
    def process_pop_up3(self):
        # selecting pop-up-3
        self.driver.switch_to.window(self.driver.window_handles[3])
        # table id privateDocs
        try:
            pop_up_03_private_docs = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table[id='privateDocs']"))
            )
        except Exception as err:
            print(f"pop-up-3-availability-error: {err}: {type(err)}")
            # closing pop-up-3
            self.close_pop_up(3)
            return
        documents = pop_up_03_private_docs.find_elements(By.TAG_NAME, "tr")[1:]
        print(f"\ndocs_for: {self.previous_patient_id}: {len(documents)}")
        for idx, doc in enumerate(documents):
            doc_properties = doc.find_elements(By.TAG_NAME, "td")[1:]
            document_details = [doc_property.text for doc_property in doc_properties]
            print(document_details)
            if (document_details and document_details[0] and document_details[1].strip().lower() == 'pdf'
                    and self.process_file_name(document_details[2].strip())):
                date = datetime.datetime.strptime(document_details[5], '%Y-%m-%d').date()
                doc_type = self.process_file_name(document_details[2].strip())
                doc_download_count = self.download_type_records.get(doc_type) or 0
                self.file_processed += 1
                if (date > datetime.datetime.strptime(self.doc_create_start_date, '%Y-%m-%d').date()
                        and doc_download_count <= self.document_download_limit):
                    t1 = time.time()
                    self.prepare_download_directory()
                    time.sleep(1)
                    download_button = doc_properties[0].find_element(By.TAG_NAME, "a")
                    download_button.click()
                    time.sleep(0.3)
                    # self.process_pop_up4(
                    #     self.process_file_name(document_details[0].strip()),
                    #     doc_type=doc_type,
                    #     idx=idx
                    # )
                    self.process_pop_up4_for_local_storage(
                        self.process_file_name(document_details[0].strip()),
                        doc_type=doc_type,
                        idx=idx
                    )
                    self.driver.switch_to.window(self.driver.window_handles[3])
                    self.download_time += (time.time() - t1)
                    print(f"download time: {time.time() - t1}")
                else:
                    time.sleep(0.0001)
            else:
                time.sleep(0.0001)
            # break

        print("*" * 50)
        # closing pop-up-3
        self.close_pop_up(3)
        time.sleep(0.1)

    def is_download_dir_empty(self):
        return bool(
            [
                _ for _ in os.listdir(self.download_directory)
                if (not str(_).startswith('.') and not str(_).endswith('.crdownload'))
            ]
        )

    '''
    check if the file download is completed or not
    '''
    def is_file_download_completed(self):
        download_st = time.time()
        while not self.is_download_dir_empty() and (self.single_download_time_out > (time.time() - download_st)):
            time.sleep(0.1)
        return self.single_download_time_out > (time.time() - download_st)

    '''
    1. process the file name
    2. upload document on google cloud storage, print the public url and update the file downloaded count
    3. update the document type
    '''
    def process_pop_up4(
        self,
        file_name,
        doc_type,
        idx=0
    ):
        file_name = file_name or f"{int(time.time())}{idx}"
        self.driver.switch_to.window(self.driver.window_handles[4])
        print(f"waiting for download {time.time()}")
        file_download_completed = self.is_file_download_completed()
        time.sleep(0.4)
        self.close_pop_up(4)
        time.sleep(1.3)
        if not file_download_completed:
            print("download timeout")
            return False
        for filename in os.listdir(self.download_directory):
            file_path = os.path.join(self.download_directory, filename)
            print(f"file_path: {file_path}")
            with open(file_path, 'rb') as fh:
                data = fh.read()
            filename = self.file_name_parser(self.process_file_name(filename), idx)
            print("file details======", filename, doc_type, file_name)
            bucket_name = STORAGE_BUCKET_NAME
            print("bucket name==============", bucket_name)
            # bucket = gcs.get_bucket(bucket_name)
            bucket = None
            print("bucket var================", bucket)
            print("filename===========", filename)
            print("file_name============", file_name)
            
            ## use this structure for uat
            # blob = bucket.blob(
            #     STORAGE_BUCKET_ROOT_PATH + "/" +
            #     f"partner_{self.emr_id}" + "/" +
            #     STORAGE_BUCKET_PATH + "/" + 
            #     doc_type + "/" +
            #     f"{file_name}_{filename}{self.previous_patient_id.strip()}.pdf"
            # )

            ## use this structure for prod
            blob = bucket.blob(
                STORAGE_BUCKET_ROOT_PATH + "/" +
                f"{self.emr_id}" + "/" +
                doc_type + "/" +
                f"{file_name}_{filename}{self.previous_patient_id.strip()}.pdf"
            )

            print("blob======", blob)

            blob.upload_from_string(data, 'application/pdf')
            print(f"blob.public_url: {blob.public_url}")
            self.file_downloaded += 1
            self.update_download_type_records(doc_type)
            # self.driver.close()


    def process_pop_up4_for_local_storage(
        self,
        file_name,
        doc_type,
        idx=0
    ):
        file_name = file_name or f"{int(time.time())}{idx}"
        self.driver.switch_to.window(self.driver.window_handles[4])
        print(f"waiting for download {time.time()}")
        file_download_completed = self.is_file_download_completed()
        time.sleep(0.4)
        self.close_pop_up(4)
        time.sleep(1.3)
        if not file_download_completed:
            print("download timeout")
            return False
        self.file_downloaded += 1
        self.update_download_type_records(doc_type)
        # for filename in os.listdir(self.download_directory):
        #     file_path = os.path.join(self.download_directory, filename)
        #     print(f"file_path: {file_path}")
        #     with open(file_path, 'rb') as fh:
        #         data = fh.read()
        #     filename = self.file_name_parser(self.process_file_name(filename), idx)
        #     print(filename, doc_type, file_name)
        #     bucket_name = STORAGE_BUCKET_NAME
        #     bucket = gcs.get_bucket(bucket_name)
        #     blob = bucket.blob(
        #         os.path.join(
        #             os.path.join(STORAGE_BUCKET_ROOT_PATH,
        #                          f"partner_{self.emr_id}",
        #                          STORAGE_BUCKET_PATH, doc_type),
        #             f"{file_name}_{filename}{self.previous_patient_id.strip()}.pdf"
        #         )
        #     )
        #     blob.upload_from_string(data, 'application/pdf')
        #     print(f"blob.public_url: {blob.public_url}")
        #     self.file_downloaded += 1
        #     self.update_download_type_records(doc_type)


    def close_pop_up(self, pos=2):
        # selecting pop-up
        self.driver.switch_to.window(self.driver.window_handles[pos])
        # closing pop-up
        self.driver.close()

    def emr_login(self):
        print("inside emr_login function=========")
        self.driver.get(self.emr_login_url)
        time.sleep(2)
        try:
            print("inside login page=========")
            form = WebDriverWait(self.driver, 6).until(
                # EC.presence_of_element_located((By.ID, "form19"))
                EC.presence_of_element_located((By.NAME, "loginForm"))
            )
        except Exception as err:
            print(f"login_page_availability_error: {err}")
            print(f"pageSource\n{self.driver.page_source}\n")
            return None
        username = form.find_element(By.ID, "username")
        
        rpa_emr_username = os.getenv("RPA_EMR_USERNAME", None)
        rpa_emr_password = os.getenv("RPA_EMR_PASSWORD", None)
        rpa_emr_pin = os.getenv("RPA_EMR_PIN", None)
        
        if rpa_emr_username:
            rpa_emr_username = rpa_emr_username.strip()
        else:
            print("rpa_emr_username is None=======")
            return None
        username.send_keys(rpa_emr_username)

        password = form.find_element(By.ID, "password")
        if rpa_emr_password:
            rpa_emr_password = rpa_emr_password.strip()
        else:
            print("rpa_emr_password is None=======")
            return None
        password.send_keys(rpa_emr_password)

        pin = form.find_element(By.ID, "pin")
        
        if rpa_emr_pin:
            rpa_emr_pin = rpa_emr_pin.strip()
        else:
            print("rpa_emr_pin is None=======")
            return None
        pin.send_keys(rpa_emr_pin)

        submit = form.find_element(By.CLASS_NAME, "button")
        # submit = form.find_element(By.NAME, "submit")
        submit.click()
        time.sleep(1)
        # print(self.driver.window_handles)
        try:
            return WebDriverWait(self.driver, 5).until(
                # EC.presence_of_element_located((By.CSS_SELECTOR, "li[id='search']"))
                EC.presence_of_element_located((By.ID, "kaiDemoSearch"))
            )
        except Exception as err:
            print(f"emr_dashboard_availability_error: {err}")
            print("traceback=======", traceback.format_exc())
        return None

    def prepare_download_directory(self):
        if os.path.exists(self.download_directory):
            pass
            for filename in os.listdir(self.download_directory):
                file_path = os.path.join(self.download_directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
        else:
            os.makedirs(self.download_directory, exist_ok=True)

    @staticmethod
    def process_file_name(file_name):
        chars = f"{string.ascii_letters}{string.digits}._- "
        return ''.join([c.replace(' ', '_') for c in file_name if c in chars])

    @staticmethod
    def file_name_parser(processed_file_name, idx=0):
        print(f"processed_file_name: {processed_file_name}")
        try:
            name, ext = os.path.splitext(processed_file_name)
        except Exception:
            return f"{int(time.time())}{idx}"
        try:
            dt, fn = name.split('_', 1)
        except Exception as err:
            print(f"file_name_parser: {err} ->>>>>>>>\n--->>---->>")
            dt, fn = name[:14], name[14:]
            print(f"dt: {dt}::fn: {fn}")
        return f"{dt}{idx}"

    def update_download_type_records(self, document_type, inc=1):
        try:
            self.download_type_records[document_type] += inc
        except KeyError:
            self.download_type_records[document_type] = inc

    def is_doc_type_limit_processed(self):
        return (
                len(
                    [k for k, v in self.download_type_records.items()
                     if v >= self.document_download_limit]
                ) >= self.expected_document_type_count
        )


def start_emr_process():
    print("inside start_emr_process=======")
    start_time = time.time()
    file_downloaded = 0
    download_time = 0
    file_processed = 0
    download_type_records = {}
    emr = None
    run_time_processed_patients_stored = None
    try:
        with open(f"session_{RPA_EMR_PHELIX_ID}.json", 'r') as fhr:
            existing_session_records = json.loads(fhr.read() or "{}")
        download_time = existing_session_records.get("download_time") or 0
        file_downloaded = existing_session_records.get("file_downloaded") or 0
        file_processed = existing_session_records.get("file_processed") or 0
        run_time_processed_patients_stored = existing_session_records.get("complete_processed_patients_to_write")
        download_type_records = existing_session_records.get("download_type_records")
    except Exception as err:
        print(f"warning: {err}")
        existing_session_records = {}
    try:
        emr = OscarEmr(
            emr_login_url=EMR_LOGIN_URL,
            emr_id=RPA_EMR_PHELIX_ID,
            download_directory=DOWNLOAD_PATH,
            processed_patients_stored=copy.deepcopy(run_time_processed_patients_stored),
            headless=True,
            # headless=False,
            download_limit=DOWNLOAD_LIMIT,
            file_downloaded=file_downloaded,
            download_type_records=download_type_records,
            document_download_limit=DOCUMENT_DOWNLOAD_LIMIT,
            file_processed=file_processed,
            expected_document_type_count=EXPECTED_DOCUMENT_TYPES_COUNT
        )
        emr.process()
    except (Exception, KeyboardInterrupt) as err:
        print(f"error: {err}")
        print("traceback========", traceback.format_exc())
    finally:
        # if emr and emr.complete_processed_patients:
        #     file_downloaded = emr.file_downloaded ## count of files downloaded
        #     file_processed = emr.file_processed ## count of files processed not checking if downloaded or not
        #     download_time = emr.download_time ## final download time
        #     download_type_records = emr.download_type_records ## document record type (dictionary with different doc types count)
        #     complete_processed_patients_to_write = emr.complete_processed_patients
        #     if emr.processed_patients_stored and len(emr.processed_patients_stored) > len(emr.complete_processed_patients):
        #         complete_processed_patients_to_write = emr.processed_patients_stored
        #     try:
        #         session_records = {
        #             "complete_processed_patients_to_write": complete_processed_patients_to_write,
        #             "download_time": download_time,
        #             "file_downloaded": file_downloaded,
        #             "time_required": time.time() - start_time, ## final time processed - initial time
        #             "download_type_records": download_type_records,
        #             "file_processed": file_processed
        #         }
        #         print(emr.complete_processed_patients)
        #         with open(f"session_{emr.emr_id}.json", 'w') as fhw:
        #             fhw.write(json.dumps(session_records, indent=4))
        #     except Exception as err:
        #         print(f"error: {err}")
        # if emr and emr.driver:
        #     emr.driver.quit()
        # print(f"time_required: {time.time() - start_time}:: \n"
        #       f"file_downloaded: {file_downloaded}: download_time: {download_time}")
        session_records = {
            "complete_processed_patients_to_write": [],
            "download_time": 123,
            "file_downloaded": 123,
            "time_required": time.time(), ## final time processed - initial time
            "download_type_records": [1],
            "file_processed": 1234
        }
        # print(emr.complete_processed_patients)
    
        with open(f"session_192.json", 'w') as fhw:
            fhw.write(json.dumps(session_records, indent=4))
            
    print("start the sleep for 2 minutes=====")
    time.sleep(60*2)
    print("sleep ended for 2 minutes=====")
    return

# start_emr_process()

