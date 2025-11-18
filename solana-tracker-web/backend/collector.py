"""
Token collector for Solana - fetches top gainers and new tokens
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database import TokenSnapshot, DailyStats

DEXSCREENER_API = "https://api.dexscreener.com"
BIRDEYE_API = "https://public-api.birdeye.so"


def _http_get(url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, retries: int = 3) -> Dict:
    """HTTP GET with retry logic"""
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=headers or {}, timeout=30)
            if response.status_code == 429:  # Rate limit
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return {}


def fetch_solana_pairs(limit: int = 500) -> List[Dict[str, Any]]:
    """
    Fetch Solana pairs from DexScreener
    Returns pairs sorted by volume
    """
    try:
        # Try search endpoint first
        data = _http_get(f"{DEXSCREENER_API}/latest/dex/search", params={"q": "SOL"})
        pairs = data.get("pairs", [])

        # Filter Solana chain
        solana_pairs = [p for p in pairs if str(p.get("chainId", "")).lower() == "solana"]

        if not solana_pairs:
            # Fallback to direct Solana endpoint
            data = _http_get(f"{DEXSCREENER_API}/latest/dex/pairs/solana")
            solana_pairs = data.get("pairs", [])

        return solana_pairs[:limit]
    except Exception as e:
        print(f"Error fetching DexScreener data: {e}")
        return []


def get_volume_24h(pair: Dict) -> float:
    """Extract 24h volume from pair data"""
    try:
        vol = pair.get("volume", {})
        if isinstance(vol, dict):
            return float(vol.get("h24", 0))
        return float(pair.get("volume24hUsd", 0) or 0)
    except:
        return 0.0


def is_new_token(created_timestamp: int, hours: int = 24) -> bool:
    """Check if token was created in the last N hours"""
    if not created_timestamp:
        return False
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    token_time = datetime.fromtimestamp(created_timestamp / 1000)  # ms to seconds
    return token_time > cutoff


def collect_top_tokens(db: Session, top_n: int = 10) -> Dict[str, Any]:
    """
    Collect top gaining tokens and new tokens
    Returns summary statistics
    """
    print("🚀 Starting token collection...")

    # Fetch all pairs
    pairs = fetch_solana_pairs(limit=500)
    if not pairs:
        return {"error": "No pairs fetched", "tokens_collected": 0}

    print(f"📊 Fetched {len(pairs)} pairs from DexScreener")

    # Deduplicate by token address (keep highest volume pair per token)
    by_token: Dict[str, Dict] = {}
    for pair in pairs:
        base = pair.get("baseToken", {})
        addr = base.get("address", "")
        if not addr:
            continue

        current_vol = get_volume_24h(pair)
        if addr not in by_token or current_vol > get_volume_24h(by_token[addr]):
            by_token[addr] = pair

    # Sort by volume (top gainers)
    sorted_tokens = sorted(by_token.values(), key=get_volume_24h, reverse=True)

    # Get top N
    top_gainers = sorted_tokens[:top_n]

    # Filter new tokens (created in last 24h)
    new_tokens = [
        p for p in sorted_tokens
        if is_new_token(p.get("pairCreatedAt", 0), hours=24)
    ][:top_n]

    # Combine (may have overlap)
    all_tracked = {p.get("baseToken", {}).get("address"): p for p in top_gainers + new_tokens}

    # Save to database
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    tokens_saved = 0

    for addr, pair in all_tracked.items():
        base = pair.get("baseToken", {})
        liquidity = pair.get("liquidity", {})
        price_change = pair.get("priceChange", {})
        txns = pair.get("txns", {}).get("h24", {})

        snapshot = TokenSnapshot(
            date=date_str,
            token_address=addr,
            token_name=base.get("name", ""),
            token_symbol=base.get("symbol", ""),
            pair_address=pair.get("pairAddress", ""),
            price_usd=float(pair.get("priceUsd", 0) or 0),
            market_cap=float(pair.get("marketCap", 0) or 0) if pair.get("marketCap") else None,
            liquidity_usd=float(liquidity.get("usd", 0) if isinstance(liquidity, dict) else liquidity or 0),
            volume_24h=get_volume_24h(pair),
            price_change_24h=float(price_change.get("h24", 0) if isinstance(price_change, dict) else 0),
            txns_24h=int((txns.get("buys", 0) or 0) + (txns.get("sells", 0) or 0)) if isinstance(txns, dict) else 0,
            created_at=pair.get("pairCreatedAt", 0),
            is_new_token=is_new_token(pair.get("pairCreatedAt", 0)),
            is_top_gainer=addr in [p.get("baseToken", {}).get("address") for p in top_gainers]
        )

        db.add(snapshot)
        tokens_saved += 1

    # Save daily stats
    stats = DailyStats(
        date=date_str,
        total_tokens_tracked=tokens_saved,
        total_volume_24h=sum(get_volume_24h(p) for p in all_tracked.values()),
        avg_price_change=sum(
            float(p.get("priceChange", {}).get("h24", 0) or 0)
            for p in all_tracked.values()
        ) / len(all_tracked) if all_tracked else 0,
        new_tokens_count=len(new_tokens)
    )
    db.add(stats)

    try:
        db.commit()
        print(f"✅ Saved {tokens_saved} tokens to database")
    except Exception as e:
        db.rollback()
        print(f"❌ Error saving to database: {e}")
        return {"error": str(e), "tokens_collected": 0}

    return {
        "date": date_str,
        "tokens_collected": tokens_saved,
        "top_gainers_count": len(top_gainers),
        "new_tokens_count": len(new_tokens),
        "total_volume_24h": stats.total_volume_24h
    }


if __name__ == "__main__":
    # Test collection
    from database import init_db, SessionLocal
    init_db()
    db = SessionLocal()
    result = collect_top_tokens(db, top_n=10)
    print(f"Collection result: {result}")
    db.close()
