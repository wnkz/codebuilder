from . import __version__ as VERSION

import click

@click.group()
@click.version_option(VERSION)
@click.option('--verbose', is_flag=True, help='Enable verbose mode')
@click.pass_context
def cli(ctx, verbose):
    """CLI helper for AWS CodeBuild and CodePipeline"""
    ctx.meta['VERBOSE'] = verbose
    pass

from .subcommands.aws import aws
from .subcommands.docker import docker
from .subcommands.github import github

cli.add_command(aws)
cli.add_command(docker)
cli.add_command(github)
