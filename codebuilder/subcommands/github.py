import os
import subprocess
import click

from codebuilder.subcommands.aws import pass_aws


@click.group()
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
        os.chmod(ssh_key_file, 0o600)

    cmdline = ['ssh-keyscan', '-H', 'github.com']
    result = subprocess.check_output(cmdline)
    with click.open_file(known_hosts_file, 'a') as f:
        click.echo(result, file=f)
    os.chmod(known_hosts_file, 0o600)
