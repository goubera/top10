# 🚀 Quick Start Guide

## Installation & Launch (30 seconds)

### Option 1: One-line start (Recommended)

```bash
cd solana-tracker-web
./start.sh
```

Then open your browser to: **http://localhost:8000/static/index.html**

### Option 2: Manual start

```bash
cd solana-tracker-web/backend
pip install -r requirements.txt
python main.py
```

Then open: **http://localhost:8000/static/index.html**

---

## 🔑 API Configuration (Optionnel mais recommandé)

L'application fonctionne de 2 façons :

### ✅ Option 1 : Avec clé API Birdeye (GRATUIT, recommandé)

**Avantages** :
- Données réelles en temps réel
- 30,000 crédits/mois GRATUITS
- Pas de carte bancaire requise

**Setup** (2 minutes) :
1. Créer compte sur [Birdeye.so](https://birdeye.so) (gratuit)
2. Obtenir votre clé API
3. Configurer :

```bash
cd backend
echo "BIRDEYE_API_KEY=votre_cle_ici" > .env
```

📖 **[Guide complet avec screenshots](./API_SETUP.md)**

### ⚡ Option 2 : Sans clé API (Mode démo)

L'application fonctionne directement avec **données mockées réalistes** :
- Dashboard complet fonctionnel
- Tokens de test (BONK, WIF, POPCAT...)
- Parfait pour tester l'interface

Pas de configuration nécessaire, lancez directement !

---

## 📊 Features Demo

Once you have data collected:

### 1. View Dashboard
```
http://localhost:8000/static/index.html
```

### 2. Use API Endpoints
```bash
# Get today's stats
curl http://localhost:8000/api/stats

# Get top gainers
curl http://localhost:8000/api/tokens/top-gainers

# Get new tokens
curl http://localhost:8000/api/tokens/new

# Get trends
curl http://localhost:8000/api/trends?days=7
```

### 3. Trigger Collection (with API key)
```bash
curl -X POST http://localhost:8000/api/collect
```

### 4. Export CSV
```bash
curl http://localhost:8000/api/export/csv > tokens.csv
```

---

## 🔧 Configuration

### Enable Daily Automation

Run scheduler in a separate terminal:

```bash
cd solana-tracker-web/backend
python scheduler.py
```

This will:
- Collect data daily at 06:00 UTC
- Continue running in background
- Press Ctrl+C to stop

### Change Collection Time

Edit `backend/scheduler.py`:

```python
scheduler.add_job(
    scheduled_collection,
    trigger=CronTrigger(hour=6, minute=0),  # Change to your preferred time
    ...
)
```

---

## 🧪 Testing with Mock Data

Create `backend/mock_data.py`:

```python
from database import SessionLocal, TokenSnapshot, DailyStats
from datetime import datetime
import random

db = SessionLocal()

# Create mock tokens
for i in range(10):
    token = TokenSnapshot(
        date=datetime.utcnow().strftime("%Y-%m-%d"),
        token_address=f"mock_address_{i}",
        token_name=f"Mock Token {i}",
        token_symbol=f"MOCK{i}",
        pair_address=f"pair_{i}",
        price_usd=random.uniform(0.0001, 10),
        market_cap=random.uniform(100000, 10000000),
        liquidity_usd=random.uniform(50000, 5000000),
        volume_24h=random.uniform(100000, 2000000),
        price_change_24h=random.uniform(-50, 200),
        txns_24h=random.randint(100, 10000),
        created_at=int(datetime.utcnow().timestamp() * 1000),
        is_new_token=i < 3,
        is_top_gainer=i < 5
    )
    db.add(token)

# Create stats
stats = DailyStats(
    date=datetime.utcnow().strftime("%Y-%m-%d"),
    total_tokens_tracked=10,
    total_volume_24h=5000000,
    avg_price_change=45.5,
    new_tokens_count=3
)
db.add(stats)

db.commit()
print("✅ Mock data added!")
```

Run it:
```bash
python backend/mock_data.py
```

---

## 📝 Common Issues

### Port 8000 already in use
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
python main.py --port 8080
```

### Database locked
```bash
# Remove and reinitialize
rm data/tracker.db
python -c "from database import init_db; init_db()"
```

### No data showing
1. Check if API key is set (`.env` file)
2. Try mock data script above
3. Check browser console for errors

---

## 🎯 Next Steps

1. ✅ Get DexScreener API key
2. ✅ Run first collection: `POST /api/collect`
3. ✅ Set up scheduler for daily automation
4. ✅ Customize dashboard UI
5. ✅ Add more analytics features

---

## 📞 Need Help?

Check:
- `README.md` - Full documentation
- Browser DevTools console
- API logs in terminal
- DexScreener API status

Enjoy tracking Solana tokens! 🚀
