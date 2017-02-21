from . import __version__ as VERSION

import os
import sys
import subprocess
import json
import click
import boto3
import dpath.util

from base64 import b64decode


class BaseHelper(object):

    def __init__(self):
        pass

    def get_version(self):
        version = None
        if os.path.isfile('VERSION'):
            with click.open_file('VERSION', 'r') as f:
                version = f.read().strip()
        return version

    def output(self, value=None, format=None, jsonpath=None, source_json_file=None, in_place=False):
        if format == 'json':
            if source_json_file:
                d = json.load(source_json_file)
            else:
                d = {}
            dpath.util.new(d, list(jsonpath) or '/value', value)
            if in_place:
                source_json_file.seek(0)
                click.echo(json.dumps(d, indent=2, sort_keys=True), file=source_json_file)
                pass
            else:
                click.echo(json.dumps(d, indent=2, sort_keys=True))
        elif format == 'text':
            click.echo(value)


# TODO: Better permissions checking
class AWSHelper(BaseHelper):

    def __init__(self):
        self._session = boto3.session.Session()

    def codepipeline_get_artifacts_revision(self):
        CODEBUILD_BUILD_ID = os.getenv('CODEBUILD_BUILD_ID')
        CODEBUILD_INITIATOR = os.getenv('CODEBUILD_INITIATOR')

        if not CODEBUILD_BUILD_ID or not CODEBUILD_INITIATOR:
            return None

        (service, pipeline_name) = CODEBUILD_INITIATOR.split('/')
        client = self._session.client('codepipeline')
        response = client.get_pipeline_state(name=pipeline_name)

        pipeline_execution_id = None
        for stage_state in response['stageStates']:
            if CODEBUILD_BUILD_ID in dpath.util.values(stage_state, '/actionStates/*/latestExecution/externalExecutionId'):
                pipeline_execution_id = stage_state['latestExecution']['pipelineExecutionId']
                break

        if not pipeline_execution_id:
            return None

        response = client.get_pipeline_execution(
            pipelineName=pipeline_name,
            pipelineExecutionId=pipeline_execution_id
        )

        return response['pipelineExecution']['artifactRevisions']

    def codepipeline_get_artifact_attribute(self, name, attribute):
        artifacts = self.codepipeline_get_artifacts_revision()
        if not artifacts:
            return None
        if not name:
            return artifacts[0].get(attribute, None)
        else:
            for artifact in artifacts:
                if name == artifact['name']:
                    return artifact.get(attribute, None)
        return None

    def ecr_get_authorization(self):
        client = self._session.client('ecr')
        response = client.get_authorization_token()
        user, token = b64decode(response['authorizationData'][0]['authorizationToken']).split(':')
        return (user, token, response['authorizationData'][0]['proxyEndpoint'])

    def ecr_prune(self, repository_name):
        client = self._session.client('ecr')
        response = client.list_images(
            repositoryName=repository_name,
            filter={
                'tagStatus': 'UNTAGGED'
            }
        )
        images_to_delete = response['imageIds']
        if images_to_delete:
            response = client.batch_delete_image(
                repositoryName=repository_name,
                imageIds=images_to_delete
            )
            for image in response['imageIds']:
                click.echo('Deleted image: {}'.format(image['imageDigest']))

    def kms_decrypt(self, blob):
        return self._session.client('kms').decrypt(CiphertextBlob=b64decode(blob))['Plaintext']

pass_aws = click.make_pass_decorator(AWSHelper, ensure=True)


class DockerHelper(AWSHelper):

    def __init__(self, image_name=None, artifact_name=None):
        super(DockerHelper, self).__init__()

        self._image_name = image_name
        self._version = self.get_version()
        self._branch = os.getenv('GITHUB_BRANCH', None)
        self._build_id = os.getenv('CODEBUILD_BUILD_ID', None)
        self._revision_id = self.codepipeline_get_artifact_attribute(artifact_name, 'revisionId')
        if self._revision_id:
            self._short_revision_id = self._revision_id[:8]

        self._available_tags = {
            'latest': 'latest'
        }

        if self._version:
            self._available_tags['version'] = self._version

        if self._revision_id and self._version:
            self._available_tags['full'] = '{}-{}'.format(self._version, self._short_revision_id)

        if self._branch:
            self._available_tags['branch'] = self._branch

        self._available_images = {}
        for k, v in self._available_tags.items():
            self._available_images[k] = '{}:{}'.format(self._image_name, v)

    def get_image(self, tag):
        return self._available_images.get(tag, None)

    def get_tag(self, tag):
        return self._available_tags.get(tag, None)

    def get_apply_tags_commands(self, tags=[]):
        commands = []
        for tag in tags:
            if tag in self._available_images:
                commands.append(['docker', 'tag', self._image_name, self._available_images[tag]])
        return commands


