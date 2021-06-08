"""Code to report results on slack.
"""
import os
import sys
import click
import requests


@click.command()
@click.option(
    "-o",
    "--ok_url",
    help="Defines the URL to be used in case the check was OK.",
)
@click.option(
    "-e",
    "--err_url",
    help="Defines the URL to be used in case the check was NOK.",
)
@click.option(
    "-n",
    "--name",
    help="Defines the name to give to this check.",
)
@click.option(
    "-f",
    "--file",
    help="Defines the file to be used in case of failure.",
)
@click.option(
    "-s",
    "--status",
    help="Exit code of previous command (by using '$?'').",
)
def slack_report(ok_url, err_url, name, file, status):
    """Main linkchecker mehthod.

    Args:
        ok_url: Url to use of the check was OK
        err_url: Url to use of the check was NOK
        name: Name to use for this check (e.g. SSCX, Portal)
        filename: Filename whose content gets added to the slack message in case of failure
        status: Exit code from the previous command (by using $?).
    """

    # get status code from env variable
    #prev = os.environ["PREV_COMMAND"]

    if int(status)==0:
        print("Check was OK")
        url = ok_url
        text = f"{name} OK"
        data = {'text': text, 'icon_emoji': ':frog:', 'username': name}
    else:
        print("Check was NOK")
        with open(file) as filein:
            errors = filein.read()
        text = f"*** {name} ERROR:\n{errors}"
        #error_list = "\n".join(errors)
        #text = f'*** SSCX Portal Check NOK.\n${error_list}'
        url = err_url
        data = {'text': text, 'icon_emoji': ':crab:', 'username': name}
    resp = requests.post(url, json=data)
    print(resp.status_code)


if __name__ == "__main__":
    slack_report()