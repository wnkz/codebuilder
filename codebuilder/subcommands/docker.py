import subprocess
import click

from codebuilder.helpers.docker import DockerHelper


@click.group()
@click.option('--image-name', help='Default: ${DOCKER_REGISTRY}/${IMAGE_NAME}')
@click.option('--artifact-name', help='CodePipeline artifact name. Default: First artifact')
@click.pass_context
def docker(ctx, image_name, artifact_name):
    ctx.obj = DockerHelper(image_name, artifact_name)


DEFAULT_TAG_CHOICE = [
    'full', # 1.0.0-ab42ab42
    'version', # 1.0.0
    'revision-id', # ab42ab42
    'branch', # master
    'latest' # latest
]


@docker.command('get-image')
@click.argument('tag', type=click.Choice(DEFAULT_TAG_CHOICE))
@click.option('--format', type=click.Choice(['text', 'json']), default='text')
@click.option('--source-json-file', type=click.File('r+'))
@click.option('--in-place', is_flag=True)
@click.argument('jsonpath', nargs=-1)
@click.pass_obj
def get_image(dkr, tag, format, source_json_file, in_place, jsonpath):
    """
    Returns a Docker image name with tags.

    Examples:

      \b
      > codebuilder docker --image-name foo/bar get-image --format text version
      foo/bar:1.0.0

      \b
      > codebuilder docker --image-name foo/bar --artifact-name MyApp get-image --format text full
      foo/bar:1.0.0-ab42ab42
    """
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
    """
    Returns a Docker tags.

    Examples:

      \b
      > codebuilder docker get-tag version
      1.0.0

      \b
      > codebuilder docker --artifact-name MyApp get-tag full
      1.0.0-ab42ab42
    """
    tag = dkr.get_tag(tag)
    if tag:
        dkr.output(tag, format, jsonpath, source_json_file, in_place)


@docker.command('apply-tags')
@click.option('--tag', '-t', 'tags', multiple=True, type=click.Choice(DEFAULT_TAG_CHOICE))
@click.pass_obj
def apply_tags(dkr, tags):
    """
    Apply tags to Docker image.

    Examples:

      \b
      > codebuilder docker --image-name foo/bar apply-tags -t version
      `docker tag foo/bar foo/bar:1.0.0`
    """
    commands = dkr.get_apply_tags_commands(tags)
    for command in commands:
        subprocess.call(command)
