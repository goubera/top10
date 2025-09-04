# Solana Meme Top10 Collector

Daily collection of the top 10 new Solana meme coins. The actual code lives in `solana-meme-top10-collector/`.

## Run locally
```bash
make venv       # create virtualenv (run once)
source .venv/bin/activate
make install    # install dependencies
make run        # run the collector
make test       # run tests
```
CSV files will appear in `solana-meme-top10-collector/data/`.

## Tests
```bash
cd solana-meme-top10-collector
pip install -r requirements.txt
pytest -q
```
Add new tests in `solana-meme-top10-collector/tests/`.

## CI details
- GitHub Actions workflow runs daily at **06:10 UTC** and on manual dispatch.
- Each run installs dependencies with caching, writes `.env` from secrets, executes tests, runs the collector, lists the `data/` folder and commits the daily CSV.

## Troubleshooting
- If Dexscreener returns no data, the run logs a warning and still creates a CSV with headers only. This is expected.
