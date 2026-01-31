import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Callable

from .exceptions import DCPCreationError


@dataclass
class DCPResult:
    """Result of a DCP creation."""

    output_path: Path
    success: bool
    stdout: str
    stderr: str


class DCPCreator:
    """Wrapper for dcpomatic2_cli to create Digital Cinema Packages."""

    def __init__(self, dcpomatic_path: str | None = None):
        """
        Initialize the DCP creator.

        Args:
            dcpomatic_path: Path to dcpomatic2_cli binary.
                          If None, searches in PATH.
        """
        if dcpomatic_path:
            self.bin_path = Path(dcpomatic_path)
            if not self.bin_path.exists():
                raise DCPCreationError(f"dcpomatic2_cli not found at {dcpomatic_path}")
        else:
            found = shutil.which("dcpomatic2_cli")
            if not found:
                raise DCPCreationError(
                    "dcpomatic2_cli not found in PATH. "
                    "Install DCP-o-matic or provide explicit path."
                )
            self.bin_path = Path(found)

    def create(
        self,
        project: Path,
        output: Path | None = None,
        encrypt: bool = False,
        progress_callback: Callable[[float], None] | None = None,
    ) -> DCPResult:
        """
        Create a DCP from a DCP-o-matic project.

        Args:
            project: Path to .dcp project file or project directory.
            output: Output directory for the DCP. If None, uses project default.
            encrypt: Whether to encrypt the DCP.
            progress_callback: Optional callback for progress updates (0.0-1.0).

        Returns:
            DCPResult with output path and status.

        Raises:
            DCPCreationError: If DCP creation fails.
        """
        if not project.exists():
            raise DCPCreationError(f"Project not found: {project}")

        cmd = [str(self.bin_path)]

        if output:
            output.mkdir(parents=True, exist_ok=True)
            cmd.extend(["-o", str(output)])

        if encrypt:
            cmd.append("-e")

        cmd.append(str(project))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
        except OSError as e:
            raise DCPCreationError(f"Failed to run dcpomatic2_cli: {e}")

        success = result.returncode == 0

        if not success:
            raise DCPCreationError(
                f"DCP creation failed (exit code {result.returncode}):\n{result.stderr}"
            )

        return DCPResult(
            output_path=output or project,
            success=success,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def version(self) -> str:
        """Get dcpomatic2_cli version."""
        result = subprocess.run(
            [str(self.bin_path), "--version"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()