import hashlib
from pathlib import Path

import httpx
import platformdirs

CACHE_DIR = Path(platformdirs.user_cache_dir("living-ice-temperature"))


def fetch(url: str, *, no_cache: bool = False) -> str:
    cache_key = hashlib.sha256(url.encode()).hexdigest()
    cache_path = CACHE_DIR / cache_key

    if not no_cache and cache_path.exists():
        return cache_path.read_text()

    response = httpx.get(url).raise_for_status()
    text = response.text

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(text)

    return text
