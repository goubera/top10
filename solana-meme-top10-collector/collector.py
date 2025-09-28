from __future__ import annotations

import csv
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

from dexscreener_client import search_pairs_solana, token_pairs
from utils import now_iso_date, ts_ms_to_iso

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CSV_HEADERS = [
    "date",
    "chain",
    "baseToken",
    "baseSymbol",
    "pairAddress",
    "tokenAddress",
    "priceUsd",
    "liquidityUsd",
    "volume24hUsd",
    "txns24h",
    "priceChange24h",
    "createdAt",
    "earlyReturnMultiple",
    "holders",
    "exitLiquidity",
    "hasMintAuth",
    "hasFreezeAuth",
    "notes",
]


def _deprecated_fetch_new_pairs_dexscreener(*_args, **_kwargs):
    raise RuntimeError("fetch_new_pairs_dexscreener has been superseded by search_pairs_solana")


def _deprecated_enrich_birdeye(*_args, **_kwargs):
    raise RuntimeError("Birdeye enrichment has been removed from the collector")


fetch_new_pairs_dexscreener = _deprecated_fetch_new_pairs_dexscreener
enrich_birdeye = _deprecated_enrich_birdeye


def rank_top10(df, min_liq_usd: float = 5000.0):
    """Legacy ranking helper retained for backward compatibility."""

    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:  # pragma: no cover - defensive fallback
        raise RuntimeError("pandas is required for rank_top10") from exc

    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    filtered = df[df["liquidityUsd"].fillna(0) >= min_liq_usd]
    if filtered.empty:
        return df.head(10)
    return filtered.sort_values(
        by=["priceChange24h", "volume24hUsd"], ascending=[False, False]
    ).head(10)


def collect_top10_solana(
    *,
    api_key: str | None,
    limit: int,
    min_liquidity_usd: float,
    date_str: str,
) -> Tuple[List[Dict[str, object]], int]:
    """Return the rows for the CSV and the raw pair count."""

    parsed_pairs: List[Dict[str, Any]]

    if fetch_new_pairs_dexscreener is not _deprecated_fetch_new_pairs_dexscreener:
        legacy_pairs = fetch_new_pairs_dexscreener(api_key, max_pairs=limit)
        parsed_pairs = [
            {
                "chainId": lp.get("chain") or "solana",
                "pairAddress": lp.get("pairAddress") or "",
                "baseToken": {
                    "address": lp.get("tokenAddress") or "",
                    "name": lp.get("baseToken") or "",
                    "symbol": lp.get("baseSymbol") or "",
                },
                "priceUsd": lp.get("priceUsd"),
                "liquidityUsd": lp.get("liquidityUsd"),
                "volume24hUsd": lp.get("volume24hUsd"),
                "txns24h": lp.get("txns24h"),
                "priceChange24h": lp.get("priceChange24h"),
                "pairCreatedAt": lp.get("createdAt"),
            }
            for lp in legacy_pairs
        ]
        raw_count = len(legacy_pairs)
    else:
        raw_pairs = search_pairs_solana(api_key=api_key, limit=limit)
        parsed_pairs = token_pairs(raw_pairs)
        raw_count = len(raw_pairs)

    best_by_address: Dict[str, Dict[str, object]] = {}

    for pair in parsed_pairs:
        chain_id = (pair.get("chainId") or "").lower()
        if chain_id and chain_id != "solana":
            continue

        base = pair.get("baseToken") or {}
        base_address = base.get("address") or ""
        if not base_address:
            continue

        liquidity = pair.get("liquidityUsd") or 0.0
        if liquidity is not None and liquidity < min_liquidity_usd:
            continue

        volume = pair.get("volume24hUsd") or 0.0
        previous = best_by_address.get(base_address)
        previous_volume = previous.get("volume24hUsd") if previous else None

        if previous is None or (previous_volume or 0.0) < (volume or 0.0):
            best_by_address[base_address] = pair

    sorted_pairs = sorted(
        best_by_address.values(), key=lambda p: p.get("volume24hUsd") or 0.0, reverse=True
    )

    rows: List[Dict[str, object]] = []
    for pair in sorted_pairs[:10]:
        base = pair.get("baseToken") or {}
        rows.append(
            {
                "date": date_str,
                "chain": pair.get("chainId") or "solana",
                "baseToken": base.get("name") or "",
                "baseSymbol": base.get("symbol") or "",
                "pairAddress": pair.get("pairAddress") or "",
                "tokenAddress": base.get("address") or "",
                "priceUsd": pair.get("priceUsd"),
                "liquidityUsd": pair.get("liquidityUsd"),
                "volume24hUsd": pair.get("volume24hUsd"),
                "txns24h": pair.get("txns24h"),
                "priceChange24h": pair.get("priceChange24h"),
                "createdAt": ts_ms_to_iso(pair.get("pairCreatedAt")),
                "earlyReturnMultiple": None,
                "holders": None,
                "exitLiquidity": None,
                "hasMintAuth": None,
                "hasFreezeAuth": None,
                "notes": "",
            }
        )

    return rows, raw_count

def main() -> int:
    start = time.time()
    load_dotenv()
    date_str = now_iso_date()
    out_path = os.path.join("data", f"top10_{date_str}.csv")
    os.makedirs("data", exist_ok=True)

    dex_key = os.getenv("DEXSCREENER_API_KEY") or None
    max_pairs = int(os.getenv("MAX_NEW_PAIRS", "500"))
    min_liq = float(os.getenv("MIN_LIQUIDITY_USD", "5000"))
    early_window = int(os.getenv("EARLY_WINDOW_MIN", "0"))

    logger.info(
        "start date=%s MAX_NEW_PAIRS=%s MIN_LIQUIDITY_USD=%s EARLY_WINDOW_MIN=%s",
        date_str,
        max_pairs,
        min_liq,
        early_window,
    )

    rows, raw_count = collect_top10_solana(
        api_key=dex_key,
        limit=max_pairs,
        min_liquidity_usd=min_liq,
        date_str=date_str,
    )

    logger.info("pairs fetched=%d", raw_count)
    logger.info("pairs filtered=%d", len(rows))

    with open(out_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    duration = time.time() - start
    logger.info("csv path=%s size=%d", out_path, size)
    logger.info("duration=%.3fs", duration)

    summary = {
        "date": date_str,
        "raw_pairs": raw_count,
        "filtered_pairs": len(rows),
        "csv_path": out_path,
        "size": size,
        "top3": rows[:3],
    }
    with open(os.path.join("data", "run_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f)

    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())

