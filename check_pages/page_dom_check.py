"""DOM checker for portal pages.

The code will load random pages and checks for expected DOM elements.
"""
# pylint: disable=R0913

import sys
import json
import time
import random
from io import BytesIO
from PIL import Image

import click
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from seleniumwire import webdriver
from seleniumbase import BaseCase


class BaseTestCase(BaseCase):
    """Defines the seleniumbase driver class."""

    def get_new_driver(self, *args, **kwargs):
        """ This method overrides get_new_driver() from BaseCase. """
        # Enable browser logging
        d = DesiredCapabilities.CHROME
        d["goog:loggingPrefs"] = {"browser": "ALL"}

        options = webdriver.ChromeOptions()
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        if self.headless:
            options.add_argument("--headless")
        return webdriver.Chrome(
            options=options,
            desired_capabilities=d,
            service_args=["--verbose", "--log-path=chromedriver.log"],
            seleniumwire_options={"enable_har": True, "disable_encoding": True}
        )


def get_driver(headless):
    """Runs a single test outside of the py.test environment.

    Replaced elements:
        sb.headless = headless
        sb.page_load_strategy = "none"
    """
    # see https://github.com/seleniumbase/SeleniumBase/blob/master/examples/raw_parameter_script.py
    # see https://github.com/seleniumbase/SeleniumBase/blob/master/help_docs/how_it_works.md
    sb = BaseTestCase()

    sb.browser = "chrome"
    sb.is_behave = False
    sb.headless = headless
    sb.headed = False
    sb.xvfb = False
    sb.start_page = None
    sb.locale_code = None
    sb.protocol = "http"
    sb.servername = "localhost"
    sb.port = 4444
    sb.data = None
    sb.var1 = None
    sb.var2 = None
    sb.var3 = None
    sb.variables = {}
    sb.account = None
    sb.environment = "test"
    sb.user_agent = None
    sb.incognito = False
    sb.guest_mode = False
    sb.devtools = False
    sb.mobile_emulator = False
    sb.device_metrics = None
    sb.extension_zip = None
    sb.extension_dir = None
    sb.database_env = "test"
    sb.log_path = "latest_logs/"
    sb.archive_logs = False
    sb.disable_csp = False
    sb.disable_ws = False
    sb.enable_ws = False
    sb.enable_sync = False
    sb.use_auto_ext = False
    sb.undetectable = False
    sb.no_sandbox = False
    sb.disable_gpu = False
    sb._multithreaded = False
    sb._reuse_session = False
    sb._crumbs = False
    sb._final_debug = False
    sb.visual_baseline = False
    sb.window_size = None
    sb.maximize_option = False
    sb._disable_beforeunload = False
    sb.save_screenshot_after_test = False
    sb.page_load_strategy = "none"
    sb.timeout_multiplier = None
    sb.pytest_html_report = None
    sb.with_db_reporting = False
    sb.with_s3_logging = False
    sb.js_checking_on = False
    sb.recorder_mode = False
    sb.recorder_ext = False
    sb.record_sleep = False
    sb.rec_behave = False
    sb.rec_print = False
    sb.report_on = False
    sb.is_pytest = False
    sb.slow_mode = False
    sb.demo_mode = False
    sb.time_limit = None
    sb.demo_sleep = None
    sb.dashboard = False
    sb._dash_initialized = False
    sb.message_duration = None
    sb.block_images = False
    sb.do_not_track = False
    sb.external_pdf = False
    sb.remote_debug = False
    sb.settings_file = None
    sb.user_data_dir = None
    sb.chromium_arg = None
    sb.firefox_arg = None
    sb.firefox_pref = None
    sb.proxy_string = None
    sb.proxy_bypass_list = None
    sb.proxy_pac_url = None
    sb.swiftshader = False
    sb.ad_block_on = False
    sb.highlights = None
    sb.interval = None
    sb.cap_file = None
    sb.cap_string = None

    # Set up the driver
    sb.setUp()

    # return the driver
    return sb


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
        driver.find_element(By.XPATH, "//*[text()='Allow']").click()
    except exceptions.NoSuchElementException:
        pass


