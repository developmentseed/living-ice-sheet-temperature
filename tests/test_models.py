from collections import defaultdict
from pathlib import Path

from pytest import MonkeyPatch

from living_ice_temperature.client import Client
from living_ice_temperature.models import Borehole


def test_boreholes(boreholes_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        Client,
        "get_borehole_data_urls",
        lambda self: defaultdict(dict),
    )
    boreholes = Borehole.from_csv(boreholes_path.read_text())
    Borehole.to_feature_collection(boreholes)
