import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .exceptions import DCPProjectCreationError
from .dcp import DCPCreator, DCPResult


class DCPContentType(Enum):
    """DCP content type classifications."""

    FTR = "FTR"  # Feature
    SHR = "SHR"  # Short
    TLR = "TLR"  # Trailer
    TST = "TST"  # Test
    XSN = "XSN"  # Transitional
    RTG = "RTG"  # Rating
    TSR = "TSR"  # Teaser
    POL = "POL"  # Policy
    PSA = "PSA"  # Public Service Announcement
    ADV = "ADV"  # Advertisement


class ContainerRatio(Enum):
    """Container aspect ratios for DCP."""

    RATIO_119 = "119"  # 1.19:1
    RATIO_133 = "133"  # 1.33:1 (4:3)
    RATIO_137 = "137"  # 1.37:1 (Academy)
    RATIO_138 = "138"  # 1.38:1
    RATIO_166 = "166"  # 1.66:1 (European Widescreen)
    RATIO_178 = "178"  # 1.78:1 (16:9)
    RATIO_185 = "185"  # 1.85:1 (Flat)
    RATIO_239 = "239"  # 2.39:1 (Scope)


class DCPStandard(Enum):
    """DCP packaging standards."""

    SMPTE = "smpte"
    INTEROP = "interop"


class Resolution(Enum):
    """DCP resolution."""

    TWO_K = "2K"
    FOUR_K = "4K"


class Dimension(Enum):
    """2D or 3D content."""

    TWO_D = "2D"
    THREE_D = "3D"


class AudioChannel(Enum):
    """Audio channel assignments."""

    L = "L"  # Left
    R = "R"  # Right
    C = "C"  # Center
    Lfe = "Lfe"  # Low Frequency Effects
    Ls = "Ls"  # Left Surround
    Rs = "Rs"  # Right Surround
    BsL = "BsL"  # Back Surround Left
    BsR = "BsR"  # Back Surround Right
    HI = "HI"  # Hearing Impaired
    VI = "VI"  # Visually Impaired


class Eye(Enum):
    """Eye assignment for 3D content."""

    LEFT = "left"
    RIGHT = "right"


@dataclass
class ContentItem:
    """A content file with optional per-file settings."""

    path: Path
    eye: Eye | None = None
    channel: AudioChannel | None = None
    gain: float | None = None
    kdm: Path | None = None
    cpl: str | None = None


@dataclass
class DCPProjectResult:
    """Result of a DCP project creation."""

    output_path: Path
    success: bool
    stdout: str
    stderr: str


