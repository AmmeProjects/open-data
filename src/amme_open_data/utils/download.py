import os
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Download:
    def __init__(
        self,
        url: str,
        path: str,
        retries: int = 5,
        backoff_factor: float = 2.0,
        timeout: int = 60,
    ) -> None:
        self.url = url
        self.path = path
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout

    def _build_session(self) -> requests.Session:
        retry = Retry(
            total=self.retries,
            connect=self.retries,
            read=self.retries,
            status=self.retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "HEAD"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/xml,text/xml,application/xhtml+xml,*/*;q=0.8",
            }
        )
        return session

    def download(self, force: bool = False) -> None:
        if not force and os.path.exists(self.path):
            return

        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp_path = f"{self.path}.tmp"

        with self._build_session() as session:
            last_exc: Exception | None = None
            for attempt in range(1, self.retries + 1):
                try:
                    with session.get(
                        self.url, stream=True, timeout=self.timeout
                    ) as response:
                        response.raise_for_status()
                        with open(tmp_path, "wb") as fp:
                            for chunk in response.iter_content(chunk_size=65536):
                                if chunk:
                                    fp.write(chunk)
                    os.replace(tmp_path, self.path)
                    return
                except requests.RequestException as exc:
                    last_exc = exc
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    if attempt < self.retries:
                        delay = self.backoff_factor * (2 ** (attempt - 1))
                        time.sleep(delay)
            if last_exc is not None:
                raise last_exc
