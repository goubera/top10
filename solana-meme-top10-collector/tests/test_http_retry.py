import pathlib
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils import http_get  # noqa: E402


class DummyResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


def test_http_retry_429(monkeypatch):
    calls = []

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append(1)
        if len(calls) == 1:
            return DummyResponse(429, {})
        return DummyResponse(200, {"ok": True})

    sleeps = []
    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    data = http_get("https://api.example.com", retries=2)

    assert data == {"ok": True}
    assert calls == [1, 1]
    assert sleeps == [1]