class DCPProjectCreator:
    """Wrapper for dcpomatic2_create to create DCP-o-matic projects from video/audio files."""

    def __init__(self, dcpomatic_create_path: str | None = None):
        """
        Initialize the DCP project creator.

        Args:
            dcpomatic_create_path: Path to dcpomatic2_create binary.
                                  If None, searches in PATH.
        """
        if dcpomatic_create_path:
            self.bin_path = Path(dcpomatic_create_path)
            if not self.bin_path.exists():
                raise DCPProjectCreationError(
                    f"dcpomatic2_create not found at {dcpomatic_create_path}"
                )
        else:
            found = shutil.which("dcpomatic2_create")
            if not found:
                raise DCPProjectCreationError(
                    "dcpomatic2_create not found in PATH. "
                    "Install DCP-o-matic or provide explicit path."
                )
            self.bin_path = Path(found)

    def create(
        self,
        content: Path | ContentItem | Sequence[Path | ContentItem],
        output: Path,
        name: str | None = None,
        encrypt: bool = False,
        content_type: DCPContentType | None = None,
        container_ratio: ContainerRatio | None = None,
        standard: DCPStandard | None = None,
        resolution: Resolution | None = None,
        dimension: Dimension | None = None,
        no_use_isdcf_name: bool = False,
        no_sign: bool = False,
    ) -> DCPProjectResult:
        """
        Create a DCP-o-matic project from video/audio content.

        Args:
            content: Path(s) to video/audio file(s), or ContentItem(s) with options.
            output: Output directory for the project.
            name: Film name. If not provided, uses filename.
            encrypt: Whether to encrypt the DCP.
            content_type: DCP content type (FTR, SHR, TLR, etc.).
            container_ratio: Container aspect ratio.
            standard: DCP standard (SMPTE or INTEROP).
            resolution: Resolution (2K or 4K).
            dimension: 2D or 3D.
            no_use_isdcf_name: Disable ISDCF naming convention.
            no_sign: Do not sign the DCP.

        Returns:
            DCPProjectResult with output path and status.

        Raises:
            DCPProjectCreationError: If project creation fails.
        """
        # Normalize content to a list
        if isinstance(content, (Path, ContentItem)):
            content_list = [content]
        else:
            content_list = list(content)

        if not content_list:
            raise DCPProjectCreationError("At least one content file is required")

        # Build command
        cmd = [str(self.bin_path)]

        # Output directory
        output.mkdir(parents=True, exist_ok=True)
        cmd.extend(["-o", str(output)])

        # Optional arguments
        if name:
            cmd.extend(["-n", name])

        if encrypt:
            cmd.append("-e")

        if content_type:
            cmd.extend(["-c", content_type.value])

        if container_ratio:
            cmd.extend(["--container-ratio", container_ratio.value])

        if standard:
            cmd.extend(["-s", standard.value])

        if resolution:
            if resolution == Resolution.FOUR_K:
                cmd.append("--fourk")

        if dimension:
            if dimension == Dimension.THREE_D:
                cmd.append("--threed")

        if no_use_isdcf_name:
            cmd.append("--no-use-isdcf-name")

        if no_sign:
            cmd.append("--no-sign")

        # Add content files with their options
        for item in content_list:
            if isinstance(item, ContentItem):
                if not item.path.exists():
                    raise DCPProjectCreationError(f"Content file not found: {item.path}")

                # Add per-content options before the content path
                if item.eye:
                    cmd.extend(["--eye", item.eye.value])
                if item.channel:
                    cmd.extend(["--channel", item.channel.value])
                if item.gain:
                    cmd.extend(["--gain", str(item.gain)])
                if item.kdm:
                    cmd.extend(["--kdm", str(item.kdm)])
                if item.cpl:
                    cmd.extend(["--cpl", item.cpl])

                cmd.append(str(item.path))
            else:
                if not item.exists():
                    raise DCPProjectCreationError(f"Content file not found: {item}")
                cmd.append(str(item))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
        except OSError as e:
            raise DCPProjectCreationError(f"Failed to run dcpomatic2_create: {e}")

        success = result.returncode == 0

        if not success:
            raise DCPProjectCreationError(
                f"Project creation failed (exit code {result.returncode}):\n{result.stderr}"
            )

        return DCPProjectResult(
            output_path=output,
            success=success,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def create_and_build(
        self,
        content: Path | ContentItem | Sequence[Path | ContentItem],
        output: Path,
        dcp_output: Path | None = None,
        name: str | None = None,
        encrypt: bool = False,
        content_type: DCPContentType | None = None,
        container_ratio: ContainerRatio | None = None,
        standard: DCPStandard | None = None,
        resolution: Resolution | None = None,
        dimension: Dimension | None = None,
        no_use_isdcf_name: bool = False,
        no_sign: bool = False,
        dcpomatic_cli_path: str | None = None,
    ) -> tuple[DCPProjectResult, DCPResult]:
        """
        Create a DCP-o-matic project and build the DCP in one step.

        Args:
            content: Path(s) to video/audio file(s), or ContentItem(s) with options.
            output: Output directory for the project.
            dcp_output: Output directory for the DCP. If None, uses project directory.
            name: Film name. If not provided, uses filename.
            encrypt: Whether to encrypt the DCP.
            content_type: DCP content type (FTR, SHR, TLR, etc.).
            container_ratio: Container aspect ratio.
            standard: DCP standard (SMPTE or INTEROP).
            resolution: Resolution (2K or 4K).
            dimension: 2D or 3D.
            no_use_isdcf_name: Disable ISDCF naming convention.
            no_sign: Do not sign the DCP.
            dcpomatic_cli_path: Path to dcpomatic2_cli binary for building.

        Returns:
            Tuple of (DCPProjectResult, DCPResult) with project and DCP creation results.

        Raises:
            DCPProjectCreationError: If project creation fails.
            DCPCreationError: If DCP building fails.
        """
        # First, create the project
        project_result = self.create(
            content=content,
            output=output,
            name=name,
            encrypt=encrypt,
            content_type=content_type,
            container_ratio=container_ratio,
            standard=standard,
            resolution=resolution,
            dimension=dimension,
            no_use_isdcf_name=no_use_isdcf_name,
            no_sign=no_sign,
        )

        # Then build the DCP
        creator = DCPCreator(dcpomatic_path=dcpomatic_cli_path)
        dcp_result = creator.create(
            project=output,
            output=dcp_output,
            encrypt=encrypt,
        )

        return project_result, dcp_result

    def version(self) -> str:
        """Get dcpomatic2_create version."""
        result = subprocess.run(
            [str(self.bin_path), "--version"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
