from . import __version__ as VERSION

import click

from .subcommands.aws import aws
from .subcommands.docker import docker
from .subcommands.github import github


@click.group()
@click.version_option(VERSION)
@click.pass_context
def cli(ctx):
    """CLI helper for AWS CodeBuild and CodePipeline"""
    pass

cli.add_command(aws)
cli.add_command(docker)
cli.add_command(github)
