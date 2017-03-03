import os
import json
import click
import dpath.util

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
