# Copied, with modifications, from https://github.com/elizadawson/ice_attenuation_temperature/blob/c0efc77db4fd50e12396d9b0c9c6aed54f45aca9/src/atten_temp_functions.py
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO

import geopandas
import numpy
import pandas
import scipy.optimize
import tqdm
from geopandas import GeoDataFrame
from obstore.store import HTTPStore
from pandas import DataFrame

K = 1.380649e-23
C = 3e8
EPS_0 = 8.854e-12
EPS_R = 3.17
EV = 1.602176634e-19
SIGMA_0 = 6.6e-6
E_PURE = 0.55 * 1.602176634e-19
T_REF = 251.0
MU_HP = 3.2
E_HP = 0.20 * 1.602176634e-19
MU_SSCL = 0.43
E_SSCL = 0.19 * 1.602176634e-19


@dataclass
class ChemistryParameters:
    molar_hp: float
    molar_sscl: float

    @classmethod
    def from_borehole_href(cls, borehole_href: str) -> ChemistryParameters:
        parts = borehole_href.rsplit("/", 1)
        store = HTTPStore.from_url(parts[0])
        result = store.get(parts[1])
        data_frame = pandas.read_csv(StringIO(bytes(result.bytes()).decode("utf-8")))
        return ChemistryParameters(
            molar_hp=data_frame["acid [mol/L]"].mean().item(),
            molar_sscl=data_frame["sscl [mol/L]"].mean().item(),
        )


class Mode(StrEnum):
    """Temperature inversion mode, determining which residual function to use."""

    chemistry = "chem"
    conductivity = "cond"
    pure_ice = "pure"

    def residual_function(
        self, chemistry_parameters: ChemistryParameters | None
    ) -> Callable[[float, float], float]:
        """Returns the residual function for this mode."""
        match self:
            case Mode.chemistry:
                if chemistry_parameters:
                    return _chemistry_residual(chemistry_parameters)
                else:
                    raise ValueError("chemistry mode requires chemistry_parameters")
            case Mode.conductivity:
                return _conductivity_residual
            case Mode.pure_ice:
                return _pure_ice_residual


def compute_along_track(
    data_frame: DataFrame,
    mode: Mode,
    chemistry_parameters: ChemistryParameters | None = None,
) -> GeoDataFrame:
    """Computes temperature along a radar track from attenuation rates.

    Uses root-finding to invert the attenuation-conductivity relationship and
    recover temperature at each point along the track.

    Args:
        data_frame: Input data with columns ``atten_rate_C0``, ``x``, and ``y``.
        mode: The inversion mode selecting which residual function to use.

    Returns:
        A GeoDataFrame with ``temperature`` and ``attenuation`` columns.

    Raises:
        ValueError: If ``atten_rate_C0`` is not in the data frame.
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
    residual_function = mode.residual_function(chemistry_parameters)
    for i in tqdm.tqdm(range(sigma.size), desc="Computing temperature"):
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


def _conductivity_residual(value: float, sigma: float) -> float:
    raise NotImplementedError


def _chemistry_residual(
    chemistry_parameters: ChemistryParameters,
) -> Callable[[float, float], float]:
    def chemistry_residual_inner(value: float, sigma: float) -> float:
        hp = (
            MU_HP
            * chemistry_parameters.molar_hp
            * numpy.exp((E_HP / K) * (1 / T_REF - 1 / value))
        )
        sscl = (
            MU_SSCL
            * chemistry_parameters.molar_sscl
            * numpy.exp((E_SSCL / K) * (1 / T_REF - 1 / value))
        )
        return _pure_ice_conductivity(value) + hp + sscl - sigma

    return chemistry_residual_inner


def _pure_ice_residual(value: float, sigma: float) -> float:
    return _pure_ice_conductivity(value) - sigma


def _pure_ice_conductivity(value: float) -> float:
    return SIGMA_0 * numpy.exp((E_PURE / K) * (1 / T_REF - 1 / value))
