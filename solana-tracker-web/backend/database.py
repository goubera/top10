"""
Database models and configuration for Solana Token Tracker
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tracker.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TokenSnapshot(Base):
    """Daily snapshot of a token's performance"""
    __tablename__ = "token_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)  # YYYY-MM-DD format
    token_address = Column(String, index=True)
    token_name = Column(String)
    token_symbol = Column(String)
    pair_address = Column(String)

    # Price & Market metrics
    price_usd = Column(Float)
    market_cap = Column(Float, nullable=True)
    liquidity_usd = Column(Float)
    volume_24h = Column(Float)

    # Performance metrics
    price_change_24h = Column(Float)
    volume_change_24h = Column(Float, nullable=True)
    txns_24h = Column(Integer)

    # Token info
    created_at = Column(Integer)  # Unix timestamp
    holders = Column(Integer, nullable=True)

    # Flags
    is_new_token = Column(Boolean, default=False)  # Created in last 24h
    is_top_gainer = Column(Boolean, default=False)  # Top volume

    # Metadata
    collected_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "token_address": self.token_address,
            "token_name": self.token_name,
            "token_symbol": self.token_symbol,
            "pair_address": self.pair_address,
            "price_usd": self.price_usd,
            "market_cap": self.market_cap,
            "liquidity_usd": self.liquidity_usd,
            "volume_24h": self.volume_24h,
            "price_change_24h": self.price_change_24h,
            "volume_change_24h": self.volume_change_24h,
            "txns_24h": self.txns_24h,
            "created_at": self.created_at,
            "holders": self.holders,
            "is_new_token": self.is_new_token,
            "is_top_gainer": self.is_top_gainer,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None
        }


class DailyStats(Base):
    """Aggregated daily statistics"""
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, index=True)

    total_tokens_tracked = Column(Integer)
    total_volume_24h = Column(Float)
    avg_price_change = Column(Float)
    new_tokens_count = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DB_PATH}")


def get_db():
    """Dependency for FastAPI to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
