from pydantic_settings import BaseSettings


class Config(BaseSettings):
    dataset_prefix: str = "englacial/ice-sheet-temperature"
    borehole_data_prefix: str = "AntarcticaBoreholeData"
    attenuation_rate_prefix: str = "AttenuationRateData"
    temperature_prefix: str = "temperature"
