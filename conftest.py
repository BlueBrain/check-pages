import json

import pytest


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


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Prints a brief summary at the end of all tests.
    Also creates a file with details on the errors, to be used for SLACK reporting.

    doc: https://docs.pytest.org/en/latest/_modules/_pytest/runner.html
    """
    # required to make the function a generator
    yield

    print(pytest.test_output)

    with open("mooc_results.txt", "w") as fileout:
        fileout.write(pytest.test_output)
