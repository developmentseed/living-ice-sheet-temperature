from io import StringIO

import click
import pandas
import tqdm
from obstore.store import HTTPStore

from .borehole import Borehole
from .client import Client
from .temperature import ChemistryParameters, Mode, compute_along_track


@click.group()
def cli() -> None:
    """Data processing for the Living Ice Sheet Temperature (list) project."""


@cli.command()
def boreholes() -> None:
    """Print borehole data as a FeatureCollection"""
    client = Client()
    text = client.get_borehole_locations_text()
    boreholes = Borehole.from_csv(text, client=client)
    features = Borehole.to_feature_collection(boreholes)
    click.echo(features.model_dump_json(indent=2))


@cli.command()
@click.argument("ATTENUATION_HREF")
@click.argument("OUTFILE")
@click.option("--mode", type=click.Choice(Mode), default=Mode.pure_ice)
@click.option("--to-wgs84", is_flag=True, default=False)
@click.option("--borehole-url")
def temperatures(
    attenuation_href: str,
    outfile: str,
    mode: Mode,
    to_wgs84: bool,
    borehole_url: str | None,
) -> None:
    """Create along-track temperatures"""
    parts = attenuation_href.rsplit("/", 1)
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

    if borehole_url:
        chemistry_parameters = ChemistryParameters.from_borehole_href(borehole_url)
    else:
        chemistry_parameters = None

    result = compute_along_track(track, mode, chemistry_parameters)
    if to_wgs84:
        result = result.to_crs("EPSG:4326")
    result.to_parquet(outfile)  # ty: ignore[invalid-argument-type]


if __name__ == "__main__":
    cli()
