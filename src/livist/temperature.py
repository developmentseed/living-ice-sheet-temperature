# Copied, with modifications, from https://github.com/elizadawson/ice_attenuation_temperature/blob/c0efc77db4fd50e12396d9b0c9c6aed54f45aca9/src/atten_temp_functions.py
from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum

import geopandas
import numpy
import scipy.optimize
import tqdm
from geopandas import GeoDataFrame
from pandas import DataFrame

K = 1.380649e-23
C = 3e8
EPS_0 = 8.854e-12
EPS_R = 3.17
EV = 1.602176634e-19
SIGMA_0 = 6.6e-6
E_PURE = 0.55 * 1.602176634e-19
E_COND = 0.22 * 1.602176634e-19
T_REF = 251.0
MU_HP = 3.2
E_HP = 0.20 * 1.602176634e-19
MU_SSCL = 0.43
E_SSCL = 0.19 * 1.602176634e-19


class Mode(StrEnum):
    """Temperature inversion mode, determining which residual function to use."""

    conductivity = "conductivity"
    pure_ice = "pure-ice"


def compute_along_track(
    data_frame: DataFrame,
    conductivity: list[float] | None,
) -> GeoDataFrame:
    """Computes temperature along a radar track from attenuation rates.

    Uses root-finding to invert the attenuation-conductivity relationship and
    recover temperature at each point along the track.

    Args:
        data_frame: Input data with columns `atten_rate_C0`, `x`, and `y`.
        conductivity: The conductivity values to use for calculation. If not
            provided, the pure-ice math will be used.

    Returns:
        A GeoDataFrame with `temperature` and `attenuation` columns.

    Raises:
        ValueError: If `atten_rate_C0` is not in the data frame.
    """
    if "atten_rate_C0" not in data_frame:
        raise ValueError("atten_rate_C0 not found in data_frame")

    attenuation = data_frame["atten_rate_C0"].to_numpy()
    sigma = (
        attenuation
        * C
        * EPS_0
        * numpy.sqrt(EPS_R)
        / (1000 * (10 * numpy.log10(numpy.exp(1))))
    )
    temperature = numpy.full_like(sigma, numpy.nan, dtype=float)
    for i in tqdm.tqdm(range(sigma.size), desc="Computing temperature"):
        if conductivity:
            residual_function = _conductivity_residual(conductivity[i])
        else:
            residual_function = _pure_ice_residual
        try:
            temperature[i] = scipy.optimize.root_scalar(
                residual_function,
                args=(sigma[i],),
                bracket=[150, 350],
                method="brentq",
            ).root
        except ValueError:
            # Attenuation is outside of model range
            temperature[i] = scipy.optimize.fsolve(
                residual_function, 250, args=(sigma[i],)
            )[0]
    return GeoDataFrame(
        data={"temperature": temperature, "attenuation": attenuation},
        geometry=geopandas.points_from_xy(data_frame["x"], data_frame["y"]),
        crs="EPSG:3031",
    )


def _conductivity_residual(
    conductivity: float,
) -> Callable[[float, float], float]:
    def inner(value: float, sigma: float) -> float:
        return conductivity * numpy.exp((E_COND / K) * (1 / T_REF - 1 / value)) - sigma

    return inner


def _pure_ice_residual(value: float, sigma: float) -> float:
    return SIGMA_0 * numpy.exp((E_PURE / K) * (1 / T_REF - 1 / value)) - sigma
