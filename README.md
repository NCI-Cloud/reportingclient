python-reportingclient
======================

Client for [reporting-api](https://github.com/NeCTAR-RC/reporting-api).

Requirements:

* Python 3
* [Requests](http://python-requests.org) Python library


active-instances.py
-------------------

This script uses data for hypervisors, projects, and instances, outputting a
comma-separated list of values describing all active instances. See

`$ ./active-instances.py --help`

for usage information.

If the `reporting-api` endpoint being used requires authentication, either set
the `OS_TOKEN` environment variable, or (if you are the kind of person who
enjoys very lengthy command lines) pass the token via `--token`.  One way to
get a valid token is from
[reporting-view](https://github.com/NeCTAR-RC/reporting-view), in which a token
may be obtained from `sessionStorage.getItem('token')` in the JavaScript
console of an authenticated browser session.
