import os
import pathlib
import sys
import datetime

# ensure collector module is importable
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import data_sources


def test_data_sources_fallback(monkeypatch):
    """Test that data sources module can be imported and has fallback mechanism."""
    # Ensure environment variables are unset
    monkeypatch.delenv("DEXSCREENER_API_KEY", raising=False)
    assert "DEXSCREENER_API_KEY" not in os.environ

    # Mock the actual HTTP calls to return fake data
    def fake_dexscreener_fetch(self, limit=10):
        return [
            {
                "chainId": "solana",
                "baseToken": {"address": "token1", "name": "Token One", "symbol": "TOK1"},
                "pairAddress": "pair1",
                "priceUsd": 1.0,
                "liquidityUsd": 10000,
                "volume24hUsd": 2000,
                "txns24h": 5,
                "priceChange24h": 0.1,
                "pairCreatedAt": 0,
            }
        ]

    # Patch DexScreenerSource to return fake data
    monkeypatch.setattr(data_sources.DexScreenerSource, "fetch_top_pairs", fake_dexscreener_fetch)

    # Test that we can fetch data
    result = data_sources.fetch_top_solana_pairs(limit=10)
    assert len(result) == 1
    assert result[0]["baseToken"]["symbol"] == "TOK1"


def test_collector_integration(monkeypatch, tmp_path):
    """Test the full collector pipeline with mocked data sources."""
    import collector

    # Mock data source to return fake pairs
    def fake_fetch_pairs(limit=10):
        return [
            {
                "chainId": "solana",
                "baseToken": {"address": f"token{i}", "name": f"Token {i}", "symbol": f"TOK{i}"},
                "pairAddress": f"pair{i}",
                "priceUsd": float(i),
                "liquidityUsd": 10000 + i * 1000,
                "volume24hUsd": 5000 - i * 100,  # Descending order
                "txns24h": 100 + i,
                "priceChange24h": 0.1 * i,
                "pairCreatedAt": 1000000 + i,
            }
            for i in range(1, 11)
        ]

    # Patch the function in the collector module where it's used
    monkeypatch.setattr(collector, "fetch_top_solana_pairs", fake_fetch_pairs)

    # Run in temporary directory
    monkeypatch.chdir(tmp_path)

    # Call collect_rows
    rows = collector.collect_rows()

    # Verify we got data back
    assert len(rows) == 10

    # All rows should have today's date (DATE_STR is set at module import time)
    expected_date = collector.DATE_STR
    assert all(row["date"] == expected_date for row in rows)
    assert all(row["chain"] == "solana" for row in rows)

    # Verify sorting by volume (descending)
    volumes = [row["volume24hUsd"] for row in rows]
    assert volumes == sorted(volumes, reverse=True)

    # Verify all required fields are present
    for row in rows:
        assert "baseToken" in row
        assert "baseSymbol" in row
        assert "pairAddress" in row
        assert "tokenAddress" in row
        assert "priceUsd" in row
        assert "liquidityUsd" in row
        assert "volume24hUsd" in row
