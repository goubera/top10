"""
Collector Solana Top10 — version fusionnée
- Conserve la logique DexScreener Top10 (tri par volume24hUsd décroissant,
  unicité par token address).
- Respecte l'ordre EXACT des en-têtes CSV utilisé par la CI.
- Échoue proprement (exit 1) + écrit data/run_summary.json si aucune donnée.
- Fallbacks légers :
    * pandas : optionnel (si absent, on écrit le CSV sans pandas)
    * dotenv : optionnel (si présent, on charge .env)
"""

import csv
import datetime
import logging
import os
import time
from typing import Any, Dict, Iterable, List, Optional

# --- Fallbacks optionnels -----------------------------------------------------
try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None  # type: ignore

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# --- Config générique ---------------------------------------------------------
logger = logging.getLogger(__name__)
HEADERS = [
    "date", "chain", "baseToken", "baseSymbol", "pairAddress", "tokenAddress",
    "priceUsd", "liquidityUsd", "volume24hUsd", "txns24h", "priceChange24h",
    "createdAt", "earlyReturnMultiple", "holders", "exitLiquidity",
    "hasMintAuth", "hasFreezeAuth", "notes"
]
DEX_API = "https://api.dexscreener.com"
DEX_KEY = os.getenv("DEXSCREENER_API_KEY", "").strip()
BIRDEYE_KEY = os.getenv("BIRDEYE_API_KEY", "").strip()
DATE_STR = datetime.datetime.utcnow().strftime("%Y-%m-%d")

try:
    from utils import enrich_birdeye as _enrich_birdeye
    from utils import fetch_new_pairs_dexscreener as _fetch_new_pairs_dexscreener
    from utils import now_iso_date as _now_iso_date
except Exception:  # pragma: no cover
    _enrich_birdeye = None  # type: ignore
    _fetch_new_pairs_dexscreener = None  # type: ignore
    _now_iso_date = None  # type: ignore

def _num(x, default=""):
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default

# --- HTTP minimal (requests standard, sans dépendances supplémentaires) -------
def _http_get(path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 20) -> Dict[str, Any]:
    import requests  # lazy import
    url = f"{DEX_API}{path}"
    headers = {"Accept": "application/json"}
    if DEX_KEY:
        headers["X-API-Key"] = DEX_KEY

    backoffs = [0, 1, 2, 4, 8]
    last_err = None
    for b in backoffs:
        if b:
            time.sleep(b)
        try:
            r = requests.get(url, params=params or {}, headers=headers, timeout=timeout)
            # Retry doux sur 429/5xx
            if r.status_code in (429, 500, 502, 503, 504):
                last_err = (r.status_code, r.text[:200])
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:  # réseau, timeouts, etc.
            last_err = str(e)
            continue
    raise RuntimeError(f"GET {path} failed after retries: {last_err}")

# --- DexScreener helpers ------------------------------------------------------
def _search_pairs_solana(query: str = "SOL", limit: int = 300) -> List[Dict[str, Any]]:
    """ /latest/dex/search?q=... → filtre chain solana """
    data = _http_get("/latest/dex/search", params={"q": query})
    pairs = data.get("pairs") or data.get("result") or []
    sol = [p for p in pairs if str(p.get("chainId") or p.get("chain") or "").lower() == "solana"]
    return sol[:limit]

def _vol24_usd(p: Dict[str, Any]) -> float:
    # champs possibles selon endpoint: volume24hUsd ou volume.h24
    v = p.get("volume24hUsd")
    if v is None:
        v = (p.get("volume") or {}).get("h24")
    try:
        return float(v or 0.0)
    except Exception:
        return 0.0

# --- Collecte & normalisation -------------------------------------------------
def collect_rows() -> List[Dict[str, Any]]:
    # 1) Échantillon large
    pairs = _search_pairs_solana(query="SOL", limit=300)

    # 2) Meilleure paire par token base (max volume 24h)
    by_token: Dict[str, Dict[str, Any]] = {}
    for p in pairs:
        base = p.get("baseToken") or {}
        addr = base.get("address") or ""
        if not addr:
            continue
        cur = by_token.get(addr)
        if cur is None or _vol24_usd(p) > _vol24_usd(cur):
            by_token[addr] = p

    # 3) Tri décroissant & top10
    best = sorted(by_token.values(), key=_vol24_usd, reverse=True)[:10]

    # 4) Mapping → schéma CSV
    rows: List[Dict[str, Any]] = []
    for p in best:
        chain = (p.get("chainId") or p.get("chain") or "solana").lower()
        base = p.get("baseToken") or {}
        liq  = p.get("liquidity") or {}
        tx   = p.get("txns") or {}
        chg  = p.get("priceChange") or {}

        rows.append({
            "date": DATE_STR,
            "chain": chain,
            "baseToken": base.get("name") or base.get("symbol") or "",
            "baseSymbol": base.get("symbol") or "",
            "pairAddress": p.get("pairAddress") or p.get("pairId") or "",
            "tokenAddress": base.get("address") or "",
            "priceUsd": _num(p.get("priceUsd")),
            "liquidityUsd": _num(liq.get("usd") if isinstance(liq, dict) else liq),
            "volume24hUsd": _num(_vol24_usd(p)),
            "txns24h": int((tx.get("h24") if isinstance(tx, dict) else tx) or 0),
            "priceChange24h": _num(chg.get("h24") if isinstance(chg, dict) else chg),
            "createdAt": int(p.get("pairCreatedAt") or p.get("createdAt") or 0),
            "earlyReturnMultiple": "",
            "holders": "",
            "exitLiquidity": "",
            "hasMintAuth": "",
            "hasFreezeAuth": "",
            "notes": "",
        })
    return rows


