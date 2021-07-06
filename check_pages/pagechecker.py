"""
Code to check all or randomly selected URLs given in file(s).
"""
import sys
import glob
import time
import random

import click
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions


def get_requests(url, interceptor):
    """Returns all requests for the specified URL.

    Args:
        url (string): The URL to be checked.
        interceptor (function): Function to inject header elements for each request.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    # Load the URL
    driver.request_interceptor = interceptor
    try:
        driver.get(url)
    except exceptions.WebDriverException:
        print(">> Webdriver exception for URL '%s'" % url)

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
                "status": request.response.status_code
            }
            request_list.append(myreq)
    driver.quit()
    print("** Analyzing %s created %d requests." % (url.strip(), len(request_list)))
    return request_list


@click.command()
@click.option(
    "-d",
    "--domain",
    help="Defines the domain URL.",
)
@click.option(
    "-f",
    "--file",
    help="Defines a file with a list of URL's.",
)
@click.option(
    "--folder",
    help="Defines a folder containing files with URL lists.",
)
@click.option(
    "-n",
    "--number",
    default=0,
    help="Defines the number of randomly selected URL's to check. Default: 0 (all).",
)
@click.option(
    "-H",
    "--header",
    multiple=True,
    help="Adds a header used for each request in the format KEY:VALUE.",
)
@click.option(
    "-o",
    "--output",
    help="Defines the output filename.",
    default="pagechecker.log"
)
@click.argument(
    "url",
    required=False
)
def linkchecker(domain, file, folder, number, header, output, url):
    """Main linkchecker method.

    Args:
        domain (string): The domain added to each URL.
        file (string): Name of a file containing a list of URL's to test.
        folder (string): Name of the folder containing URL files.
        number (string): Number of URL's to check.
        header (string): Optional header used for each request (e.g. for authorization)
        output (string): Name for the output file.
        url (string): Single URL (e.g. for testing purposes)
    """

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
        raise ValueError("Must specify either an url, or one of the option 'urls' or 'folder'.")

    # Add the domain
    if domain:
        urls = [domain + url for url in urls]

    # Define the interceptor to inject headers into each request
    def interceptor(request):
        for header_item in header:
            key, value = header_item.split(":")
            request.headers[key] = value

    # Select the sample
    if number == 0:
        selected_urls = urls
    else:
        selected_urls = random.sample(urls, number)
    print("Analyzing %d URL's" % len(selected_urls))

    # Check each URL
    errors = []
    for use_url in selected_urls:
        req = get_requests(use_url, interceptor)
        for request in req:
            if request["status"] >= 400:
                msg = f"ERROR {request['status']} -> {request['url']}  from {use_url}"
                print(msg)
                errors.append(msg)

    with open(output, "w") as fileout:
        for error in errors:
            fileout.write(error + "\n")

    if errors:
        sys.exit(1)
