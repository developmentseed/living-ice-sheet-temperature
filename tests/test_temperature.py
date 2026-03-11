from pathlib import Path

from living_ice_temperature import temperature
from living_ice_temperature.temperature import Mode


def test_compute_along_track(attenuation_path: Path) -> None:
    temperature.compute_along_track(attenuation_path, Mode.pure_ice)
