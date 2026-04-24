import csv
import urllib.parse
from collections import defaultdict
from io import StringIO
from pathlib import Path

import pandas
import tqdm
from pandas import DataFrame

from . import temperature
from .borehole import Borehole
from .config import Config
from .temperature import Chemistry, Mode


class Client:
    """A client for our data on source.coop."""

    def __init__(self, config: Config | None = None) -> None:
        """Initializes the client with HTTP and S3 stores.

        Args:
            config: Optional configuration. Uses default Config if not provided.
        """
        self.config = config or Config()  # pyright: ignore[reportCallIssue]
        self.http_store = self.config.source_coop.http_store()
        self.s3_store = self.config.source_coop.s3_store()

    def get_borehole_data_urls(self) -> defaultdict[str, dict[str, str]]:
        """Builds a mapping of borehole data URLs by variable and name.

        Lists CSV files in the borehole data prefix and organizes them into a
        nested dict keyed by variable (e.g. "temp", "imp") then borehole name.

        Returns:
            A defaultdict mapping variable names to dicts of
            ``{borehole_name: url}``.
        """
        urls = defaultdict(dict)
        for list_result in self.s3_store.list(
            prefix=str(Path(self.config.borehole_path).parent)
        ):
            for object_meta in list_result:
                path = object_meta["path"]
                if not path.endswith(".csv"):
                    continue
                path_parts = path.split("/")
                if len(path_parts) != 3:
                    continue
                parts = path_parts[-1].split(".")[0].split("_")
                if not len(parts) == 2:
                    continue
                name = parts[0].lower()
                variable = parts[1]
                urls[variable][name] = urllib.parse.urljoin(
                    self.http_store.url + "/", path
                )
        return urls

    def get_boreholes(self) -> list[Borehole]:
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
        result = self.http_store.get(self.config.borehole_path)
        text = bytes(result.bytes()).decode("utf-8")
        reader = csv.DictReader(text.splitlines(), fieldnames=fieldnames)

        next(reader)  # discard headers

        data_urls = self.get_borehole_data_urls()
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

    def compute_along_track(self, attenuation_name: str, mode: Mode) -> DataFrame:
        data_frame = self.get_attenuation(attenuation_name)
        if mode == Mode.chemistry:
            chemistry = self.get_chemistry()
        else:
            chemistry = None

        return temperature.compute_along_track(data_frame, chemistry)

    def get_attenuation(self, attenuation_name: str) -> DataFrame:
        try:
            path = self.config.attenuation_paths[attenuation_name]
        except KeyError:
            raise ValueError(
                f"Unknown attenuation name: {attenuation_name}. "
                "Valid values are: "
                ", ".join(list(self.config.attenuation_paths.keys()))
            )
        result = self.http_store.get(path)
        text = ""
        with tqdm.tqdm(
            total=result.meta["size"],
            desc="Fetching attenuation data",
            unit="B",
            unit_scale=True,
        ) as progress:
            for chunk in result:
                text += chunk.decode("utf-8")
                progress.update(len(chunk))
        return pandas.read_csv(StringIO(text))

    def get_chemistry(self) -> list[Chemistry]:
        raise NotImplementedError
