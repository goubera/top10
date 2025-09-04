import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import collector  # noqa: E402


def fake_fetch_new_pairs_dexscreener(api_key, max_pairs=500):
    return []


def fake_enrich_birdeye(token_address, birdeye_key):
    return {}


def fake_now_iso_date():
    return "2020-01-01"


def test_output_file_pattern_and_idempotence(monkeypatch, tmp_path):
    monkeypatch.setattr(collector, "fetch_new_pairs_dexscreener", fake_fetch_new_pairs_dexscreener)
    monkeypatch.setattr(collector, "enrich_birdeye", fake_enrich_birdeye)
    monkeypatch.setattr(collector, "now_iso_date", fake_now_iso_date)
    monkeypatch.chdir(tmp_path)

    collector.main()
    collector.main()

    data_dir = tmp_path / "data"
    files = list(data_dir.glob("top10_*.csv"))
    assert len(files) == 1
    assert files[0].name == "top10_2020-01-01.csv"
