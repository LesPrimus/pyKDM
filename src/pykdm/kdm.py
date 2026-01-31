import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .exceptions import KDMGenerationError


class KDMType(Enum):
    """KDM output format type."""

    MODIFIED_TRANSITIONAL_1 = "modified-transitional-1"
    DCI_ANY = "dci-any"
    DCI_SPECIFIC = "dci-specific"


@dataclass
class KDMResult:
    """Result of KDM generation."""

    output_path: Path
    success: bool
    stdout: str
    stderr: str


class KDMGenerator:
    """Wrapper for dcpomatic2_kdm_cli to generate Key Delivery Messages."""

    def __init__(self, dcpomatic_kdm_path: str | None = None):
        """
        Initialize the KDM generator.

        Args:
            dcpomatic_kdm_path: Path to dcpomatic2_kdm_cli binary.
                               If None, searches in PATH.
        """
        if dcpomatic_kdm_path:
            self.bin_path = Path(dcpomatic_kdm_path)
            if not self.bin_path.exists():
                raise KDMGenerationError(
                    f"dcpomatic2_kdm_cli not found at {dcpomatic_kdm_path}"
                )
        else:
            found = shutil.which("dcpomatic2_kdm_cli")
            if not found:
                raise KDMGenerationError(
                    "dcpomatic2_kdm_cli not found in PATH. "
                    "Install DCP-o-matic or provide explicit path."
                )
            self.bin_path = Path(found)

    @staticmethod
    def _exec(cmd, *, error_prefix: str = "Command") -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except OSError as e:
            raise KDMGenerationError(f"{error_prefix} failed: {e}")
        if result.returncode != 0:
            raise KDMGenerationError(
                f"{error_prefix} failed (exit code {result.returncode}):\n{result.stderr}"
            )
        return result

    def _run(self, cmd, output_path: Path, *, error_prefix: str = "KDM generation"):
        result = self._exec(cmd, error_prefix=error_prefix)
        return KDMResult(
            output_path=output_path,
            success=True,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def generate(
        self,
        project: Path,
        certificate: Path,
        output: Path,
        valid_from: datetime,
        valid_to: datetime,
        kdm_type: KDMType = KDMType.MODIFIED_TRANSITIONAL_1,
        cinema_name: str | None = None,
        screen_name: str | None = None,
    ) -> KDMResult:
        """
        Generate a KDM for an encrypted DCP.

        Args:
            project: Path to the DCP-o-matic project folder (the project
                    used to create the encrypted DCP, not the DCP output
                    folder itself). The project folder contains metadata.xml.
            certificate: Path to the target certificate (.pem).
            output: Output path for the KDM file.
            valid_from: Start of validity period.
            valid_to: End of validity period.
            kdm_type: Type of KDM to generate.
            cinema_name: Optional cinema name for the KDM.
            screen_name: Optional screen name for the KDM.

        Returns:
            KDMResult with output path and status.

        Raises:
            KDMGenerationError: If KDM generation fails.
        """
        if not project.exists():
            raise KDMGenerationError(f"Project not found: {project}")

        if not certificate.exists():
            raise KDMGenerationError(f"Certificate not found: {certificate}")

        output.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.bin_path),
            "-o",
            str(output),
            "-K",
            kdm_type.value,
            "-S",
            str(certificate),
            "-f",
            valid_from.strftime("%Y-%m-%d %H:%M"),
            "-t",
            valid_to.strftime("%Y-%m-%d %H:%M"),
        ]

        if cinema_name:
            cmd.extend(["-c", cinema_name])

        if screen_name:
            cmd.extend(["-s", screen_name])

        cmd.append(str(project))

        return self._run(cmd, output_path=output)

    def generate_from_dkdm(
        self,
        dkdm: Path,
        certificate: Path,
        output: Path,
        valid_from: datetime,
        valid_to: datetime,
        kdm_type: KDMType = KDMType.MODIFIED_TRANSITIONAL_1,
    ) -> KDMResult:
        """
        Generate a KDM from a DKDM (Distribution KDM).

        Args:
            dkdm: Path to the DKDM file.
            certificate: Path to the target certificate (.pem).
            output: Output path for the KDM file.
            valid_from: Start of validity period.
            valid_to: End of validity period.
            kdm_type: Type of KDM to generate.

        Returns:
            KDMResult with output path and status.

        Raises:
            KDMGenerationError: If KDM generation fails.
        """
        if not dkdm.exists():
            raise KDMGenerationError(f"DKDM not found: {dkdm}")

        if not certificate.exists():
            raise KDMGenerationError(f"Certificate not found: {certificate}")

        output.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.bin_path),
            "-o",
            str(output),
            "-K",
            kdm_type.value,
            "-S",
            str(certificate),
            "-f",
            valid_from.strftime("%Y-%m-%d %H:%M"),
            "-t",
            valid_to.strftime("%Y-%m-%d %H:%M"),
            "-D",
            str(dkdm),
        ]

        return self._run(cmd, output_path=output)

    def create_dkdm(
        self,
        project: Path,
        certificate: Path,
        output: Path,
        valid_from: datetime,
        valid_to: datetime,
        kdm_type: KDMType = KDMType.MODIFIED_TRANSITIONAL_1,
    ) -> KDMResult:
        """
        Create a DKDM (Distribution KDM) from a DCP-o-matic project.

        A DKDM is a KDM targeted at your own certificate, allowing you to
        later generate KDMs for other recipients without needing the original
        project.

        Args:
            project: Path to the DCP-o-matic project folder (the project
                    used to create the encrypted DCP).
            certificate: Path to your own certificate (.pem) - the certificate
                        associated with your decryption key.
            output: Output path for the DKDM file.
            valid_from: Start of validity period.
            valid_to: End of validity period.
            kdm_type: Type of KDM to generate.

        Returns:
            KDMResult with output path and status.

        Raises:
            KDMGenerationError: If DKDM creation fails.
        """
        if not project.exists():
            raise KDMGenerationError(f"Project not found: {project}")

        if not certificate.exists():
            raise KDMGenerationError(f"Certificate not found: {certificate}")

        output.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.bin_path),
            "-o",
            str(output),
            "-F",
            kdm_type.value,
            "-C",
            str(certificate),
            "-f",
            valid_from.strftime("%Y-%m-%d %H:%M"),
            "-t",
            valid_to.strftime("%Y-%m-%d %H:%M"),
            str(project),
        ]

        return self._run(cmd, output_path=output, error_prefix="DKDM creation")

    def version(self) -> str:
        """Get DCP-o-matic version (via dcpomatic2_cli, as dcpomatic2_kdm_cli lacks --version)."""
        cli_path = shutil.which("dcpomatic2_cli")
        if not cli_path:
            raise KDMGenerationError(
                "dcpomatic2_cli not found in PATH. Cannot determine version."
            )
        result = self._exec([cli_path, "--version"], error_prefix="Version check")
        return result.stdout.strip()