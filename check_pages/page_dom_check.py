"""DOM checker for portal pages.

The code will load random pages and checks for expected DOM elements.
"""

import re
import sys
import json
import time
import random
from io import BytesIO
from PIL import Image

import click
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.chrome.options import Options


def make_full_screenshot(driver, savename):
    """Performs a full screenshot of the entire page.
    Taken from https://gist.github.com/fabtho/13e4a2e7cfbfde671b8fa81bbe9359fb
    """
    print(f"Taking full screenshot: {savename}")
    # initiate value
    img_li = []  # to store image fragment
    offset = 0  # where to start

    # js to get height of the window
    try:
        height = driver.execute_script(
            "return Math.max(" "document.documentElement.clientHeight, window.innerHeight);"
        )
    except exceptions.WebDriverException:
        return

    # js to get the maximum scroll height
    # Ref--> https://stackoverflow.com/questions/17688595/
    #        finding-the-maximum-scroll-position-of-a-page
    max_window_height = driver.execute_script(
        "return Math.max("
        "document.body.scrollHeight, "
        "document.body.offsetHeight, "
        "document.documentElement.clientHeight, "
        "document.documentElement.scrollHeight, "
        "document.documentElement.offsetHeight);"
    )

    # looping from top to bottom, append to img list
    # Ref--> https://gist.github.com/fabtho/13e4a2e7cfbfde671b8fa81bbe9359fb
    header_height = 0
    while offset < max_window_height:
        driver.execute_script(f"window.scrollTo(0, {offset});")
        time.sleep(2)

        # get the screenshot of the current window
        img = Image.open(BytesIO((driver.get_screenshot_as_png())))
        img_li.append(img)
        offset += height - header_height

    # Stitch image into one, set up the full screen frame
    img_frame_height = sum([img_frag.size[1] for img_frag in img_li])
    img_frame = Image.new("RGB", (img_li[0].size[0], img_frame_height))
    offset = 0
    counter = 0
    for img_frag in img_li:
        # image fragment must be cropped in case the page is a jupyter notebook;
        # also make sure the last image fragment gets added correctly to avoid overlap.
        offset1 = offset + img_frag.size[1]
        if offset1 > max_window_height:
            top_offset = img_frag.size[1] - max_window_height + offset
            box = (0, top_offset, img_frag.size[0], img_frag.size[1])
        else:
            box = (0, header_height, img_frag.size[0], img_frag.size[1])
        img_frame.paste(img_frag.crop(box), (0, offset))
        offset += img_frag.size[1] - header_height
        counter += 1
    img_frame.save(savename)


def get_savename(text):
    """Return a simplified name for saving."""
    for ch in ['/', '-', '=', '?', '&']:
        if ch in text:
            text = text.replace(ch, "_")
    text = text.replace("-", "")
    return text


def accept_cookies(driver):
    """Safely accepting the possible cookies popup."""
    try:
        driver.find_element_by_xpath("//*[text()='Allow']").click()
    except exceptions.NoSuchElementException:
        pass


def find_element(driver, method, name):
    """Returns True, if elements exists in webpage, False else.

    Args:
        method (string): Name of the selenium method to find an element.
        name (string): Name of the element to find.
    """
    try:
        driver.find_element(method, name)
        return True
    except exceptions.NoSuchElementException:
        return False


def write_errors(filename, site, url, errors):
    """Adds a new entry to the output file when an expected ID is not found.

    Args:
        filename (string): Output filename.
        site (string): The portal site the error has been found on.
        url (string): The exact URL on which the error has been found.
        errors (list): The element(s) that were not found.
    """
    with open(filename, "a+") as fileout:
        fileout.write(f"{site} -> {url}: {errors}\n")


@click.command()
@click.option(
    "-d",
    "--domain",
    help="Defines the domain URL.",
)
@click.option(
    "--use_all",
    is_flag=True,
    help="Will check all URLs.",
)
@click.option(
    "-n",
    "--number",
    default=5,
    help="Defines the number of randomly selected URL's to check per site. Default: 5",
)
@click.option(
    "-w",
    "--wait",
    default=20,
    help="Defines the maximum time to wait for an element to appear [seconds]. Default: 20 s",
)
@click.option(
    "-p",
    "--params",
    help="Defines the json files containing the parameters; the URLs and elements to check.",
)
@click.option(
    "-o",
    "--output",
    help="Defines the output filename.",
    default="page_dom_check.log"
)
@click.option(
    "--screenshots",
    is_flag=True,
    help="Will make screenshots.",
)
def page_check(domain, use_all, number, wait, params, output, screenshots):
    """The main code to check elements in some/all URL's of a portal.
    """
    has_error = False

    # Read the page data from the given json
    with open(params) as json_file:
        page_data = json.load(json_file)

    # Initialize selenium driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    # Loop over the page sections
    for site, page in page_data.items():
        # Read all URL's
        with open(page["urls"]) as filein:
            urls = filein.read().splitlines()

        # Select the URL's to check
        if use_all:
            selected_urls = urls
        else:
            selected_urls = random.sample(urls, number)
        print(f"\nAnalyzing {len(selected_urls)} URLs for {site}")

        # Get all elements to be checked for this set of URLs
        elements = [("id", element) for element in page["ids"]]
        elements.extend([("class name", element) for element in page["classes"]])

        # Now check all elements in the given page
        for url in selected_urls:
            # Load the URL
            complete_url = domain + url
            savename = get_savename(url[1:])
            time.sleep(5)
            driver.get(complete_url)
            time.sleep(5)
            # Allow cookies
            accept_cookies(driver)

            # Wait a maximum of 'wait' seconds for an element to appear
            elements_check = {element: False for element in elements}
            counter = 0
            for _ in range(wait):
                # Check missing elements
                for element in elements:
                    if not elements_check[element]:
                        elements_check[element] = find_element(driver, *element)

                # Check if we found all elements
                if all(elements_check.values()):
                    print(f"All elements found for {site} after {counter} s, URL: {complete_url}")
                    break

                time.sleep(1)
                counter += 1
                if screenshots:
                    make_full_screenshot(driver, f"screenshots/{savename}_{counter}.png")
            else:
                # Not all elements found after time limit: we have a missing element
                has_error = True
                print(f"ERROR {site} with URL '{complete_url}':")

                screenshot_name = re.sub(r"[/\&\?=]", "_", url[1:]) + ".png"
                counter = 0
                while counter < 5:
                    try:
                        driver.save_screenshot(screenshot_name)
                        print("Screenshot was successful.")
                        break
                    except exceptions.WebDriverException:
                        print(f"ERROR taking screenshot, try {counter}")
                        counter += 1
                        time.sleep(1)

                errors = []
                for element, found in elements_check.items():
                    if not found:
                        errors.append(element)
                        print(f"    Not found: {element}")
                write_errors(output, site, url, errors)

    # Quit webdriver
    driver.quit()

    # User output
    if has_error:
        print("Errors have been found")
        sys.exit(1)
    print("Page check was OK")
