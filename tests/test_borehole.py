import numpy
from pandas import DataFrame

from livist.borehole import get_borehole_conductivity


def test_get_borehole_conductivity(wais_divide_imp: DataFrame) -> None:
    assert numpy.isclose(get_borehole_conductivity(wais_divide_imp), 6.380e-06)
