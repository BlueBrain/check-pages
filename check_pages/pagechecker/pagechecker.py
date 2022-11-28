"""
Code to check all or randomly selected URLs given in file(s) for 4xx/5xx errors.
"""
import sys
import glob
import time
import random
from concurrent import futures

import click
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions


def get_requests(seldriver, url, interceptor):
    """Returns all requests for the specified URL.

    Args:
        seldriver: The seleniumbase driver instance.
        url (string): The URL to be checked.
        interceptor (function): Function to inject header elements for each request.
    """
    # Get the original selenium-wire driver
    driver = seldriver.driver

    # Set the function to inject header elements
    driver.request_interceptor = interceptor

    # Try to open the URL
    try:
        driver.get(url)
    except exceptions.WebDriverException:
        return f"WEBDRIVER EXCEPTION for URL '{url}'"

    numbers = len(driver.requests)
    while True:
        time.sleep(5)
        if len(driver.requests) == numbers:
            break
        numbers = len(driver.requests)

    # Access requests via the `requests` attribute
    request_list = []
    for request in driver.requests:
        if request.response:
            myreq = {
                "url": request.url,
                "headers": dict(request.headers),
                "method": request.method,
                "status": request.response.status_code,
            }
            request_list.append(myreq)
    return request_list


def test_link_checking(selbase, test_details):
    """Main linkchecker method.

    Args:
        selbase: The seleniumbase driver.
        test_details: A dictionary with details of the test to perform.
    """
    domain = test_details["domain"]
    file = test_details["file"]
    folder = test_details["folder"]
    number = test_details["number"]
    header = test_details["header"]
    output = test_details["output"]
    url = test_details["url"]

    if folder:
        files = glob.glob(folder + "/*.txt")
    if file:
        files = [file]

    # Get the URLs
    if url:
        urls = [url]
    elif files:
        urls = []
        for filename in files:
            with open(filename) as filein:
                urls.extend(filein.readlines())
    else:
        raise ValueError(
            "Must specify either an url, or one of the option 'urls' or 'folder'."
        )

    # Add the domain
    if domain:
        # urllib.parse.urljoin cannot be used because of the hash for the NMC portal
        urls = [domain + url for url in urls]

    # Define the interceptor to inject headers into each request
    def interceptor(request):
        if header:
            for header_item in header:
                key, value = header_item.split(":")
                request.headers[key] = value

    # Select the sample
    if number == 0:
        selected_urls = urls
    else:
        selected_urls = random.sample(urls, number)
    print(f"Analyzing {len(selected_urls)} URL's")

    errors = []
    n = len(selected_urls)
    with futures.ThreadPoolExecutor() as executor:
        # Put the functions calls into the pool
        url_requests = [
            executor.submit(get_requests, selbase, use_url, interceptor)
            for use_url in selected_urls
        ]
        # Check the results
        for index, url_request, use_url in zip(range(n), url_requests, selected_urls):
            print(f"Analyzed {index}/{n} -> {use_url.strip()}")
            req = url_request.result()
            if isinstance(req, str):
                print(req)
                errors.append(req)
            else:
                for request in req:
                    if request["status"] >= 400 and request["status"] != 403:
                        msg = (
                            f"ERROR {request['status']} -> {request['url']}  from {use_url}"
                        )
                        print(msg)
                        errors.append(msg)

    # Write any error to a file (for slack)
    with open(output, "w") as fileout:
        for error in errors:
            fileout.write(error + "\n")

    if errors:
        sys.exit(1)
