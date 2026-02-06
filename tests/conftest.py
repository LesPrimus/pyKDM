import subprocess
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def tmp_output(tmp_path):
    """Provide a temporary output directory."""
    return tmp_path / "output"


@pytest.fixture
def fake_binary(tmp_path):
    """Create a fake binary file that passes the exists() check."""
    binary = tmp_path / "fake_binary"
    binary.touch()
    binary.chmod(0o755)
    return binary


@pytest.fixture
def mock_which():
    """Patch shutil.which to return a fake path."""
    with patch("pykdm.runner.shutil.which") as mock:
        mock.return_value = "/usr/bin/fake_binary"
        yield mock


@pytest.fixture
def mock_subprocess_run():
    """Patch subprocess.run to return a successful result."""
    with patch("pykdm.runner.subprocess.run") as mock:
        result = MagicMock(spec=subprocess.CompletedProcess)
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""
        mock.return_value = result
        yield mock


@pytest.fixture
def sample_video(tmp_path):
    """Create a dummy video file for testing content paths."""
    video = tmp_path / "sample.mxf"
    video.write_bytes(b"\x00" * 64)
    return video


@pytest.fixture
def sample_certificate(tmp_path):
    """Create a dummy certificate file for path-based tests."""
    cert = tmp_path / "cert.pem"
    cert.write_text("FAKE CERT")
    return cert


@pytest.fixture
def sample_project_dir(tmp_path):
    """Create a dummy DCP-o-matic project directory."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "metadata.xml").write_text("<Metadata/>")
    return project
