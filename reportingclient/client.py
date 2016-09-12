import sys
import json
import requests
from urllib import urlencode


class ReportingClient(object):

    def __init__(self, endpoint, token=None, cache=False, debug=False, output=sys.stdout):
        self.token = token
        self.endpoint = endpoint
        self.cache = cache
        self.debug = debug
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
        Fetch specified report from reporting-api endpoint, optionally passing given
        token as X-Auth-Token header.
    
        If `cache` is a truthy value, then instead of talking to the endpoint,
        the data will be read from the file "./{report}.json". If that file does
        not exist, it will be created and filled with data retrieved normally.
        This is only to speed up development, avoiding the need to query endpoint
        repeatedly when having live data is not important.
        """
        def query_endpoint():
            return self._request(self.get_report_url(report), **params)
    
        if self.cache:
            path = './{report}.json'.format(report=report)
            try:
                with open(path, 'r') as f:
                    return json.loads(f.read())
            except IOError:
                data = query_endpoint()
                with open(path, 'w') as f:
                    f.write(json.dumps(data))
                return data
    
        return query_endpoint()

    def fetch_w(self, report, **params):
        """
        Wrapper for `fetch`, incorporating commandline arguments and a little
        bit of error handling to make users' lives easier.
        """
        if self.debug:
            print 'Fetching "{}"...'.format(report)
        data = self.fetch(report, **params)
        if self.debug:
            print 'Fetched "{}".'.format(report)
        return data
