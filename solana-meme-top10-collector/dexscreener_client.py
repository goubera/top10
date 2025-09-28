 """
Dexscreener client — version fusionnée

- search_pairs_solana(query="SOL", limit=300): utilise /latest/dex/search
  filtré sur Solana, puis retombe sur 2 endpoints pairs « solana » si besoin.
- token_pairs(pairs_iterable): NORMALISE une liste de paires (compat avec l’ancienne signature)
- token_pairs_api(chain_id, token_address): appelle /token-pairs/v1/{chainId}/{tokenAddress}
  (équivalent fonctionnel du "token_pairs(token_address)" de l’autre version, mais avec un nom distinct)
- pair_detail(chain_id, pair_id): /latest/dex/pairs/{chainId}/{pairId}

Points clés:
- Header optionnel X-API-Key via env DEXSCREENER_API_KEY (ou param).
- Retry/backoff sur 429/5xx.
- Pas de dépendance nouvelle (requests uniquement).
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterable, List, Optional

import requests

BASE_URL = "https://api.dexscreener.com"
DEFAULT_HEADERS: Dict[str, str] = {
    "Accept": "application/json",
    "User-Agent": "solana-meme-top10-collector/1.0",
}
API_KEY_ENV = "DEXSCREENER_API_KEY"

# Fallback endpoints si /latest/dex/search renvoie peu/aucun résultat
DEX_SCREENER_SOLANA_URLS = (
    "/latest/dex/pairs/solana",
    "/latest/dex/pairs?chainId=solana",
)


def _headers(api_key: Optional[str] = None) -> Dict[str, str]:
    h = dict(DEFAULT_HEADERS)
    key = (api_key or os.getenv(API_KEY_ENV, "")).strip()
    if key:
        h["X-API-Key"] = key  # header case-insensitive
    return h


def _get(path: str, params: Optional[Dict[str, Any]] = None, *, api_key: Optional[str] = None,
         timeout: int = 20) -> Dict[str, Any]:
    """GET avec retries exponentiels sur 429/5xx."""
    url = f"{BASE_URL}{path}"
    backoff = 0.5
    for attempt in range(1, 6):
        r = requests.get(url, params=params or {}, headers=_headers(api_key), timeout=timeout)
        if r.status_code in (429, 500, 502, 503, 504):
            if attempt == 5:
                r.raise_for_status()
            time.sleep(backoff)
            backoff *= 2
            continue
        r.raise_for_status()
        return r.json()
    # ne devrait pas arriver
    raise RuntimeError(f"GET {path} failed after retries")


# ---------------------- API de plus haut niveau -------------------------------

def search_pairs_solana(query: str = "SOL", limit: int = 300, *, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Récupère une grande liste de paires, filtre "solana", et applique un limit.
    Fallback: si /latest/dex/search est pauvre → on tente 2 endpoints pairs solana.
    """
    # 1) Essai via /latest/dex/search
    data = _get("/latest/dex/search", params={"q": query}, api_key=api_key)
    pairs = data.get("pairs") or data.get("result") or []
    sol = [p for p in pairs if str(p.get("chainId") or p.get("chain") or "").lower() == "solana"]

    # 2) Fallback si vide
    if not sol:
        for path in DEX_SCREENER_SOLANA_URLS:
            d = _get(path, api_key=api_key)
            cand = d.get("pairs") or d.get("result") or []
            if cand:
                sol = cand
                break

    if limit is not None and limit >= 0:
        sol = sol[:limit]
    return sol


def token_pairs(pairs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    NORMALISE des payloads de paires (compat avec l’ancienne signature).
    Retourne des dicts avec clés stables utilisées par le collector.
    """
    def _safe_float(v, default=0.0):
        try:
            return float(v)
        except Exception:
            return default

    def _safe_int(v, default=0):
        try:
            return int(v)
        except Exception:
            return default

    normalised: List[Dict[str, Any]] = []
    for pair in pairs or []:
        base = pair.get("baseToken") or {}
        txns = pair.get("txns") or {}
        txns_h24 = txns.get("h24") or {}
        liq = pair.get("liquidity") or {}
        vol = pair.get("volume") or {}
        chg = pair.get("priceChange") or {}

        normalised.append(
            {
                "chainId": pair.get("chainId") or pair.get("chain") or "solana",
                "pairAddress": pair.get("pairAddress") or pair.get("pairId") or "",
                "baseToken": {
                    "address": base.get("address") or "",
                    "name": base.get("name") or "",
                    "symbol": base.get("symbol") or "",
                },
                "priceUsd": _safe_float(pair.get("priceUsd"), 0.0),
                "liquidityUsd": _safe_float(liq.get("usd") if isinstance(liq, dict) else liq, 0.0),
                "volume24hUsd": _safe_float(vol.get("h24") if isinstance(vol, dict) else vol, 0.0),
                "txns24h": _safe_int(txns_h24.get("buys"), 0) + _safe_int(txns_h24.get("sells"), 0),
                "priceChange24h": _safe_float(chg.get("h24") if isinstance(chg, dict) else chg, 0.0),
                "pairCreatedAt": pair.get("pairCreatedAt") or pair.get("createdAt"),
            }
        )
    return normalised


def token_pairs_api(chain_id: str, token_address: str, *, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Appelle l’endpoint documenté : /token-pairs/v1/{chainId}/{tokenAddress}
    (garde un nom différent pour ne pas entrer en collision avec la fonction de normalisation ci-dessus).
    """
    return _get(f"/token-pairs/v1/{chain_id}/{token_address}", api_key=api_key)


def pair_detail(chain_id: str, pair_id: str, *, api_key: Optional[str] = None) -> Dict[str, Any]:
    """ /latest/dex/pairs/{chainId}/{pairId} """
    return _get(f"/latest/dex/pairs/{chain_id}/{pair_id}", api_key=api_key)
