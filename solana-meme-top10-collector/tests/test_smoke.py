import pathlib, sys
import pandas as pd

# ensure collector module path
COLLECTOR_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(COLLECTOR_DIR))
import collector


def test_rank_top10_smoke():
    empty_df = pd.DataFrame(columns=["liquidityUsd", "priceChange24h", "volume24hUsd"])
    result_empty = collector.rank_top10(empty_df)
    assert result_empty.empty

    df = pd.DataFrame({
        "liquidityUsd": [6000] * 12,
        "priceChange24h": list(range(12)),
        "volume24hUsd": list(range(12))
    })
    res = collector.rank_top10(df)
    assert len(res) <= 10
