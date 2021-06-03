
import sys
import glob
import time
import random
import logging
import click
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options


L = logging.getLogger(__name__)


def get_requests(url, interceptor):
    """Returns all requests for the specified URL.

    Args:
        url: The URL to be checked
        interceptor: Function to insert header elements
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    # Load the URL
    driver.request_interceptor = interceptor
    driver.get(url)

    numbers = len(driver.requests)
    while True:
        time.sleep(5)
        if len(driver.requests) == numbers:
            break
        numbers = len(driver.requests)

    
    # Access requests via the `requests` attribute
    requests = []
    for request in driver.requests:
        if request.response:
            myreq = {
                "url": request.url,
                "headers": dict(request.headers),
                "method": request.method,
                "status": request.response.status_code
            }
            requests.append(myreq)
    driver.quit()
    L.info("** Analyzing %s created %d requests.", url.strip(), len(requests))
    return requests


@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="-v for DEBUG",
)
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
@click.argument(
    "url",
    required=False
)
def linkchecker(verbose, domain, file, folder, number, header, url):
    """Main linkchecker mehthod.

    Args:
        verbose: Defines the logging level
        domain: The domain added to each URL
        urls: Name of a file containing a list of URL's to test
        folders: Name of the folder containing URL files
        number: Number of URL's to check
        header: Optional header used for each request
        url: Single URL (e.g. for testing purposes)
    """

    # Set the logging level
    level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 2)]
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')


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
        urls = [domain+url for url in urls]

    # Define the interceptor to inject headers into each request
    def interceptor(request):
        for header_item in header:
            key, value = header_item.split(":")
            request.headers[key] = value

    # Select the sample
    if number==0:
        selected_urls = urls
    else:
        selected_urls = random.sample(urls, number)
    L.info("Analyzing %s URL's", len(selected_urls))

    # Check each URL
    errors = []
    status_code = 0
    for url in selected_urls:
        req = get_requests(url, interceptor)
        for request in req:
            if request["status"] >= 400:
                L.error(f"{request['status']} -> {request['url']}  from {url}")
                errors.append(f"{request['status']} -> {request['url']}  from {url}")
                status_code = 1

    with open("errors.list", "w") as fileout:
        for error in errors:
            fileout.write(error + "\n")


if __name__ == "__main__":
    linkchecker()