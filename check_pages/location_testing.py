"""Code to perform API performance testing of some URL in different worldwide locations
"""
import os
import json
from threading import Thread
from queue import Queue
import click
import requests

from check_pages import gtmetrix

FORM_ENDPOINT = (
    "https://docs.google.com/forms/u/0/d/e/"
    "1FAIpQLScTLaWu1wk6xCACiQ-FBKY8qncZoCkmmPYYz-8tTrPSsSvb4Q/formResponse"
)


def test_worker(gt, location_queue, domain, test_urls, HTTP_AUTH, portal, timestamp):
    """
    Checking the URLs based in order based on locacation
    """
    while not location_queue.empty():
        loc_number, location = location_queue.get()
        for test_url in test_urls:
            url = domain + test_url
            test_id = gt.test(url, location=loc_number, auth=HTTP_AUTH)
            if test_id is not None:
                print(f"Started test for {location}: {url}")
                gt.wait_test(test_id)
                print(f"Test for {location}: {url} completed")

                # Retrieve the metrics
                result = gt.request(f"tests/{test_id}")
                print(result)  # Print the API response for debugging purposes

                # Retrieve the metrics
                result = gt.request(f"tests/{test_id}")
                metrics = result["data"]["attributes"]
                time0_fb = metrics["time_to_first_byte"]
                time1_fcp = metrics["first_contentful_paint"]
                time2_dcl = metrics["dom_content_loaded_time"]
                time3_onload = metrics["onload_time"]
                time4_flt = metrics["fully_loaded_time"]
                number_requests = metrics["page_requests"]
                bytes_page = metrics["page_bytes"]

                print(f"Testing {location}: {url}  Test ID {test_id}")
                print(
                    f"   TTFB {time0_fb} | FCP: {time1_fcp} | DCL: {time2_dcl} | "
                    f"Onload: {time3_onload} | FLT: {time4_flt}"
                )
                print(f"   #requests: {number_requests}  Page bytes: {bytes_page}")

                # Post the results to the Google Form
                files = {
                    "entry.231103326": (None, portal),
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

        location_queue.task_done()


@click.command()
@click.option(
    "-p",
    "--params",
    help="Defines the json files containing the URLs to use for the test.",
)
@click.option(
    "--portal",
    help="Defines the portal tested.",
)
@click.option(
    "--test/--no-test",
    default=False,
    help="When set, will only use on location for one URL.",
)
def location_test(params, portal, test):
    """Performs the location performance test.

    Args:
        params (string): Name of the json file containing the testing data.
    """
    # Get variables
    USER_EMAIL = os.environ["GTMETRIX_USER"]
    API_KEY = os.environ["GTMETRIX_APIKEY"]
    if "HTTP_AUTH_LOGIN" in os.environ and "HTTP_AUTH_PASSWD" in os.environ:
        HTTP_AUTH = (os.environ["HTTP_AUTH_LOGIN"], os.environ["HTTP_AUTH_PASSWD"])
    else:
        HTTP_AUTH = None
    # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Read the json data
    with open(params) as filein:
        parameter = json.load(filein)
    domain = parameter["domain"]
    test_urls = parameter["urls"]

    # Instantiate GTMetrix object
    gt = gtmetrix.GTMetrix(USER_EMAIL, API_KEY)
    print(f"Credits left for testing: {gt.credits()}")

    if test:
        test_urls = [test_urls[0]]
        locations = [list(gt.LOCATIONS.items())[0]]
    else:
        locations = gt.LOCATIONS.items()

    # Loop over the URLS to be tested and the location
    # for test_url in test_urls:
    #
    #     url = domain + test_url
    #     for loc_number, location in locations:
    #
    #         # Start and wait for the test to be finished
    #         test_id = gt.test(url, location=loc_number, auth=HTTP_AUTH)
    #         result = gt.wait_test(test_id)

    location_queue = Queue()
    for loc_number, location in locations:
        location_queue.put((loc_number, location))

    num_threads = min(len(locations), 2)  # Maximum 2 concurrent tests
    threads = []
    for _ in range(num_threads):
        thread = Thread(target=test_worker,
                        args=(gt, location_queue, domain, test_urls, HTTP_AUTH))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    print(f"Credits left for testing: {gt.credits()}")
    if __name__ == "__main__":
        location_test()
