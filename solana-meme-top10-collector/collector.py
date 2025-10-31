"""
Collector Solana Top10 — version fusionnée avec multi-source fallback
- Utilise le module data_sources.py avec fallback automatique
- Conserve la logique DexScreener Top10 (tri par volume24hUsd décroissant,
  unicité par token address).
- Respecte l'ordre EXACT des en-têtes CSV utilisé par la CI.
- Échoue proprement (exit 1) + écrit data/run_summary.json si aucune donnée.
- Fallbacks légers :
    * pandas : optionnel (si absent, on écrit le CSV sans pandas)
    * dotenv : optionnel (si présent, on charge .env)
"""

import os
import csv
import json
import datetime
import logging
from typing import Any, Dict, List

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

# Import multi-source data fetcher
from data_sources import fetch_top_solana_pairs

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Config générique ---------------------------------------------------------
DATE_STR = datetime.datetime.utcnow().strftime("%Y-%m-%d")
HEADERS = [
    "date", "chain", "baseToken", "baseSymbol", "pairAddress", "tokenAddress",
    "priceUsd", "liquidityUsd", "volume24hUsd", "txns24h", "priceChange24h",
    "createdAt", "earlyReturnMultiple", "holders", "exitLiquidity",
    "hasMintAuth", "hasFreezeAuth", "notes"
]

def _num(x, default=""):
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default

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
    """
    Collect top 10 Solana pairs using multi-source fallback strategy.

    Returns:
        List of row dictionaries ready for CSV export

    Raises:
        RuntimeError: If all data sources fail
    """
    # 1) Fetch from data sources with automatic fallback
    logger.info(f"Starting data collection for {DATE_STR}")
    pairs = fetch_top_solana_pairs(limit=300)

    if not pairs:
        raise RuntimeError("No pairs returned from any data source")

    logger.info(f"Received {len(pairs)} pairs from data source")

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

    logger.info(f"Found {len(by_token)} unique tokens")

    # 3) Tri décroissant & top10
    best = sorted(by_token.values(), key=_vol24_usd, reverse=True)[:10]
    logger.info(f"Selected top {len(best)} pairs by volume")

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

# --- Entrée principale --------------------------------------------------------
if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    summary_file = os.path.join("data", "run_summary.json")

    try:
        rows = collect_rows()

        # Si aucune donnée → on échoue proprement + résumé pour la CI
        if not rows:
            logger.error("No rows collected!")
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump({
                    "date": DATE_STR,
                    "success": False,
                    "raw_pairs": 0,
                    "reason": "no_pairs_after_filtering",
                    "message": "Data sources returned data but filtering resulted in 0 pairs"
                }, f, indent=2)
            raise SystemExit(1)

        # Écriture CSV (pandas si dispo, sinon csv standard)
        out = os.path.join("data", f"top10_{DATE_STR}.csv")

        if pd is not None:
            df = pd.DataFrame(rows)
            # Assure tri & unicité
            df = df.sort_values("volume24hUsd", ascending=False)
            df = df.drop_duplicates(subset=["tokenAddress"], keep="first")
            df = df[HEADERS]
            df.to_csv(out, index=False)
        else:
            with open(out, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=HEADERS)
                w.writeheader()
                for r in rows:
                    w.writerow(r)

        # Write success summary
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump({
                "date": DATE_STR,
                "success": True,
                "rows_collected": len(rows),
                "csv_file": out
            }, f, indent=2)

        logger.info(f"✓ Successfully wrote {out} with {len(rows)} rows")
        print(f"Wrote {out} with {len(rows)} rows")

    except Exception as e:
        # Log error and write failure summary
        logger.error(f"Collection failed: {e}", exc_info=True)

        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump({
                "date": DATE_STR,
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": (
                    "Data collection failed. This usually means:\n"
                    "1. DexScreener API requires an API key (set DEXSCREENER_API_KEY)\n"
                    "2. All fallback APIs are unavailable\n"
                    "3. Network connectivity issues\n\n"
                    "To fix: Get a free API key from https://dexscreener.com/ and add it to GitHub Secrets"
                )
            }, f, indent=2)

        # Exit with error code
        raise SystemExit(1)
