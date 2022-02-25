"""Conftest for py.test environment to contain the following features:

- supress the output of the dots
- enable fixtures for specifying the tests and headless
- enable the output of the test results to a file (for slack)
- create a seleniumbase testing class incorporating the seleniumwire driver to record the requests
"""
import pytest
from seleniumbase import BaseCase
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

from check_pages import mooc_tests

# Define common test variables
pytest.test_output = ""
pytest.test_success = True


def pytest_addoption(parser):
    """Defines the extra options for the MOOC tests."""
    parser.addoption(
        "--tests",
        help="Defines the json files containing the test parameters.",
    )
    parser.addoption(
        "--output",
        default="mooc_results.txt",
        help="Defines the results output filename.",
    )


@pytest.fixture
def headless(request):
    """Returns True if driver should run headless."""
    return request.config.getoption("--headless")


@pytest.fixture(scope="function")
def selbase(headless):
    """Fixture to return the seleniumbase driver with seleniumwire webdriver."""
    seleniumbasedriver = get_driver(headless)
    return seleniumbasedriver


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Prints a brief summary at the end of all tests.
    Also creates a file with details on the errors, to be used for SLACK reporting.

    doc: https://docs.pytest.org/en/latest/_modules/_pytest/runner.html
    """
    # required to make the function a generator
    yield

    with open("mooc_results.txt", "w") as fileout:
        fileout.write(pytest.test_output)


def pytest_report_teststatus(report):
    """Avoid printing .xFE for a test.
    see https://stackoverflow.com/questions/53374551/avoid-printing-of-dots
    """
    category, short, verbose = "", "", ""
    if hasattr(report, "wasxfail"):
        if report.skipped:
            category = "xfailed"
            verbose = "xfail"
        elif report.passed:
            category = "xpassed"
            verbose = ("XPASS", {"yellow": True})
        return (category, short, verbose)
    elif report.when in ("setup", "teardown"):
        if report.failed:
            category = "error"
            verbose = "ERROR"
        elif report.skipped:
            category = "skipped"
            verbose = "SKIPPED"
        return (category, short, verbose)
    category = report.outcome
    verbose = category.upper()
    return (category, short, verbose)


def pytest_sessionfinish(session, exitstatus):
    if not pytest.test_success:
        session.exitstatus = 1
        print("\n\n")
        print(100 * "=")
        print("THERE WERE FAILED TESTS")
        print(100 * "=")


class BaseTestCase(BaseCase):
    """Defines the seleniumbase driver class."""

    def get_new_driver(self, *args, **kwargs):
        """ This method overrides get_new_driver() from BaseCase. """
        options = webdriver.ChromeOptions()
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        if self.headless:
            options.add_argument("--headless")
        return webdriver.Chrome(options=options)


def get_driver(headless):
    """Runs a single test outside of the py.test environment."""

    sb = BaseTestCase()

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

    # Set up the driver
    sb.setUp()

    # return the driver
    return sb
