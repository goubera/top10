"""
Token collector for Solana - Solution RÉALISTE
Utilise Birdeye Free Tier (30k crédits/mois GRATUIT)
Inscription requise mais reste 100% gratuite
"""
import requests
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database import TokenSnapshot, DailyStats

# Configuration
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")
BIRDEYE_API = "https://public-api.birdeye.so"

# Fallback data si pas d'API key
FALLBACK_MODE = not BIRDEYE_API_KEY


def _http_get(url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, retries: int = 3) -> Dict:
    """HTTP GET avec retry logic"""
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers or {},
                timeout=30
            )
            if response.status_code == 429:  # Rate limit
                time.sleep(2 ** attempt)
                continue
            if response.status_code == 403:
                print(f"⚠️  403 Forbidden - API key required or invalid")
                return {}
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == retries - 1:
                print(f"⚠️  Error fetching {url}: {e}")
                return {}
            time.sleep(2 ** attempt)
    return {}


def fetch_birdeye_trending() -> List[Dict[str, Any]]:
    """
    Fetch trending tokens from Birdeye API
    Nécessite une clé API gratuite : https://birdeye.so
    """
    if not BIRDEYE_API_KEY:
        print("❌ BIRDEYE_API_KEY not set")
        print("💡 Get a FREE API key at: https://birdeye.so")
        return []

    try:
        headers = {
            "X-API-KEY": BIRDEYE_API_KEY,
            "Accept": "application/json"
        }

        # Endpoint pour tokens trending
        url = f"{BIRDEYE_API}/defi/trending_tokens"
        params = {
            "chain": "solana",
            "sort_by": "volume24hUSD",
            "sort_type": "desc",
            "offset": 0,
            "limit": 50
        }

        data = _http_get(url, params=params, headers=headers)

        if not data or "data" not in data:
            print("⚠️  No data from Birdeye API")
            return []

        tokens = data.get("data", {}).get("tokens", [])
        print(f"✅ Fetched {len(tokens)} tokens from Birdeye")
        return tokens

    except Exception as e:
        print(f"❌ Error fetching Birdeye data: {e}")
        return []


def normalize_birdeye_token(token: Dict) -> Optional[Dict[str, Any]]:
    """
    Normalise les données Birdeye au format commun
    """
    try:
        return {
            "token_address": token.get("address", ""),
            "token_name": token.get("name", "Unknown"),
            "token_symbol": token.get("symbol", "???"),
            "pair_address": token.get("liquidity", {}).get("pair", ""),
            "price_usd": float(token.get("price", 0) or 0),
            "market_cap": float(token.get("mc", 0) or 0),
            "liquidity_usd": float(token.get("liquidity", {}).get("usd", 0) or 0),
            "volume_24h": float(token.get("v24hUSD", 0) or 0),
            "price_change_24h": float(token.get("v24hChangePercent", 0) or 0),
            "txns_24h": int(token.get("trade24h", 0) or 0),
            "created_at": int(token.get("creation_time", 0) or 0) * 1000,
        }
    except Exception as e:
        print(f"⚠️  Error normalizing token: {e}")
        return None


