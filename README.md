# expresso

## Background

Expresso is a CDK app that will automatically provision user-defined AWS SSO Permissions Sets and Assignments based on account structure and mappings for the AWS Organization.

Ezpresso is backed by the AWS CDK Pipeline for automated deployment of changes.

If accounts are provisioned through Control Tower or changes are made to the OU structure, the pipeline will automatically start execution through [Lifecycle Events](https://docs.aws.amazon.com/controltower/latest/userguide/lifecycle-events.html), specifically the following events:

* [CreateManagedAccount](https://docs.aws.amazon.com/controltower/latest/userguide/lifecycle-events.html#create-managed-account)
* [UpdateManagedAccount](https://docs.aws.amazon.com/controltower/latest/userguide/lifecycle-events.html#update-managed-account)
* [RegisterOrganizationalUnit](https://docs.aws.amazon.com/controltower/latest/userguide/lifecycle-events.html#register-organizational-unit)
* [DeregisterOrganizationalUnit](https://docs.aws.amazon.com/controltower/latest/userguide/lifecycle-events.html#deregister-organizational-unit)

## Prerequisites

The following prerequisites must be actioned in order to carry out a successful deployment of the CDK app and pipeline.

### Node.js 16+

The CDK requires the Node.js 16+ runtime.

A simple option is to use [nvm](https://github.com/nvm-sh/nvm) to manage Node.js and to install in the local user environment without the need for root/sudo.

### CDK version 2+

CDK version 2+ must be [installed](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) to deploy the pipeline and stacks.

Simplest option is to execute `npm install -g aws-cdk`.

### AWS credentials for the AWS Organizations Management account

Source a suitable set of AWS credentials to the AWS Organizations management account, which will allow deployment of AWS resources including CodePipeline, CodeBuild, IAM roles and policies.

### Fork this repository

Fork this repository to your own or company github owner/name.

Record the github owner/name for later.

### Configure a CodeStar Connection

Create a [CodeStar Connection to GitHub](https://docs.aws.amazon.com/codepipeline/latest/userguide/connections-github.html) in the AWS Organizations Management account in the region where SSO is deployed.

This connection enables the CDK pipeline to get access to the GitHub repository and set-up a webhook for commit/merge notifications.

Record the Arn of the connection.

### CDK bootstrap AWS Organizations management account

Bootstrap the AWS Organizations management account with the CDK in the region where AWS SSO exists:

```bash
cdk bootstrap aws://<account id>/<region>
```

### Decide on an identity store group prefix

In order to uniquely identify groups in the chosen SSO-integrated identity store, it is strongly recommended that a prefix is chosen for each group.

This makes identifying, filtering and sorting groups in the identity store simpler.

Example: `AWS_SSO_`.

### Identify required AWS Organizations parameters 

* SSO instance Arn: In the AWS Organizations management account either use the AWS Identity Center Management Console to find it or execute the following CLI command: `aws sso-admin list-instances --query ' Instances[0].InstanceArn'`

* SSO Identity Store Id: In the AWS Organizations management account either use the AWS Identity Center Management Console to find it or execute the following CLI command: `aws sso-admin list-instances --query ' Instances[0].IdentityStoreId'`

Record the values for later.

### Define AWS SSO groups

Before attempting to deploy SSO Permission Sets, the mapped identity store groups must exist in the chosen identity store and be replicated to the AWS SSO identity store.

Important! Ensure that *all* of the created identity store groups have the group prefix, e.g. `AWS_SSO_`, which will be used to link the SSO permission sets to the groups (see above). 

### Define SSO Permission Sets

SSO Permission Sets are defined in the file `config/sso-permission-sets.yaml` (examples provided in this file).

The SSO Permission Sets can be deployed in stages (Cloudformation stacks) on the pipeline. See [Notes](#notes) for use cases.

### Define CDK app configuration

The CDK app contains a CDK pipeline and requires input parameters in the form of CDK app [context](https://docs.aws.amazon.com/cdk/v2/guide/context.html).

There are several ways to provide the CDK app configuration, including:

* `--context`/`-c` option when running the CDK app (e.g. `cdk deploy` or `cdk synth`)

* `cdk.json` file in the git repository directory

* `$HOME/.cdk.json` file in the user's home directory

Important! Do not attempt to mix these context options.

The required configuration for the CDK app per the last two options is:

```json
{
  "context": {
    "env_name": "dev", # Environment and pipeline postfix (e.g. dev/test/prod)
    "permission_sets_file": "config/sso-permission-sets.yaml", # The Yaml file containing the SSO Permission Sets definitionsß
    "codestar_connection_arn": "arn:aws:codestar-connections:eu-west-1:123456789012:connection/12345678-1234-1234-abcd-1234567890ab", # The CodeStar Connection Arn from above
    "github_repo": "mjvirt/expresso", # GitHub repository owner/name
    "github_repo_branch": "main", # Git branch that CDK app and pipeline run from
    "sso_instance_arn": "arn:aws:sso:::instance/ssoins-01234567890abcdef", # The SSO instance Arn from above
    "identity_store": "d-1234567890", # The identity store id from above
    "group_prefix": "AWS_SSO_" # The chosen identity store group name prefix
  }
}
```

## Deployment

The CDK app creates a pipeline, which is associated with the chosen GitHub repository branch (e.g. `main`). This enables the pipeline to automatically deploy changes on commit/merge to the branch

To deploy the CDK app & pipeline follow these instructions from a shell:

If using a `cdk.json` context file, run:

```bash
cdk deploy
```

If entering input parameters directly, run:

```bash
cdk deploy \
    -c env_name=dev \
    -c permission_sets_file=config/sso-permission-sets.yaml \
    -c codestar_connection_arn=arn:aws:codestar-connections:eu-west-1:123456789012:connection/12345678-1234-1234-abcd-1234567890ab \
    -c github_repo=mjvirt/expresso \
    -c github_repo_branch=main \
    -c sso_instance_arn=arn:aws:sso:::instance/ssoins-01234567890abcdef \
    -c identity_store=d-1234567890 \
    -c group_prefix=AWS_SSO_
```

## Operating

As previously mentioned, the CDK pipeline and CDK app will automatically execute for certain Control Tower [Lifecycle Events](https://docs.aws.amazon.com/controltower/latest/userguide/lifecycle-events.html).

In addition, the pipeline will automatically execute on commit/merge to the chosen pipeline branch.

Finally, the CDK pipeline can also be manually executed by logging in to the AWS Management Console [CodePipeline page](https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines), choosing the correct region and then the pipeline and clicking on the Release Change button.

## Development

To develop, add a python virtualenv `.venv` and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt
```

To run CDK app tests, simply run `pytest`.

### Notes

The following points are worth bearing in mind about the CDK app implementation:

* The `aws identitystore list-groups` SDK & CLI call [do not allow for wildcard searches](https://github.com/aws/aws-sdk/issues/109). Identity store group names must therefore be predictable (lookup by `group prefixes` + `group name`). This is achieved in the script `scripts/get-sso-group-mappings.py`, which iterates through the SSO Permission Sets configuration file to collect all group names to perform a lookup of each SSO group id

* Several stages/stacks of SSO Permission Sets can be deployed by the pipeline. There can be several reasons for doing this:
    * To logically group SSO Permission Sets together and deploy them in order
    * So many defined permission sets that SSO throttles Cloudformation deployment
    * To ensure that the size of the Cloudformation template stays below AWS limits

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## License

   Copyright [2022] [Morten Jensen]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
