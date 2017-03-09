"""
Python client binding to the OpenStack Reporting API.
"""

from urllib import urlencode
import logging
import requests
from keystoneclient import client as keystone_client
from keystoneclient import exceptions


class ReportingClient(object):
    """
    Encapsulates the Reporting API and provides access to its reports.
    """

    # This constructor does indeed have many arguments, but they are all
    # optional, because one of several possible subsets of them is required.
    # But there seems to be no way to make PyLint understand either of these
    # two facts. So just silence it.
    # pylint: disable=too-many-arguments
    def __init__(self, endpoint=None, token=None,
                 username=None, password=None,
                 project_name=None, auth_url=None):
        self.logger = logging.getLogger(__name__)
        self.versions = None
        self.reports = None
        if token and auth_url:
            self.token = token
            keystone = keystone_client.Client(token=token, auth_url=auth_url)
        elif username and password and project_name and auth_url:
            keystone = keystone_client.Client(
                username=username,
                password=password,
                project_name=project_name,
                auth_url=auth_url
            )
        else:
            keystone = None
        if keystone:
            if not keystone.authenticate():
                raise ValueError("Keystone authentication failed")
            self.token = keystone.auth_ref['token']['id']
        if endpoint:
            self.endpoint = endpoint
        elif keystone:
            try:
                self.endpoint = keystone.service_catalog.url_for(
                    service_type='reporting',
                    endpoint_type='public'
                )
            except exceptions.EndpointNotFound:
                raise ValueError("No reporting endpoint found in the catalog")
        else:
            raise ValueError(
                "No endpoint URL supplied, "
                "and neither token nor credentials supplied, "
                "so no way to obtain endpoint URL from catalog"
            )
    # pylint: enable=too-many-arguments

    def _request(self, url, **params):
        """
        Send a GET request to the API service.
        """
        if self.endpoint.endswith('/') or url.startswith('/'):
            url = self.endpoint + url
        else:
            url = self.endpoint + '/' + url
        if len(params):
            url = url + '?' + urlencode(params)
        headers = {}
        if self.token:
            headers['X-Auth-Token'] = self.token
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_versions(self):
        """
        Return a list of details of available versions of the API.
        """
        if not self.versions:
            self.versions = self._request('')
        return self.versions

    def get_version(self, version_id):
        """
        Return details of the given version of the API.
        """
        for version in self.get_versions():
            if version.id == version_id:
                return version
        raise ValueError(
            "No server support for API version '" + version_id + "'"
        )

    def get_any_version_link(self, link_type):
        """
        Return details of the first link of the given type found in
        any available version of the API.
        """
        for version in self.get_versions():
            if link_type in version['links']:
                return version['links'][link_type]
        raise ValueError(
            "No server API version supports link type '" + link_type + "'"
        )

    def get_reports(self):
        """
        Return a list of all reports available on the server.
        """
        if not self.reports:
            self.reports = self._request(self.get_any_version_link('reports'))
        return self.reports

    def get_report_url(self, report_name):
        """
        Return the URL from which the given-named report will be served
        in response to a GET request.
        """
        for report in self.get_reports():
            if report['name'] == report_name:
                return report['links']['self']
        raise ValueError("No report '" + report_name + "' available")

    def fetch(self, report, **params):
        """
        Fetch the named report, optionally passing the given parameters to it.
        """
        self.logger.debug('Fetching "%s"...', report)
        data = self._request(self.get_report_url(report), **params)
        self.logger.debug('Fetched "%s".', report)
        return data
