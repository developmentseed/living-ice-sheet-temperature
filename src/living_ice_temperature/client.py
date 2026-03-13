import urllib.parse
from collections import defaultdict

from obstore.store import HTTPStore, S3Store

from .config import Config

HTTP_URL = "https://data.source.coop"
S3_URL = "s3://us-west-2.opendata.source.coop"


class Client:
    """A client for our data on source.coop."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.http_store = HTTPStore.from_url(f"{HTTP_URL}/{self.config.dataset_prefix}")
        self.s3_store = S3Store.from_url(
            f"{S3_URL}/{self.config.dataset_prefix}",
            default_region="us-west-2",
            skip_signature=True,
        )

    def get_borehole_locations_text(self) -> str:
        result = self.http_store.get(
            f"{self.config.borehole_data_prefix}/BoreholeLocations.csv"
        )
        return bytes(result.bytes()).decode("utf-8")

    def get_borehole_data_urls(self) -> defaultdict[str, dict[str, str]]:
        urls = defaultdict(dict)
        for list_result in self.s3_store.list(prefix=self.config.borehole_data_prefix):
            for object_meta in list_result:
                path = object_meta["path"]
                if not path.endswith(".csv"):
                    continue
                path_parts = path.split("/")
                if len(path_parts) != 3:
                    continue
                parts = path_parts[-1].split(".")[0].split("_")
                if not len(parts) == 2:
                    continue
                name = parts[0].lower()
                variable = parts[1]
                urls[variable][name] = urllib.parse.urljoin(
                    self.http_store.url + "/", path
                )
        return urls
