from click.testing import CliRunner
import pytest
import os
import json

from codebuilder import __version__ as VERSION
from codebuilder.cli import cli as codebuilder

runner = CliRunner()

def test_version():
    r = runner.invoke(codebuilder, ['--version'])
    assert r.exit_code == 0
    assert VERSION in r.output

class TestAWS:
    def test_base(self):
        r = runner.invoke(codebuilder, ['aws'])
        assert r.exit_code == 0

class TestDocker:
    def test_base(self):
        r = runner.invoke(codebuilder, ['docker'])
        assert r.exit_code == 0

    def test_get_image_version(self, tmpdir):
        tmpdir.join('VERSION').write('1.0.0')
        tmpdir.chdir()
        r = runner.invoke(codebuilder, ['docker', '--image-name', 'foo/bar', 'get-image', 'version'])
        assert r.output == 'foo/bar:1.0.0\n'

    def test_get_image_version_json(self, tmpdir):
        tmpdir.join('VERSION').write('1.0.0')
        tmpdir.chdir()
        r = runner.invoke(codebuilder, ['docker', '--image-name', 'foo/bar', 'get-image', '--format', 'json', 'version'])
        assert r.output == json.dumps({'value': 'foo/bar:1.0.0'}, indent=2) + '\n'

    def test_get_image_from_env_version(self, tmpdir):
        tmpdir.join('VERSION').write('1.0.0')
        tmpdir.chdir()
        os.environ['DOCKER_REGISTRY'] = 'foo'
        os.environ['IMAGE_NAME'] = 'bar'
        r = runner.invoke(codebuilder, ['docker', 'get-image', 'version'])
        assert r.output == 'foo/bar:1.0.0\n'

    def test_get_tag_version(self, tmpdir):
        tmpdir.join('VERSION').write('1.0.0')
        tmpdir.chdir()
        r = runner.invoke(codebuilder, ['docker', 'get-tag', 'version'])
        assert r.output == '1.0.0\n'

    def test_get_tag_latest(self):
        r = runner.invoke(codebuilder, ['docker', 'get-tag', 'latest'])
        assert r.output == 'latest\n'

class TestGithub:
    def test_base(self):
        r = runner.invoke(codebuilder, ['github'])
        assert r.exit_code == 0
