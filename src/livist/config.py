from obstore.store import HTTPStore, S3Store
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class SourceCoop(BaseSettings):
    """Configuration for data access on source.coop"""

    http_url: str = "https://data.source.coop"
    s3_url: str = "s3://us-west-2.opendata.source.coop"
    s3_region: str = "us-west-2"

    def http_store(self) -> HTTPStore:
        return HTTPStore.from_url(f"{self.http_url}")

    def s3_store(self) -> S3Store:
        return S3Store.from_url(
            f"{self.s3_url}",
            default_region=self.s3_region,
            skip_signature=True,
        )


class Config(BaseSettings):
    """General configuration."""

    borehole_path: str
    attenuation_paths: dict[str, str]
    source_coop: SourceCoop = SourceCoop()

    model_config = SettingsConfigDict(toml_file="config.toml")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)
