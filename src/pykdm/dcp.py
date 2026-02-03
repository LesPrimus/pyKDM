from pathlib import Path
from dataclasses import dataclass
from typing import Callable

from .exceptions import DCPCreationError
from .runner import Runner, CLIResult


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
        self.runner = Runner("dcpomatic2_cli", dcpomatic_path)

    def create(
        self,
        project: Path,
        output: Path | None = None,
        encrypt: bool = False,
        progress_callback: Callable[[float], None] | None = None,
    ) -> CLIResult:
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

        cmd = []

        if output:
            output.mkdir(parents=True, exist_ok=True)
            cmd.extend(["-o", str(output)])

        if encrypt:
            cmd.append("-e")

        cmd.append(str(project))

        return self.runner.run(
            *cmd, output_path=output or project, error_prefix="DCP creation"
        )

    def version(self) -> str:
        """Get dcpomatic2_cli version."""
        return self.runner.version()
