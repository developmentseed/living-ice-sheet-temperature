from io import StringIO

import click
import pandas
import tqdm
from obstore.store import HTTPStore

from .borehole import Borehole
from .client import Client
from .temperature import Mode, compute_along_track


@click.group()
def cli() -> None:
    """Data processing for Living Ice Temperature."""


@cli.command()
def boreholes() -> None:
    """Process borehole data into a FeatureCollection"""
    client = Client()
    text = client.get_borehole_locations_text()
    boreholes = Borehole.from_csv(text, client=client)
    features = Borehole.to_feature_collection(boreholes)
    click.echo(features.model_dump_json(indent=2))


@cli.command()
@click.argument("HREF")
@click.argument("OUTFILE")
@click.option("--mode", type=click.Choice(Mode), default=Mode.pure_ice)
@click.option("--to-wgs84", is_flag=True, default=False)
def temperature(href: str, outfile: str, mode: Mode, to_wgs84: bool) -> None:
    """Create along-track temperatures."""
    parts = href.rsplit("/", 1)
    store = HTTPStore.from_url(parts[0])
    result = store.get(parts[1])
    text = ""
    with tqdm.tqdm(
        total=result.meta["size"], desc="Fetching data", unit="B", unit_scale=True
    ) as progress:
        for chunk in result:
            text += chunk.decode("utf-8")
            progress.update(len(chunk))
    track = pandas.read_csv(StringIO(text))
    result = compute_along_track(track, mode, to_wgs84)
    result.to_parquet(outfile)  # ty: ignore[invalid-argument-type]


if __name__ == "__main__":
    cli()
