"""
Class for GTMetrix API access.

Documentation: https://gtmetrix.com/api/docs/2.0
Webpage: https://gtmetrix.com/
"""

import os
import json
import time
import base64
from pathlib import Path

import requests


class GTMetrix:
    """Class to handle API testing with GTMetrix."""

    ACCESS_URL = "https://gtmetrix.com/api/2.0/"

    LOCATIONS = {
        1: "Vancouver, CA",
        2: "London, GB",
        4: "San Antonio, US",
        7: "Hong Kong, CN"
    }

    def __init__(self, email=None, api_key=None):
        """Initializes the object with user and api key.

        Args:
            email (string): The email adress associated with the GTMetrix account.
            api_key (string): The API key  associated with the GTMetrix account.
        """
        if email:
            self.email = email
        else:
            self.email = os.environ["GTMETRIX_EMAIL"]
        if api_key:
            self.apikey = api_key
        else:
            self.apikey = os.environ["GTMETRIX_APIKEY"]

        # Define the access header
        self.headers = {
            "Content-Type": "application/vnd.api+json",
            "Authorization": "Basic %s" % base64.b64encode(self.apikey.encode()).decode()
        }

    def request(self, command):
        """Wrapper for making a get request to GTMetrix.

        Args:
            command (string): The GTMetrix command to be executed.
        """
        url = self.ACCESS_URL + command
        response = requests.get(url, headers=self.headers)
        try:
            response_json = response.json()
            return response_json
        except json.JSONDecodeError:
            print(f"JSON decode error for URL '{command}'")
            print(response.text)
            return None

    def credits(self):
        """Return the amount of credits available."""
        response = self.request("status")
        if response:
            return float(response["data"]["attributes"]["api_credits"])
        else:
            return -1

    def test(self, url, location=1, browser=3, auth=None):
        """Start the test of a webpage and returns the test id.

        Args:
            url (string): URL to be tested.
            location (int): Location ID
            browser (int): Browser ID
            auth (list): Pptional tuple for page authorization (username, password)
        """

        # Create the test parameters
        parameters = {
            "data": {
                "type": "test",
                "attributes": {
                    "url": url,
                    "report": "none",
                    "location": str(location),
                    "browser": str(browser)
                }
            }
        }

        # Adding page authorization if needed
        if auth:
            parameters["data"]["attributes"]["httpauth_username"] = auth[0]
            parameters["data"]["attributes"]["httpauth_password"] = auth[1]

        # Run the post request
        response = requests.post(self.ACCESS_URL + "tests", headers=self.headers, json=parameters)
        return response.json()["data"]["id"]

    def wait_test(self, test_id):
        """Waits until the test with the given test ID has finished
        and returns the dict of the result URLs.

        Args:
            test_id (string): The Test ID.
        """
        while True:
            response = self.request(f"tests/{test_id}")
            if response["data"]["type"] == "report":
                break
            time.sleep(3)

        return response["data"]

    def download_pdf(self, link, filename="gtmetrix_report.pdf"):
        """Get the pdf and store its content in a file. Might be used later.

        Args:
            link (string): The link to the pdf as returned from GTMetrix.
            filename (string): The name for the created pdf.
        """
        response = requests.get(link, headers=self.headers)
        filename = Path(filename)
        filename.write_bytes(response.content)
