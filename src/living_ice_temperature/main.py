import click

from .models import Borehole

DEFAULT_BOREHOLE_HREF = "https://data.source.coop/englacial/ice-sheet-temperature/AntarcticaBoreholeData/BoreholeLocations.csv"


@click.group()
def cli() -> None:
    """Data processing for Living Ice Temperature."""


@cli.command()
@click.option("--href")
def boreholes(href: str | None) -> None:
    """Process borehole data into a FeatureCollection"""
    if href is None:
        href = DEFAULT_BOREHOLE_HREF
    boreholes = Borehole.from_csv_href(href)
    features = Borehole.to_feature_collection(boreholes)
    click.echo(features.model_dump_json(indent=2))


if __name__ == "__main__":
    cli()
