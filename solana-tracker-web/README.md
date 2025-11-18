# 🚀 Solana Token Tracker

A modern web dashboard for tracking top-gaining and newly created Solana tokens in real-time.

## ✨ Features

- 📊 **Real-time Dashboard** - Beautiful web interface with live data
- 🔥 **Top Gainers** - Track tokens with highest 24h volume
- ✨ **New Tokens** - Monitor newly created tokens (< 24h old)
- 📈 **Trend Analysis** - Multi-day trending tokens analysis
- 📉 **Charts** - Visual representation of volume and new tokens over time
- 💾 **CSV Export** - Download daily data in CSV format
- ⏰ **Automated Collection** - Daily scheduled data collection at 06:00 UTC
- 🎨 **Modern UI** - Dark theme, responsive design, beautiful visualizations

## 🏗️ Architecture

```
solana-tracker-web/
├── backend/
│   ├── main.py          # FastAPI REST API
│   ├── collector.py     # Token data collector
│   ├── database.py      # SQLAlchemy models
│   ├── scheduler.py     # Automated scheduling
│   └── requirements.txt
├── frontend/
│   ├── index.html       # Dashboard UI
│   ├── style.css        # Styling
│   └── app.js          # JavaScript logic
└── data/
    └── tracker.db      # SQLite database
```

## 📋 Requirements

- Python 3.8+
- Modern web browser

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd solana-tracker-web/backend
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python -c "from database import init_db; init_db()"
```

### 3. Collect Initial Data (Optional)

```bash
python collector.py
```

### 4. Start the Server

**Option A: API Only**
```bash
python main.py
```

**Option B: With Scheduler (Recommended)**
```bash
# In one terminal - Start API
python main.py

# In another terminal - Start scheduler
python scheduler.py
```

### 5. Access Dashboard

Open your browser and navigate to:
```
http://localhost:8000/static/index.html
```

## 📡 API Endpoints

### General
- `GET /` - API information
- `GET /api/stats` - Overall statistics

### Tokens
- `GET /api/tokens` - All tracked tokens
- `GET /api/tokens/top-gainers` - Top gainers by volume
- `GET /api/tokens/new` - Newly created tokens
- `GET /api/token/{address}` - Token detail and history

### Analysis
- `GET /api/trends?days=7` - Trending tokens analysis

### Actions
- `POST /api/collect` - Trigger manual collection
- `GET /api/export/csv?date=YYYY-MM-DD` - Export CSV

## 🎯 Data Collection

The system collects tokens based on:

1. **Volume Ranking** - Sorts tokens by 24h trading volume
2. **New Token Detection** - Identifies tokens created in last 24h
3. **Deduplication** - One entry per token (highest volume pair)
4. **Top 10 Selection** - Stores top 10 gainers + top 10 new tokens

### Data Sources

- **DexScreener API** - Primary source for DEX data
- No API key required for basic usage
- Rate limiting handled with exponential backoff

## 📊 Dashboard Features

### Stats Cards
- Total tokens tracked today
- Total 24h volume
- Number of new tokens
- Average price change

### Charts
- Volume trend over last 7 days
- New tokens trend

### Tables
- **Top Gainers** - Sorted by volume with price, change, liquidity
- **New Tokens** - Recently created tokens with age
- **Trending** - Tokens appearing multiple days

### Actions
- 🔄 Refresh data manually
- 📥 Trigger collection
- 💾 Export CSV

## ⏰ Automated Scheduling

The scheduler runs daily at **06:00 UTC**:

```bash
python scheduler.py
```

To customize the schedule, edit `scheduler.py`:

```python
scheduler.add_job(
    scheduled_collection,
    trigger=CronTrigger(hour=6, minute=0),  # Change time here
    ...
)
```

## 🗄️ Database Schema

### TokenSnapshot
- Token identification (address, symbol, name)
- Price metrics (USD, market cap)
- Volume & liquidity (24h)
- Performance (price change, txns)
- Flags (is_new_token, is_top_gainer)
- Timestamp tracking

### DailyStats
- Aggregated daily metrics
- Total volume, average changes
- New tokens count

## 🔧 Configuration

### Environment Variables (Optional)

Create `.env` file in backend/:

```env
DEXSCREENER_API_KEY=your_key_here  # Optional, for higher rate limits
```

### Customization

**Change collection frequency:**
- Edit `scheduler.py` cron trigger

**Change top N tokens:**
- Modify `top_n` parameter in collection calls

**Adjust data retention:**
- Add cleanup jobs in `scheduler.py`

## 🐛 Troubleshooting

### API Returns No Data
- Check DexScreener API status
- Verify internet connection
- Try manual collection: `POST /api/collect`

### Charts Not Displaying
- Ensure at least 2 days of data collected
- Check browser console for errors
- Verify Chart.js CDN loaded

### Database Locked
- Close other database connections
- Restart the server
- Check file permissions on `data/tracker.db`

## 🚀 Production Deployment

### Using Uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker (Advanced)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Reverse Proxy (Nginx)

```nginx
location / {
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 📝 License

MIT License - feel free to use and modify!

## 🤝 Contributing

Contributions welcome! Feel free to:
- Add new data sources
- Improve UI/UX
- Add more analytics features
- Optimize performance

## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Review API logs
3. Open an issue with details

---

**Built with ❤️ for the Solana community**
