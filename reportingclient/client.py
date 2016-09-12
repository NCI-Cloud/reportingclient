import sys
import json
import requests


class ReportingClient(object):
    def __init__(self, endpoint, token=None, cache=False, debug=False, output=sys.stdout):
        self.token = token
        self.endpoint = endpoint
        self.cache = cache
        self.debug = debug

    def fetch(self, report):
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
            url = '{ep}/v1/reports/{re}'.format(ep=self.endpoint, re=report)
            headers = {}
            if self.token:
                headers['X-Auth-Token'] = self.token
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            return r.json()
    
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

    def fetch_w(self, report):
        """
        Wrapper for `fetch`, incorporating commandline arguments and a little
        bit of error handling to make users' lives easier.
        """
        if self.debug:
            print 'Fetching "{}"...'.format(report)
        try:
            data = self.fetch(report)
            if self.debug:
                print 'Fetched "{}".'.format(report)
            return data
        except requests.exceptions.HTTPError as ex:
            if ex.response.status_code == 401 and not self.token:
                # it's easy to forget to set OS_TOKEN
                print >> sys.stderr, 'Hint: maybe you need to set OS_TOKEN.'
            raise
