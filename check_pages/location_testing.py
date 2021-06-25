"""Code to perform API performance testing of some URL in different worldwide locations
"""
import os
import json
import datetime

import click
import requests

from check_pages import gtmetrix

FORM_ENDPOINT = (
    "https://docs.google.com/forms/u/0/d/e/"
    "1FAIpQLScTLaWu1wk6xCACiQ-FBKY8qncZoCkmmPYYz-8tTrPSsSvb4Q/formResponse"
)


@click.command()
@click.option(
    "-p",
    "--params",
    help="Defines the json files containing the URLs to use for the test.",
)
def location_test(params):
    """Performs the location performance test.

    Args:
        params (string): Name of the json file containing the testing data.
    """
    # Get variables
    USER_EMAIL = os.environ["GTMETRIX_USER"]
    API_KEY = os.environ["GTMETRIX_APIKEY"]
    HTTP_AUTH = (os.environ["HTTP_AUTH_LOGIN"], os.environ["HTTP_AUTH_PASSWD"])

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Read the json data
    with open(params) as filein:
        parameter = json.load(filein)
    domain = parameter["domain"]
    test_urls = parameter["urls"]

    # Instantiate GTMetrix object
    gt = gtmetrix.GTMetrix(USER_EMAIL, API_KEY)
    print("Credits left for testing: %f" % gt.credits())

    # Loop over the URLS to be tested and the location
    for test_url in test_urls:

        url = domain + test_url
        for loc_number, location in gt.LOCATIONS.items():

            # Start and wait for the test to be finished
            test_id = gt.test(url, location=loc_number, auth=HTTP_AUTH)
            result = gt.wait_test(test_id)

            # Retrieve the metrics
            metrics = result["attributes"]
            time0_fb = metrics["time_to_first_byte"]  # time to first byte
            time1_fcp = metrics["time_to_first_byte"]  # time to first contentful paint
            time2_dcl = metrics["dom_content_loaded_time"]  # time to dom content loaded
            time3_onload = metrics["onload_time"]  # time onload
            time4_flt = metrics["fully_loaded_time"]  # time to fully loaded

            number_requests = metrics["page_requests"]
            bytes_page = metrics["page_bytes"]

            print(f"Testing {location}: {url}  Test ID {test_id}")
            print(
                f"   TTFB {time0_fb} | FCP: {time1_fcp} | DCL: {time2_dcl} | "
                f"Onload: {time3_onload} | FLT: {time4_flt}"
            )
            print(f"   #requests: {number_requests}  Page bytes: {bytes_page} ")

            # Post the results to the google form
            files = {
                "entry.730635873": (None, timestamp),
                "entry.2044683746": (None, url),
                "entry.537616198": (None, location),
                "entry.1913486253": (None, test_id),
                "entry.2051253403": (None, time0_fb),
                "entry.233018127": (None, time1_fcp),
                "entry.1934771090": (None, time2_dcl),
                "entry.1055212914": (None, time3_onload),
                "entry.2050306922": (None, time4_flt),
                "entry.914840766": (None, number_requests),
                "entry.1179656135": (None, bytes_page),
            }
            response = requests.post(FORM_ENDPOINT, files=files)
            print(f"Result of Post: {response.reason}")

    print("Credits left for testing: %f" % gt.credits())
