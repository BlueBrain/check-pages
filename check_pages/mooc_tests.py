"""Tests for the MOOC 2 (2019)

In order to see all the tests collected do
py.test --tests <path to json> --collect-only

To execute a singl test do e.g.
py.test -k test_mooc_service[SimulationApp]
"""

import os
import json
import time
import traceback
import datetime
from urllib.parse import urlparse

import pytest
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException


@pytest.hookimpl
def pytest_generate_tests(metafunc):
    """Sets the parameters dynamically for the fixture 'testparam' used for "test_mooc_service".

    Whenever pytest calls a test function, and this function requires the fixture 'testparam',
    a list of parameters are set that are being read from the json file.
    """
    if "testparam" in metafunc.fixturenames:
        with open(metafunc.config.option.tests) as f:
            tests = json.load(f)

        # add parametrization for fixture
        metafunc.parametrize("testparam", tests.items(), ids=tests.keys())


class MoocTests:
    """Defines the MOOC Testing class."""

    # This URL leads to a special edx page containing links to all test apps and services.
    URL = ("https://app.courseware.epfl.ch/learning/course/course-v1:EPFL+SimNeuro2+2019_2/home"
           # The previous URL used is kept below:
           # "https://courseware.epfl.ch/courses/course-v1:EPFL+SimNeuro2+2019_2/courseware/"
           # "ba6f8be8f0bb4956a94147f7a09e4cf4/fc4b687d340a4c69a862661e110970b1/1"
           )
    SIMUI_NAME = "SIMUI.INFO"
    PSPAPP_NAME = "PSPAPP.INFO"

    OUTPUT = "debug"

    def __init__(self, driver):
        """Initializes this test object with the seleniumbase-seleniumwire webdriver."""
        # The driver
        self.driver = driver
        # The starting time
        self.time0 = time.time()
        # The current step
        self.step = None

    def next(self, text):
        """Set the next step."""
        self.step = text

    def debug(self, text):
        """Print out some infos."""
        print(f"... {self.timestamp()} {text}")

    @staticmethod
    def timestamp():
        """Returns the current time in human readable format."""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def login_edx(self):
        """Open the main QA page and login."""
        self.next("Login: Opening page")
        self.driver.open(self.URL)
        self.debug("Opened page")
        signin = self.driver.find_element("//a[@href='https://courseware.epfl.ch/login?next=https"
                                          "%3A%2F%2Fapp.courseware.epfl.ch%2Flearning%2Fcourse"
                                          "%2Fcourse-v1%3AEPFL%2BSimNeuro2%2B2019_2%2Fhome' and "
                                          "text()='Sign in' and @class='btn btn-primary']")
        self.driver.execute_script("arguments[0].click();", signin)
        # Maximize the browser window
        self.driver.maximize_window()

        # Get the login credentials
        if "EDX_LOGIN" not in os.environ:
            raise ValueError("Error: EDX login undefined!")
        username = os.environ["EDX_LOGIN"]
        password = os.environ["EDX_PW"]

        # Click on the edu-ID button
        self.next("Login: Waiting for'SWITCH edu-ID'")
        self.driver.click('button:contains("SWITCH edu-ID")', timeout=60)
        self.debug("Clicked on 'SWITCH edu-ID'")

        # Login by entering username then clicking login
        self.next("Login: Inserting username for authentication")
        self.driver.type("#username", username)
        self.next("Login: Waiting for login button")
        self.next("Login: Clicking 'Login' button first time")
        self.driver.click("login-button", by=By.ID, timeout=60)
        self.debug("Clicked on first 'Login' button")
        self.driver.type("#password", password)
        self.next("Login: Waiting for login button")
        self.driver.click("login-button", by=By.ID, timeout=60)
        self.debug("Clicked on 'Login' second time")
        staging_area = self.driver.find_element("//div[@class='collapsible-trigger' and "
                                                "@role='button']//span[contains(text(), 'Staging "
                                                "Area')]")
        self.driver.execute_script("arguments[0].click();", staging_area)
        QA_page = self.driver.find_element("//a[@href='/learning/course/course-v1:EPFL+SimNeuro2"
                                           "+2019_2/block-v1:EPFL+SimNeuro2+2019_2+type"
                                           "@sequential+block@fc4b687d340a4c69a862661e110970b1']")
        time.sleep(3)
        self.driver.execute_script("arguments[0].click();", QA_page)

    def check_page(self, name, params):
        """Test a certain page or service."""

        # Get the timeout to be used
        if "wait" in params:
            timeout = params["wait"]
        else:
            timeout = 5

        time.sleep(3)
        self.driver.save_screenshot(f"{self.OUTPUT}/test_{name}_1.png")

        # Click on the next test
        self.switch_to_iframe("unit-iframe")
        print("Switched to iframe")
        time.sleep(3)

        text = params["test"]
        self.next("Test: Waiting for app button")
        time.sleep(10)
        self.debug(f"Attempting to click on the app button: {text}")
        time.sleep(10)
        element_selector = f"button:contains('{text}')"
        element = self.driver.find_element(element_selector)
        self.driver.execute_script("arguments[0].click();", element)
        self.debug(f"Button for {text} has been clicked using JavaScript")
        self.driver.save_screenshot(f"{self.OUTPUT}test_{name}_2.png")
        self.next(f"Waiting to switch to the new tab")
        self.driver.switch_to_window(1)

        # Check the actual element
        self.next(f"Test: Waiting for element {params['element']['element']} to check")
        self.driver.save_screenshot(f"{self.OUTPUT}/test_{name}_2.5.png")
        self.driver.find_element(
            params["element"]["element"],
            by=params["element"]["by"],
            timeout=timeout
        )
        self.driver.save_screenshot(f"{self.OUTPUT}/test_{name}_3.png")

        # Go back to the main tab
        self.next("Waiting to switch back to the original tab")
        self.driver.switch_to_window(0)
        self.debug("Test: Success")

    def switch_to_iframe(self, frame_id=None):
        """
        Switch to the given iFrame.
        If frame_id is None, switch back to the default content
        """

        if frame_id is None:
            self.debug('frame_id is None - switching to default content')
            self.driver.driver.switch_to.default_content()
        else:
            self.debug(f'Trying to find iframe with ID {frame_id}')
            iframe = self.driver.find_element(frame_id, by=By.ID, timeout=30)
            self.debug('iFrame found - switching')
            self.driver.driver.switch_to.frame(iframe)

    def get_grader_key(self):
        """Get and returns the current grader key for the demo exercise."""

        # Click on the next test
        self.next("Test: Waiting for 'KeyGrading' button")
        self.switch_to_iframe("unit-iframe")
        element = self.driver.find_element('button:contains("KeyGrading")')
        self.driver.execute_script("arguments[0].click();", element)
        self.debug("Button for 'KeyGrading' has been clicked using JavaScript")

        self.driver.save_screenshot(f"{self.OUTPUT}/test_grade_submission_1.png")

        self.driver.switch_to_window(1)

        # Get the element and extract the attribute
        self.next("Test: Get submission key")
        element = self.driver.find_element("#submissionKey")
        attribute = element.get_attribute("value")
        self.debug(f"Submission key found: {attribute}")

        # Go back to main tab
        self.driver.switch_to_window(0)
        return attribute

    def grade_submission(self):
        """Checks if the grade submission works."""

        # Get and set grader key
        key = self.get_grader_key()

        # Set the grader key and click on "submit" to submit the answer to the grader
        self.switch_to_iframe("unit-iframe")
        self.next("Set the grader key and click on submit")
        self.driver.type("//input[@id='vizKey']", key)
        submit_button = self.driver.find_element("//button[text()='Submit']")
        self.driver.execute_script("arguments[0].click();", submit_button)
        self.debug("Clicked on submit using JavaScript")
        self.driver.save_screenshot(f"{self.OUTPUT}/test_grade_submission_2.png")

        # Check result; sleep is required because element can be found, but it is empty
        time.sleep(10)
        self.next("Check the answer")
        element = self.driver.find_element("//div[@id='bbpGraderAnswer']")
        text = element.text
        self.debug(f"Answer is: {text}")

        # Do I get a valid json in return with grade=1?
        self.next("Check the json content")
        result = json.loads(text)
        assert result["grade"]["value"] == 1
        self.debug("Test: Success")

    def write_info(self, filename, info):
        """Write information for the next round."""
        self.debug(f"Writing to file {filename}: '{info}'")
        with open(filename, "w") as fileout:
            fileout.write(info)

    def read_info(self, filename):
        """Read information from the previous round."""
        with open(filename) as filein:
            info = filein.read().strip()
        self.debug(f"Reading from file {filename}: '{info}'")
        return info

    def text_visible(self, text, timeout=10):
        """Checks that the text is visible, and making screenshots along the way"""
        # Check that text RUNNING is visible
        t0 = time.time()
        while time.time() - t0 < timeout:
            time.sleep(1)
            if self.driver.is_text_visible(text):
                return True
        return False

    def open_page(self, pagename):
        """Opens the page of the app, and returns the authentification token."""
        # Choose the page and retrieve the auth token from the page URL (???)
        self.next(f"Clicking on '{pagename}'")
        self.switch_to_iframe("unit-iframe")
        time.sleep(10)
        page_app = f"//button[contains(text(),'{pagename}')]"
        page_element = self.driver.find_element(page_app)
        self.driver.execute_script("arguments[0].click();", page_element)
        self.debug(f"The PageApp button was found and clicked using JavaScript")
        time.sleep(10)
        self.next("Get the URL token")
        self.driver.switch_to_newest_window()
        url = self.driver.get_current_url()
        self.debug(f"URL retrieved is `{pagename}`  ->  {url}")
        return url.split("?")[1]

    def check_simui(self):
        """Verify the previous run of a SimUI job."""
        screenshot_name = f"{self.OUTPUT}/check_simui_{{}}.png"

        # open the SimUI page and get the auth token (TODO: Why is this needed? Anymore?)
        auth = self.open_page("AppSim")
        time.sleep(5)
        # Read SimUI progress page URL and open it
        url = self.read_info(self.SIMUI_NAME) + "?" + auth
        self.next(f"Open CHECK_SIMUI URL: {url}")
        self.driver.open(url)
        self.debug(f"Opened page {url}")
        self.driver.save_screenshot(screenshot_name.format("1-status"))

        self.next("Wait for 'SUCCESSFUL'")
        self.text_visible("SUCCESSFUL", timeout=60)
        self.driver.save_screenshot(screenshot_name.format("2-checksuccess"))
        self.debug("Test Success")

    def check_pspapp(self):
        """Verify the previous run of a pspapp job."""
        screenshot_name = f"{self.OUTPUT}/check_pspapp_{{}}.png"

        # Open the SimUI page and get the auth token (????)
        auth = self.open_page("AppPSP")
        time.sleep(10)
        self.driver.save_screenshot(screenshot_name.format("1-open"))

        # Read the name of the job to check
        job_name = self.read_info(self.PSPAPP_NAME)
        self.debug(f"CHECK_PSPAPP job name: {job_name}")

        # Open the status page for the job
        url = "https://bbp-mooc-sim-neuro.epfl.ch/psp-validation/list" + "?" + auth
        self.next(f"Open the overview page {url}")
        self.driver.open(url)
        self.debug("Opened the overview page")
        self.driver.save_screenshot(screenshot_name.format("2-overview"))

        self.next(f"Click on the job name {job_name}")
        job_name_element = f"//span[contains(text(),'{job_name}')]"
        try:
            job_name_selector = self.driver.find_element(job_name_element, timeout=60)
        except:
            self.driver.save_screenshot(screenshot_name.format("2b-issue"))
            raise
        self.driver.execute_script("arguments[0].click();", job_name_selector)
        self.debug(f"Clicked on the job name {job_name} using JavaScript")
        self.driver.save_screenshot(screenshot_name.format("3-clickedjob"))
        self.next("Wait for 'SUCCESSFUL'")
        self.text_visible("SUCCESSFUL", timeout=60)
        self.driver.save_screenshot(screenshot_name.format("4-checksuccess"))
        self.debug("Test Success")

    def start_simui(self):
        """Test the SimUI by starting a simulation and checking it is running."""
        screenshot_name = f"{self.OUTPUT}/start_simui_{{}}.png"

        # Open the page
        self.open_page("AppSim")
        time.sleep(10)
        # Choose the mc1 column as the population
        self.next("Select mc1 popluation")
        self.driver.click("//input[@placeholder='Select']", by=By.XPATH)
        self.driver.click("//ul/li/div[text()='mc1_Column']", by=By.XPATH)

        # Click continue
        self.next("Click Continue")
        self.driver.click("//button/span[contains(text(),'Continue')]", by=By.XPATH)

        # Set title and click on "Run Simulation"
        self.next("Set title and click Run Simulation")
        id_ = f"{time.time():.0f}"
        self.driver.type("//input[@placeholder='Title']", id_)
        self.driver.click('//button/span[contains(text(),"Run Simulation")]', by=By.XPATH)
        self.debug(f"Clicked on 'Run Simulation'. Jobtitle: {id_}")
        self.driver.save_screenshot(screenshot_name.format("launch"))

        # Wait for the text QUEUED to appear
        self.next("Wait for 'QUEUED'")
        self.text_visible("QUEUED", timeout=60)

        # Write SimUI progress page URL to file
        url = urlparse(self.driver.get_current_url())
        self.write_info(self.SIMUI_NAME, f"{url.scheme}://{url.netloc}{url.path}")
        self.debug("Test Success")

    def start_pspapp(self):
        """Test the PSP Validation by starting a validation and checking it is running."""
        screenshot_name = f"{self.OUTPUT}/start_pspapp_{{}}.png"
        # open the PSPApp page
        self.open_page("AppPSP")
        time.sleep(10)

        # Click on Continue and to run the app.
        self.next("Start a PSPApp Simulation")
        self.driver.click('//button/span[contains(text(),"Continue")]', by=By.XPATH)
        self.driver.click('//button/span[contains(text(),"Run PSP")]', by=By.XPATH)
        self.debug("PSPApp simulation has been started")

        # Set title and click on "Run Simulation"
        self.next("Set title and click on 'Run Simulation'")
        id_ = f"{time.time():.0f}"
        self.driver.type("//input[@placeholder='Job name']", id_)
        self.driver.save_screenshot(screenshot_name.format("launch"))
        self.driver.click('//button/span[contains(text(),"Launch")]', by=By.XPATH)
        self.debug(f"Clicked on 'Run Simulation'. Jobtitle: {id_}")

        # Write PSPApp ID to file
        self.write_info(self.PSPAPP_NAME, id_)
        time.sleep(5)
        self.debug("Test Success")

    def save_requests(self, name):
        """Save the requests and responses."""
        request_list = []
        for request in self.driver.driver.requests:
            if request.response:
                myreq = {
                    "url": request.url,
                    "headers": dict(request.headers),
                    "method": request.method,
                    "status": request.response.status_code,
                    "date_response": str(request.response.date),
                    "date_request": str(request.date)
                }
                request_list.append(myreq)
        with open(f"{self.OUTPUT}/request_{name}.json", "w") as json_out:
            json.dump(request_list, json_out)

    def perform_test(self, method, name, *params):
        """Performs a selenium test in a safe environment."""
        # Print the name of the test
        print(f"\nRunning test {name} at {self.timestamp()}")

        try:
            # Log in to edX
            self.login_edx()

            # Call the actual test method
            print(f"-> Test start at {self.timestamp()}")
            method(*params)
            print(f"-> Test end at {self.timestamp()}")

            # Set output for summary
            success = True
            output = f"{name} ... OK\n"
        except (NoSuchElementException, ElementNotVisibleException, IndexError) as e:
            # Handle the error
            self.debug(f"ERROR for step: {self.step}")
            self.debug(f"Error is {e}")
            print(100 * "-")
            print(traceback.format_exc())
            print(100 * "-")

            # Final screenshot
            self.driver.save_screenshot(f"{self.OUTPUT}/test_{name}_ERROR.png")

            # Set output for summary
            success = False
            output = f"{name} ... TEST FAILED: {self.step}\n"

            self.save_requests(name)

        # Remember the test
        pytest.test_output += output
        pytest.test_success &= success

        # Quit the browser
        self.driver.tearDown()


def test_mooc_grade_submission(selbase):
    """Tests the grade submission backend."""
    mooc = MoocTests(selbase)
    mooc.perform_test(mooc.grade_submission, "grade_submission")


def test_mooc_service(selbase, testparam):
    """Tests a Mooc service (like jupyter, Bryans, Keys etc.)"""
    mooc = MoocTests(selbase)
    mooc.perform_test(mooc.check_page, testparam[0], *testparam)


@pytest.mark.parametrize("appname", ["check_simui", "check_pspapp", "start_simui", "start_pspapp"])
def test_mooc_apps(selbase, appname):
    """Tests a service by starting the application and wait until it is running."""
    mooc = MoocTests(selbase)
    mooc.perform_test(getattr(mooc, appname), appname)