@click.group()
@click.version_option(VERSION)
@click.pass_context
def cli(ctx):
    """CLI helper for AWS CodeBuild and CodePipeline"""
    pass


@cli.group()
def aws():
    pass


@aws.group()
def kms():
    pass


@kms.command()
@click.argument('blob')
@click.option('--format', type=click.Choice(['text', 'json']), default='text')
@click.option('--source-json-file', type=click.File('r+'))
@click.option('--in-place', is_flag=True)
@click.argument('jsonpath', nargs=-1)
@pass_aws
def decrypt(aws, blob, format, source_json_file, in_place, jsonpath):
    value = aws.kms_decrypt(blob)
    aws.output(value, format, jsonpath, source_json_file, in_place)


@aws.group()
def ecr():
    pass


@ecr.command()
@pass_aws
def login(aws):
    (user, token, endpoint) = aws.ecr_get_authorization()
    logincmd = ['docker', 'login', '-u', user, '-p', token, endpoint]
    subprocess.call(logincmd)

# TODO: Add option to delete old images
@ecr.command(short_help='Delete images from ECR')
@click.argument('repository-name', envvar='IMAGE_NAME')
@pass_aws
def prune(aws, repository_name):
    """Delete images in the ECR repository (default from $IMAGE_NAME)"""
    aws.ecr_prune(repository_name)


@aws.group()
def codepipeline():
    pass


@codepipeline.command('get-revision')
@click.option('--artifact-name')
@click.option('--short', is_flag=True)
@click.argument('attribute', type=click.Choice(['revisionUrl', 'name', 'created', 'revisionId', 'revisionSummary', 'revisionChangeIdentifier']), default='revisionId')
@pass_aws
def get_revision(aws, artifact_name, short, attribute):
    value = aws.codepipeline_get_artifact_attribute(artifact_name, attribute)
    if attribute == 'revisionId' and short:
        value = value[:8]
    click.echo(value)


@cli.group()
@click.argument('image-name')
@click.option('--artifact-name')
@click.pass_context
def docker(ctx, image_name, artifact_name):
    ctx.obj = DockerHelper(image_name, artifact_name)


DEFAULT_TAG_CHOICE = [
    'full',
    'branch',
    'version',
    'latest'
]


@docker.command('get-image')
@click.argument('tag', type=click.Choice(DEFAULT_TAG_CHOICE))
@click.option('--format', type=click.Choice(['text', 'json']), default='json')
@click.option('--source-json-file', type=click.File('r+'))
@click.option('--in-place', is_flag=True)
@click.argument('jsonpath', nargs=-1)
@click.pass_obj
def get_image(dkr, tag, format, source_json_file, in_place, jsonpath):
    image = dkr.get_image(tag)
    if image:
        dkr.output(image, format, jsonpath, source_json_file, in_place)


@docker.command('get-tag')
@click.argument('tag', type=click.Choice(DEFAULT_TAG_CHOICE))
@click.option('--format', type=click.Choice(['text', 'json']), default='text')
@click.option('--source-json-file', type=click.File('r+'))
@click.option('--in-place', is_flag=True)
@click.argument('jsonpath', nargs=-1)
@click.pass_obj
def get_tag(dkr, tag, format, source_json_file, in_place, jsonpath):
    tag = dkr.get_tag(tag)
    if tag:
        dkr.output(tag, format, jsonpath, source_json_file, in_place)


@docker.command('apply-tags')
@click.option('--tag', '-t', multiple=True, type=click.Choice(DEFAULT_TAG_CHOICE))
@click.pass_obj
def apply_tags(dkr, tag):
    commands = dkr.get_apply_tags_commands(tag)
    for command in commands:
        subprocess.call(command)


@cli.group()
def github():
    pass


@github.command('ssh-config')
@click.argument('encrypted-ssh-key', envvar='ENCRYPTED_SSH_KEY')
@pass_aws
def ssh_config(aws, encrypted_ssh_key):
    decrypted_ssh_key = aws.kms_decrypt(encrypted_ssh_key)
    dir = os.path.expanduser('~/.ssh')
    if not os.path.exists(dir):
        os.makedirs(dir)
    ssh_key_file = dir + '/' + 'id_rsa'
    known_hosts_file = dir + '/' + 'known_hosts'

    if os.path.isfile(ssh_key_file):
        click.echo('{} already exists'.format(ssh_key_file), err=True)
        raise click.Abort()
    else:
        with click.open_file(ssh_key_file, 'w') as f:
            click.echo(decrypted_ssh_key, file=f)
        os.chmod(ssh_key_file, 0600)

    cmdline = ['ssh-keyscan', '-H', 'github.com']
    result = subprocess.check_output(cmdline)
    with click.open_file(known_hosts_file, 'a') as f:
        click.echo(result, file=f)
    os.chmod(known_hosts_file, 0600)
