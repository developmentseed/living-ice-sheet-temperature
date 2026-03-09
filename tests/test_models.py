from pathlib import Path

import httpx
import pytest
import respx
from pytest import MonkeyPatch
from respx import MockRouter

from living_ice_temperature import cache
from living_ice_temperature.models import Borehole

URL = "https://example.com/BoreholeLocations.csv"


def test_boreholes(boreholes_path: Path) -> None:
    boreholes = Borehole.from_csv_href(str(boreholes_path))
    Borehole.to_feature_collection(boreholes)


@pytest.fixture
def cache_dir(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    return tmp_path


def test_from_csv_href_caches(
    boreholes_path: Path, cache_dir: Path, respx_mock: MockRouter
) -> None:
    route = respx_mock.get(URL).mock(
        return_value=httpx.Response(200, text=boreholes_path.read_text())
    )
    boreholes = Borehole.from_csv_href(URL)
    assert len(boreholes) > 0
    assert len(list(cache_dir.iterdir())) == 1
    assert route.call_count == 1

    boreholes_again = Borehole.from_csv_href(URL)
    assert len(boreholes_again) == len(boreholes)
    assert route.call_count == 1


def test_from_csv_href_no_cache(
    boreholes_path: Path, cache_dir: Path, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(URL).mock(
        return_value=httpx.Response(200, text=boreholes_path.read_text())
    )
    Borehole.from_csv_href(URL, no_cache=True)
    assert route.call_count == 1

    Borehole.from_csv_href(URL, no_cache=True)
    assert route.call_count == 2
