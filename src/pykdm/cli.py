import click
from datetime import datetime
from pathlib import Path

from .dcp import DCPCreator
from .kdm import KDMGenerator, KDMType
from .exceptions import DCPCreationError, KDMGenerationError


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