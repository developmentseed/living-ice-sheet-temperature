import csv
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import numpy
import pandas
import tqdm
from pandas import DataFrame
from pykrige import OrdinaryKriging
from pyproj import Transformer

from . import temperature
from .borehole import Borehole
from .config import Config
from .temperature import Chemistry, Mode


@dataclass
class ChemistryKriging:
    molar: OrdinaryKriging
    sscl: OrdinaryKriging


class Client:
    """A client for our data on source.coop."""

    def __init__(self, config: Config | None = None) -> None:
        """Initializes the client with HTTP and S3 stores.

        Args:
            config: Optional configuration. Uses default Config if not provided.
        """
        self.config = config or Config()  # ty: ignore[missing-argument]
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
            prefix=str(Path(self.config.borehole_path).parent) + "/"
        ):
            for object_meta in list_result:
                path = object_meta["path"]
                if not path.endswith(".csv"):
                    continue
                path_parts = path.split("/")
                if len(path_parts) != 5:
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
            chemistry = self.get_chemistry(
                data_frame["x"].tolist(), data_frame["y"].tolist()
            )
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
        local_path = self.config.data_directory / path
        if not local_path.exists():
            result = self.http_store.get(path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with (
                local_path.open("wb") as f,
                tqdm.tqdm(
                    total=result.meta["size"],
                    desc="Fetching attenuation data",
                    unit="B",
                    unit_scale=True,
                ) as progress,
            ):
                for chunk in result:
                    f.write(chunk)
                    progress.update(len(chunk))
        return pandas.read_csv(local_path)

    def get_chemistry(self, x: list[float], y: list[float]) -> list[Chemistry]:
        chemistry_kriging = self.get_chemistry_kriging()
        molar_values, _ = chemistry_kriging.molar.execute("points", x, y)
        sscl_values, _ = chemistry_kriging.sscl.execute("points", x, y)
        return [
            Chemistry(molar_hp=a, molar_sscl=b)
            for a, b in zip(molar_values, sscl_values)
        ]

    def get_chemistry_kriging(self) -> ChemistryKriging:
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3031")
        boreholes = self.get_boreholes()
        borehole_x = list()
        borehole_y = list()
        molar_hp = list()
        molar_sscl = list()
        for borehole in boreholes:
            if borehole.chemistry_data_url:
                result = self.http_store.get(
                    urllib.parse.urlparse(borehole.chemistry_data_url).path
                )
                text = bytes(result.bytes()).decode("utf-8")
                data_frame = pandas.read_csv(StringIO(text))
                if "acid [mol/L]" in data_frame and "sscl [mol/L]" in data_frame:
                    proj_x, proj_y = transformer.transform(borehole.lat, borehole.lon)
                    borehole_x.append(proj_x)
                    borehole_y.append(proj_y)
                    hp = data_frame[["depth [m]", "acid [mol/L]"]].dropna()
                    sscl = data_frame[["depth [m]", "sscl [mol/L]"]].dropna()
                    hp_depth = numpy.asarray(hp["depth [m]"])
                    sscl_depth = numpy.asarray(sscl["depth [m]"])
                    molar_hp.append(
                        numpy.trapezoid(numpy.asarray(hp["acid [mol/L]"]), hp_depth)
                        / (hp_depth[-1] - hp_depth[0])
                    )
                    molar_sscl.append(
                        numpy.trapezoid(numpy.asarray(sscl["sscl [mol/L]"]), sscl_depth)
                        / (sscl_depth[-1] - sscl_depth[0])
                    )
        molar = OrdinaryKriging(borehole_x, borehole_y, molar_hp)
        sscl = OrdinaryKriging(borehole_x, borehole_y, molar_sscl)
        return ChemistryKriging(molar, sscl)

    def write_temperature_file(
        self,
        attenuation_name: str,
        mode: Mode,
        data_frame: DataFrame,
        suffix: str | None = None,
    ) -> None:
        outfile = self.config.get_temperature_file_name(
            attenuation_name, mode, suffix or ""
        )
        data_frame.to_parquet(outfile)
