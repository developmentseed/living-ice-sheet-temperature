import numpy
import pytest
from pandas import DataFrame

from living_ice_temperature import temperature
from living_ice_temperature.temperature import Mode


@pytest.mark.parametrize("mode,column", [(Mode.pure_ice, "pure_temperature_K")])
def test_compute_along_track(sample_data: DataFrame, mode: Mode, column: str) -> None:
    result = temperature.compute_along_track(sample_data, mode)
    numpy.testing.assert_allclose(
        result["temperature"].to_numpy(), sample_data[column], rtol=1e-6
    )
