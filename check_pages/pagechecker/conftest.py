"""Conftest for py.test environment to contain the following features:

- supress the output of the dots
- enable fixtures for specifying the tests and headless
- enable the output of the test results to a file (for slack)
- create a seleniumbase testing class incorporating the seleniumwire driver to record the requests
"""
import pytest
from seleniumbase import BaseCase


def pytest_addoption(parser):
    """Defines the extra options for the MOOC tests."""
    parser.addoption(
        "--file",
        help="Defines a file with a list of URL's.",
    )
    parser.addoption(
        "--folder",
        help="Defines a folder containing files with URL lists.",
    )
    parser.addoption(
        "--header",
        action="append",
        help="Adds a header used for each request in the format KEY:VALUE.",
    )


@pytest.fixture
def test_details(request):
    """Return the test details."""
    details = {
        "domain": request.config.getoption("--domain"),
        "file": request.config.getoption("--file"),
        "folder": request.config.getoption("--folder"),
        "number": request.config.getoption("--number"),
        "header": request.config.getoption("--header"),
        "output": request.config.getoption("--output"),
        "url": request.config.getoption("--url")
    }
    return details


@pytest.fixture()
def selbase(request):
    """Defines the basic seleniumbase driver."""

    sb = BaseCase()
    sb.setUp()
    yield sb
    sb.tearDown()


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Prints a brief summary at the end of all tests.
    Also creates a file with details on the errors, to be used for SLACK reporting.

    doc: https://docs.pytest.org/en/latest/_modules/_pytest/runner.html
    """
    # required to make the function a generator
    yield

    with open("service_results.txt", "w") as fileout:
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
    """Defines a method for a finished session."""
    if not pytest.test_success:
        session.exitstatus = 1
        print("\n\n")
        print(100 * "=")
        print("THERE WERE FAILED TESTS")
        print(100 * "=")
