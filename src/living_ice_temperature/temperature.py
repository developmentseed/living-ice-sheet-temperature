# Copied, with modifications, from https://github.com/elizadawson/ice_attenuation_temperature/blob/c0efc77db4fd50e12396d9b0c9c6aed54f45aca9/src/atten_temp_functions.py


from enum import StrEnum
from pathlib import Path
from typing import Callable

import geopandas
import numpy
import pandas
from pandas import DataFrame
import scipy.optimize
import tqdm
from geopandas import GeoDataFrame

K = 1.380649e-23
C = 3e8
EPS_0 = 8.854e-12
EPS_R = 3.17
EV = 1.602176634e-19
SIGMA_0 = 6.6e-6
E_PURE = 0.55 * 1.602176634e-19
T_REF = 251.0


class Mode(StrEnum):
    chemistry = "chem"
    conductivity = "cond"
    pure_ice = "pure"

    def residual_function(self) -> Callable[[float, float], float]:
        match self:
            case Mode.chemistry:
                return chemistry_residual
            case Mode.conductivity:
                return conductivity_residual
            case Mode.pure_ice:
                return pure_ice_residual


def compute_along_track_from_path(path: Path, mode: Mode) -> GeoDataFrame:
    data_frame = pandas.read_csv(path)
    return compute_along_track(data_frame, mode)

def compute_along_track(data_frame: DataFrame, mode: Mode) -> GeoDataFrame:
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
    residual_function = mode.residual_function()
    for i in tqdm.tqdm(range(sigma.size)):
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
    ).to_crs("EPSG:4326")


def conductivity_residual(value: float, sigma: float):
    raise NotImplementedError


def chemistry_residual(value: float, sigma: float):
    raise NotImplementedError


def pure_ice_residual(value: float, sigma: float):
    return (SIGMA_0 * numpy.exp((E_PURE / K) * (1 / T_REF - 1 / value))) - sigma
