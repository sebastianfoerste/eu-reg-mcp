import importlib.util
import os
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "smoke_list_tools.py"


@pytest.fixture(scope="module")
def smoke():
    spec = importlib.util.spec_from_file_location("smoke_list_tools", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def venv_on_path(tmp_path, monkeypatch):
    """Put an active virtual environment ahead of a plain directory on PATH."""
    venv = tmp_path / "venv"
    (venv / "bin").mkdir(parents=True)
    (venv / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    plain = tmp_path / "tools" / "bin"
    plain.mkdir(parents=True)
    monkeypatch.setenv("VIRTUAL_ENV", str(venv))
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setenv("PATH", os.pathsep.join([str(venv / "bin"), str(plain)]))
    return venv / "bin", plain


@pytest.mark.parametrize("uvx", ["uvx", "/opt/uv/bin/uvx"])
def test_uvx_server_gets_no_virtual_environment(smoke, venv_on_path, uvx):
    _, plain = venv_on_path
    env = smoke.server_env([uvx, "--from", ".[lint,classify]", "eu-reg-mcp"])
    assert env["PATH"].split(os.pathsep) == [str(plain)]
    assert "VIRTUAL_ENV" not in env
    assert env["HTTPS_PROXY"] == "http://proxy.invalid:3128"


def test_other_server_commands_keep_the_callers_environment(smoke, venv_on_path):
    assert smoke.server_env(["eu-reg-mcp"]) == dict(os.environ)