def generate_fallback_data(top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Génère des données de fallback pour tests
    Utilisé si pas de clé API
    """
    import random

    print("\n" + "="*60)
    print("⚠️  FALLBACK MODE: Generating mock data")
    print("   No API key detected - using simulated data")
    print("   Get a FREE Birdeye API key at: https://birdeye.so")
    print("="*60 + "\n")

    tokens = []
    sample_names = [
        ("BONK", "Bonk"),
        ("WIF", "dogwifhat"),
        ("POPCAT", "Popcat"),
        ("MYRO", "Myro"),
        ("WEN", "Wen"),
        ("SILLY", "Silly Dragon"),
        ("MEW", "cat in a dogs world"),
        ("HARAMBE", "Harambe"),
        ("FARTCOIN", "Fartcoin"),
        ("PONKE", "Ponke")
    ]

    for i, (symbol, name) in enumerate(sample_names[:top_n]):
        tokens.append({
            "token_address": f"mock_address_{i}_{int(time.time())}",
            "token_name": name,
            "token_symbol": symbol,
            "pair_address": f"pair_{i}",
            "price_usd": random.uniform(0.0001, 5.0),
            "market_cap": random.uniform(1000000, 100000000),
            "liquidity_usd": random.uniform(500000, 5000000),
            "volume_24h": random.uniform(100000, 10000000),
            "price_change_24h": random.uniform(-50, 200),
            "txns_24h": random.randint(1000, 50000),
            "created_at": int((datetime.utcnow() - timedelta(days=random.randint(1, 30))).timestamp() * 1000),
        })

    return tokens


def is_new_token(created_timestamp: int, hours: int = 24) -> bool:
    """Check if token was created in the last N hours"""
    if not created_timestamp or created_timestamp == 0:
        return False
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        token_time = datetime.fromtimestamp(created_timestamp / 1000)
        return token_time > cutoff
    except:
        return False


def collect_top_tokens(db: Session, top_n: int = 10) -> Dict[str, Any]:
    """
    Collecte les top tokens depuis Birdeye (free tier)
    Fallback sur données mockées si pas de clé API
    """
    print("🚀 Starting token collection...")

    # Vérifier si API key disponible
    if FALLBACK_MODE:
        tokens = generate_fallback_data(top_n)
        data_source = "Mock data (no API key)"
    else:
        # Utiliser Birdeye
        birdeye_tokens = fetch_birdeye_trending()

        if not birdeye_tokens:
            print("⚠️  Birdeye API failed, using fallback data")
            tokens = generate_fallback_data(top_n)
            data_source = "Mock data (API fallback)"
        else:
            tokens = []
            for token in birdeye_tokens:
                normalized = normalize_birdeye_token(token)
                if normalized:
                    tokens.append(normalized)
            data_source = "Birdeye API (free tier)"

    if not tokens:
        return {"error": "No data available", "tokens_collected": 0}

    # Dédupliquer et trier
    by_token: Dict[str, Dict] = {}
    for token in tokens:
        addr = token["token_address"]
        if not addr:
            continue

        current_vol = token["volume_24h"]
        if addr not in by_token or current_vol > by_token[addr]["volume_24h"]:
            by_token[addr] = token

    # Trier par volume
    sorted_tokens = sorted(by_token.values(), key=lambda x: x["volume_24h"], reverse=True)
    top_gainers = sorted_tokens[:top_n]

    # Nouveaux tokens
    new_tokens = [
        t for t in sorted_tokens
        if is_new_token(t["created_at"], hours=24)
    ][:top_n]

    # Combiner
    all_tracked = {t["token_address"]: t for t in top_gainers + new_tokens}

    # Sauvegarder en base
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    tokens_saved = 0

    for addr, token in all_tracked.items():
        snapshot = TokenSnapshot(
            date=date_str,
            token_address=addr,
            token_name=token["token_name"],
            token_symbol=token["token_symbol"],
            pair_address=token.get("pair_address", ""),
            price_usd=float(token.get("price_usd", 0)),
            market_cap=float(token.get("market_cap", 0)) if token.get("market_cap") else None,
            liquidity_usd=float(token.get("liquidity_usd", 0)),
            volume_24h=float(token.get("volume_24h", 0)),
            price_change_24h=float(token.get("price_change_24h", 0)),
            txns_24h=int(token.get("txns_24h", 0)),
            created_at=token.get("created_at", 0),
            is_new_token=is_new_token(token.get("created_at", 0)),
            is_top_gainer=addr in [t["token_address"] for t in top_gainers]
        )

        db.add(snapshot)
        tokens_saved += 1

    # Stats quotidiennes
    stats = DailyStats(
        date=date_str,
        total_tokens_tracked=tokens_saved,
        total_volume_24h=sum(t["volume_24h"] for t in all_tracked.values()),
        avg_price_change=sum(t["price_change_24h"] for t in all_tracked.values()) / len(all_tracked) if all_tracked else 0,
        new_tokens_count=len(new_tokens)
    )
    db.add(stats)

    try:
        db.commit()
        print(f"✅ Saved {tokens_saved} tokens to database")
    except Exception as e:
        db.rollback()
        print(f"❌ Database error: {e}")
        return {"error": str(e), "tokens_collected": 0}

    return {
        "date": date_str,
        "tokens_collected": tokens_saved,
        "top_gainers_count": len(top_gainers),
        "new_tokens_count": len(new_tokens),
        "total_volume_24h": stats.total_volume_24h,
        "data_source": data_source
    }


if __name__ == "__main__":
    # Test collection
    from database import init_db, SessionLocal

    print("\n" + "="*60)
    print("🎯 Solana Token Collector")
    print("="*60)

    if BIRDEYE_API_KEY:
        print("✅ Birdeye API key detected")
    else:
        print("⚠️  No API key - will use mock data")
        print("💡 Get FREE key at: https://docs.birdeye.so/reference/get-your-api-key")

    print("="*60 + "\n")

    init_db()
    db = SessionLocal()

    result = collect_top_tokens(db, top_n=10)

    print("\n" + "="*60)
    print("📊 Collection Result:")
    print("="*60)
    for key, value in result.items():
        print(f"  {key}: {value}")
    print("="*60 + "\n")

    db.close()
