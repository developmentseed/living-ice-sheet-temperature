from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration for data access on source.coop.

    Attributes:
        dataset_prefix: Top-level dataset path on source.coop.
        borehole_data_prefix: Sub-path for borehole CSV files.
        attenuation_rate_prefix: Sub-path for attenuation rate data.
        temperature_prefix: Sub-path for temperature data.
    """

    dataset_prefix: str = "englacial/ice-sheet-temperature"
    borehole_data_prefix: str = "AntarcticaBoreholeData"
    attenuation_rate_prefix: str = "AttenuationRateData"
    temperature_prefix: str = "temperature"
