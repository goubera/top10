import os, time, json, logging
import pandas as pd
from dotenv import load_dotenv
from utils import now_iso_date, fetch_new_pairs_dexscreener, enrich_birdeye, ts_ms_to_iso

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def rank_top10(df: pd.DataFrame, min_liq_usd: float = 5000.0):
    filt = df[(df["liquidityUsd"].fillna(0) >= min_liq_usd)]
    if filt.empty: return df.head(10)
    return filt.sort_values(by=["priceChange24h","volume24hUsd"], ascending=[False,False]).head(10)

def main():
    start = time.time()
    load_dotenv()
    date_str = now_iso_date()
    out_path = os.path.join("data", f"top10_{date_str}.csv")
    os.makedirs("data", exist_ok=True)

    dex_key = os.getenv("DEXSCREENER_API_KEY") or None
    birdeye_key = os.getenv("BIRDEYE_API_KEY") or None
    max_pairs = int(os.getenv("MAX_NEW_PAIRS", "500"))
    min_liq = float(os.getenv("MIN_LIQUIDITY_USD", "5000"))
    early_window = int(os.getenv("EARLY_WINDOW_MIN", "0"))

    if not birdeye_key:
        logger.warning("BIRDEYE_API_KEY missing - skipping enrichment")

    logger.info(
        "start date=%s MAX_NEW_PAIRS=%s MIN_LIQUIDITY_USD=%s EARLY_WINDOW_MIN=%s",
        date_str,
        max_pairs,
        min_liq,
        early_window,
    )

    pairs = fetch_new_pairs_dexscreener(dex_key, max_pairs=max_pairs)
    logger.info("pairs fetched=%d", len(pairs))

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
    logger.info("pairs filtered=%d", len(top10))
    top10.to_csv(out_path, index=False)

    size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    duration = time.time() - start
    logger.info("csv path=%s size=%d", out_path, size)
    logger.info("duration=%.3fs", duration)

    summary = {
        "date": date_str,
        "raw_pairs": len(pairs),
        "filtered_pairs": len(top10),
        "csv_path": out_path,
        "size": size,
        "top3": top10.head(3).to_dict(orient="records"),
    }
    with open(os.path.join("data", "run_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f)

if __name__ == "__main__":
    main()
