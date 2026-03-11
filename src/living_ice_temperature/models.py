from __future__ import annotations

import csv
import urllib.parse
from collections import defaultdict
from typing import Annotated, Any, Literal

from geojson_pydantic import Feature, FeatureCollection, Point
from geojson_pydantic.types import Position2D
from obstore.store import S3Store
from pydantic import BaseModel, BeforeValidator, model_validator

from . import cache

BOREHOLE_URL = "https://data.source.coop/englacial/ice-sheet-temperature/AntarcticaBoreholeData/BoreholeLocations.csv"
BOREHOLE_DATA_URL = (
    "https://data.source.coop/englacial/ice-sheet-temperature/AntarcticaBoreholeData/"
)
BOREHOLE_DATA_S3_URL = "s3://us-west-2.opendata.source.coop/englacial/ice-sheet-temperature/AntarcticaBoreholeData/"


def parse_bool(value: Any) -> bool:
    if value == "NaN":
        return False
    else:
        return bool(value)


class Borehole(BaseModel):
    name: str
    location: str
    region: Literal["East", "West"]
    start_year: int | None
    end_year: int | None
    type: str
    lat: float
    lon: float
    ice_thickness: float
    drilled_depth: float
    original_publication: str
    has_temperature: Annotated[bool, BeforeValidator(parse_bool)]
    has_chemistry: Annotated[bool, BeforeValidator(parse_bool)]
    has_conductivity: Annotated[bool, BeforeValidator(parse_bool)]
    has_grain_size: Annotated[bool, BeforeValidator(parse_bool)]
    temperature_data_url: str | None = None
    chemistry_data_url: str | None = None
    grainsize_data_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def split_years(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if years_drilled := data.pop("years_drilled", None):
                if years_drilled == "NaN":
                    data["start_year"] = None
                    data["end_year"] = None
                else:
                    if isinstance(years_drilled, str):
                        parts = (
                            years_drilled.replace("—", "-").replace("–", "-").split("-")
                        )
                    else:
                        raise ValueError(
                            f"years_drilled was not a string: {years_drilled}"
                        )
                    data["start_year"] = parts[0]
                    if len(parts) == 1:
                        data["end_year"] = parts[0]
                    elif len(parts) == 2:
                        data["end_year"] = parts[1]
                    else:
                        raise ValueError(
                            f"Too many parts in years_drilled: {years_drilled}"
                        )
        return data

    @classmethod
    def from_csv_href(cls, *, no_cache: bool = False) -> list[Borehole]:
        boreholes = []
        fieldnames = [
            "name",
            "location",
            "region",
            "years_drilled",
            "type",
            "lat",
            "lon",
            "ice_thickness",
            "drilled_depth",
            "has_temperature",
            "has_chemistry",
            "has_conductivity",
            "has_grain_size",
            "original_publication",
        ]
        path = cache.fetch(BOREHOLE_URL, no_cache=no_cache)
        text = path.read_text()
        reader = csv.DictReader(text.splitlines(), fieldnames=fieldnames)

        next(reader)  # discard headers

        data_urls = get_data_urls()
        for row in reader:
            if row["name"]:
                borehole = Borehole.model_validate(row)
                borehole.temperature_data_url = data_urls["temp"].get(
                    borehole.name.lower()
                )
                borehole.chemistry_data_url = data_urls["imp"].get(
                    borehole.name.lower()
                )
                borehole.grainsize_data_url = data_urls["grainsize"].get(
                    borehole.name.lower()
                )
                boreholes.append(borehole)
        return boreholes

    @classmethod
    def to_feature_collection(cls, boreholes: list[Borehole]) -> FeatureCollection:
        return FeatureCollection(
            type="FeatureCollection",
            features=[borehole.to_feature() for borehole in boreholes],
        )

    def to_feature(self) -> Feature:
        return Feature(
            type="Feature",
            geometry=self.to_point(),
            properties=self.model_dump(exclude={"lat", "lon"}),
        )

    def to_point(self) -> Point:
        return Point(type="Point", coordinates=Position2D(self.lon, self.lat))


def get_data_urls() -> defaultdict[str, dict[str, str]]:
    store = S3Store.from_url(BOREHOLE_DATA_S3_URL, skip_signature=True)
    urls = defaultdict(dict)
    for list_result in store.list():
        for object_meta in list_result:
            path = object_meta["path"]
            if not path.endswith(".csv"):
                continue
            path_parts = path.split("/")
            if len(path_parts) != 2:
                continue
            parts = path_parts[1].split(".")[0].split("_")
            if not len(parts) == 2:
                continue
            name = parts[0].lower()
            variable = parts[1]
            urls[variable][name] = urllib.parse.urljoin(BOREHOLE_DATA_URL, path)
    return urls
