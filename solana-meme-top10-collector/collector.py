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

import os
import csv
import json
import time
import datetime
from typing import Any, Dict, List, Optional

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
DATE_STR = datetime.datetime.utcnow().strftime("%Y-%m-%d")
HEADERS = [
    "date", "chain", "baseToken", "baseSymbol", "pairAddress", "tokenAddress",
    "priceUsd", "liquidityUsd", "volume24hUsd", "txns24h", "priceChange24h",
    "createdAt", "earlyReturnMultiple", "holders", "exitLiquidity",
    "hasMintAuth", "hasFreezeAuth", "notes"
]
DEX_API = "https://api.dexscreener.com"
DEX_KEY = os.getenv("DEXSCREENER_API_KEY", "").strip()

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

# --- Entrée principale --------------------------------------------------------
if __name__ == "__main__":
    rows = collect_rows()

    # Si aucune donnée → on échoue proprement + résumé pour la CI
    if not rows:
        os.makedirs("data", exist_ok=True)
        with open(os.path.join("data", "run_summary.json"), "w", encoding="utf-8") as f:
            json.dump({"date": DATE_STR, "raw_pairs": 0, "reason": "dexscreener_pairs_empty"}, f)
        raise SystemExit(1)

    # Écriture CSV (pandas si dispo, sinon csv standard)
    os.makedirs("data", exist_ok=True)
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

    print(f"Wrote {out} with {len(rows)} rows")
