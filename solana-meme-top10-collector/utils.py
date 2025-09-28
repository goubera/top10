import time, requests, logging
from datetime import datetime, timezone

DEX_NEW_PAIRS_URLS = [
    "https://api.dexscreener.com/latest/dex/pairs/solana",
    "https://api.dexscreener.com/latest/dex/pairs?chainId=solana",
]
BIRDEYE_BASE = "https://public-api.birdeye.so"
DEFAULT_HEADERS = {"User-Agent": "top10-collector/1.0"}
logger = logging.getLogger(__name__)

def now_iso_date():
    return datetime.now(timezone.utc).astimezone().date().isoformat()

def ts_ms_to_iso(ts_ms: int) -> str:
    try:
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
    except Exception:
        return ""

def http_get(url, headers=None, params=None, timeout=15, retries=3):
    headers = {**DEFAULT_HEADERS, **(headers or {})}
    last_error = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
            if r.status_code == 429 or r.status_code >= 500:
                logger.warning("http_get retry=%s status=%s", attempt, r.status_code)
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_error = str(e)
            logger.warning("http_get error attempt=%s err=%s", attempt, e)
            time.sleep(2 ** attempt)
    return {"_error": last_error or "unknown"}

def safe_float(x):
    try: return float(x)
    except: return None

def safe_int(x):
    try: return int(x)
    except: return 0

def fetch_new_pairs_dexscreener(api_key: str | None, max_pairs: int = 500):
    """
    Utilise /latest/dex/search?q=SOL puis filtre chainId=solana.
    Normalise les champs attendus par le collector.
    """
    headers = {"X-API-KEY": (api_key or "").strip()} if api_key else {}
    data = http_get(
        "https://api.dexscreener.com/latest/dex/search",
        headers=headers,
        params={"q": "SOL"},
    )
    pairs = (data.get("pairs") or data.get("result") or [])
    pairs = [p for p in pairs if str(p.get("chainId") or p.get("chain") or "").lower() == "solana"]
    out = []
    for p in pairs[:max_pairs]:
        base = (p.get("baseToken") or {})
        txns_h24 = ((p.get("txns") or {}).get("h24") or {})
        out.append({
            "chain": p.get("chainId") or "solana",
            "pairAddress": p.get("pairAddress") or p.get("pairId") or "",
            "tokenAddress": base.get("address") or "",
            "baseSymbol": base.get("symbol") or "",
            "baseToken": base.get("name") or "",
            "priceUsd": safe_float(p.get("priceUsd")),
            "liquidityUsd": safe_float((p.get("liquidity") or {}).get("usd")),
            "volume24hUsd": safe_float((p.get("volume24hUsd") or (p.get("volume") or {}).get("h24"))),
            "txns24h": safe_int(txns_h24.get("buys")) + safe_int(txns_h24.get("sells")),
            "priceChange24h": safe_float((p.get("priceChange") or {}).get("h24")),
            "createdAt": p.get("pairCreatedAt") or p.get("createdAt"),
        })
    if not out:
        logger.warning("Dexscreener /latest/dex/search returned no Solana pairs")
    return out

def enrich_birdeye(token_address: str, birdeye_key: str | None):
    if not birdeye_key or not token_address:
        return {"holders": None, "exitLiquidity": None, "hasMintAuth": None, "hasFreezeAuth": None}
    headers = {"X-API-KEY": birdeye_key, "accept": "application/json"}
    holders = None
    try:
        resp = http_get(f"{BIRDEYE_BASE}/defi/token_holders", headers=headers, params={"address": token_address})
        holders = resp.get("data", {}).get("holders") if isinstance(resp, dict) else None
    except: pass
    sec = {}
    try:
        sec = http_get(f"{BIRDEYE_BASE}/defi/token_security", headers=headers, params={"address": token_address})
    except: sec = {}
    return {
        "holders": holders,
        "exitLiquidity": (sec.get("data") or {}).get("exit_liquidity") if isinstance(sec, dict) else None,
        "hasMintAuth": (sec.get("data") or {}).get("mint_authority_exists") if isinstance(sec, dict) else None,
        "hasFreezeAuth": (sec.get("data") or {}).get("freeze_authority_exists") if isinstance(sec, dict) else None,
    }
