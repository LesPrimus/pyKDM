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

    def generate(
        self,
        dcp: Path,
        certificate: Path,
        output: Path,
        valid_from: datetime,
        valid_to: datetime,
        kdm_type: KDMType = KDMType.MODIFIED_TRANSITIONAL_1,
        cinema_name: str | None = None,
        screen_name: str | None = None,
    ) -> KDMResult:
        """
        Generate a KDM for a DCP.

        Args:
            dcp: Path to the encrypted DCP.
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
        if not dcp.exists():
            raise KDMGenerationError(f"DCP not found: {dcp}")

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

        cmd.append(str(dcp))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
        except OSError as e:
            raise KDMGenerationError(f"Failed to run dcpomatic2_kdm_cli: {e}")

        success = result.returncode == 0

        if not success:
            raise KDMGenerationError(
                f"KDM generation failed (exit code {result.returncode}):\n{result.stderr}"
            )

        return KDMResult(
            output_path=output,
            success=success,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def generate_for_dkdm(
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

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
        except OSError as e:
            raise KDMGenerationError(f"Failed to run dcpomatic2_kdm_cli: {e}")

        success = result.returncode == 0

        if not success:
            raise KDMGenerationError(
                f"KDM generation failed (exit code {result.returncode}):\n{result.stderr}"
            )

        return KDMResult(
            output_path=output,
            success=success,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def version(self) -> str:
        """Get dcpomatic2_kdm_cli version."""
        result = subprocess.run(
            [str(self.bin_path), "--version"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()