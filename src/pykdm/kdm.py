from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .exceptions import KDMGenerationError
from .runner import Runner, CLIResult


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
        self.runner = Runner("dcpomatic2_kdm_cli", dcpomatic_kdm_path)

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
    ) -> CLIResult:
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

        output.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
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

        return self.runner.run(*cmd, output_path=output)

    def generate_from_dkdm(
        self,
        dkdm: Path,
        certificate: Path,
        output: Path,
        valid_from: datetime,
        valid_to: datetime,
        kdm_type: KDMType = KDMType.MODIFIED_TRANSITIONAL_1,
    ) -> CLIResult:
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
            CLIResult with output path and status.

        Raises:
            CLIError: If KDM generation fails.
        """
        if not dkdm.exists():
            raise KDMGenerationError(f"DKDM not found: {dkdm}")

        if not certificate.exists():
            raise KDMGenerationError(f"Certificate not found: {certificate}")

        output.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
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

        return self.runner.run(*cmd, output_path=output)

    def create_dkdm(
        self,
        project: Path,
        certificate: Path,
        output: Path,
        valid_from: datetime,
        valid_to: datetime,
        kdm_type: KDMType = KDMType.MODIFIED_TRANSITIONAL_1,
    ) -> CLIResult:
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

        return self.runner.run(*cmd, output_path=output, error_prefix="DKDM creation")
