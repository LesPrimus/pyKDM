import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pykdm.runner import Runner, CLIResult
from pykdm.exceptions import CLIError


class TestRunnerInit:
    def test_init_with_valid_binary_path(self, fake_binary):
        runner = Runner("test_bin", str(fake_binary))
        assert runner.binary_path == fake_binary

    def test_init_with_invalid_binary_path(self, tmp_path):
        with pytest.raises(CLIError, match="not found at"):
            Runner("test_bin", str(tmp_path / "nonexistent"))

    def test_init_finds_binary_in_path(self, mock_which):
        runner = Runner("fake_binary")
        assert runner.binary_path == Path("/usr/bin/fake_binary")
        mock_which.assert_called_once_with("fake_binary")

    def test_init_raises_when_binary_not_in_path(self):
        with patch("pykdm.runner.shutil.which", return_value=None):
            with pytest.raises(CLIError, match="not found in PATH"):
                Runner("nonexistent_binary")


class TestRunnerExecute:
    def test_execute_returns_completed_process(
        self, mock_which, mock_subprocess_run
    ):
        runner = Runner("fake_binary")
        result = runner.execute("--flag", "value", error_prefix="Test")

        assert mock_subprocess_run.called
        cmd = mock_subprocess_run.call_args[0][0]
        assert cmd == ["/usr/bin/fake_binary", "--flag", "value"]

    def test_execute_raises_on_os_error(self, mock_which):
        runner = Runner("fake_binary")
        with patch(
            "pykdm.runner.subprocess.run", side_effect=OSError("exec failed")
        ):
            with pytest.raises(CLIError, match="Test failed"):
                runner.execute("--flag", error_prefix="Test")


class TestRunnerRun:
    def test_run_returns_cli_result_on_success(
        self, mock_which, mock_subprocess_run, tmp_path
    ):
        output = tmp_path / "out"
        runner = Runner("fake_binary")
        result = runner.run("arg1", output_path=output)

        assert isinstance(result, CLIResult)
        assert result.success is True
        assert result.output_path == output

    def test_run_raises_on_nonzero_exit(self, mock_which, tmp_path):
        runner = Runner("fake_binary")
        failed = MagicMock(spec=subprocess.CompletedProcess)
        failed.returncode = 1
        failed.stderr = "something went wrong"

        with patch("pykdm.runner.subprocess.run", return_value=failed):
            with pytest.raises(CLIError, match="failed"):
                runner.run("arg1", output_path=tmp_path, error_prefix="Build")


class TestRunnerVersion:
    def test_version_returns_stripped_stdout(
        self, mock_which, mock_subprocess_run
    ):
        mock_subprocess_run.return_value.stdout = "  2.16.0\n"
        runner = Runner("fake_binary")
        assert runner.version() == "2.16.0"
