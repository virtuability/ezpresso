#!/usr/bin/env python3

import boto3
import json
from typing import Dict
import argparse
from utility.file_helpers import file_read_yaml

from sso.permission_sets import PermissionSets

def list_identitystore_group(is_client, identity_store: str, display_name: str) -> Dict:

    group_response = is_client.list_groups(
        IdentityStoreId=identity_store,
        Filters=[
            {
                "AttributePath" : "DisplayName",
                "AttributeValue" : f"{display_name}"
            }
        ]
    )

    for group in group_response['Groups']:
        if group['DisplayName'] == f"{display_name}":
            return group
        else:
            raise ValueError('Unable to find group in identity store: ' + f"{group}")


def get_sso_group_mappings(
    is_client,
    group_prefix: str,
    identity_store: str,
    permission_sets: PermissionSets,
) -> Dict:

    # Use set to de-duplicate groups
    group_names = set()

    for stage in permission_sets.get_stages():
        for permission_set in stage['permission_sets']:
            for group in permission_set['group_assignments']:
                group_names.add(group['name'])

    group_mappings = []

    for group_name in group_names:

        display_name = f"{group_prefix}{group_name}"

        is_group = list_identitystore_group(is_client, identity_store, display_name)

        group_mappings.append(
            {
                'group_id' : is_group['GroupId'],
                'group_name' : is_group['DisplayName']
            }
        )

    return { "sso_group_mappings": group_mappings }


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Get AWS SSO group mappings from permission set names and environment name.')
    parser.add_argument('group_prefix', type=str, help='The Group Prefix used in the directory')
    parser.add_argument('identity_store', type=str, help='The AWS identity store id')
    parser.add_argument('permission_sets_file', type=str, help='The SSO permission sets file')
    parser.add_argument('aws_region', type=str, help='The AWS region of the identity store')
    args = parser.parse_args()

    is_client = boto3.client(service_name="identitystore", region_name=args.aws_region)

    content = file_read_yaml(args.permission_sets_file)
    permission_sets = PermissionSets(content)

    group_mappings = get_sso_group_mappings(
        is_client=is_client,
        group_prefix=args.group_prefix,
        identity_store=args.identity_store,
        permission_sets=permission_sets,
    )

    print(json.dumps(group_mappings, indent=2, default=str))
