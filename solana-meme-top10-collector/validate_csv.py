import sys, csv, glob
EXPECTED = [
    "date","chain","baseToken","baseSymbol","pairAddress","tokenAddress",
    "priceUsd","liquidityUsd","volume24hUsd","txns24h","priceChange24h",
    "createdAt","earlyReturnMultiple","holders","exitLiquidity",
    "hasMintAuth","hasFreezeAuth","notes"
]
files = sorted(glob.glob("data/top10_*.csv"))
if not files:
    print("No CSV found in data/"); sys.exit(1)
path = files[-1]
with open(path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    if list(reader.fieldnames) != EXPECTED:
        print("Bad headers:", reader.fieldnames); sys.exit(2)
    rows = list(reader)
    if len(rows) == 0:
        print("CSV has 0 data rows:", path)
        sys.exit(3)
print("CSV validated:", path)
