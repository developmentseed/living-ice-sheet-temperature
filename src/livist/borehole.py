from __future__ import annotations

import csv
from typing import Annotated, Any, Literal

from geojson_pydantic import Feature, FeatureCollection, Point
from geojson_pydantic.types import Position2D
from pydantic import BaseModel, BeforeValidator, model_validator

from .client import Client


def parse_bool(value: Any) -> bool:
    """Parses a value to bool, treating ``"NaN"`` as False.

    Args:
        value: The value to parse.

    Returns:
        False if the value is ``"NaN"``, otherwise ``bool(value)``.
    """
    if value == "NaN":
        return False
    else:
        return bool(value)


class Borehole(BaseModel):
    """An Antarctic borehole with location, metadata, and data URLs.

    Attributes:
        name: Short identifier for the borehole.
        location: Human-readable location description.
        region: East or West Antarctica.
        start_year: First year the borehole was drilled, or None if unknown.
        end_year: Last year the borehole was drilled, or None if unknown.
        type: Borehole type descriptor.
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.
        ice_thickness: Ice thickness at the borehole in meters.
        drilled_depth: Depth drilled in meters.
        original_publication: Citation for the original data publication.
        has_temperature: Whether temperature data is available.
        has_chemistry: Whether chemistry data is available.
        has_conductivity: Whether conductivity data is available.
        has_grain_size: Whether grain size data is available.
        temperature_data_url: URL to the temperature CSV, if available.
        chemistry_data_url: URL to the chemistry CSV, if available.
        grainsize_data_url: URL to the grain size CSV, if available.
    """

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
    def from_csv(cls, text: str, client: Client | None = None) -> list[Borehole]:
        """Parses borehole locations from CSV text and attaches data URLs.

        Args:
            text: Raw CSV content with borehole location data.
            client: Optional client for fetching data URLs. Creates a default
                client if not provided.

        Returns:
            A list of Borehole instances with data URLs populated.
        """
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
        reader = csv.DictReader(text.splitlines(), fieldnames=fieldnames)

        next(reader)  # discard headers

        data_urls = (client or Client()).get_borehole_data_urls()
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
        """Converts a list of boreholes to a GeoJSON FeatureCollection.

        Args:
            boreholes: The boreholes to convert.

        Returns:
            A GeoJSON FeatureCollection with one Point feature per borehole.
        """
        return FeatureCollection(
            type="FeatureCollection",
            features=[borehole.to_feature() for borehole in boreholes],
        )

    def to_feature(self) -> Feature:
        """Converts this borehole to a GeoJSON Feature.

        Returns:
            A GeoJSON Feature with a Point geometry and borehole properties.
        """
        return Feature(
            type="Feature",
            geometry=self.to_point(),
            properties=self.model_dump(exclude={"lat", "lon"}),
        )

    def to_point(self) -> Point:
        """Converts this borehole's location to a GeoJSON Point.

        Returns:
            A GeoJSON Point at the borehole's longitude and latitude.
        """
        return Point(type="Point", coordinates=Position2D(self.lon, self.lat))
