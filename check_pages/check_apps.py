import os
import time
import random

from seleniumbase import BaseCase
from selenium.webdriver.common.by import By

URL = (
    "https://courseware.epfl.ch/courses/course-v1:EPFL+SimNeuro2+2019_2/"
    "courseware/ba6f8be8f0bb4956a94147f7a09e4cf4/fc4b687d340a4c69a862661e110970b1/1"
)


class AppTests(BaseCase):
    """Performs tests by starting the applications."""

    def init(self):
        """Logs in to the edX service to perform the tests."""
        # Open the selection page
        self.open(URL)

        # Get the login credentials
        username = os.environ["EDX_LOGIN"]
        password = os.environ["EDX_PW"]

        # Perform the login
        self.type("#login-email", username)
        self.type("#login-password", password)
        edx_button = (
            "/html/body/div[3]/div[2]/div/main/div/div/section[1]/div/form/button"
        )
        self.click(edx_button, by=By.XPATH)

    def test_simui(self):
        """Test the SimUI by starting a simulation and checking it is running."""
        # Login
        self.init()

        # Choose the SimUI App
        self.click("//button[contains(text(),'AppSim')]", by=By.XPATH)

        # Switch to new tab
        self.switch_to_newest_window()

        # Choose the mc1 column as the population
        self.click("//input[@placeholder='Select']", by=By.XPATH)
        self.click("//ul/li/div[text()='mc1_Column']", by=By.XPATH)

        # Click continue
        self.click("//button/span[contains(text(),'Continue')]", by=By.XPATH)

        # Set title and click on "Sun Simulation"
        id_ = f"{time.time():.0f}"
        self.type("//input[@placeholder='Title']", id_)
        self.click('//button/span[contains(text(),"Run Simulation")]', by=By.XPATH)

        # Check RUNNING is visible on the page
        self.assert_text("RUNNING", timeout=60)
        print("Sim running")

    def test_pspapp(self):
        """Test the PSP Validation by starting a validation and checking it is running."""
        # Login
        self.init()

        # Choose the PSP Validation App
        self.click('//button[contains(text(),"AppPSP")]', by=By.XPATH)

        # Switch to new tab
        self.switch_to_newest_window()

        # Click on Continue ansd to run the app
        self.click('//button/span[contains(text(),"Continue")]', by=By.XPATH)
        self.click('//button/span[contains(text(),"Run PSP")]', by=By.XPATH)

        # Set title and click on "Sun Simulation"
        id_ = f"{time.time():.0f}"
        self.type("//input[@placeholder='Job name']", id_)
        self.click('//button/span[contains(text(),"Launch")]', by=By.XPATH)

        # Open list page
        self.open("https://bbp-mooc-sim-neuro.epfl.ch/psp-validation/list")
        time.sleep(10)

        # check id is there
        if not self.is_text_visible(id_):
            print("Text not visible!!!")

        # check status is running
        xpath = "//span[contains(@class, 'status-text')]"
        elements = self.find_elements(xpath, by=By.XPATH)
        correct_text = ["READY", "SUCCESSFUL"]
        for element in elements:
            assert element.text in correct_text


def run_test(test_name, headless):

    sb = AppTests(test_name)
    sb.browser = "chrome"
    sb.headless = headless
    sb.headed = False
    sb.xvfb = False
    sb.start_page = None
    sb.locale_code = None
    sb.protocol = "http"
    sb.servername = "localhost"
    sb.port = 4444
    sb.data = None
    sb.environment = "test"
    sb.user_agent = None
    sb.incognito = False
    sb.guest_mode = False
    sb.devtools = False
    sb.mobile_emulator = False
    sb.device_metrics = None
    sb.extension_zip = None
    sb.extension_dir = None
    sb.database_env = "test"
    sb.log_path = "latest_logs/"
    sb.archive_logs = False
    sb.disable_csp = False
    sb.disable_ws = False
    sb.enable_ws = False
    sb.enable_sync = False
    sb.use_auto_ext = False
    sb.no_sandbox = False
    sb.disable_gpu = False
    sb._multithreaded = False
    sb._reuse_session = False
    sb._crumbs = False
    sb.visual_baseline = False
    sb.maximize_option = False
    sb.save_screenshot_after_test = False
    sb.timeout_multiplier = None
    sb.pytest_html_report = None
    sb.with_db_reporting = False
    sb.with_s3_logging = False
    sb.js_checking_on = False
    sb.report_on = False
    sb.is_pytest = False
    sb.slow_mode = False
    sb.demo_mode = False
    sb.time_limit = None
    sb.demo_sleep = 1
    sb.dashboard = False
    sb._dash_initialized = False
    sb.message_duration = 2
    sb.block_images = False
    sb.remote_debug = False
    sb.settings_file = None
    sb.user_data_dir = None
    sb.chromium_arg = None
    sb.firefox_arg = None
    sb.firefox_pref = None
    sb.proxy_string = None
    sb.swiftshader = False
    sb.ad_block_on = False
    sb.highlights = None
    sb.check_js = False
    sb.interval = None
    sb.cap_file = None
    sb.cap_string = None

    sb.setUp()
    testok = True
    try:
        getattr(sb, test_name)()
        time.sleep(5)
    except:
        testok = False
    finally:
        sb.tearDown()
        del sb
    return testok


def check_apps(headless):
    output = ""
    error = False
    for test_name in ["test_simui", "test_pspapp"]:
        if run_test(test_name, headless):
            text = f"{test_name} ... OK"
        else:
            text = f"{test_name} ... TEST FAILED"
            error = True
        print(text)
        output += text + "\n"
    return output, error
