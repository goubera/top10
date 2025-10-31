"""
Multi-source data collector with fallbacks for Solana DEX pairs.

Priority order:
1. DexScreener API (with API key if available)
2. Raydium API (public)
3. CoinGecko Solana trending (public)

Each source implements a common interface for fetching top pairs by volume.
"""

import os
import time
import logging
from typing import Any, Dict, List, Optional
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSource:
    """Base class for data sources."""

    def fetch_top_pairs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch top trading pairs by volume. Must be implemented by subclasses."""
        raise NotImplementedError


class DexScreenerSource(DataSource):
    """DexScreener API source (requires API key for reliable access)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEXSCREENER_API_KEY", "").strip()
        self.base_url = "https://api.dexscreener.com"

    def _http_get(self, path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 20) -> Dict[str, Any]:
        """HTTP GET with retries and exponential backoff."""
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        backoffs = [0, 1, 2, 4, 8]
        last_err = None

        for b in backoffs:
            if b:
                time.sleep(b)
            try:
                r = requests.get(url, params=params or {}, headers=headers, timeout=timeout)
                # Retry on rate limit or server errors
                if r.status_code in (429, 500, 502, 503, 504):
                    last_err = (r.status_code, r.text[:200])
                    continue
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_err = str(e)
                continue

        raise RuntimeError(f"GET {path} failed after retries: {last_err}")

    def fetch_top_pairs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch top Solana pairs from DexScreener."""
        try:
            # Try search endpoint first
            try:
                data = self._http_get("/latest/dex/search", params={"q": "SOL"})
                pairs = data.get("pairs", [])
                sol_pairs = [p for p in pairs if str(p.get("chainId", "")).lower() == "solana"]
            except Exception as e:
                logger.warning(f"DexScreener search failed: {e}")
                sol_pairs = []

            # Fallback to direct pairs endpoint
            if not sol_pairs:
                logger.info("Trying DexScreener pairs endpoint as fallback...")
                data = self._http_get("/latest/dex/pairs/solana")
                sol_pairs = data.get("pairs", [])

            if not sol_pairs:
                raise ValueError("No pairs returned from DexScreener")

            # Sort by volume and return top
            sol_pairs.sort(key=lambda p: self._get_volume(p), reverse=True)
            logger.info(f"DexScreener: fetched {len(sol_pairs)} pairs")
            return sol_pairs[:limit]

        except Exception as e:
            logger.error(f"DexScreener source failed: {e}")
            return []

    def _get_volume(self, pair: Dict[str, Any]) -> float:
        """Extract 24h volume from pair data."""
        v = pair.get("volume24hUsd") or (pair.get("volume", {}) or {}).get("h24")
        try:
            return float(v or 0.0)
        except:
            return 0.0


class RaydiumSource(DataSource):
    """Raydium API source (public, no API key needed)."""

    def __init__(self):
        self.base_url = "https://api.raydium.io"

    def fetch_top_pairs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch top pairs from Raydium API."""
        try:
            url = f"{self.base_url}/v2/main/pairs"
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            data = r.json()

            # Filter for Solana chain and sort by volume
            pairs = []
            for pair in data:
                if not isinstance(pair, dict):
                    continue

                # Convert Raydium format to DexScreener-like format
                volume_24h = float(pair.get("volume_24h_usd", 0) or 0)
                if volume_24h > 0:
                    pairs.append({
                        "chainId": "solana",
                        "pairAddress": pair.get("amm_id", ""),
                        "baseToken": {
                            "address": pair.get("base_mint", ""),
                            "name": pair.get("name", "").split("/")[0].strip() if "/" in pair.get("name", "") else "",
                            "symbol": pair.get("name", "").split("/")[0].strip() if "/" in pair.get("name", "") else "",
                        },
                        "priceUsd": float(pair.get("price", 0) or 0),
                        "liquidityUsd": float(pair.get("liquidity", 0) or 0),
                        "volume24hUsd": volume_24h,
                        "txns24h": 0,  # Not available from Raydium
                        "priceChange24h": float(pair.get("price_change_24h", 0) or 0),
                        "pairCreatedAt": 0,  # Not available
                    })

            pairs.sort(key=lambda p: p.get("volume24hUsd", 0), reverse=True)
            logger.info(f"Raydium: fetched {len(pairs)} pairs")
            return pairs[:limit]

        except Exception as e:
            logger.error(f"Raydium source failed: {e}")
            return []


def fetch_top_solana_pairs(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch top Solana trading pairs using multiple sources with fallback.

    Returns:
        List of pair dictionaries in standardized format

    Raises:
        RuntimeError: If all data sources fail
    """
    sources = [
        ("DexScreener", DexScreenerSource()),
        ("Raydium", RaydiumSource()),
    ]

    for source_name, source in sources:
        try:
            logger.info(f"Trying {source_name}...")
            pairs = source.fetch_top_pairs(limit=limit)
            if pairs:
                logger.info(f"✓ {source_name} succeeded with {len(pairs)} pairs")
                return pairs
        except Exception as e:
            logger.warning(f"✗ {source_name} failed: {e}")
            continue

    # All sources failed
    error_msg = (
        "All data sources failed. Please check:\n"
        "1. Network connectivity\n"
        "2. DEXSCREENER_API_KEY environment variable (get one at https://dexscreener.com/)\n"
        "3. API service status"
    )
    logger.error(error_msg)
    raise RuntimeError(error_msg)
