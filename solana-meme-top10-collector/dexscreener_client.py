"""Client for interacting with the Dexscreener API."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import requests

BASE_URL = "https://api.dexscreener.com/latest"
_API_KEY_ENV_VAR = "DEXSCREENER_API_KEY"
_DEFAULT_HEADERS: Dict[str, str] = {
    "Accept": "application/json",
    "User-Agent": "solana-meme-top10-collector/1.0",
}


def _headers() -> Dict[str, str]:
    """Return request headers, including the optional API key."""
    headers = dict(_DEFAULT_HEADERS)
    api_key = os.getenv(_API_KEY_ENV_VAR)
    if api_key:
        headers["X-API-Key"] = api_key.strip()
    return headers


def _get(path: str, params: Optional[Dict[str, Any]] = None, *, timeout: int = 10) -> Dict[str, Any]:
    """Perform a GET request with retry and exponential backoff."""
    url = f"{BASE_URL}{path}"
    retries = 5
    backoff = 0.5
    for attempt in range(1, retries + 1):
        response = requests.get(url, params=params, headers=_headers(), timeout=timeout)
        if response.status_code in {429} or response.status_code >= 500:
            if attempt == retries:
                response.raise_for_status()
            time.sleep(backoff)
            backoff *= 2
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError("Failed to fetch data from Dexscreener API")


def search_pairs_solana(query: str) -> Dict[str, Any]:
    """Search for pairs on Solana matching the given query."""
    data = _get("/dex/search", params={"q": query})
    if "pairs" in data:
        data["pairs"] = [pair for pair in data["pairs"] if pair.get("chainId") == "solana"]
    return data


def token_pairs(token_address: str) -> Dict[str, Any]:
    """Return pairs for a given token address."""
    return _get(f"/dex/tokens/{token_address}")


def pair_detail(pair_address: str) -> Dict[str, Any]:
    """Return details for a specific pair on Solana."""
    return _get(f"/dex/pairs/solana/{pair_address}")
