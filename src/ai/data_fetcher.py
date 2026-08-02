"""Simple, safe HTTP data fetch utilities used by AI components.

Notes:
- Keep requests conservative (timeouts, UA). Add retries/caching where appropriate.
- Respect robots.txt and the target site's terms of service. Do not use this to scrape protected content.
"""

from typing import Optional, Dict, Any

try:
    import requests
except ImportError:  # requests is a common dependency; hint if missing
    raise ImportError("requests is required by src.ai.data_fetcher — install with `pip install requests`")


class DataFetcher:
    """A lightweight HTTP data fetcher.

    Usage:
        fetcher = DataFetcher()
        data = fetcher.fetch_json("https://api.example.com/data")
    """

    def __init__(self, user_agent: str = "Ultramaroon-Larp-DataFetcher/1.0", timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None, stream: bool = False):
        resp = self.session.get(url, params=params, timeout=self.timeout, stream=stream)
        resp.raise_for_status()
        return resp

    def fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch JSON from url and return parsed object."""
        resp = self._get(url, params=params)
        return resp.json()

    def fetch_text(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Fetch text content from url."""
        resp = self._get(url, params=params)
        return resp.text

    def fetch_binary(self, url: str, params: Optional[Dict[str, Any]] = None) -> bytes:
        """Fetch binary content from url."""
        resp = self._get(url, params=params, stream=True)
        return resp.content


# Small example (do not run on import)
if __name__ == "__main__":
    f = DataFetcher()
    print(f.fetch_text("https://httpbin.org/get"))
