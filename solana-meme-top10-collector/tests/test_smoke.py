import csv
import logging
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import collector  # noqa: E402

EXPECTED_HEADERS = [
    "date","chain","baseToken","baseSymbol","pairAddress","tokenAddress",
    "priceUsd","liquidityUsd","volume24hUsd","txns24h","priceChange24h",
    "createdAt","earlyReturnMultiple","holders","exitLiquidity",
    "hasMintAuth","hasFreezeAuth","notes"
]


def fake_fetch_new_pairs_dexscreener(api_key, max_pairs=500):
    return [
        {
            "chain": "solana",
            "baseToken": "Token A",
            "baseSymbol": "TKA",
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


def test_collector_creates_csv(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(collector, "fetch_new_pairs_dexscreener", fake_fetch_new_pairs_dexscreener)
    monkeypatch.setattr(collector, "enrich_birdeye", fake_enrich_birdeye)
    monkeypatch.setattr(collector, "now_iso_date", fake_now_iso_date)
    monkeypatch.chdir(tmp_path)

    with caplog.at_level(logging.INFO):
        collector.main()

    out_file = tmp_path / "data" / "top10_2020-01-01.csv"
    assert out_file.exists()

    with out_file.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert reader.fieldnames == EXPECTED_HEADERS
        assert len(rows) >= 1

    # basic log keys
    text = " ".join(caplog.messages)
    assert "pairs fetched" in text
    assert "pairs filtered" in text
    assert "duration" in text
