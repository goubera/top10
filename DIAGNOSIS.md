# Diagnosis - Data Collection Failure

## Current Issue (October 2025)

### Symptom
All CSV files since September 2025 contain only headers, no actual data.

### Root Cause
DexScreener API now requires authentication (API key) for all endpoints, returning `403 Forbidden` errors. This changed sometime in September 2025.

**Error:**
```
RuntimeError: GET /latest/dex/search failed after retries: 403 Client Error: Forbidden for url: https://api.dexscreener.com/latest/dex/search?q=SOL
```

## Solution Implemented

### 1. Multi-Source Data Collection
Created `data_sources.py` with automatic fallback between multiple APIs:
- **Primary**: DexScreener API (with API key support)
- **Fallback**: Raydium API (public)

### 2. Better Error Handling
- Clear error messages in logs
- Creates `data/run_summary.json` with diagnostic information
- Fails gracefully without creating empty CSV files

### 3. Required Configuration

**You MUST add a DexScreener API key to GitHub Secrets:**

1. Get a free API key from https://dexscreener.com/
2. Go to your repository Settings → Secrets and variables → Actions
3. Add a new secret named `DEXSCREENER_API_KEY` with your API key
4. The workflow will automatically use it (already configured in `.github/workflows/collect.yml`)

### Verification

After adding the API key, the workflow should:
- Successfully fetch data from DexScreener
- Create CSV files with actual trading pair data
- Generate a success summary in `data/run_summary.json`

Check the Action logs for messages like:
```
INFO:data_sources:Trying DexScreener...
INFO:data_sources:✓ DexScreener succeeded with X pairs
INFO:__main__:✓ Successfully wrote data/top10_YYYY-MM-DD.csv with 10 rows
```

---

## Previous Issue (Resolved)

### Root cause
The GitHub Actions run failed in the **Install deps** step:
```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

### Why it happened
The workflow executed commands from the repository root while the project and its `requirements.txt` live in the `solana-meme-top10-collector/` subfolder.

### Fix applied
The workflow now installs dependencies using the correct path and sets the working directory for all relevant steps.
