import aws_cdk as cdk
from sso.permission_sets import PermissionSets

from sso.permission_sets_stack import PermissionSetsStack
from sso.account_structure import AccountStructure
from sso.group_mappings import GroupMappings

class SSOStage (cdk.Stage):
  
    def __init__(self, scope, id, *, env=None, outdir=None, properties: dict, account_structure: AccountStructure, group_mappings: GroupMappings, permission_sets: PermissionSets):
        super().__init__(scope, id, env=env, outdir=outdir)

        permission_sets_stack = PermissionSetsStack(self, f"PermissionSetsStack",
            env=cdk.Environment(account=self.account, region=self.region),
            properties=properties,
            account_structure=account_structure,
            group_mappings=group_mappings,
            permission_sets=permission_sets,
            stack_name=f"sso-permission-sets-{properties['env_name']}",
        )
