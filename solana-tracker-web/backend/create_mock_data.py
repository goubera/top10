"""
Create mock data for testing the dashboard without API access
"""
from database import SessionLocal, TokenSnapshot, DailyStats, init_db
from datetime import datetime, timedelta
import random

# Initialize database
init_db()
db = SessionLocal()

print("🧪 Creating mock data for testing...")

# Token names and symbols for variety
MOCK_TOKENS = [
    ("SolanaDogeKing", "SDK", "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"),
    ("MoonRocket", "MOON", "2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo"),
    ("PepeCoin", "PEPE", "8qJSyQprMC57TWKaYEmetUR3UUiTP2M3hXdcvFhkZdmv"),
    ("SafeMoon", "SAFE", "9vMJfxuKxXBoEa7rM12mYLMwTacLMLDJqHozw96WQL8i"),
    ("DiamondHands", "DIAMOND", "5jqocXfQKxvEBNHA3qxHPt1RFUFh79jWpybVyTBmyQ7w"),
    ("ToTheMoon", "TTM", "3KpUJYXx92KHCmzvwCd6c3E3iYwKR8WR5PEW8NUqUx7P"),
    ("LamboToken", "LAMBO", "6dKCoGBENJCMshEWYvY3Xo8PGhxfqRxQ3ePZLsQDnQ4u"),
    ("HodlCoin", "HODL", "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"),
    ("YeetToken", "YEET", "BkPhZNfG7DjmjwqKLZQMVxG2BH6qLqYPbAqQRCCrhHxh"),
    ("Stonks", "STONK", "CuieVDEDtLo7FypA9SbLM9saXFdb1dsshEkyErMqkRQq")
]

# Create data for last 7 days
for day_offset in range(7):
    date = (datetime.utcnow() - timedelta(days=day_offset)).strftime("%Y-%m-%d")

    print(f"📅 Creating data for {date}...")

    day_tokens = []

    # Create 10 tokens for this day
    for i in range(10):
        token_idx = (i + day_offset) % len(MOCK_TOKENS)
        name, symbol, address = MOCK_TOKENS[token_idx]

        # Generate realistic-looking data
        base_price = random.uniform(0.0001, 5.0)
        base_volume = random.uniform(50000, 5000000)

        # Add some variation over days
        price_variation = 1 + (random.random() - 0.5) * 0.3
        volume_variation = 1 + (random.random() - 0.5) * 0.5

        token = TokenSnapshot(
            date=date,
            token_address=f"{address}_{day_offset}",
            token_name=name,
            token_symbol=symbol,
            pair_address=f"pair_{address}_{i}",
            price_usd=base_price * price_variation,
            market_cap=base_price * base_volume * 100 * price_variation,
            liquidity_usd=base_volume * 0.3 * volume_variation,
            volume_24h=base_volume * volume_variation,
            price_change_24h=random.uniform(-70, 300),  # Meme coin volatility!
            txns_24h=random.randint(500, 50000),
            created_at=int((datetime.utcnow() - timedelta(days=day_offset, hours=random.randint(0, 23))).timestamp() * 1000),
            holders=random.randint(50, 10000),
            is_new_token=i < 3,  # First 3 are "new"
            is_top_gainer=i < 7,  # First 7 are "top gainers"
        )

        day_tokens.append(token)
        db.add(token)

    # Create daily stats
    stats = DailyStats(
        date=date,
        total_tokens_tracked=len(day_tokens),
        total_volume_24h=sum(t.volume_24h for t in day_tokens),
        avg_price_change=sum(t.price_change_24h for t in day_tokens) / len(day_tokens),
        new_tokens_count=sum(1 for t in day_tokens if t.is_new_token)
    )
    db.add(stats)

    print(f"  ✅ Created {len(day_tokens)} tokens and stats")

# Commit all changes
try:
    db.commit()
    print("\n✅ Mock data created successfully!")
    print("\n📊 Summary:")
    print(f"   - Days: 7")
    print(f"   - Tokens per day: 10")
    print(f"   - Total snapshots: 70")
    print("\n🚀 You can now start the server and view the dashboard!")
    print("   Run: python main.py")
    print("   Then open: http://localhost:8000/static/index.html")
except Exception as e:
    db.rollback()
    print(f"\n❌ Error creating mock data: {e}")
finally:
    db.close()
