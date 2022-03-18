"""DOM checker for portal pages.

The code will load random pages and checks for expected DOM elements.
"""

import sys
import json
import time
import random
from io import BytesIO
import psutil
from PIL import Image

import click
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from seleniumbase import get_driver


def make_full_screenshot(driver, savename):
    """Performs a full screenshot of the entire page.
    Taken from https://gist.github.com/fabtho/13e4a2e7cfbfde671b8fa81bbe9359fb
    """
    # initiate value
    img_list = []  # to store image fragment
    offset = 0  # where to start

    # js to get height of the window
    try:
        height = driver.execute_script(
            "return Math.max("
            "document.documentElement.clientHeight, window.innerHeight);"
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
        time.sleep(1)

        # get the screenshot of the current window
        img = Image.open(BytesIO((driver.get_screenshot_as_png())))
        img_list.append(img)
        offset += height - header_height

    # Stitch image into one, set up the full screen frame
    img_frame_height = sum([img_frag.size[1] for img_frag in img_list])
    img_frame = Image.new("RGB", (img_list[0].size[0], img_frame_height))

    offset = 0  # offset used to create the snapshots
    img_loc = 0  # offset used to create the final image
    for img_frag in img_list:
        # image fragment must be cropped in case the page is a jupyter notebook;
        # also make sure the last image fragment gets added correctly to avoid overlap.
        offset1 = offset + height
        if offset1 > max_window_height:
            top_offset = offset + height - max_window_height
            box = (0, top_offset, img_frag.size[0], img_frag.size[1])
        else:
            box = (0, header_height, img_frag.size[0], img_frag.size[1])
        img_frame.paste(img_frag.crop(box), (0, img_loc))
        img_loc += img_frag.size[1] - header_height
        offset += height - header_height

    # Save the final image
    img_frame.save(savename)


def get_savename(text):
    """Return a simplified name for saving."""
    for ch in ["/", "-", "=", "?", "&"]:
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


def check_url(site, domain, url, checks, wait, screenshots, output):
    """Function to check a single URL."""

    ram = float(psutil.virtual_memory().available) / 1048576.0
    print(f"available ram: {ram:.1f} MB")

    # enable browser logging
    d = DesiredCapabilities.CHROME
    d["loggingPrefs"] = {"browser": "ALL"}

    # Initialize selenium driver
    time.sleep(5)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--dns-prefetch-disable")
    driver = webdriver.Chrome(
        options=chrome_options,
        desired_capabilities=d,
        service_args=["--verbose", "--log-path=chromedriver.log"],
    )

    # driver = get_driver("chrome", headless=True)

    # Create the names used
    complete_url = domain + url
    savename = get_savename(url[1:])

    # Call selenium method to open URL
    driver.get(complete_url)
    time0 = time.time()
    time.sleep(5)

    # Allow cookies
    accept_cookies(driver)

    # Prepare the check dict
    check_result = {name: False for name in checks.keys()}

    # Wait a maximum of 'wait' seconds for all element to appear
    timeout = False
    t_end = time.time() + wait
    while True:
        # Check all elements
        for name, check in checks.items():
            if not check_result[name]:
                found = False
                for element in check:
                    if find_element(driver, *element):
                        found = True
                        break
                check_result[name] = found

        # Check if we found all elements
        if all(check_result.values()):
            print(f"    All elements found after {time.time()-time0:.1f} s")
            break

        # Make full screenshot if required
        if screenshots:
            filename = f"screenshots/{savename}_{time.time()-time0:.1f}.png"
            make_full_screenshot(driver, filename)

        # Check if wait time has elapsed
        time.sleep(1)
        if time.time() > t_end:
            timeout = True
            break

    if timeout:
        # Not all elements found after time limit
        filename = f"screenshots/{savename}_{time.time()-time0:.1f}_error.png"
        make_full_screenshot(driver, filename)

        errors = []
        for element, found in check_result.items():
            if not found:
                errors.append(element)

        print(f"    ERROR: Elements missing after {time.time()-time0:.1f} s: {errors}")
        write_errors(output, site, complete_url, errors)
    else:
        filename = f"screenshots/{savename}_{time.time()-time0:.1f}_ok.png"
        make_full_screenshot(driver, filename)

    driver.quit()
    return timeout


@click.command()
@click.option("-d", "--domain", help="Defines the domain URL.")
@click.option("--use_all", is_flag=True, help="Will check all URLs.")
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
    "-g",
    "--group",
    help="Defines the group to be tested. Only pages from this group will be tested.",
)
@click.option(
    "-o", "--output", help="Defines the output filename.", default="page_dom_check.log"
)
@click.option("--screenshots", is_flag=True, help="Will make screenshots.")
def page_check(domain, use_all, number, wait, params, group, output, screenshots):
    """The main code to check elements in some/all URL's of a portal.
    """
    has_error = False

    # Read the page data from the given json
    with open(params) as json_file:
        page_data = json.load(json_file)

    # Select the group to be tested
    if group:
        print(f"Checking only group {group}.")
        page_data = {group: page_data[group]}

    # Loop over the page sections
    for site, page in page_data.items():
        # Read all URL's
        with open(page["urls"]) as filein:
            urls = filein.read().splitlines()

        # Select the URL's to check
        if use_all:
            selected_urls = urls
        else:
            selected_urls = random.sample(urls, min(len(urls), number))
        print(f"\nAnalyzing {len(selected_urls)} URLs for {site}")

        # Create hashable keys
        checks = {"_".join(check[0]): check for check in page["checks"]}

        # Now check all elements in the given page
        for url in selected_urls:
            print(f"Checking {url}")

            counter = 1
            while counter < 5:
                try:
                    has_error |= check_url(
                        site, domain, url, checks, wait, screenshots, output
                    )
                    break
                except exceptions.WebDriverException as e:
                    print(f"    #{counter}  UNEXPECTED ERROR: {e}")
                counter += 1

    # User output
    if has_error:
        print("Errors have been found")
        sys.exit(1)
    print("\npage_dom_check was OK")
