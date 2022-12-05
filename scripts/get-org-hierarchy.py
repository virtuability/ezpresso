#!/usr/bin/env python3

import boto3
import json


class Org:

    # AWS Organizations is global, hence region of us-east-1
    org_client = boto3.client(service_name="organizations", region_name="us-east-1")

    def list_accounts(self):
        paginator = self.org_client.get_paginator("list_accounts")
        page_iterator = paginator.paginate()

        accounts = []

        for page in page_iterator:
            for account in page["Accounts"]:
                print(account)
                accounts.append(account)

        return accounts

    def list_roots(self):
        paginator = self.org_client.get_paginator("list_roots")
        page_iterator = paginator.paginate()

        roots = []

        for page in page_iterator:
            for root in page["Roots"]:
                roots.append(root)

        return roots

    def list_organizational_units_for_parent(self, parent_id):
        paginator = self.org_client.get_paginator("list_organizational_units_for_parent")
        page_iterator = paginator.paginate(ParentId=parent_id)

        ous = []

        for page in page_iterator:
            for ou in page["OrganizationalUnits"]:
                ous.append(ou)

        return ous

    def list_accounts_for_parent(self, parent_id):
        paginator = self.org_client.get_paginator("list_accounts_for_parent")
        page_iterator = paginator.paginate(ParentId=parent_id)

        accounts = []

        for page in page_iterator:
            for account in page["Accounts"]:
                accounts.append(account)

        return accounts

    def path_by_id(self, ou_stack):
        path = ""

        for l in ou_stack:
            path = path + "/" + l["Id"]
        return path

    def path_by_name(self, ou_stack):
        path = ""

        for l in ou_stack:
            path = path + "/" + l["Name"]
        return path

    def get_org_hierarchy(self, ou_stack=None, org=None):

        if (ou_stack is None and org is None) or (ou_stack is not None and org is not None):
            pass
        else:
            raise ValueError("parent_id and prefix must either both be None or both be set.")

        # Start from top
        if ou_stack is None:
            # There is only ever one OU root - at least for now
            root = self.list_roots()[0]
            ou_stack = []
            ou_stack.append(
                {
                    "Id": root["Id"],
                    "Name": root["Name"],
                    "Arn": root["Arn"],
                }
            )
            org = {}
            org["Accounts"] = []

        for account in self.list_accounts_for_parent(ou_stack[-1]["Id"]):

            account["name_path"] = self.path_by_name(ou_stack)
            account["id_path"] = self.path_by_id(ou_stack)

            org["Accounts"].append(account)

        for ou in self.list_organizational_units_for_parent(ou_stack[-1]["Id"]):

            ou_stack.append(
                {
                    "Id": ou["Id"],
                    "Name": ou["Name"],
                    "Arn": ou["Arn"],
                }
            )

            self.get_org_hierarchy(ou_stack, org)
            ou_stack.pop()

        return org


if __name__ == "__main__":
    org = Org()

    accounts = org.get_org_hierarchy()
    print(json.dumps(accounts, indent=2, default=str))
