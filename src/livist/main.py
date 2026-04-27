import click
from click import Choice

from .borehole import Borehole
from .client import Client
from .config import Config
from .temperature import Mode


@click.group()
def cli() -> None:
    """Data processing for the Living Ice Sheet Temperature (livist) project."""


@cli.command()
def config() -> None:
    """Print the current configuration"""
    click.echo(Config().model_dump_json(indent=2))  # ty: ignore[missing-argument]


@cli.command()
def boreholes() -> None:
    """Print borehole data as a FeatureCollection"""
    client = Client()
    boreholes = client.get_boreholes()
    features = Borehole.to_feature_collection(boreholes)
    click.echo(features.model_dump_json(indent=2))


@cli.command()
@click.argument("ATTENUATION_NAME")
@click.argument("MODE", type=Choice([m.value for m in Mode]))
@click.option("--to-wgs84", is_flag=True, default=False)
def temperature(
    attenuation_name: str,
    mode: Mode,
    to_wgs84: bool,
) -> None:
    """Create along-track temperatures"""
    client = Client()
    data_frame = client.compute_along_track(attenuation_name, mode)
    if to_wgs84:
        data_frame = data_frame.to_crs("EPSG:4326")
    client.write_temperature_file(attenuation_name, mode, data_frame)


if __name__ == "__main__":
    cli()
