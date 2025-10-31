import pathlib
import sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import collector  # noqa: E402


def test_rank_top10_ordering():
    df = pd.DataFrame(
        {
            "liquidityUsd": [6000, 7000, 8000, 9000],
            "priceChange24h": [1, 1, 2, 2],
            "volume24hUsd": [100, 200, 100, 50],
        }
    )
    res = collector.rank_top10(df)
    assert len(res) <= 10
    values = list(zip(res["priceChange24h"], res["volume24hUsd"]))
    assert values == [(2, 100), (2, 50), (1, 200), (1, 100)]
