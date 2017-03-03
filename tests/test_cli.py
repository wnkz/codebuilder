from click.testing import CliRunner
import pytest

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
