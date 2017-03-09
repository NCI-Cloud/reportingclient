#!/usr/bin/env python

"""
Output reports downloaded from the Reporting API
in either CSV or JSON formats.
"""

from __future__ import print_function
import argparse
import csv
import logging
import os
from pprint import pprint
from reportingclient.client import ReportingClient
import sys


def get_arg_or_env_var(args, name):
    """
    Retrieve a named parameter's value, either from a command-line argument
    or from an environment variable.
    Both the arguments and variables follow the OpenStack naming scheme.
    If no parameter with the given name is found, return None.
    """
    name = 'os_' + name
    name_with_underscores = name.replace('-', '_')
    try:
        value = getattr(args, name_with_underscores.lower())
    except AttributeError:
        # Not supplied in a command-line argument
        try:
            value = os.environ[name_with_underscores.upper()]
        except KeyError:
            # Not supplied in environment either
            value = None
    return value


def get_one_report(client, report_name, **params):
    """
    Output data from the given-named report.
    """
    return client.fetch(report_name, **params)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Query the reporting API'
    )
    parser.add_argument(
        '--endpoint', required=False, default=None,
        help='reporting-api endpoint'
    )
    parser.add_argument(
        '--os-token', default=argparse.SUPPRESS,
        help='auth token for reporting-api'
    )
    parser.add_argument(
        '--debug', default=False, action='store_true',
        help='enable debug output (for development)'
    )
    parser.add_argument(
        '--os-username', default=argparse.SUPPRESS, help='Username'
    )
    parser.add_argument(
        '--os-password', default=argparse.SUPPRESS, help="User's password"
    )
    parser.add_argument(
        '--os-auth-url', default=argparse.SUPPRESS, help='Authentication URL'
    )
    parser.add_argument(
        '--os-project-name', default=argparse.SUPPRESS,
        help='Project name to scope to'
    )
    parser.add_argument(
        '--os-tenant-name', default=argparse.SUPPRESS,
        help='Project name to scope to'
    )
    parser.add_argument(
        '--filter', default=[],
        action='append',
        help='Supply a report filter criterion in name=value format.' +
        'Repeat for multiple critera.'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--report', default=None,
        help='Report name'
    )
    group.add_argument(
        '--list-reports', action='store_true', default=False,
        help="List available reports",
    )
    parser.add_argument(
        '--format', action='store', default='csv',
        help="Output format"
    )
    parser.add_argument(
        '-o', '--outfile', action='store',
        help="Output filename"
    )
    return parser.parse_args()


def write_csv(outfile, results):
    fieldnames = results[0].keys()
    fieldnames.sort()
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)
    return


def write_json(outfile, results):
    pprint(results, indent=2, width=1, stream=outfile)
    return


def main():
    """
    Test harness for OpenStack Reporting API client
    """
    args = parse_args()
    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.WARN
    logging.basicConfig(level=log_level)
    logger = logging.getLogger('reportingclient.client')
    logger.setLevel(log_level)
    filter_criteria = dict(criterion.split('=') for criterion in args.filter)

    token = get_arg_or_env_var(args, 'token')
    auth_url = get_arg_or_env_var(args, 'auth_url')
    username = get_arg_or_env_var(args, 'username')
    password = get_arg_or_env_var(args, 'password')
    project_name = get_arg_or_env_var(args, 'project_name')
    if not project_name:
        project_name = get_arg_or_env_var(args, 'tenant_name')
    try:
        client = ReportingClient(endpoint=args.endpoint,
                                 username=username,
                                 password=password,
                                 project_name=project_name,
                                 auth_url=auth_url,
                                 token=token)
    except ValueError as e:
        print("Reporting Client error:", e.message)
        return 1
    if args.list_reports:
        reports = client.get_reports()
        for report in reports:
            print("%s report: %s" % (report['name'], report['description']))
            print("\tLast Updated: %s" % (report['lastUpdated']))
        return 0
    results = get_one_report(client, args.report, **filter_criteria)
    if len(results) == 0:
        print("Empty result set")
        return 0

    outfile = sys.stdout
    if args.outfile:
        outfile = open(args.outfile, "w")
    if args.format.lower() == 'csv':
        write_csv(outfile, results)
    elif args.format.lower() == 'json':
        write_json(outfile, results)
    else:
        print("Unknown output format", args.format)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
