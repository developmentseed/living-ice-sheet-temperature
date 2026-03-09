import click

from . import cache
from .models import Borehole

DEFAULT_BOREHOLE_HREF = "https://data.source.coop/englacial/ice-sheet-temperature/AntarcticaBoreholeData/BoreholeLocations.csv"

no_cache = click.option("--no-cache", is_flag=True, help="Ignore the local file cache.")


@click.group()
def cli() -> None:
    """Data processing for Living Ice Temperature."""


@cli.command()
@click.option("--href")
@no_cache
def boreholes(href: str | None, no_cache: bool) -> None:
    """Process borehole data into a FeatureCollection"""
    if href is None:
        href = DEFAULT_BOREHOLE_HREF
    boreholes = Borehole.from_csv_href(href, no_cache=no_cache)
    features = Borehole.to_feature_collection(boreholes)
    click.echo(features.model_dump_json(indent=2))


@cli.command()
@click.argument("URL")
@no_cache
def fetch(url: str, no_cache: bool) -> None:
    """Fetch a url and return its contents.

    Caches the value locally for later fetches.
    """
    data = cache.fetch(url, no_cache=no_cache)
    click.echo(data)


if __name__ == "__main__":
    cli()
