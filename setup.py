#!/usr/bin/env python

from setuptools import setup, find_packages

from check_pages.version import VERSION


setup(
    name='check-pages',
    version=VERSION,
    install_requires=[
        'click>=7.0',
        'requests',
        'selenium'
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "check_pages.resources": ["*"]
    },
    author='BlueBrain NSE',
    author_email='bbp-ou-nse@groupes.epfl.ch',
    description='NSE Page checking tool',
    license='BBP-internal-confidential',
    url='http://bluebrain.epfl.ch',
    entry_points={
        'console_scripts': [
            'pagechecker=check_pages.pagechecker:linkchecker',
            'page_dom_check=check_pages.page_dom_check:page_check',
            'slack_reporter=check_pages.slack_reporter:slack_report',
            'location_test=check_pages.location_testing:location_test'
        ],
    }
)
