import requests
from urllib import urlencode
import logging


class ReportingClient(object):

    def __init__(self, endpoint, token=None):
        self.logger = logging.getLogger(__name__)
        self.token = token
        self.endpoint = endpoint
        self.versions = None
        self.reports = None

    def _request(self, url, **params):
        if self.endpoint.endswith('/') or url.startswith('/'):
            url = self.endpoint + url
        else:
            url = self.endpoint + '/' + url
        if len(params):
            url = url + '?' + urlencode(params)
        headers = {}
        if self.token:
            headers['X-Auth-Token'] = self.token
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return r.json()

    def get_versions(self):
        if not self.versions:
            self.versions = self._request('')
        return self.versions

    def get_version(self, version_id):
        for version in self.get_versions():
            if version.id == version_id:
                return version
        raise ValueError("No server support for API version '" + version_id + "'")

    def get_any_version_link(self, link_type):
        for version in self.get_versions():
            if link_type in version['links']:
                return version['links'][link_type]
        raise ValueError("No server API version supports link type '" + link_type + "'")

    def get_reports(self):
        if not self.reports:
            self.reports = self._request(self.get_any_version_link('reports'))
        return self.reports

    def get_report_url(self, report_name):
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
