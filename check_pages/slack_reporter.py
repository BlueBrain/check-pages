"""Code to report results on slack.
"""
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
    help="Defines the name of this check.",
)
@click.option(
    "-f",
    "--filename",
    help="Defines the filename whose contents should be shown on slack in case of failure.",
)
@click.option(
    "-m",
    "--message",
    help="Defines the message to be shown on slack in case of failure.",
)
@click.option(
    "-s",
    "--status",
    help="Exit code of previous command (by using '$?'').",
)
def slack_report(ok_url, err_url, name, filename, message, status):
    """Main linkchecker method.

    Args:
        ok_url (string): Url to use of the check was OK
        err_url (string): Url to use of the check was NOK
        name (string): Name to use for this check (e.g. SSCX, Portal)
        filename (string): Filename whose content gets added to the slack message in case of failure
        status (int): Exit code from the previous command (by using $? in the CI).
    """
    if int(status) == 0:
        print("Check was OK")
        url = ok_url
        text = f"{name} OK"
        data = {'text': text, 'icon_emoji': ':frog:', 'username': name}
    else:
        print("Check was NOK")
        if filename:
            with open(filename) as filein:
                msg = filein.read()
        else:
            msg = message
        text = f"*** {name} ERROR:\n{msg}"
        url = err_url
        data = {'text': text, 'icon_emoji': ':crab:', 'username': name}

    print(f"Sending to URL {url}")
    resp = requests.post(url, json=data)
    print(resp.status_code)
