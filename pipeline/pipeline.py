from unicodedata import name
import aws_cdk as cdk

from aws_cdk import (
    aws_iam as iam,
    pipelines as pipelines,
    aws_codebuild as codebuild,
    aws_events as events,
    aws_events_targets as targets
)

from pipeline.stage import SSOStage
from sso.account_structure import AccountStructure
from sso.group_mappings import GroupMappings
from sso.permission_sets import PermissionSets

# Note that there is an original and a modern version of CDK pipelines
# as per https://github.com/aws/aws-cdk/blob/master/packages/@aws-cdk/pipelines/ORIGINAL_API.md

class PipelineStack (cdk.Stack):
    def __init__(self, scope: cdk.App, construct_id: str, properties: dict, account_structure: AccountStructure, group_mappings: GroupMappings, permission_sets: PermissionSets, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Preference for CodePipeline V2 integration via CodeStar Connection
        pipeline_input = pipelines.CodePipelineSource.connection(
            repo_string=properties['github_repo'],
            branch=properties['github_repo_branch'],
            connection_arn=properties['codestar_connection_arn'],
        )

        synth_action = pipelines.ShellStep('Synth',
            input=pipeline_input,
            commands=[
                f"pip install -r requirements.txt",
                f"npm install -g aws-cdk@2.x",
                f"export PYTHONPATH=$PWD",
                f"scripts/get-org-hierarchy.py >accounts.yaml",
                f"scripts/get-sso-group-mappings.py"
                f" {properties['group_prefix']}"
                f" {properties['identity_store']}"
                f" {properties['permission_sets_file']}"
                f" $AWS_REGION"
                f" >group-mappings.yaml",
                f"cdk synth"
                f" -c env_name={properties['env_name']}"
                f" -c group_prefix={properties['group_prefix']}"
                f" -c permission_sets_file={properties['permission_sets_file']}"
                f" -c codestar_connection_arn={properties['codestar_connection_arn']}"
                f" -c github_repo={properties['github_repo']}"
                f" -c github_repo_branch={properties['github_repo_branch']}"
                f" -c sso_instance_arn={properties['sso_instance_arn']}"
                f" -c accounts_file=accounts.json"
                f" -c group_mappings_file=group-mappings.json"
                f" -c identity_store={properties['identity_store']}"
            ]
        )

        pipeline = pipelines.CodePipeline(self, f"SSOPipeline{properties['env_name']}",
            cross_account_keys=True,
            code_build_defaults=self.__codebuild_default_options(),
            synth=synth_action,
            self_mutation=True,
        )

        for stage in permission_sets.get_stages():
            pipeline.add_stage(
                SSOStage(self, 
                    f"SSOStage",
                    properties=properties,
                    account_structure=account_structure,
                    group_mappings=group_mappings,
                    permission_sets=stage['permission_sets'],
                ),
            )

        # Build pipeline to make available for event rule target
        pipeline.build_pipeline()

        ct_lifecycle_event_rule = events.Rule(self, f"ControlTowerLifecycleEventRule",
            description='Capture Control Tower Lifecycle Events',
            rule_name=f"ControlTowerLifecycleEvents-{properties['env_name']}",
            enabled=True,
            event_pattern=events.EventPattern(
                source=['aws.controltower'],
                detail_type=['AWS API Call via CloudTrail'],
                detail={
                    'eventSource': ['controltower.amazonaws.com'],
                    'eventName': ['CreateManagedAccount', 'UpdateManagedAccount', 'RegisterOrganizationalUnit', 'DeregisterOrganizationalUnit'],
                },
            )
        )

        ct_lifecycle_event_rule.add_target(
            targets.CodePipeline(
                pipeline=pipeline.pipeline
            )
        )


    def __codebuild_default_options(self) -> pipelines.CodeBuildOptions:
        """ Create CodeBuild defaults for Amazon Linux 2 (version 3)
            with required AWS Organizations permissions to do lookups
        """
        role_policy=[
            # iam.PolicyStatement(
            #     sid='CDKAssumeLookup',
            #     effect=iam.Effect.ALLOW,
            #     actions=[
            #         'sts:AssumeRole',
            #     ],
            #     resources=[ f"arn:aws:iam::*:role/cdk-hnb659fds-lookup-role-*-*" ],
            # ),
            iam.PolicyStatement(
                sid='IdLookup',
                effect=iam.Effect.ALLOW,
                actions=[
                    'sso:List*',
                    'sso:Describe*',
                    'identitystore:List*',
                    'identitystore:Describe*',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid='OrganizationsLookup',
                effect=iam.Effect.ALLOW,
                actions=[
                    'organizations:List*',
                    'organizations:Descibe*',
                ],
                resources=['*'],
            )
        ]

        # TODO: Fix for Node.js 16 support when available
        # https://github.com/aws/aws-codebuild-docker-images/issues/490
        # https://github.com/aws/aws-cdk/issues/20960
        n16_build_spec = codebuild.BuildSpec.from_object(
            {
                "version": "0.2",
                "phases": {
                    "install": {
                        "commands": [
                            "n 16",
                        ]
                    }
                },
            }
        )

        codebuild_options = pipelines.CodeBuildOptions(
            partial_build_spec=n16_build_spec,
            build_environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.MEDIUM,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                ),
                role_policy=role_policy,
        )

        return codebuild_options