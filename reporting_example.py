#!/usr/bin/python

"""
Output various reports downloaded from the Reporting API
in Comma-Separated Values format.
"""

import sys
import os
import argparse
import logging
from pprint import pprint
from keystoneclient import client as keystone_client
from reportingclient.client import ReportingClient


def get_arg_or_env_var(args, name):
    """
    Retrieve a named parameter's value, either from a command-line argument
    or from an environment variable.
    Both the arguments and variables follow the OpenStack naming scheme.
    If no parameter with the given name is found, return None.
    """
    name = 'os-' + name
    try:
        name_with_hyphens = name.replace('_', '-').lower()
        value = getattr(args, name_with_hyphens)
    except AttributeError:
        # Not supplied in a command-line argument
        name_with_underscores = name.replace('-', '_').upper()
        try:
            value = os.environ[name_with_underscores]
        except KeyError:
            # Not supplied in environment either
            value = None
    return value


def active_instances(client):
    """
    Return a data structure describing active cloud instances.
    """
    logger = logging.getLogger(__name__)
    # grab all the required data
    hypervisors = client.fetch('hypervisor')
    instances = client.fetch('instance', active=1)
    projects = client.fetch('project')

    # check that every hypervisor has availability_zone defined
    # (since that's what we'll be using to determine AZ for each instance)
    for hypervisor in hypervisors:
        if not hypervisor['availability_zone']:
            logger.error(
                'No availability_zone for hypervisor %s', hypervisor['id']
            )
            sys.exit(1)
    logger.debug('Checked hypervisor AZ values.')

    # hypervisor 'hostname' field is fully qualified but instance 'hypervisor'
    # field is sometimes not; make a lookup table of hypervisors
    # by "short" (non-fully-qualified) names
    hyp_short = {}
    for hypervisor in hypervisors:
        short_name = hypervisor['hostname'].split('.')[0]
        if short_name in hyp_short:
            logger.warn(
                'Duplicate short hypervisor names %s (%s and %s).',
                short_name, hyp_short[short_name]['id'], hypervisor['id']
            )
            if hypervisor['last_seen'] < hyp_short[short_name]['last_seen']:
                # only care about the most recently seen hypervisor
                continue
        hyp_short[short_name] = hypervisor

    # check that every instance has a valid hypervisor and project_id defined
    project_by_id = {project['id']: project for project in projects}
    instance_hypervisor = {}  # maps instance id to hypervisor object
    instance_by_id = {}  # maps instance id to instance object
    for instance in instances:
        if instance['hypervisor'] is None:
            logger.warn(
                'Instance %s has no hypervisor; it will be ignored.',
                instance['id']
            )
            continue
        short_name = instance['hypervisor'].split('.')[0]
        if short_name not in hyp_short:
            logger.error(
                'Could not determine hypervisor for instance %s',
                instance['id']
            )
            sys.exit(1)
        if instance['project_id'] not in project_by_id:
            logger.warn(
                'Instance %s has invalid project_id %s; it will be ignored.',
                instance['id'], instance['project_id']
            )
            continue

        instance_hypervisor[instance['id']] = hyp_short[short_name]
        instance_by_id[instance['id']] = instance
    logger.debug('Checked instance hypervisor values.')

    # at this point, sanity checks have been done on all the data;
    # now join data, decorating instance objects with additional fields
    for instance_id in instance_hypervisor:
        instance = instance_by_id[instance_id]

        # replace availability_zone value with hypervisor's
        # current version of reporting-pollster sets this unreliably
        # old_az = instance['availability_zone']
        # this is more reliable
        new_az = instance_hypervisor[instance_id]['availability_zone']
        instance['availability_zone'] = new_az

        # add project display names
        instance['project_display_name'] = project_by_id[
            instance['project_id']
        ]['display_name']

    return (instance for instance in instance_by_id.values())


def test_one_report(client, report_name, **params):
    """
    Output the given-named report to the given-named
    Comma Separated Values-format file.
    """
    for result in client.fetch(report_name, **params):
        pprint(result)


def test_all_reports(client, **params):
    """
    Output each available report in sequence to the given-named
    Comma Separated Values-format file, overwriting the file each time.
    """
    for report_name in (report['name'] for report in client.get_reports()):
        test_one_report(client, report_name, **params)


def test_active_instances(client):
    """
    Output information about active instances to the given-named
    Comma Separated Values-format file.
    """
    for result in active_instances(client):
        pprint(result)


def main():
    """
    Test harness for OpenStack Reporting API client
    """
    parser = argparse.ArgumentParser(
        description='Compile list of all active instances.'
    )
    parser.add_argument(
        '--endpoint', required=True, help='reporting-api endpoint'
    )
    parser.add_argument(
        '--token', default=argparse.SUPPRESS,
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
    parser.add_argument(
        '--report', default=None,
        help='Report name'
    )
    parser.add_argument(
        '--list-reports', action='store_true', default=False,
        help="List available reports",
    )
    args = parser.parse_args()

    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.WARN
    logging.basicConfig(level=log_level)
    logger = logging.getLogger('reportingclient.client')
    logger.setLevel(log_level)
    filter_criteria = dict(criterion.split('=') for criterion in args.filter)

    args.token = get_arg_or_env_var(args, 'token')
    if args.token is None:
        # Attempt to obtain authentication credentials
        username = get_arg_or_env_var(args, 'username')
        password = get_arg_or_env_var(args, 'password')
        project_name = get_arg_or_env_var(args, 'project_name')
        if not project_name:
            project_name = get_arg_or_env_var(args, 'tenant_name')
        auth_url = get_arg_or_env_var(args, 'auth_url')
        if username and password and project_name and auth_url:
            keystone = keystone_client.Client(
                username=username,
                password=password,
                project_name=project_name,
                auth_url=auth_url
            )
            if not keystone.authenticate():
                raise ValueError("Keystone authentication failed")
            args.token = keystone.auth_ref['token']['id']

    client = ReportingClient(args.endpoint, args.token)
    if args.list_reports:
        reports = client.get_reports()
        for report in reports:
            print("%s report: %s" % (report['name'], report['description']))
            print("\tLast Updated: %s" % (report['lastUpdated']))
    elif args.report:
        test_one_report(client, args.report, **filter_criteria)
    else:
        test_all_reports(client, **filter_criteria)
        test_active_instances(client)

    return 0

if __name__ == '__main__':
    sys.exit(main())
