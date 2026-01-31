import click
from datetime import datetime
from pathlib import Path

from .dcp import DCPCreator
from .kdm import KDMGenerator, KDMType
from .project import (
    DCPProjectCreator,
    DCPContentType,
    ContainerRatio,
    DCPStandard,
    Resolution,
    Dimension,
)
from .exceptions import DCPCreationError, KDMGenerationError, DCPProjectCreationError


def parse_datetime(value: str) -> datetime:
    """Parse datetime string in format YYYY-MM-DD HH:MM or YYYY-MM-DD."""
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise click.BadParameter(f"Invalid datetime format: {value}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM")


class DateTimeType(click.ParamType):
    """Custom Click parameter type for datetime parsing."""

    name = "datetime"

    def convert(self, value, param, ctx):
        if isinstance(value, datetime):
            return value
        return parse_datetime(value)


DATETIME = DateTimeType()


@click.group()
@click.version_option(package_name="pykdm")
def cli():
    """pyKDM - Python wrapper for DCP-o-matic CLI tools."""
    pass


@cli.group()
def dcp():
    """DCP creation commands."""
    pass


@dcp.command("create")
@click.argument("project", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output directory for the DCP.")
@click.option("-e", "--encrypt", is_flag=True, help="Encrypt the DCP.")
@click.option("--bin-path", type=click.Path(exists=True, path_type=Path), help="Path to dcpomatic2_cli binary.")
def dcp_create(project: Path, output: Path | None, encrypt: bool, bin_path: Path | None):
    """Create a DCP from a DCP-o-matic project.

    PROJECT is the path to a .dcp project file or project directory.
    """
    try:
        creator = DCPCreator(dcpomatic_path=str(bin_path) if bin_path else None)
        click.echo(f"Creating DCP from {project}...")

        result = creator.create(project=project, output=output, encrypt=encrypt)

        click.echo(f"DCP created successfully at: {result.output_path}")
        if result.stdout:
            click.echo(result.stdout)
    except DCPCreationError as e:
        raise click.ClickException(str(e))


@dcp.command("version")
@click.option("--bin-path", type=click.Path(exists=True, path_type=Path), help="Path to dcpomatic2_cli binary.")
def dcp_version(bin_path: Path | None):
    """Show dcpomatic2_cli version."""
    try:
        creator = DCPCreator(dcpomatic_path=str(bin_path) if bin_path else None)
        click.echo(creator.version())
    except DCPCreationError as e:
        raise click.ClickException(str(e))


@dcp.command("create-from-video")
@click.argument("content", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", required=True, type=click.Path(path_type=Path), help="Output directory for the project.")
@click.option("-n", "--name", help="Film name.")
@click.option("-e", "--encrypt", is_flag=True, help="Create encrypted DCP.")
@click.option(
    "-c",
    "--content-type",
    type=click.Choice([t.value for t in DCPContentType], case_sensitive=False),
    help="DCP content type.",
)
@click.option(
    "--container-ratio",
    type=click.Choice([r.value for r in ContainerRatio], case_sensitive=False),
    help="Container aspect ratio.",
)
@click.option("--twok/--fourk", "resolution", default=True, flag_value=True, help="Resolution (default: 2K).")
@click.option(
    "--standard",
    type=click.Choice([s.value for s in DCPStandard], case_sensitive=False),
    help="DCP standard (smpte or interop).",
)
@click.option("--build", is_flag=True, help="Also build the DCP after creating project.")
@click.option("--dcp-output", type=click.Path(path_type=Path), help="Output directory for built DCP (with --build).")
@click.option("--bin-path", type=click.Path(exists=True, path_type=Path), help="Path to dcpomatic2_create binary.")
@click.option("--cli-bin-path", type=click.Path(exists=True, path_type=Path), help="Path to dcpomatic2_cli binary (for --build).")
def dcp_create_from_video(
    content: tuple[Path, ...],
    output: Path,
    name: str | None,
    encrypt: bool,
    content_type: str | None,
    container_ratio: str | None,
    resolution: bool,
    standard: str | None,
    build: bool,
    dcp_output: Path | None,
    bin_path: Path | None,
    cli_bin_path: Path | None,
):
    """Create a DCP-o-matic project from video/audio files.

    CONTENT is one or more paths to video or audio files.

    \b
    Examples:
      pykdm dcp create-from-video video.mp4 -o ./my-project -n "My Film"
      pykdm dcp create-from-video video.mp4 audio.wav -o ./project --build
      pykdm dcp create-from-video video.mp4 -o ./project -e --build --dcp-output ./dcp
    """
    try:
        creator = DCPProjectCreator(dcpomatic_create_path=str(bin_path) if bin_path else None)

        # Convert option strings to enums
        content_type_enum = DCPContentType(content_type) if content_type else None
        container_ratio_enum = ContainerRatio(container_ratio) if container_ratio else None
        standard_enum = DCPStandard(standard) if standard else None
        resolution_enum = Resolution.TWO_K if resolution else Resolution.FOUR_K

        content_paths = list(content)

        if build:
            click.echo(f"Creating project and building DCP from {len(content_paths)} file(s)...")
            project_result, dcp_result = creator.create_and_build(
                content=content_paths,
                output=output,
                dcp_output=dcp_output,
                name=name,
                encrypt=encrypt,
                content_type=content_type_enum,
                container_ratio=container_ratio_enum,
                standard=standard_enum,
                resolution=resolution_enum,
                dcpomatic_cli_path=str(cli_bin_path) if cli_bin_path else None,
            )
            click.echo(f"Project created at: {project_result.output_path}")
            click.echo(f"DCP created at: {dcp_result.output_path}")
            if project_result.stdout:
                click.echo(project_result.stdout)
            if dcp_result.stdout:
                click.echo(dcp_result.stdout)
        else:
            click.echo(f"Creating project from {len(content_paths)} file(s)...")
            result = creator.create(
                content=content_paths,
                output=output,
                name=name,
                encrypt=encrypt,
                content_type=content_type_enum,
                container_ratio=container_ratio_enum,
                standard=standard_enum,
                resolution=resolution_enum,
            )
            click.echo(f"Project created successfully at: {result.output_path}")
            if result.stdout:
                click.echo(result.stdout)
    except DCPProjectCreationError as e:
        raise click.ClickException(str(e))
    except DCPCreationError as e:
        raise click.ClickException(str(e))


@dcp.command("project-version")
@click.option("--bin-path", type=click.Path(exists=True, path_type=Path), help="Path to dcpomatic2_create binary.")
def dcp_project_version(bin_path: Path | None):
    """Show dcpomatic2_create version."""
    try:
        creator = DCPProjectCreator(dcpomatic_create_path=str(bin_path) if bin_path else None)
        click.echo(creator.version())
    except DCPProjectCreationError as e:
        raise click.ClickException(str(e))


@cli.group()
def kdm():
    """KDM generation commands."""
    pass


@kdm.command("generate")
@click.argument("dcp", type=click.Path(exists=True, path_type=Path))
@click.option("-c", "--certificate", type=click.Path(exists=True, path_type=Path), required=True, help="Path to the target certificate (.pem).")
@click.option("-o", "--output", type=click.Path(path_type=Path), required=True, help="Output path for the KDM file.")
@click.option("-f", "--valid-from", type=DATETIME, required=True, help="Start of validity period (YYYY-MM-DD or YYYY-MM-DD HH:MM).")
@click.option("-t", "--valid-to", type=DATETIME, required=True, help="End of validity period (YYYY-MM-DD or YYYY-MM-DD HH:MM).")
@click.option(
    "-K",
    "--kdm-type",
    type=click.Choice([t.value for t in KDMType], case_sensitive=False),
    default=KDMType.MODIFIED_TRANSITIONAL_1.value,
    help="KDM output format type.",
)
@click.option("--cinema-name", help="Cinema name for the KDM.")
@click.option("--screen-name", help="Screen name for the KDM.")
@click.option("--bin-path", type=click.Path(exists=True, path_type=Path), help="Path to dcpomatic2_kdm_cli binary.")
def kdm_generate(
    dcp: Path,
    certificate: Path,
    output: Path,
    valid_from: datetime,
    valid_to: datetime,
    kdm_type: str,
    cinema_name: str | None,
    screen_name: str | None,
    bin_path: Path | None,
):
    """Generate a KDM for an encrypted DCP.

    DCP is the path to the encrypted DCP directory.
    """
    try:
        generator = KDMGenerator(dcpomatic_kdm_path=str(bin_path) if bin_path else None)

        kdm_type_enum = KDMType(kdm_type)

        click.echo(f"Generating KDM for {dcp}...")
        result = generator.generate(
            dcp=dcp,
            certificate=certificate,
            output=output,
            valid_from=valid_from,
            valid_to=valid_to,
            kdm_type=kdm_type_enum,
            cinema_name=cinema_name,
            screen_name=screen_name,
        )

        click.echo(f"KDM created successfully at: {result.output_path}")
        if result.stdout:
            click.echo(result.stdout)
    except KDMGenerationError as e:
        raise click.ClickException(str(e))


@kdm.command("generate-dkdm")
@click.argument("dkdm", type=click.Path(exists=True, path_type=Path))
@click.option("-c", "--certificate", type=click.Path(exists=True, path_type=Path), required=True, help="Path to the target certificate (.pem).")
@click.option("-o", "--output", type=click.Path(path_type=Path), required=True, help="Output path for the KDM file.")
@click.option("-f", "--valid-from", type=DATETIME, required=True, help="Start of validity period (YYYY-MM-DD or YYYY-MM-DD HH:MM).")
@click.option("-t", "--valid-to", type=DATETIME, required=True, help="End of validity period (YYYY-MM-DD or YYYY-MM-DD HH:MM).")
@click.option(
    "-K",
    "--kdm-type",
    type=click.Choice([t.value for t in KDMType], case_sensitive=False),
    default=KDMType.MODIFIED_TRANSITIONAL_1.value,
    help="KDM output format type.",
)
@click.option("--bin-path", type=click.Path(exists=True, path_type=Path), help="Path to dcpomatic2_kdm_cli binary.")
def kdm_generate_dkdm(
    dkdm: Path,
    certificate: Path,
    output: Path,
    valid_from: datetime,
    valid_to: datetime,
    kdm_type: str,
    bin_path: Path | None,
):
    """Generate a KDM from a DKDM (Distribution KDM).

    DKDM is the path to the DKDM file.
    """
    try:
        generator = KDMGenerator(dcpomatic_kdm_path=str(bin_path) if bin_path else None)

        kdm_type_enum = KDMType(kdm_type)

        click.echo(f"Generating KDM from DKDM {dkdm}...")
        result = generator.generate_for_dkdm(
            dkdm=dkdm,
            certificate=certificate,
            output=output,
            valid_from=valid_from,
            valid_to=valid_to,
            kdm_type=kdm_type_enum,
        )

        click.echo(f"KDM created successfully at: {result.output_path}")
        if result.stdout:
            click.echo(result.stdout)
    except KDMGenerationError as e:
        raise click.ClickException(str(e))


@kdm.command("version")
@click.option("--bin-path", type=click.Path(exists=True, path_type=Path), help="Path to dcpomatic2_kdm_cli binary.")
def kdm_version(bin_path: Path | None):
    """Show dcpomatic2_kdm_cli version."""
    try:
        generator = KDMGenerator(dcpomatic_kdm_path=str(bin_path) if bin_path else None)
        click.echo(generator.version())
    except KDMGenerationError as e:
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli()