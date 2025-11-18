"""
Scheduler for automated daily token collection
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import SessionLocal
from collector import collect_top_tokens
from datetime import datetime


def scheduled_collection():
    """Run daily token collection"""
    print(f"\n{'='*60}")
    print(f"🕒 Scheduled collection triggered at {datetime.utcnow()}")
    print(f"{'='*60}\n")

    db = SessionLocal()
    try:
        result = collect_top_tokens(db, top_n=10)
        print(f"\n✅ Collection completed: {result}\n")
    except Exception as e:
        print(f"\n❌ Collection failed: {e}\n")
    finally:
        db.close()


def start_scheduler():
    """
    Start the background scheduler
    Runs collection daily at 06:00 UTC
    """
    scheduler = BackgroundScheduler()

    # Schedule daily collection at 06:00 UTC
    scheduler.add_job(
        scheduled_collection,
        trigger=CronTrigger(hour=6, minute=0),
        id='daily_collection',
        name='Daily token collection',
        replace_existing=True
    )

    scheduler.start()
    print("📅 Scheduler started - Daily collection at 06:00 UTC")

    return scheduler


if __name__ == "__main__":
    # Test scheduler
    print("Testing scheduler...")
    scheduler = start_scheduler()

    # Run collection immediately for testing
    print("\n🧪 Running test collection...")
    scheduled_collection()

    # Keep running
    try:
        import time
        print("\n⏰ Scheduler is running. Press Ctrl+C to exit.")
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("\n👋 Scheduler stopped")