def find_element(driver, method, name):
    """Returns True, if elements exists in webpage, False else.

    Args:
        method (string): Name of the selenium method to find an element.
        name (string): Name of the element to find.
    """
    try:
        driver.find_element(name, by=method, timeout=1.0)
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


def check_url(site, domain, url, checks, wait, screenshots, output, headless):
    """Function to check a single URL."""
    # Get the seleniumbase driver
    driver = get_driver(headless)

    # Create the names used
    complete_url = domain + url
    savename = get_savename(url[1:])

    # Call selenium method to open URL
    driver.get(complete_url)
    time0 = time.time()

    # Allow cookies
    accept_cookies(driver)

    # Prepare the check dict
    check_result = {name: False for name in checks.keys()}

    # Wait a maximum of 'wait' seconds for all element to appear
    timeout = False
    while True:

        # Check all elements
        for name, check in checks.items():
            if not check_result[name]:
                found = False
                for element in check:
                    time_method = time.time()
                    found = find_element(driver, *element)
                    # Increase the 'wait' time by the execution time of 'find_element'
                    # which sometimes can be much longer than the actual timeout.
                    delay_find = time.time() - time_method
                    print(f"    Finding `{element[1]}` took {delay_find:.1f} s. Found: {found}")
                    wait += delay_find

                    if found:
                        break
                check_result[name] = found

        # Get the total time passed for the check of the URL
        time_passed = time.time() - time0

        # Check if we found all elements
        if all(check_result.values()):
            print(f"    At {time_passed:.1f} all elements have been found.")
            break

        # If not, print the missing elements
        missing_elements = [name for name, check in check_result.items() if not check]
        print(f"    At {time_passed:.1f} missing elements are: {missing_elements}.")

        # Make full screenshot if required
        if screenshots:
            filename = f"output/{savename}_{time.time()-time0:.1f}.png"
            make_full_screenshot(driver, filename)

        # Check if wait time has elapsed
        if time_passed > wait:
            print(f"    Timeout after {time_passed:.1f} s (wait time: {wait:.1f} s).")
            timeout = True
            break

        time.sleep(1)

    if timeout:
        # Not all elements found after time limit
        filename = f"output/{savename}_{time.time()-time0:.1f}_error.png"
        make_full_screenshot(driver, filename)

        errors = []
        for element, found in check_result.items():
            if not found:
                errors.append(element)

        print(f"    ERROR: Elements missing after {time.time()-time0:.1f} s: {errors}")
        write_errors(output, site, complete_url, errors)
    else:
        if screenshots:
            filename = f"output/{savename}_{time.time()-time0:.1f}_ok.png"
            make_full_screenshot(driver, filename)

    browser_log = driver.driver.get_log("browser")
    with open(f"output/{savename}.json", "w") as outfile:
        json.dump(browser_log, outfile)
    with open(f"output/{savename}.har", "w") as outfile:
        json.dump(driver.driver.har, outfile)

    if timeout:
        for entry in browser_log:
            if entry['level'] == "SEVERE":
                print(f"    console: {entry['level']}  {entry['source']}: {entry['message']}")

    driver.driver.quit()
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
@click.option(
    "--headless", is_flag=True, help="Runs the tests without browser."
)
@click.option("--screenshots", is_flag=True, help="Will make screenshots.")
def page_check(domain, use_all, number, wait, params, group, output, headless, screenshots):
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
            selected_urls = urls[:number]
        print(f"\nAnalyzing {len(selected_urls)} URLs for {site}")

        # Create hashable keys
        checks = {"_".join(check[0]): check for check in page["checks"]}

        # Now check all elements in the given page
        for index, url in enumerate(selected_urls):
            print(f"{site} {index+1}/{number} - Checking {url}")

            counter = 1
            while counter < 5:
                try:
                    has_error |= check_url(
                        site, domain, url, checks, wait, screenshots, output, headless
                    )
                    break
                except exceptions.WebDriverException as e:
                    print(f"    #{counter}  UNEXPECTED ERROR: {e}")
                    has_error = True
                counter += 1

    # User output
    if has_error:
        print("Errors have been found")
        sys.exit(1)
    print("\npage_dom_check was OK")
