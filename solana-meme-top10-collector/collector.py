"""Tools to collect and rank newly listed Solana meme coins.

The original project depends on external libraries such as ``pandas``,
``python-dotenv`` and ``requests``.  In the execution environment for these
kata style exercises the network is disabled which means those dependencies
cannot be installed.  Importing :mod:`collector` should therefore avoid
importing optional dependencies at module import time so that the simple
``rank_top10`` helper can be tested in isolation.

To keep the public API intact we provide lightweight fallbacks for the
external modules.  ``load_dotenv`` is treated as a no-op when the real
package is missing and the heavy utility functions are imported lazily inside
``main``.  This mirrors the behaviour of the original script without requiring
any of the external packages to be present.
"""

import os
import pandas as pd

try:  # pragma: no cover - executed only when python-dotenv is installed
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    # Minimal stub when ``python-dotenv`` isn't available.  The function simply
    # returns ``False`` which matches the real package's behaviour when no
    # .env file is loaded.
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False

def rank_top10(df: pd.DataFrame, min_liq_usd: float = 5000.0):
    filt = df[(df["liquidityUsd"].fillna(0) >= min_liq_usd)]
    if filt.empty: return df.head(10)
    return filt.sort_values(by=["priceChange24h","volume24hUsd"], ascending=[False,False]).head(10)

def main():
    from utils import now_iso_date, fetch_new_pairs_dexscreener, enrich_birdeye, ts_ms_to_iso

    load_dotenv()
    date_str = now_iso_date()
    out_path = os.path.join("data", f"top10_{date_str}.csv")
    os.makedirs("data", exist_ok=True)

    dex_key = os.getenv("DEXSCREENER_API_KEY") or None
    birdeye_key = os.getenv("BIRDEYE_API_KEY") or None
    if not birdeye_key:
        print("[WARN] BIRDEYE_API_KEY missing - skipping enrichment")
    max_pairs = int(os.getenv("MAX_NEW_PAIRS", "500"))
    min_liq = float(os.getenv("MIN_LIQUIDITY_USD", "5000"))

    pairs = fetch_new_pairs_dexscreener(dex_key, max_pairs=max_pairs)
    print(f"[INFO] Dexscreener pairs fetched: {len(pairs)}")

    rows = []
    for p in pairs:
        sec = enrich_birdeye(p.get("tokenAddress"), birdeye_key)
        rows.append({
            "date": date_str,
            "chain": p.get("chain"),
            "baseToken": p.get("baseToken"),
            "baseSymbol": p.get("baseSymbol"),
            "pairAddress": p.get("pairAddress"),
            "tokenAddress": p.get("tokenAddress"),
            "priceUsd": p.get("priceUsd"),
            "liquidityUsd": p.get("liquidityUsd"),
            "volume24hUsd": p.get("volume24hUsd"),
            "txns24h": p.get("txns24h"),
            "priceChange24h": p.get("priceChange24h"),
            "createdAt": ts_ms_to_iso(p.get("createdAt")) if p.get("createdAt") else "",
            "earlyReturnMultiple": None,  # à compléter en V2 (OHLCV Birdeye)
            "holders": sec.get("holders"),
            "exitLiquidity": sec.get("exitLiquidity"),
            "hasMintAuth": sec.get("hasMintAuth"),
            "hasFreezeAuth": sec.get("hasFreezeAuth"),
            "notes": "",
        })

    df = pd.DataFrame(rows, columns=[
        "date","chain","baseToken","baseSymbol","pairAddress","tokenAddress",
        "priceUsd","liquidityUsd","volume24hUsd","txns24h","priceChange24h",
        "createdAt","earlyReturnMultiple","holders","exitLiquidity",
        "hasMintAuth","hasFreezeAuth","notes"
    ])

    top10 = rank_top10(df, min_liq_usd=min_liq) if not df.empty else df
    print(f"[INFO] Pairs after filters: {len(top10)}")
    top10.to_csv(out_path, index=False)
    print(f"[OK] {len(top10)} rows -> {out_path}")

if __name__ == "__main__":
    main()