def now_iso_date() -> str:
    if _now_iso_date is not None:
        return _now_iso_date()
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def fetch_new_pairs_dexscreener(api_key: Optional[str], max_pairs: int = 500) -> List[Dict[str, Any]]:
    if _fetch_new_pairs_dexscreener is not None:
        return _fetch_new_pairs_dexscreener(api_key, max_pairs=max_pairs)
    pairs = _search_pairs_solana(query="SOL", limit=max_pairs)
    return [
        {
            "chain": p.get("chainId") or p.get("chain") or "solana",
            "baseToken": (p.get("baseToken") or {}).get("name") or "",
            "baseSymbol": (p.get("baseToken") or {}).get("symbol") or "",
            "pairAddress": p.get("pairAddress") or p.get("pairId") or "",
            "tokenAddress": (p.get("baseToken") or {}).get("address") or "",
            "priceUsd": _num(p.get("priceUsd")),
            "liquidityUsd": _num((p.get("liquidity") or {}).get("usd")),
            "volume24hUsd": _num(_vol24_usd(p)),
            "txns24h": int(((p.get("txns") or {}).get("h24") or {}).get("buys") or 0)
            + int(((p.get("txns") or {}).get("h24") or {}).get("sells") or 0),
            "priceChange24h": _num((p.get("priceChange") or {}).get("h24")),
            "createdAt": p.get("pairCreatedAt") or p.get("createdAt"),
        }
        for p in pairs
    ]


def enrich_birdeye(token_address: str, birdeye_key: Optional[str]) -> Dict[str, Any]:
    if _enrich_birdeye is not None:
        return _enrich_birdeye(token_address, birdeye_key)
    return {"holders": None, "exitLiquidity": None, "hasMintAuth": None, "hasFreezeAuth": None}


def _rows_from_dataframe(df: Any) -> List[Dict[str, Any]]:
    if df is None:
        return []
    if isinstance(df, list):
        return [dict(row) for row in df]
    if hasattr(df, "to_dict"):
        return list(df.to_dict("records"))
    if hasattr(df, "_rows"):
        return [dict(row) for row in df._rows]  # type: ignore[attr-defined]
    try:
        return [dict(row) for row in df]
    except Exception:
        return []


def rank_top10(df: Any) -> Any:
    rows = _rows_from_dataframe(df)
    def _safe_num(value: Any) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0

    filtered = [row for row in rows if _safe_num(row.get("liquidityUsd")) >= 5000]
    filtered.sort(
        key=lambda row: (_safe_num(row.get("priceChange24h")), _safe_num(row.get("volume24hUsd"))),
        reverse=True,
    )
    top = filtered[:10]
    if pd is not None:
        return pd.DataFrame(top)
    return top


def _write_csv(rows: Iterable[Dict[str, Any]], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    start = time.time()
    date_str = now_iso_date()
    pairs = fetch_new_pairs_dexscreener(DEX_KEY, max_pairs=500)
    logger.info("pairs fetched=%s", len(pairs))

    df = pd.DataFrame(pairs) if pd is not None else list(pairs)
    ranked = rank_top10(df)
    ranked_rows = _rows_from_dataframe(ranked)
    logger.info("pairs filtered=%s", len(ranked_rows))

    out_rows: List[Dict[str, Any]] = []
    for row in ranked_rows:
        enrich = enrich_birdeye(row.get("tokenAddress"), BIRDEYE_KEY)
        out_rows.append(
            {
                "date": date_str,
                "chain": row.get("chain") or "solana",
                "baseToken": row.get("baseToken") or "",
                "baseSymbol": row.get("baseSymbol") or "",
                "pairAddress": row.get("pairAddress") or "",
                "tokenAddress": row.get("tokenAddress") or "",
                "priceUsd": row.get("priceUsd"),
                "liquidityUsd": row.get("liquidityUsd"),
                "volume24hUsd": row.get("volume24hUsd"),
                "txns24h": row.get("txns24h"),
                "priceChange24h": row.get("priceChange24h"),
                "createdAt": row.get("createdAt"),
                "earlyReturnMultiple": "",
                "holders": enrich.get("holders"),
                "exitLiquidity": enrich.get("exitLiquidity"),
                "hasMintAuth": enrich.get("hasMintAuth"),
                "hasFreezeAuth": enrich.get("hasFreezeAuth"),
                "notes": "",
            }
        )

    out = os.path.join("data", f"top10_{date_str}.csv")
    _write_csv(out_rows, out)
    duration = time.time() - start
    logger.info("duration=%.2fs", duration)

# --- Entrée principale --------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
