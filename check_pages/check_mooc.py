"""
Performs MOOC Tests, i.e. accessing various applications and obtaining relevant keys
"""
import sys
import json

import click

from check_pages import mooc_tools


@click.command()
@click.option(
    "-t",
    "--tests",
    help="Defines the json files containing the test parameters.",
)
@click.option(
    "-o",
    "--output",
    default="mooc_results.txt",
    help="Defines the results output filename.",
)
@click.option(
    "--headless/--no-headless",
    default=False,
    help="Starts the test in a headless browser.",
)
def mooc_checking(tests, output, headless):
    """Performs the MOOC checks of application and services."""
    
    # Read the MOOC tests
    with open(tests) as f:
        tests = json.load(f)

    # Setup the MOOC driver including edX login
    mooc = mooc_tools.MoocChecker(headless)

    # Perform the grade submission test
    mooc.test_grade_submission()

    # Perform the other tests
    for name, params in tests.items():
        mooc.test_page(name, params)

    # Quit the browser
    mooc.browser.quit()

    # Write all results to a file
    with open(output, "w") as fileout:
        fileout.write(mooc.output)

    # Exit the code
    if mooc.error:
        sys.exit(1)
    sys.exit(0)
