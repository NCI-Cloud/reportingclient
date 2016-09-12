#!/usr/bin/python

import json
import csv
import sys
import os
import argparse
import requests


class ReportingClient(object):
    def __init__(self, endpoint, token=None, cache=False, debug=False, output=sys.stdout):
        self.token = token
        self.endpoint = endpoint
        self.cache = cache

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
        if args.debug:
            print 'Fetching "{}"...'.format(report)
        try:
            data = self.fetch(report)
            if args.debug:
                print 'Fetched "{}".'.format(report)
            return data
        except requests.exceptions.HTTPError as ex:
            if ex.response.status_code == 401 and not args.token:
                # it's easy to forget to set OS_TOKEN
                print >> sys.stderr, 'Hint: maybe you need to set OS_TOKEN.'
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compile list of all active instances.'
    )
    parser.add_argument('--endpoint', required=True, help='reporting-api endpoint')
    parser.add_argument('--output', required=True, help='output path')
    parser.add_argument('--token', default=None, help='auth token for reporting-api')
    parser.add_argument('--cache', default=False, action='store_true', help='cache results (for development)')
    parser.add_argument('--debug', default=False, action='store_true', help='enable debug output (for development)')
    args = parser.parse_args()
    if args.token is None:
        try:
            args.token = os.environ['OS_TOKEN']
        except KeyError:
            pass  # hope that reporting-api endpoint does not require token

    client = ReportingClient(**vars(args))

    # grab all the required data
    hypervisor = client.fetch_w('hypervisor')
    instance = client.fetch_w('instance?active=1')
    project = client.fetch_w('project')

    # check that every hypervisor has availability_zone defined
    # (since that's what we'll be using to determine AZ for each instance)
    for h in hypervisor:
        if not h['availability_zone']:
            print >> sys.stderr, 'Error: no availability_zone for hypervisor {}'.format(h['id'])
            sys.exit(1)
    if args.debug:
        print('Checked hypervisor AZ values.')

    # hypervisor 'hostname' field is fully qualified but instance 'hypervisor'
    # field is sometimes not; make a lookup table of hypervisors
    # by "short" (non-fully-qualified) names
    hyp_short = {}
    for h in hypervisor:
        short_name = h['hostname'].split('.')[0]
        if short_name in hyp_short:
            print >> sys.stderr, 'Warning: duplicate short hypervisor names {} ({} and {}).'.format(
                short_name, hyp_short[short_name]['id'], h['id'])
            if h['last_seen'] < hyp_short[short_name]['last_seen']:
                # only care about the most recently seen hypervisor
                continue
        hyp_short[short_name] = h

    # check that every instance has a valid hypervisor and project_id defined
    project_by_id = {p['id']: p for p in project}
    instance_hypervisor = {}  # maps instance id to hypervisor object
    instance_by_id = {}  # maps instance id to instance object
    for i in instance:
        if i['hypervisor'] is None:
            print >> sys.stderr, 'Warning: instance {} has no hypervisor; it will be ignored.'.format(i['id'])
            continue
        short_name = i['hypervisor'].split('.')[0]
        if short_name not in hyp_short:
            print >> sys.stderr, 'Error: could not determine hypervisor for instance {}'.format(i['id'])
            sys.exit(1)
        if i['project_id'] not in project_by_id:
            print >> sys.stderr, 'Warning: instance {} has invalid project_id {}; it will be ignored.'.format(i['id'], i['project_id'])
            continue

        instance_hypervisor[i['id']] = hyp_short[short_name]
        instance_by_id[i['id']] = i
    if args.debug:
        print 'Checked instance hypervisor values.'

    # at this point, sanity checks have been done on all the data;
    # now join data, decorating instance objects with additional fields
    for iid in instance_hypervisor:
        i = instance_by_id[iid]

        # replace availability_zone value with hypervisor's
        old_az = i['availability_zone']  # current version of reporting-pollster sets this unreliably
        new_az = instance_hypervisor[iid]['availability_zone']  # this is more reliable
        i['availability_zone'] = new_az

        # add project display names
        i['project_display_name'] = project_by_id[i['project_id']]['display_name']

    # output csv
    with open(args.output, 'w') as csvfile:
        fieldnames = i.keys()  # reusing 'i' (whatever instance was last processed above)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for (iid, i) in instance_by_id.items():
            writer.writerow(i)
