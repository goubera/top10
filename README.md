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

## Configuration Required

### DexScreener API Key (Required)

As of September 2025, DexScreener API requires authentication. You must configure an API key:

1. **Get an API key**: Visit https://dexscreener.com/ and sign up for a free API key
2. **Add to GitHub Secrets**:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `DEXSCREENER_API_KEY`
   - Value: Your API key from DexScreener
3. **The workflow will automatically use it** (already configured in `.github/workflows/collect.yml`)

### Data Sources

The collector uses multiple data sources with automatic fallback:
1. **Primary**: DexScreener API (requires API key)
2. **Fallback**: Raydium API (public, no key needed)

This ensures data collection continues even if one source fails.

## Troubleshooting

### Empty CSV Files
If CSV files contain only headers (no data):
- **Most likely**: Missing or invalid DEXSCREENER_API_KEY in GitHub Secrets
- Check `solana-meme-top10-collector/data/run_summary.json` for error details
- Review GitHub Actions logs for API errors

### Debugging
After each run, check `data/run_summary.json`:
```json
{
  "date": "2025-10-31",
  "success": true,
  "rows_collected": 10,
  "csv_file": "data/top10_2025-10-31.csv"
}
```

If `success: false`, the file contains error details and suggested fixes.

### Network Issues
- For network flakiness, the collector retries HTTP requests with exponential backoff
- If all data sources fail, check GitHub Actions network connectivity
