from pathlib import Path

import pytest


@pytest.fixture
def data_path() -> Path:
    return Path(__file__).parents[1] / "data"


@pytest.fixture
def boreholes_path(data_path: Path) -> Path:
    return data_path / "BoreholeLocations.csv"


@pytest.fixture
def attenuation_path(data_path: Path) -> Path:
    return data_path / "FullDataSet_Randomized_head.txt"
