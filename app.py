#!/usr/bin/env python3
from importlib.resources import contents
import os

import aws_cdk as cdk

from pipeline.pipeline import PipelineStack
from sso.account_structure import AccountStructure
from sso.group_mappings import GroupMappings
from sso.permission_sets import PermissionSets
from utility.file_helpers import file_read_yaml

app = cdk.App()

# Enable remote debug as needed locally (VSCode remote debug)
if app.node.try_get_context("debug") == "true":
    import debugpy

    debugpy.listen(5678)
    print("Waiting for debugger attach")
    debugpy.wait_for_client()
    debugpy.breakpoint()
    print("break on this line")

context_keys = [
    "env_name",
    "group_prefix",
    "permission_sets_file",
    "codestar_connection_arn",
    "github_repo",
    "github_repo_branch",
    "sso_instance_arn",
    "identity_store",
]

properties = {}

for context_key in context_keys:
    context = app.node.try_get_context(context_key)
    if context is None:
        raise ValueError(f"Must specify context parameter: {context_key}")
    properties[context_key] = context

content = file_read_yaml(properties["permission_sets_file"])
permission_sets = PermissionSets(content)

accounts_file = app.node.try_get_context("accounts_file")
if accounts_file is not None:
    content = file_read_yaml(accounts_file)
    account_structure = AccountStructure(content)
else:
    # CDK is run (deploy/diff/ls) outside of pipeline (CodeBuild)
    # so use empty account structure to bootstrap pipeline itself
    account_structure = AccountStructure({"Accounts": []})

group_mappings_file = app.node.try_get_context("group_mappings_file")
if group_mappings_file is not None:
    content = file_read_yaml(group_mappings_file)
    group_mappings = GroupMappings(properties["group_prefix"], content)
else:
    # CDK is run (deploy/diff/ls) outside of pipeline (CodeBuild)
    # so use empty groups mappings to bootstrap pipeline itself
    group_mappings = GroupMappings(properties["group_prefix"], [])

PipelineStack(
    app,
    f"SSOPipeline",
    env=cdk.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
    properties=properties,
    account_structure=account_structure,
    group_mappings=group_mappings,
    permission_sets=permission_sets,
    stack_name=f"sso-pipeline-{properties['env_name']}",
)

app.synth()
