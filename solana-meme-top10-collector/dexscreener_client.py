"""Helper functions for querying Dexscreener and normalising payloads."""

from __future__ import annotations

from typing import Iterable, List, Dict, Any

from utils import http_get, safe_float, safe_int


DEX_SCREENER_SOLANA_URLS = (
    "https://api.dexscreener.com/latest/dex/pairs/solana",
    "https://api.dexscreener.com/latest/dex/pairs?chainId=solana",
)


def search_pairs_solana(api_key: str | None = None, limit: int | None = None) -> List[Dict[str, Any]]:
    """Return the raw pair payloads for Solana markets.

    The helper tries a couple of API endpoints that Dexscreener exposes for
    Solana pairs, mirroring the behaviour that previously lived in
    ``fetch_new_pairs_dexscreener``.  Any errors are reported through the
    ``_error`` sentinel contained in ``http_get``'s response.
    """

    headers = {"X-API-KEY": api_key} if api_key else {}
    pairs: List[Dict[str, Any]] = []

    for url in DEX_SCREENER_SOLANA_URLS:
        data = http_get(url, headers=headers)
        if isinstance(data, dict) and "_error" not in data:
            pairs = list(data.get("pairs") or [])
            if pairs:
                break
        else:
            # ``http_get`` already logged the error, simply try the next URL.
            continue

    if limit is not None and limit >= 0:
        return pairs[:limit]
    return pairs


def token_pairs(pairs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalise raw pair payloads into the structure used by the collector."""

    normalised: List[Dict[str, Any]] = []

    for pair in pairs or []:
        base = pair.get("baseToken") or {}
        txns = pair.get("txns") or {}
        txns_h24 = txns.get("h24") or {}

        normalised.append(
            {
                "chainId": pair.get("chainId") or "solana",
                "pairAddress": pair.get("pairAddress") or "",
                "baseToken": {
                    "address": base.get("address") or "",
                    "name": base.get("name") or "",
                    "symbol": base.get("symbol") or "",
                },
                "priceUsd": safe_float(pair.get("priceUsd")),
                "liquidityUsd": safe_float((pair.get("liquidity") or {}).get("usd")),
                "volume24hUsd": safe_float((pair.get("volume") or {}).get("h24")),
                "txns24h": safe_int(txns_h24.get("buys")) + safe_int(txns_h24.get("sells")),
                "priceChange24h": safe_float((pair.get("priceChange") or {}).get("h24")),
                "pairCreatedAt": pair.get("pairCreatedAt"),
            }
        )

    return normalised

