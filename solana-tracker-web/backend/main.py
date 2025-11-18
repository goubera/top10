"""
FastAPI backend for Solana Token Tracker
Provides REST API endpoints for the dashboard
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import os

from database import init_db, get_db, TokenSnapshot, DailyStats
from collector import collect_top_tokens

# Initialize FastAPI app
app = FastAPI(
    title="Solana Token Tracker",
    description="Track top Solana memecoins and new tokens",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("✅ Database initialized")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Solana Token Tracker API",
        "version": "1.0.0",
        "endpoints": {
            "tokens": "/api/tokens",
            "top_gainers": "/api/tokens/top-gainers",
            "new_tokens": "/api/tokens/new",
            "stats": "/api/stats",
            "trends": "/api/trends",
            "collect": "/api/collect"
        }
    }


@app.get("/api/tokens")
async def get_tokens(
    date: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all tracked tokens
    Query params:
    - date: YYYY-MM-DD (default: today)
    - limit: max results (default: 50)
    """
    if not date:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    tokens = db.query(TokenSnapshot)\
        .filter(TokenSnapshot.date == date)\
        .order_by(desc(TokenSnapshot.volume_24h))\
        .limit(limit)\
        .all()

    return {
        "date": date,
        "count": len(tokens),
        "tokens": [t.to_dict() for t in tokens]
    }


@app.get("/api/tokens/top-gainers")
async def get_top_gainers(
    date: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get top gainers by 24h volume
    """
    if not date:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    tokens = db.query(TokenSnapshot)\
        .filter(TokenSnapshot.date == date)\
        .filter(TokenSnapshot.is_top_gainer == True)\
        .order_by(desc(TokenSnapshot.volume_24h))\
        .limit(limit)\
        .all()

    return {
        "date": date,
        "count": len(tokens),
        "top_gainers": [t.to_dict() for t in tokens]
    }


@app.get("/api/tokens/new")
async def get_new_tokens(
    date: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get newly created tokens (last 24h)
    """
    if not date:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    tokens = db.query(TokenSnapshot)\
        .filter(TokenSnapshot.date == date)\
        .filter(TokenSnapshot.is_new_token == True)\
        .order_by(desc(TokenSnapshot.volume_24h))\
        .limit(limit)\
        .all()

    return {
        "date": date,
        "count": len(tokens),
        "new_tokens": [t.to_dict() for t in tokens]
    }


@app.get("/api/token/{token_address}")
async def get_token_detail(
    token_address: str,
    db: Session = Depends(get_db)
):
    """
    Get token details and history
    """
    # Get all snapshots for this token
    snapshots = db.query(TokenSnapshot)\
        .filter(TokenSnapshot.token_address == token_address)\
        .order_by(desc(TokenSnapshot.date))\
        .all()

    if not snapshots:
        raise HTTPException(status_code=404, detail="Token not found")

    return {
        "token_address": token_address,
        "token_name": snapshots[0].token_name,
        "token_symbol": snapshots[0].token_symbol,
        "history_count": len(snapshots),
        "history": [s.to_dict() for s in snapshots]
    }


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get overall statistics
    """
    # Today's stats
    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_stats = db.query(DailyStats).filter(DailyStats.date == today).first()

    # Total tokens ever tracked
    total_tokens = db.query(func.count(func.distinct(TokenSnapshot.token_address))).scalar()

    # Recent daily stats (last 7 days)
    week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    recent_stats = db.query(DailyStats)\
        .filter(DailyStats.date >= week_ago)\
        .order_by(desc(DailyStats.date))\
        .all()

    return {
        "today": today_stats.date if today_stats else None,
        "total_unique_tokens": total_tokens,
        "today_stats": {
            "tokens_tracked": today_stats.total_tokens_tracked if today_stats else 0,
            "total_volume": today_stats.total_volume_24h if today_stats else 0,
            "avg_price_change": today_stats.avg_price_change if today_stats else 0,
            "new_tokens": today_stats.new_tokens_count if today_stats else 0
        },
        "recent_days": [
            {
                "date": s.date,
                "tokens": s.total_tokens_tracked,
                "volume": s.total_volume_24h,
                "new_tokens": s.new_tokens_count
            } for s in recent_stats
        ]
    }


@app.get("/api/trends")
async def get_trends(days: int = 7, db: Session = Depends(get_db)):
    """
    Get trend analysis over the last N days
    """
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Get tokens that appear multiple times (trending)
    trending = db.query(
        TokenSnapshot.token_address,
        TokenSnapshot.token_symbol,
        func.count(TokenSnapshot.id).label('appearances'),
        func.avg(TokenSnapshot.volume_24h).label('avg_volume'),
        func.avg(TokenSnapshot.price_change_24h).label('avg_change')
    ).filter(
        TokenSnapshot.date >= cutoff
    ).group_by(
        TokenSnapshot.token_address,
        TokenSnapshot.token_symbol
    ).having(
        func.count(TokenSnapshot.id) > 1
    ).order_by(
        desc('appearances')
    ).limit(20).all()

    return {
        "days_analyzed": days,
        "trending_tokens": [
            {
                "token_address": t.token_address,
                "token_symbol": t.token_symbol,
                "days_in_top": t.appearances,
                "avg_volume_24h": t.avg_volume,
                "avg_price_change": t.avg_change
            } for t in trending
        ]
    }


@app.post("/api/collect")
async def trigger_collection(db: Session = Depends(get_db)):
    """
    Manually trigger token collection
    """
    try:
        result = collect_top_tokens(db, top_n=10)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/csv")
async def export_csv(date: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Export tokens as CSV
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv

    if not date:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    tokens = db.query(TokenSnapshot)\
        .filter(TokenSnapshot.date == date)\
        .order_by(desc(TokenSnapshot.volume_24h))\
        .all()

    # Create CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'date', 'token_symbol', 'token_name', 'token_address',
        'price_usd', 'market_cap', 'volume_24h', 'liquidity_usd',
        'price_change_24h', 'txns_24h', 'is_new_token', 'is_top_gainer'
    ])

    writer.writeheader()
    for token in tokens:
        writer.writerow({
            'date': token.date,
            'token_symbol': token.token_symbol,
            'token_name': token.token_name,
            'token_address': token.token_address,
            'price_usd': token.price_usd,
            'market_cap': token.market_cap,
            'volume_24h': token.volume_24h,
            'liquidity_usd': token.liquidity_usd,
            'price_change_24h': token.price_change_24h,
            'txns_24h': token.txns_24h,
            'is_new_token': token.is_new_token,
            'is_top_gainer': token.is_top_gainer
        })

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=solana_tokens_{date}.csv"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
