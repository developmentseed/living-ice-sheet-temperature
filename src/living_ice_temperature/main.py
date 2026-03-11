import urllib.parse
from pathlib import Path

import click

from . import cache
from .models import Borehole
from .temperature import Mode
from .temperature import compute_along_track_from_path as compute_temperature_along_track_from_path

DEFAULT_BOREHOLE_HREF = "https://data.source.coop/englacial/ice-sheet-temperature/AntarcticaBoreholeData/BoreholeLocations.csv"

no_cache = click.option("--no-cache", is_flag=True, help="Ignore the local file cache.")


@click.group()
def cli() -> None:
    """Data processing for Living Ice Temperature."""


@cli.command()
@no_cache
def boreholes(no_cache: bool) -> None:
    """Process borehole data into a FeatureCollection"""
    boreholes = Borehole.from_csv_href(no_cache=no_cache)
    features = Borehole.to_feature_collection(boreholes)
    click.echo(features.model_dump_json(indent=2))


@cli.command()
@click.argument("URL")
@no_cache
def fetch(url: str, no_cache: bool) -> None:
    """Fetch a url and return its local file path."""
    path = cache.fetch(url, no_cache=no_cache)
    click.echo(path)


@cli.command()
@click.argument("INFILE")
@click.argument("OUTFILE")
@click.option("--mode", type=click.Choice(Mode), default=Mode.pure_ice)
@no_cache
def temperature(infile: str, outfile: str, mode: Mode, no_cache: bool) -> None:
    """Create along-track temperatures."""
    if urllib.parse.urlparse(infile).scheme:
        path = cache.fetch(infile)
    else:
        path = Path(infile)
    temperature = compute_temperature_along_track_from_path(path, mode)
    temperature.to_parquet(outfile)  # ty: ignore[invalid-argument-type]


if __name__ == "__main__":
    cli()
