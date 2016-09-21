#!/usr/bin/python

"""
Application metadata.
"""

from setuptools import setup, find_packages
from pip.req import parse_requirements

VERSION = "0.1.0"

setup(
    name='reportingclient',
    version=VERSION,
    packages=find_packages(),
    author="NCI Cloud team",
    author_email="cloud.team@nci.org.au",
    description="OpenStack Reporting system client library",
    license="Apache 2.0",
    scripts=['reporting_example.py'],
    install_requires=[
        str(r.req) for r in parse_requirements(
            "requirements.txt", session=False
        )
    ]
)
