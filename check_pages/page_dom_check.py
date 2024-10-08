# Copyright (c) 2024 Blue Brain Project/EPFL
#
# SPDX-License-Identifier: Apache-2.0

"""DOM checker for portal pages.

The code will load random pages and checks for expected DOM elements.
"""
# pylint: disable=R0913

import time
import json
import random
from io import BytesIO
from PIL import Image
import pytest
from selenium.common import exceptions
from seleniumbase.common import exceptions as sb_exceptions

LOG_OUTPUT = "page_dom_check.log"


@pytest.hookimpl
def pytest_generate_tests(metafunc):
    """Sets the parameters dynamically for the fixture 'testparam' used for "test_mooc_service".

    Whenever pytest calls a test function, and this function requires the fixture 'testparam',
    a list of parameters are set that are being read from the json file.
    """
    if "testparam" in metafunc.fixturenames:
        params_file = metafunc.config.option.params
        group = metafunc.config.option.group
        number = metafunc.config.option.number
        use_all = metafunc.config.option.use_all

        # Read the page data from the given json
        with open(params_file) as json_file:
            page_data = json.load(json_file)

        # Select the group to be tested
        if group:
            print(f"Checking only group {group}.")
            page_data = {group: page_data[group]}

        # Loop over the page sections
        tests = {}
        for site, page in page_data.items():
            # Read all URL's
            with open(page["urls"]) as filein:
                urls = filein.read().splitlines()

            # Select the URL's to check
            if use_all:
                selected_urls = urls
            else:
                selected_urls = random.sample(urls, min(len(urls), number))
                selected_urls = urls[:number]
            print(f"\nAnalyzing {len(selected_urls)} URLs for {site}")

            for index, url in enumerate(selected_urls):
                # Create a unique test id (as key)
                id_ = f"{site}_{index}"

                # Create hashable keys for every check to be done for the given URL
                checks = {"_".join(check[0]): check for check in page["checks"]}

                # Add the test to the list of tests
                test_data = (site, url, checks)
                tests[id_] = test_data

        # add parametrization for fixture
        metafunc.parametrize("testparam", tests.items(), ids=tests.keys())


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
        img = Image.open(BytesIO((driver.driver.get_screenshot_as_png())))
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
        driver.click_xpath("//*[text()='Allow']")
        # driver.find_element(By.XPATH, "//*[text()='Allow']").click()
        # //*[@id="__next"]/div[6]/div/div[3]/a/span
    except exceptions.NoSuchElementException:
        pass


def find_element(driver, method, name):
    """Returns True, if elements exists in webpage, False else.

    Args:
        driver: Selenium WebDriver instance
        method (string): Name of the selenium method to find an element.
        name (string): Name of the element to find.
    """
    try:
        driver.find_element(name, by=method, timeout=1.0)
        return True
    except exceptions.NoSuchElementException:
        return False
    except sb_exceptions.NoSuchElementException:
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


def check_url(driver, site, domain, url, checks, wait, screenshots):
    """Function to check a single URL."""

    time0 = time.time()

    def debug(txt):
        time_now = time.time() - time0
        print(f"    {time_now:.1f} - {txt}")

    # Create the names used
    complete_url = domain + url
    savename = get_savename(url[1:])

    # Call selenium method to open URL
    debug(f"Opening URL {complete_url}")
    driver.open(complete_url)

    # Allow cookies
    debug("Accepting cookies")
    accept_cookies(driver)

    # Prepare the check dict
    check_result = {name: False for name in checks.keys()}

    # Wait a maximum of 'wait' seconds for all element to appear
    success = True
    while True:

        # Check all elements
        debug("Trying to find the elements")
        time.sleep(1)
        for name, check in checks.items():
            if not check_result[name]:
                found = False
                for element in check:
                    time_method = time.time()
                    found = find_element(driver, *element)
                    # Increase the 'wait' time by the execution time of 'find_element'
                    # which sometimes can be much longer than the actual timeout.
                    delay_find = time.time() - time_method
                    debug(
                        f"Checking for `{element[1]}` took {delay_find:.1f} s. Found: {found}"
                    )
                    wait += delay_find

                    if found:
                        break
                check_result[name] = found

        # Check if we found all elements
        if all(check_result.values()):
            debug("All elements have been found. Exiting.")
            break

        # If not, print the missing elements
        missing_elements = [name for name, check in check_result.items() if not check]
        debug(f"Missing elements are: {missing_elements}.")

        # Make full screenshot if required
        if screenshots:
            debug("Making screenshot")
            filename = f"output/{savename}_{time.time() - time0:.1f}.png"
            make_full_screenshot(driver, filename)

        # Check if wait time has elapsed
        if time.time() - time0 > wait:
            debug(f"Timeout occurred after wait time: {wait:.1f} s. Exiting")
            success = False
            break

        time.sleep(1)

    if not success:
        # Not all elements found after time limit
        debug("Making full screenshot because of timeout.")
        filename = f"output/{savename}_{time.time() - time0:.1f}_error.png"
        make_full_screenshot(driver, filename)

        errors = []
        for element, found in check_result.items():
            if not found:
                errors.append(element)

        debug(f"ERROR: Elements missing after {time.time() - time0:.1f} s: {errors}")
        write_errors(LOG_OUTPUT, site, complete_url, errors)
    else:
        if screenshots:
            filename = f"output/{savename}_{time.time() - time0:.1f}_ok.png"
            make_full_screenshot(driver, filename)

    browser_log = driver.driver.get_log("browser")
    with open(f"output/{savename}.json", "w") as outfile:
        json.dump(browser_log, outfile)
    # Creation of the HAR file currently not possible
    # with open(f"output/{savename}.har", "w") as outfile:
    #     json.dump(driver.driver.har, outfile)

    if not success:
        for entry in browser_log:
            if entry["level"] == "SEVERE":
                debug(
                    f"console: {entry['level']}  {entry['source']}: {entry['message']}"
                )

    # Close the current driver
    driver.driver.close()
    driver.driver.quit()
    return success


def test_sscx_dom(selbase, test_details, testparam):
    """Runs the tests for the SSCX dom checks."""
    success = True
    wait = test_details["wait"]
    domain = test_details["domain"]

    id_ = testparam[0]
    site, url, checks = testparam[1]

    print(f"Checking {id_}  ->  {url}")
    try:
        success &= check_url(
            selbase,
            site,
            domain,
            url,
            checks,
            wait,
            test_details["screenshots"],
        )
    except exceptions.WebDriverException as e:
        print(f"    UNEXPECTED ERROR: {e}")
        success = False

    # Create the output information for this test
    pytest.test_success &= success
    if success:
        pytest.test_output += f"pass {id_}\n"
    else:
        output = f"FAIL {id_} for URL {domain}{url}"
        pytest.test_output += output + "\n"
