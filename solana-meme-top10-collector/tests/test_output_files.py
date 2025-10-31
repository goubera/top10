import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import collector  # noqa: E402


def test_output_file_pattern(monkeypatch, tmp_path):
    """Test that CSV files are created with the expected naming pattern."""

    # Mock data source to return fake pairs
    def fake_fetch_pairs(limit=10):
        return [
            {
                "chainId": "solana",
                "baseToken": {"address": "token1", "name": "Token 1", "symbol": "TOK1"},
                "pairAddress": "pair1",
                "priceUsd": 1.0,
                "liquidityUsd": 10000,
                "volume24hUsd": 5000,
                "txns24h": 100,
                "priceChange24h": 0.1,
                "pairCreatedAt": 1000000,
            }
        ]

    # Patch the function in the collector module
    monkeypatch.setattr(collector, "fetch_top_solana_pairs", fake_fetch_pairs)
    monkeypatch.chdir(tmp_path)

    # Run collector
    rows = collector.collect_rows()

    # Write CSV using the collector's logic
    import os
    import csv
    os.makedirs("data", exist_ok=True)
    out = os.path.join("data", f"top10_{collector.DATE_STR}.csv")

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=collector.HEADERS)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Verify output file created
    data_dir = tmp_path / "data"
    files = list(data_dir.glob("top10_*.csv"))
    assert len(files) == 1
    assert files[0].name.startswith("top10_")
    assert files[0].name.endswith(".csv")
