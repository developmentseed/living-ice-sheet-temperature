import json
from pathlib import Path

import pytest
from pandas import DataFrame


@pytest.fixture
def data_path() -> Path:
    return Path(__file__).parents[1] / "data"


@pytest.fixture
def boreholes_path(data_path: Path) -> Path:
    return data_path / "BoreholeLocations.csv"


@pytest.fixture
def attenuation_path(data_path: Path) -> Path:
    return data_path / "FullDataSet_Randomized_head.txt"


@pytest.fixture
def sample_data_path(data_path: Path) -> Path:
    return data_path / "sample_data.json"


@pytest.fixture
def sample_data(sample_data_path: Path) -> DataFrame:
    with open(sample_data_path) as f:
        data = json.load(f)
    points = data["points"]
    return DataFrame(
        {
            "x": [p["x"] for p in points],
            "y": [p["y"] for p in points],
            "atten_rate_C0": [p["attenuation_rate"] for p in points],
            "pure_temperature_K": [p["pure"]["temperature_K"] for p in points],
        }
    )
