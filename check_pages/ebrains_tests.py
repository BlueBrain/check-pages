# Copyright (c) 2024 Blue Brain Project/EPFL
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for ebrains

In order to see all the tests collected do
py.test --tests <path to json> --collect-only

To execute a singl test do e.g.
py.test -k test_mooc_service[SimulationApp]
"""

import os
import json
import time
import traceback


import pytest
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotVisibleException,
)


class EbrainsTests:
    """Defines the ebrains Testing class."""

    # These URL lead to the simui pages.
    URL = {
        "CA1": "https://simulation-launcher-bsp-epfl.apps.hbp.eu/index.html#"
               "/circuits/hippo_hbp_sa_full_ca1",
        "MICRO": "https://simulation-launcher-bsp-epfl.apps.hbp.eu/index.html#"
                 "/circuits/hippo_mooc_sa_microcircuit",
    }
    POPULATION = {"CA1": "slice69", "MICRO": "mc1_Column"}
    SIMUI_NAME = "SIMUI_{}.INFO"
    OUTPUT = "debug"

    def __init__(self, driver, urlkey):
        """Initializes this test object with the seleniumbase-seleniumwire webdriver."""
        # The driver
        self.driver = driver
        # The URL
        self.urlkey = urlkey
        # The starting time
        self.time0 = time.time()
        # The current step
        self.step = None

    def next(self, text):
        """Set the next step."""
        self.step = text

    def debug(self, text):
        """Print out some infos."""
        print(f"... {time.time()-self.time0:.2f}: {text}")

    def login_ebrains(self):
        """Open the ebrains SimUI pages."""
        self.next("Login: Opening page")
        self.driver.open(self.URL[self.urlkey])
        self.debug("Opened page")

        # Get the login credentials
        if "EBRAINS_LOGIN" not in os.environ:
            raise ValueError("Error: EBRAINS login undefined!")
        username = os.environ["EBRAINS_LOGIN"]
        password = os.environ["EBRAINS_PW"]

        # Set username and password
        self.next("Login: Inserting authorization")
        self.driver.type("#username", username)
        self.driver.type("#password", password)

        # Click on login
        self.next("Login: Waiting for login button")
        self.driver.click("#kc-login", timeout=60)
        self.debug("Clicked on 'Login")

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

    def check_simui(self, circuit):
        """Verify the previous run of a SimUI job."""
        screenshot_name = f"{self.OUTPUT}/check_simui_{circuit}_{{}}.png"

        # Read SimUI progress page URL
        url = self.read_info(self.SIMUI_NAME.format(circuit))  # + "?" + auth
        if not url.startswith("http"):
            self.debug(f"SKIPPING TEST: URL does not start with http: '{url}'")
            return

        # Open that page
        self.next(f"Open CHECK_SIMUI URL: {url}")
        self.driver.open(url)
        self.driver.open(url)
        self.debug(f"Opened page {url}")
        self.driver.save_screenshot(screenshot_name.format("1-status"))

        self.next("Wait for 'SUCCESSFUL'")
        if not self.text_visible("SUCCESSFUL", timeout=60):
            raise NoSuchElementException
        self.driver.save_screenshot(screenshot_name.format("2-checksuccess"))
        self.debug("Test Success")

    def start_simui(self, circuit):
        """Test the SimUI by starting a simulation and checking it is queued."""
        screenshot_name = f"{self.OUTPUT}/start_simui_{circuit}_{{}}.png"

        # Choose the mc1 column as the population
        population = self.POPULATION[circuit]
        self.next(f"Select popluation {population}")
        self.driver.type("//input[@placeholder='Duration']", 30)
        self.driver.click("//input[@placeholder='Select']", by=By.XPATH)
        self.driver.click(f"//ul/li/div[text()='{population}']", by=By.XPATH)

        # Click continue
        self.next("Click Continue")
        self.driver.click("//button/span[contains(text(),'Continue')]", by=By.XPATH)

        # Set title and click on "Run Simulation"
        self.next("Set title and click Run Simulation")
        id_ = f"{time.time():.0f}"
        self.driver.type("//input[@placeholder='Title']", id_)
        self.driver.type("//input[@placeholder='Node to allocate']", "4")
        self.driver.click(
            '//button/span[contains(text(),"Run Simulation")]', by=By.XPATH
        )
        self.debug("Run Simulation has been clicked.")
        self.driver.save_screenshot(screenshot_name.format("launch"))

        # Wait for the text QUEUED to appear
        self.next("Wait for 'QUEUED'")
        self.text_visible("QUEUED", timeout=60)

        # Write SimUI progress page URL to file
        url = self.driver.get_current_url()
        self.write_info(self.SIMUI_NAME.format(circuit), url)
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
                    "date_request": str(request.date),
                }
                request_list.append(myreq)
        with open(f"{self.OUTPUT}/request_{name}.json", "w") as json_out:
            json.dump(request_list, json_out)

    def perform_test(self, method, name, *params):
        """Performs a selenium test in a safe environment."""
        # Print the name of the test
        print(f"\nRunning test {name}")

        try:
            # Log in to edX
            self.login_ebrains()

            # Call the actual test method
            method(*params)

            # Set output for summary
            success = True
            output = f"{name} ... OK\n"
        except (NoSuchElementException, ElementNotVisibleException, IndexError):
            # Handle the error
            print(f"ERROR for step: {self.step}")
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


@pytest.mark.parametrize(
    "appname,circuit",
    [
        ("check_simui", "CA1"),
        ("check_simui", "MICRO"),
        ("start_simui", "CA1"),
        ("start_simui", "MICRO"),
    ],
)
def test_ebrains(selbase, appname, circuit):
    """Tests a service by starting the application and wait until it is running."""
    ebrains = EbrainsTests(selbase, circuit)
    ebrains.perform_test(getattr(ebrains, appname), f"{appname}_{circuit}", circuit)
