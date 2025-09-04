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
Local:
```bash
cd solana-meme-top10-collector
pip install -r requirements.txt
pytest -q
```
CI runs `pytest` only when test files exist.

## CI details
- Daily workflow runs at **06:10 UTC** (`collect.yml`).
- If `SLACK_WEBHOOK_URL` is defined, a short summary is posted to Slack after each run.
- CSV output is committed back to the repo.

## Archive & Cleanup
- `archive.yml` moves the previous month's CSV files into `solana-meme-top10-collector/archive/YYYY-MM/` on the 1st of each month.
- `cleanup.yml` deletes CSV files older than 180 days from both `data/` and `archive/` on a weekly schedule.

## Slack (optionnel)
Define a `SLACK_WEBHOOK_URL` secret to receive daily notifications. The workflow continues even if the webhook is missing or fails.

## Troubleshooting
- If Dexscreener returns no data, the run logs a warning and still creates a CSV with headers only. This is expected.
- For network flakiness, the collector retries HTTP requests with exponential backoff.
