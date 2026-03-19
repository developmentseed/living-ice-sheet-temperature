import numpy
from pandas import DataFrame

from livist import temperature
from livist.temperature import ChemistryParameters, Mode


def test_compute_along_track_pure_ice(sample_data: DataFrame) -> None:
    result = temperature.compute_along_track(sample_data, Mode.pure_ice)
    numpy.testing.assert_allclose(
        result["temperature"].to_numpy(), sample_data["pure_temperature_K"], rtol=1e-6
    )


def test_compute_along_track_chemistry(
    sample_data: DataFrame, chemistry_parameters: ChemistryParameters
) -> None:
    result = temperature.compute_along_track(
        sample_data, Mode.chemistry, chemistry_parameters=chemistry_parameters
    )
    numpy.testing.assert_allclose(
        result["temperature"].to_numpy(), sample_data["chem_temperature_K"], rtol=1e-6
    )
