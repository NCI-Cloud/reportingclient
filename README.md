python-reportingclient
======================

Client for [reporting-api](https://github.com/NeCTAR-RC/reporting-api).

Requirements:

* Python 2.7
* [Requests](http://python-requests.org) Python library
* [Python Keystone client](https://pypi.python.org/pypi/python-keystoneclient)


reportingclient
---------------

This package contains a Python client for the reporting API.

reporting_example.py
--------------------

This script is an example of using the Python client library to query
the reporting API.
It can either display an (optionally filtered) report, or all reports.
It also contains an example of custom analytics, using data for hypervisors,
projects, and instances to generate aggregated data about active instances.

For usage information. see:

`$ ./reporting_example.py --help`

If the `reporting-api` endpoint being used requires authentication,
you must either supply a previously-generated Keystone token, or supply
the credentials necessary to obtain a new token from Keystone.