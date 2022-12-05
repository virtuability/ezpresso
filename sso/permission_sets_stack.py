import aws_cdk as cdk
import aws_cdk.aws_sso as sso
from sso.permission_sets import PermissionSets
from utility.cfn_helpers import file_sub
from sso.account_structure import AccountStructure
from sso.group_mappings import GroupMappings
from sso.account_structure import AccountStructure


class PermissionSetsStack(cdk.Stack):
    """Generate AWS SSO Permission Sets and Account Assignments.

    Based on account structure with recursive account path mappings and group mappings as input
    the implementation generates a stack with SSO permission sets and SSO group & account assignments.

    Note that group names must be predictable as the identity store group lookup doesn't support wildcard searches.
    """

    def __init__(
        self,
        scope: cdk.App,
        construct_id: str,
        properties: dict,
        account_structure: AccountStructure,
        group_mappings: GroupMappings,
        permission_sets: PermissionSets,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        for permission_set in permission_sets:

            # Optionally attach an inline policy document to the SSO Permission Set
            if "inline_policy_document_file" in permission_set:
                inline_policy_document = file_sub(
                    f"{permission_set['inline_policy_document_file']}"
                )
            else:
                inline_policy_document = None

            sso_permission_set = sso.CfnPermissionSet(
                self,
                f"{permission_set['permission_set_name']}",
                instance_arn=properties["sso_instance_arn"],
                name=f"{properties['env_name']}-{permission_set['permission_set_name']}",
                description=permission_set.get("description"),
                inline_policy=inline_policy_document,
                managed_policies=permission_set.get("aws_managed_policies"),
                relay_state_type=permission_set.get("relayStateType"),
                session_duration=permission_set.get("session_duration"),
            )

            accounts_groups_mappings = []

            # Add Permission Set OU assignments with account lookups (optionally recursive)
            if "ou_assignments" in permission_set:
                for ou_assignment in permission_set["ou_assignments"]:

                    ou_path = ou_assignment["path"]
                    ou_recursive = ou_assignment.get("recursive", False)

                    if not ou_path.startswith("/"):
                        raise ValueError(f"OU path must start with a /: {ou_path}")

                    if ou_path.endswith("/"):
                        raise ValueError(f"OU path must not end with a /: {ou_path}")

                    for group_assignment in permission_set["group_assignments"]:

                        for account in account_structure.accounts:

                            # Match either exactly or with startswith with slash because
                            # '/Root/Dev'(/...) would still otherwise match '/Root/Development' too
                            if account["name_path"] == ou_path or (
                                ou_recursive and account["name_path"].startswith(ou_path + "/")
                            ):
                                accounts_groups_mappings.append(
                                    {
                                        "account_id": account["Id"],
                                        "group_name": group_assignment["name"],
                                    }
                                )

            # Add Permission Set direct accounts assignments
            if permission_set.get("account_assignments") is not None:
                for account_assignment in permission_set["account_assignments"]:
                    for group_assignment in permission_set["group_assignments"]:

                        accounts_groups_mappings.append(
                            {
                                "account_id": account_assignment,
                                "group_name": group_assignment["name"],
                            }
                        )

            # De-duplicate accounts and group assignments as they can overlap
            dedup = [dict(s) for s in set(frozenset(d.items()) for d in accounts_groups_mappings)]

            # Now create SSO assignments by SSO permission set, AWS account and identity store group
            for accounts_groups_mapping in dedup:

                group_name_prefix = properties["env_name"]
                group_name = accounts_groups_mapping["group_name"]
                account_id = accounts_groups_mapping["account_id"]

                group_mapping = group_mappings.get_mapping_by_name(group_name)
                group_id = group_mapping["group_id"]

                # Each SSO assignment resource name needs to be unique
                sso_assignment = sso.CfnAssignment(
                    self,
                    f"{permission_set['permission_set_name']}-{account_id}-{group_name_prefix}{group_name}",
                    instance_arn=properties["sso_instance_arn"],
                    permission_set_arn=sso_permission_set.attr_permission_set_arn,
                    principal_id=group_id,
                    principal_type="GROUP",
                    target_id=account_id,
                    target_type="AWS_ACCOUNT",
                )
