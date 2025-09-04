import os
import pathlib
import sys

# ensure collector module is importable
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import collector


def test_main_runs_without_env(monkeypatch, tmp_path):
    # Ensure environment variables are unset
    monkeypatch.delenv("BIRDEYE_API_KEY", raising=False)
    monkeypatch.delenv("HELIUS_API_KEY", raising=False)
    assert "BIRDEYE_API_KEY" not in os.environ
    assert "HELIUS_API_KEY" not in os.environ

    # Patch network calls
    def fake_fetch_new_pairs_dexscreener(api_key, max_pairs=500):
        return [
            {
                "chain": "solana",
                "baseToken": "tok",
                "baseSymbol": "TOK",
                "pairAddress": "pair1",
                "tokenAddress": "token1",
                "priceUsd": 1.0,
                "liquidityUsd": 10000,
                "volume24hUsd": 2000,
                "txns24h": 5,
                "priceChange24h": 0.1,
                "createdAt": 0,
            }
        ]

    def fake_enrich_birdeye(token_address, birdeye_key):
        return {
            "holders": 1,
            "exitLiquidity": 100,
            "hasMintAuth": False,
            "hasFreezeAuth": False,
        }

    def fake_now_iso_date():
        return "2020-01-01"

    monkeypatch.setattr(collector, "fetch_new_pairs_dexscreener", fake_fetch_new_pairs_dexscreener)
    monkeypatch.setattr(collector, "enrich_birdeye", fake_enrich_birdeye)
    monkeypatch.setattr(collector, "now_iso_date", fake_now_iso_date)

    # run in temporary directory to avoid writing to repo
    monkeypatch.chdir(tmp_path)

    collector.main()  # should not raise

    # Ensure output file created
    out_file = tmp_path / "data" / "top10_2020-01-01.csv"
    assert out_file.exists()
