"""Tests for the MOOC 2 (2019)

In order to see all the tests collected do
py.test --tests <path to json> --collect-only

To execute a singl test do e.g.
py.test -k test_mooc_service[SimulationApp]
"""
import json
import pytest

from check_pages import mooc_tools, check_apps


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


def test_mooc_grade_submission(headless):
    """Tests the grade submission backend."""
    # Setup the MOOC driver including edX login.
    mooc = mooc_tools.MoocChecker(headless)

    # Perform the grade submission test
    success, output = mooc.test_grade_submission()

    # Remember the test
    pytest.test_output += output
    pytest.test_success &= success

    # Quit the browser
    mooc.browser.quit()
    assert success


def test_mooc_service(testparam, headless):
    """Tests a Mooc service (like jupyter, Bryans, Keys etc.)"""
    # Setup the MOOC driver including edX login
    mooc = mooc_tools.MoocChecker(headless)

    # Perform the test
    success, output = mooc.test_page(testparam[0], testparam[1])

    # Remember the test
    pytest.test_output += output
    pytest.test_success &= success

    # Quit the browser
    mooc.browser.quit()
    assert success


@pytest.mark.parametrize("appname", ["check_simui", "check_pspapp", "start_simui", "start_pspapp"])
def test_apps(appname, headless):
    """Tests a service by starting the application and wait until it is running."""

    # Run the test
    success, output = check_apps.run_test(appname, headless)

    # Remember the test
    pytest.test_output += output
    pytest.test_success &= success

    assert success
