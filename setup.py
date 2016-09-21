#!/usr/bin/python

from setuptools import setup, find_packages
from pip.req import parse_requirements

version = "0.1.0"

requirements = parse_requirements("requirements.txt", session=False)

setup(
    name = 'reportingclient',
    version = version,
    packages = find_packages(),
    author = "NCI Cloud team",
    author_email = "cloud.team@nci.org.au",
    description = "OpenStack Reporting system client library",
    license = "Apache 2.0",
    scripts = ['reporting_example.py'],
    install_requires = [str(r.req) for r in requirements],
)
