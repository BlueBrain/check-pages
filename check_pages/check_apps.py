"""Running tests on applications."""
import os
import time
import traceback
from urllib.parse import urlparse

from seleniumbase import BaseCase
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException

URL = (
    "https://courseware.epfl.ch/courses/course-v1:EPFL+SimNeuro2+2019_2/"
    "courseware/ba6f8be8f0bb4956a94147f7a09e4cf4/fc4b687d340a4c69a862661e110970b1/1"
)

SIMUI_NAME = "SIMUI.INFO"
PSPAPP_NAME = "PSPAPP.INFO"


class AppTests(BaseCase):
    """Performs tests by starting the applications."""

    def init(self):
        """Logs in to the edX service to perform the tests."""
        # Open the selection page
        self.open(URL)

        # Get the login credentials
        if "EDX_LOGIN" not in os.environ:
            raise ValueError("Error: EDX login undefined!")
        username = os.environ["EDX_LOGIN"]
        password = os.environ["EDX_PW"]

        # Perform the login
        self.type("#login-email", username)
        self.type("#login-password", password)
        self.save_screenshot("screenshots/login.png")
        edx_button = (
            "/html/body/div[3]/div[2]/div/main/div/div/section[1]/div/form/button"
        )
        self.click(edx_button, by=By.XPATH)

    def text_visible(self, text, filename, timeout=10):
        """Checks that the text is visible, and making screenshots along the way"""
        # Check that text RUNNING is visible
        t0 = time.time()
        while time.time() - t0 < timeout:
            time.sleep(5)
            time_passed = time.time() - t0
            print(f"Time passed: {time_passed:.1f} s")
            self.save_screenshot(filename.format(f"{time_passed:03.0f}"))
            if self.is_text_visible(text):
                return True
        return False

    @staticmethod
    def write_info(filename, info):
        """Write information for the next round."""
        print(f"Writing to file {filename}: '{info}'")
        with open(filename, "w") as fileout:
            fileout.write(info)

    @staticmethod
    def read_info(filename):
        """Read information from the previous round."""
        with open(filename) as filein:
            info = filein.read().strip()
        print(f"Reading from file {filename}: '{info}'")
        return info

    def open_page(self, pagename):
        """Opens the page of the app, and returns the authentification token."""
        screenshot_name = f"screenshots/open_{pagename}_{{}}.png"
        # Login
        self.init()
        self.save_screenshot(screenshot_name.format("init"))

        # Choose the page and retrieve the auth token from the page URL (???)
        self.click(f"//button[contains(text(),'{pagename}')]", by=By.XPATH)
        time.sleep(5)
        self.switch_to_newest_window()
        url = self.get_current_url()
        print(f"Clicking on {pagename}  ->  {url}")
        return url.split("?")[1]

    def check_simui(self):
        """Verify the previous run of a SimUI job."""
        screenshot_name = "screenshots/check_simui_{}.png"

        # open the SimUI page and get the auth token (????)
        auth = self.open_page("AppSim")

        # Read SimUI progress page URL and open it
        url = self.read_info(SIMUI_NAME) + "?" + auth
        print(f"CHECK_SIMUI URL: {url}")
        self.open(url)
        self.save_screenshot(screenshot_name.format("status"))

        # Check if the text SUCCESSFUL appears on the page
        if self.text_visible("SUCCESSFUL", screenshot_name.format("wait_{}")):
            print(f"SimUI Check OK")
        else:
            raise ElementNotVisibleException(f"SIMUI not successfull")

    def check_pspapp(self):
        """Verify the previous run of a pspapp job."""
        screenshot_name = "screenshots/check_pspapp_{}.png"

        # Open the SimUI page and get the auth token (????)
        auth = self.open_page("AppPSP")
        time.sleep(5)
        self.save_screenshot(screenshot_name.format("open"))

        # Read the name of the job to check
        job_name = self.read_info(PSPAPP_NAME)
        print(f"CHECK_PSPAPP job name: {job_name}")

        # Open the overview page
        url = "https://bbp-mooc-sim-neuro.epfl.ch/psp-validation/list" + "?" + auth
        print(f"CHECK_PSPAPP list URL: {url}")
        self.open(url)
        time.sleep(5)
        self.save_screenshot(screenshot_name.format("overview"))

        self.click(f"//span[contains(text(),'{job_name}')]", by=By.XPATH)
        time.sleep(5)
        self.save_screenshot(screenshot_name.format("clicked"))

        # Check if the text SUCCESSFUL appears on the page
        if self.text_visible("SUCCESSFUL", screenshot_name.format("wait_{}")):
            print(f"PSPApp Check OK")
        else:
            self.save_screenshot(screenshot_name.format("failure"))
            raise ElementNotVisibleException(f"PSPApp not successfull")

    def start_simui(self):
        """Test the SimUI by starting a simulation and checking it is running."""
        screenshot_name = "screenshots/start_simui_{}.png"
        # Open the page
        self.open_page("AppSim")

        # Choose the mc1 column as the population
        self.click("//input[@placeholder='Select']", by=By.XPATH)
        self.click("//ul/li/div[text()='mc1_Column']", by=By.XPATH)

        # Click continue
        self.click("//button/span[contains(text(),'Continue')]", by=By.XPATH)

        # Set title and click on "Run Simulation"
        id_ = f"{time.time():.0f}"
        self.type("//input[@placeholder='Title']", id_)
        self.click('//button/span[contains(text(),"Run Simulation")]', by=By.XPATH)
        self.save_screenshot(screenshot_name.format("launch"))

        # Wait for the text QUEUED to appear
        t0 = time.time()
        if self.text_visible("QUEUED", screenshot_name.format("wait_{}")):
            time_visible = time.time() - t0
            print(f"SimUI Test OK after {time_visible:.1f} seconds")
        else:
            raise ElementNotVisibleException(f"PSPApp Text ID {id_} NOT visible after timeout")

        # Write SimUI progress page URL to file
        url = urlparse(self.get_current_url())
        self.write_info(SIMUI_NAME, f"{url.scheme}://{url.netloc}{url.path}")

        return time_visible

    def start_pspapp(self):
        """Test the PSP Validation by starting a validation and checking it is running."""
        screenshot_name = "screenshots/start_pspapp_{}.png"
        # open the PSPApp page
        self.open_page("AppPSP")

        # Click on Continue and to run the app.
        self.click('//button/span[contains(text(),"Continue")]', by=By.XPATH)
        self.click('//button/span[contains(text(),"Run PSP")]', by=By.XPATH)

        # Set title and click on "Run Simulation"
        id_ = f"{time.time():.0f}"
        self.type("//input[@placeholder='Job name']", id_)
        self.save_screenshot(screenshot_name.format("launch"))
        self.click('//button/span[contains(text(),"Launch")]', by=By.XPATH)

        # Write PSPApp ID to file
        self.write_info(PSPAPP_NAME, id_)


def run_test(test_name, headless):
    """Runs a single test outside of the py.test environment."""

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
    print(f"Running test {test_name}")
    try:
        time_visible = getattr(sb, test_name)()
        time.sleep(5)
    except Exception as e:
        print(f"APP-ERROR: {repr(e)}")
        traceback.print_exc()
        print(100 * "#")
        testok = False
    finally:
        sb.tearDown()
        del sb

    if testok:
        time_info = ""
        if time_visible:
            time_info = f"  {time_visible:.1f} seconds"
        msg = f"{test_name} ... OK {time_info}\n"
    else:
        msg = f"{test_name} ... TEST FAILED\n"
    return testok, msg
