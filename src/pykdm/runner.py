import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pykdm.exceptions import CLIError


@dataclass
class CLIResult:
    """Result of a CLI command execution."""
    output_path: Path
    success: bool
    stdout: str
    stderr: str

class Runner:
    def __init__(self, binary_name: str, binary_path: str | None = None):
        self.binary_name = binary_name
        if binary_path:
            self.binary_path = Path(binary_path)
            if not self.binary_path.exists():
                raise CLIError(f"{binary_name} not found at {binary_path}")
        else:
            found = shutil.which(binary_name)
            if not found:
                raise CLIError(f"{binary_name} not found in PATH.")
            self.binary_path = Path(found)

    def execute(self, *args: str, error_prefix) -> subprocess.CompletedProcess:
        cmd = [str(self.binary_path), *args]
        try:
            return subprocess.run(cmd, capture_output=True, text=True)
        except OSError as e:
            raise CLIError(f"{error_prefix} failed: {e}")

    def run(self, *args: str, output_path: Path, error_prefix: str = "Command") -> CLIResult:

        result = self.execute(*args, error_prefix=error_prefix)

        if result.returncode != 0:
            raise CLIError(
                f"{error_prefix} failed (exit code {result.returncode}):\n{result.stderr}"
            )

        return CLIResult(
            output_path=output_path,
            success=True,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def version(self) -> str:
        """Get the binary version."""
        result = self.execute("--version", error_prefix="Version check")
        return result.stdout.strip()
