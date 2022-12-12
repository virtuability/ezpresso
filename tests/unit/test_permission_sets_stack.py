import aws_cdk as cdk
import aws_cdk.assertions as assertions
from sso.account_structure import AccountStructure
from sso.group_mappings import GroupMappings
from sso.permission_sets import PermissionSets
from sso.permission_sets_stack import PermissionSetsStack


class TestPermissionSetsStack:
    def test_permission_set_assignments(self):

        app = cdk.App()

        sso_instance_arn = "arn:aws:sso:::instance/ssoins-1234567890abcdef"

        # Two SSO Permission Sets:
        #   * One for Development but not assigned recursively
        #   * One for Production and assigned recursively
        permission_sets_raw = {
            "stages": [
                {
                    "name": "PermissionSets",
                    "permission_sets": [
                        {
                            "permission_set_name": "PermissionSetDevelopment",
                            "description": "Permission set for development",
                            "session_duration": "PT04H",
                            "aws_managed_policies": ["arn:aws:iam::aws:policy/PowerUserAccess"],
                            "ou_assignments": [{"path": "/Root/Development", "recursive": False}],
                            "group_assignments": [{"name": "Development"}],
                        },
                        {
                            "permission_set_name": "PermissionSetProduction",
                            "description": "Permission set for production",
                            "session_duration": "PT04H",
                            "aws_managed_policies": ["arn:aws:iam::aws:policy/ViewOnlyAccess"],
                            "ou_assignments": [{"path": "/Root/Production", "recursive": True}],
                            "group_assignments": [{"name": "Production"}],
                        },
                    ],
                }
            ]
        }

        permission_sets = PermissionSets(permission_sets_raw)

        group_prefix = "PR_AWS_SSO_"

        # 2 groups:
        group_mappings_raw = {
            "sso_group_mappings": [
                {
                    "group_id": "1234567890-12345678-1230-1230-1230-123456789012",
                    "group_name": group_prefix + "Development",
                },
                {
                    "group_id": "2345678911-12345678-1230-1230-1230-123456789012",
                    "group_name": group_prefix + "Production",
                },
            ]
        }

        group_mappings = GroupMappings(group_prefix, group_mappings_raw)

        # 4 accounts:
        #   * /Root/Development: 123456789012
        #   * /Root/Development/SubPath: 234567890123
        #   * /Root/Production: 345678901232
        #   * /Root/Production/SubPath: 456789012323
        account_structure_raw = {
            "Accounts": [
                {
                    "Id": "123456789012",
                    "Arn": "arn:aws:organizations::012345678901:account/o-g1h2nv345q/123456789012",
                    "Email": "awsdevelopment@example.com",
                    "Name": "awsdevelopment@example.com",
                    "Status": "ACTIVE",
                    "JoinedMethod": "INVITED",
                    "JoinedTimestamp": "2017-03-02 19:04:31.312000+00:00",
                    "name_path": "/Root/Development",
                    "id_path": "/r-abcd/ou-abcd-scf1ga23",
                },
                {
                    "Id": "234567890123",
                    "Arn": "arn:aws:organizations::012345678901:account/o-g1h2nv345q/234567890123",
                    "Email": "awssubdevelopment@example.com",
                    "Name": "awssubdevelopment@example.com",
                    "Status": "ACTIVE",
                    "JoinedMethod": "INVITED",
                    "JoinedTimestamp": "2017-03-02 19:04:31.312000+00:00",
                    "name_path": "/Root/Development/SubPath",
                    "id_path": "/r-abcd/ou-abcd-tcf1ga23",
                },
                {
                    "Id": "345678901232",
                    "Arn": "arn:aws:organizations::012345678901:account/o-g1h2nv345q/345678901232",
                    "Email": "awsproduction@example.com",
                    "Name": "awsproduction@example.com",
                    "Status": "ACTIVE",
                    "JoinedMethod": "CREATED",
                    "JoinedTimestamp": "2019-06-02 10:11:40.879000+00:00",
                    "name_path": "/Root/Production",
                    "id_path": "/r-abcd/ou-abcd-vwp1y2h3",
                },
                {
                    "Id": "456789012323",
                    "Arn": "arn:aws:organizations::012345678901:account/o-g1h2nv345q/456789012323",
                    "Email": "awssubproduction@example.com",
                    "Name": "awssubproduction@example.com",
                    "Status": "ACTIVE",
                    "JoinedMethod": "CREATED",
                    "JoinedTimestamp": "2019-06-02 10:11:40.879000+00:00",
                    "name_path": "/Root/Production/SubPath",
                    "id_path": "/r-abcd/ou-abcd-xwp1y2h3",
                },
            ]
        }

        account_structure = AccountStructure(account_structure_raw)

        properties = {
            "env_name": "dev",
            "config_file": "tests/unit/sso-permission-sets.yaml",
            "codestar_connection_arn": "arn:aws:codestar-connections:eu-west-1:123456789012:connection/12345678-1234-1234-abcd-1234567890ab",
            "github_repo": "virtuability/expresso",
            "github_repo_branch": "feature/refactor",
            "sso_instance_arn": "arn:aws:sso:::instance/ssoins-1234567890abcdef",
            "identity_store": "d-12345677890",
        }

        stack = PermissionSetsStack(
            app,
            "PermissionSets",
            properties=properties,
            account_structure=account_structure,
            group_mappings=group_mappings,
            permission_sets=permission_sets.get_stages()[0]["permission_sets"],
        )

        template = assertions.Template.from_stack(stack)

        # Expect the two SSO Permission Sets
        template.resource_count_is("AWS::SSO::PermissionSet", 2)

        # print(template.to_json())

        template.has_resource_properties(
            "AWS::SSO::PermissionSet",
            {
                "InstanceArn": "arn:aws:sso:::instance/ssoins-1234567890abcdef",
                "Name": "dev-PermissionSetDevelopment",
                "Description": "Permission set for development",
                "ManagedPolicies": ["arn:aws:iam::aws:policy/PowerUserAccess"],
                "SessionDuration": "PT04H",
            },
        )

        template.has_resource_properties(
            "AWS::SSO::PermissionSet",
            {
                "InstanceArn": "arn:aws:sso:::instance/ssoins-1234567890abcdef",
                "Name": "dev-PermissionSetProduction",
                "Description": "Permission set for production",
                "ManagedPolicies": ["arn:aws:iam::aws:policy/ViewOnlyAccess"],
                "SessionDuration": "PT04H",
            },
        )

        # Expect only the 3 assignments because without recursive one
        # development account won't match
        template.resource_count_is("AWS::SSO::Assignment", 3)

        template.has_resource_properties(
            "AWS::SSO::Assignment",
            {
                "InstanceArn": "arn:aws:sso:::instance/ssoins-1234567890abcdef",
                "PermissionSetArn": {
                    "Fn::GetAtt": ["PermissionSetDevelopment", "PermissionSetArn"]
                },
                "PrincipalId": "1234567890-12345678-1230-1230-1230-123456789012",
                "PrincipalType": "GROUP",
                "TargetId": "123456789012",
                "TargetType": "AWS_ACCOUNT",
            },
        )

        template.has_resource_properties(
            "AWS::SSO::Assignment",
            {
                "InstanceArn": "arn:aws:sso:::instance/ssoins-1234567890abcdef",
                "PermissionSetArn": {"Fn::GetAtt": ["PermissionSetProduction", "PermissionSetArn"]},
                "PrincipalId": "2345678911-12345678-1230-1230-1230-123456789012",
                "PrincipalType": "GROUP",
                "TargetId": "345678901232",
                "TargetType": "AWS_ACCOUNT",
            },
        )

        template.has_resource_properties(
            "AWS::SSO::Assignment",
            {
                "InstanceArn": "arn:aws:sso:::instance/ssoins-1234567890abcdef",
                "PermissionSetArn": {"Fn::GetAtt": ["PermissionSetProduction", "PermissionSetArn"]},
                "PrincipalId": "2345678911-12345678-1230-1230-1230-123456789012",
                "PrincipalType": "GROUP",
                "TargetId": "456789012323",
                "TargetType": "AWS_ACCOUNT",
            },
        )
