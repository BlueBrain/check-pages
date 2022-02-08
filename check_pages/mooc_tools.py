"""
Module to hold the elemental browser, login to edX, perform the tests
"""
import os
import time
import json

import elemental
from elemental.exceptions import NoSuchElementError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
)


class MoocChecker:
    """Defines the MOOC Checking class."""

    # This URL leads to a special edx page containing links to all test apps and services.
    URL = (
        "https://courseware.epfl.ch/courses/course-v1:EPFL+SimNeuro2+2019_2/courseware/"
        "ba6f8be8f0bb4956a94147f7a09e4cf4/fc4b687d340a4c69a862661e110970b1/1"
    )

    def __init__(self, headless):
        """Initialize new elemental driver and log into edX."""
        # Initialize selenium driver
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--start-maximized')
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(60)
        driver.set_page_load_timeout(60)

        self.browser = elemental.Browser(selenium_webdriver=driver)
        self.browser.visit(self.URL)

        # Perform the edx login
        self.login_edx()

    def login_edx(self):
        """Log into edX with several trials."""
        username = os.environ["EDX_LOGIN"]
        password = os.environ["EDX_PW"]

        while "Sign in or Register" in self.browser.title:
            self.browser.get_input(id="login-email").fill(username)
            self.browser.get_input(id="login-password").fill(password)
            time.sleep(1)

            try:
                self.browser.get_button(occurrence=3, partial_text="Sign in").click()
            except (
                ElementClickInterceptedException,
                NoSuchElementError,
                StaleElementReferenceException,
            ):
                time.sleep(1)
            time.sleep(2)

        self.report_check(True, "EDX Login")

    def get_grader_key(self):
        """Get and returns the current grader key for the demo exercise."""
        time.sleep(5)
        self.browser.get_button(partial_text="KeyGrading").click()
        time.sleep(5)

        # Switch to new tab
        driver = self.browser.selenium_webdriver
        driver.switch_to.window(driver.window_handles[-1])

        # Get the element and extract the attribute
        element = self.browser.get_element(id="submissionKey")
        attribute = element.attribute("value")

        # Close tab and go back to main tab
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        return attribute

    @staticmethod
    def report_check(result, text):
        """Logs and prints the result of a check."""
        if result:
            return True, f"{text} ... OK\n"
        else:
            return False, f"{text} ... TEST FAILED\n"

    def test_page(self, name, params):
        """Test a certain page or service."""
        if "wait" in params:
            wait = params["wait"]
        else:
            wait = 5

        # Click on next test
        driver = self.browser.selenium_webdriver
        time.sleep(5)
        driver.save_screenshot(f"screenshots/test_{name}_1.png")
        self.browser.get_button(partial_text=params["test"]).click()
        time.sleep(5)
        driver.save_screenshot(f"screenshots/test_{name}_2.png")

        # Switch to new tab
        driver = self.browser.selenium_webdriver
        driver.switch_to.window(driver.window_handles[-1])

        # Check the element
        try:
            element = self.browser.get_element(**params["element"], wait=wait)
        except NoSuchElementError:
            element = None
        driver.save_screenshot(f"screenshots/test_{name}_3.png")

        # Close tab and go back to main tab
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        # Test Results
        if "negative" in params:
            if not element:
                element = True

        return self.report_check(element, name)

    def test_grade_submission(self):
        """Checks if the grade submission works."""

        # Get and set grader key
        try:
            key = self.get_grader_key()
        except NoSuchElementError:
            return self.report_check(False, "Grade Submission (Grader Key)")

        self.browser.get_element(xpath="//input[@id='vizKey']", wait=5).fill(key)
        # Click on submit button with the 'correct' answer already filled in
        self.browser.get_element(xpath="//button[text()='Submit']").click()

        # Check result; sleep is required because element can be found, but it is empty
        time.sleep(10)
        text = self.browser.get_element(xpath="//div[@id='bbpGraderAnswer']").text
        try:
            result = json.loads(text)
            if "grade" in result:
                testok = bool(result["grade"]["value"] == 1)
            else:
                testok = False
        except json.JSONDecodeError:
            testok = False

        return self.report_check(testok, "Grade Submission")
