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

class AWSHelper(BaseHelper):
    def __init__(self):
        self._session = boto3.session.Session()

    def ecr_prune(self, repository_name):
        client = self._session.client('ecr')
        response = client.list_images(
            repositoryName=repository_name,
            filter={
                'tagStatus': 'UNTAGGED'
            }
        )
        images_to_delete = response['imageIds']
        if not images_to_delete:
            click.echo('No images to delete')
            return

        click.echo('Preparing to delete {} images ...'.format(len(images_to_delete)))
        response = client.batch_delete_image(
            repositoryName=repository_name,
            imageIds=images_to_delete
        )
        click.echo('Deleted {} images'.format(len(response['imageIds'])))

    def kms_decrypt(self, blob):
        return self._session.client('kms').decrypt(CiphertextBlob=b64decode(blob))['Plaintext']

pass_aws = click.make_pass_decorator(AWSHelper, ensure=True)

class DockerHelper(BaseHelper):
    def __init__(self, aws_account_id=None, aws_region=None, build_id=None, image_name=None, version=None):
        self._aws_account_id = aws_account_id or self.__guess_account_id()
        self._aws_region = aws_region
        self._build_id = build_id
        self._image_version = version or self.__guess_version()
        self._image_name = self._aws_account_id + '.dkr.ecr.' + self._aws_region + '.amazonaws.com/' + image_name
        self._full_image_name = '{}:latest'.format(self._image_name)
        self._versionned_image_name = '{}:{}'.format(self._image_name, self._image_version)

    def info(self):
        cmdline = ['docker', 'info']
        subprocess.call(cmdline)

    def build(self):
        cmdline = ['docker', 'build', '-t']
        cmdline += [self._image_name]
        cmdline += ['--build-arg', 'build_id=' + self._build_id]
        if self._image_version:
            cmdline += ['--build-arg', 'app_version=' + self._image_version]
        cmdline += ['.']
        subprocess.call(cmdline)

    def tag(self):
        cmdline = ['docker', 'tag', self._full_image_name, '{}:{}'.format(self._image_name, self._image_version)]
        subprocess.call(cmdline)

    def image_name(self):
        return self._image_name

    def versionned_image_name(self):
        return self._versionned_image_name

    def __guess_account_id(self):
        click.echo('[WARNING] No AWS_ACCOUNT_ID supplied, trying to guess ...', err=True)
        return boto3.client('sts').get_caller_identity().get('Account')

    def __guess_version(self):
        version = None
        if os.path.isfile('VERSION'):
            with click.open_file('VERSION', 'r') as f:
                version = f.read().strip()
        return version

@click.group()
@click.version_option(VERSION)
@click.pass_context
def cli(ctx):
    pass

@cli.group()
@click.pass_context
def aws(ctx):
    ctx.obj = AWSHelper()

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
def login():
    logincmd = subprocess.check_output(['aws', 'ecr', 'get-login']).split()
    subprocess.call(logincmd)

@ecr.command()
@click.argument('repository-name', envvar='IMAGE_REPO_NAME')
@pass_aws
def prune(aws, repository_name):
    aws.ecr_prune(repository_name)

@cli.group()
@click.option('--aws-account-id', envvar='AWS_ACCOUNT_ID', help='AWS Account Number [default: $AWS_ACCOUNT_ID]')
@click.option('--aws-region', envvar='AWS_DEFAULT_REGION', default='eu-west-1')
@click.option('--build-id', envvar='CODEBUILD_BUILD_ID', default='CUSTOM_BUILD')
@click.option('--image-name', envvar='IMAGE_REPO_NAME')
@click.option('--version')
@click.pass_context
def docker(ctx, aws_account_id, aws_region, build_id, image_name, version):
    ctx.obj = DockerHelper(aws_account_id, aws_region, build_id, image_name, version)

@docker.command()
@click.pass_context
def build(ctx):
    ctx.obj.build()
    ctx.obj.tag()

@docker.command()
@click.pass_context
def push(ctx):
    cmdline = ['docker', 'push', ctx.obj.image_name()]
    subprocess.call(cmdline)

@docker.command('get-image')
@click.option('--format', type=click.Choice(['text', 'json']), default='json')
@click.option('--source-json-file', type=click.File('r+'))
@click.option('--in-place', is_flag=True)
@click.argument('jsonpath', nargs=-1)
@click.pass_context
def get_image(ctx, format, source_json_file, in_place, jsonpath):
    ctx.obj.output(ctx.obj.versionned_image_name(), format, jsonpath, source_json_file, in_place)

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
