import numpy
import pytest
from pandas import DataFrame

from livist import temperature


def test_compute_along_track_pure_ice(sample_data: DataFrame) -> None:
    result = temperature.compute_along_track(sample_data, None)
    numpy.testing.assert_allclose(
        result["temperature"].to_numpy(), sample_data["pure_temperature_K"], rtol=1e-6
    )


@pytest.mark.skip("Don't have upstream kriging results to compare against")
def test_compute_along_track_chemistry(sample_data: DataFrame) -> None:
    result = temperature.compute_along_track(sample_data, ([], []))
    numpy.testing.assert_allclose(
        result["temperature"].to_numpy(), sample_data["chem_temperature_K"], rtol=1e-6
    )
