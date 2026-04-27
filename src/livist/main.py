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
@click.option("--attenuation-name", "attenuation_name", default=None)
@click.option("--mode", "mode", type=Choice([m.value for m in Mode]), default=None)
@click.option("--to-wgs84", is_flag=True, default=False)
def temperature(
    attenuation_name: str | None,
    mode: str | None,
    to_wgs84: bool,
) -> None:
    """Create along-track temperatures"""
    client = Client()
    attenuation_names = (
        [attenuation_name]
        if attenuation_name
        else list(client.config.attenuation_paths.keys())
    )
    modes = [Mode(mode)] if mode else list(Mode)
    for name in attenuation_names:
        for m in modes:
            data_frame = client.compute_along_track(name, m)
            if to_wgs84:
                data_frame = data_frame.to_crs("EPSG:4326")
            client.write_temperature_file(name, m, data_frame)


if __name__ == "__main__":
    cli()
