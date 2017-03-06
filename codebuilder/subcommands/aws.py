import subprocess
import click

from codebuilder.helpers.aws import AWSHelper

pass_aws = click.make_pass_decorator(AWSHelper, ensure=True)


@click.group()
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
    """
    Login to default ECR registry in default region.

    Examples:

      \b
      > codebuilder aws ecr login
      `docker login -u AWS -p {TOKEN} https://123456789012.dkr.ecr.eu-west-1.amazonaws.com`
    """
    (user, token, endpoint) = aws.ecr_get_authorization()
    logincmd = ['docker', 'login', '-u', user, '-p', token, endpoint]
    subprocess.call(logincmd)


# TODO: Add option to delete old images
@ecr.command(short_help='Delete images from ECR')
@click.argument('repository-name', envvar='IMAGE_NAME')
@pass_aws
def prune(aws, repository_name):
    """
    Delete images in the ECR repository (default from $IMAGE_NAME)
    """
    deleted_images = aws.ecr_prune(repository_name)
    if not deleted_images:
        click.echo('No image deleted')
    else:
        for image in deleted_images:
            click.echo('Deleted image: {}'.format(image['imageDigest']))



@aws.group()
def codepipeline():
    pass


@codepipeline.command('get-revision')
@click.option('--artifact-name')
@click.option('--short', is_flag=True)
@click.argument('attribute', type=click.Choice(['revisionUrl', 'name', 'created', 'revisionId', 'revisionSummary', 'revisionChangeIdentifier']), default='revisionId')
@pass_aws
def get_revision(aws, artifact_name, short, attribute):
    """
    Retrieves an attribute of CodePipeline source artifacts.

    \b
    Default artifact is the first one returned unless --artifact-name is specified
    Default attribute is revisionId unless overidden by [ATTRIBUTE]
    """
    value = aws.codepipeline_get_artifact_attribute(artifact_name, attribute)
    if attribute == 'revisionId' and short:
        value = value[:8]
    click.echo(value)
