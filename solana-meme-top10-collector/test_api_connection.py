#!/usr/bin/env python3
"""
Test script to verify DexScreener API connection and data collection.
Run this to ensure your API key is working correctly.

Usage:
    export DEXSCREENER_API_KEY="your-api-key-here"
    python test_api_connection.py
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from data_sources import fetch_top_solana_pairs
import logging

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_api_connection():
    """Test the API connection and data fetching."""

    # Check if API key is set
    api_key = os.getenv("DEXSCREENER_API_KEY", "").strip()

    print("\n" + "="*70)
    print("DexScreener API Connection Test")
    print("="*70)

    if not api_key:
        print("\n⚠️  WARNING: DEXSCREENER_API_KEY environment variable is not set!")
        print("\nTo set it:")
        print("  export DEXSCREENER_API_KEY='your-api-key-here'")
        print("\nOr create a .env file with:")
        print("  DEXSCREENER_API_KEY=your-api-key-here")
        print("\n❌ Test cannot proceed without API key.\n")
        return False

    print(f"\n✓ API key is set (length: {len(api_key)} characters)")
    print(f"✓ API key starts with: {api_key[:8]}...")

    print("\n" + "-"*70)
    print("Attempting to fetch data from DexScreener API...")
    print("-"*70 + "\n")

    try:
        # Try to fetch data
        pairs = fetch_top_solana_pairs(limit=5)

        if not pairs:
            print("\n❌ No pairs returned from API")
            print("This could mean:")
            print("  - API key is invalid")
            print("  - API rate limit exceeded")
            print("  - Network connectivity issues")
            return False

        print(f"\n✅ SUCCESS! Fetched {len(pairs)} pairs from DexScreener API\n")

        # Display sample data
        print("Sample data from first pair:")
        print("-"*70)
        first_pair = pairs[0]
        print(f"  Chain:         {first_pair.get('chainId', 'N/A')}")
        print(f"  Token:         {first_pair.get('baseToken', {}).get('symbol', 'N/A')}")
        print(f"  Pair Address:  {first_pair.get('pairAddress', 'N/A')[:20]}...")
        print(f"  Price USD:     ${first_pair.get('priceUsd', 0)}")
        print(f"  Volume 24h:    ${first_pair.get('volume24hUsd', 0):,.2f}")
        print(f"  Liquidity:     ${first_pair.get('liquidityUsd', 0):,.2f}")
        print("-"*70)

        print("\n✅ All tests passed! Your API key is working correctly.")
        print("\nNext steps:")
        print("  1. The GitHub Actions workflow will use this API key")
        print("  2. Daily collections should now work properly")
        print("  3. Check the workflow logs after the next scheduled run (06:10 UTC)")
        print("\n")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        print("Common issues:")
        print("  1. Invalid API key - verify it's correct")
        print("  2. Network connectivity - check your connection")
        print("  3. API rate limit - wait and try again")
        print("  4. API service down - check https://dexscreener.com/")
        print("\n")
        return False


if __name__ == "__main__":
    success = test_api_connection()
    sys.exit(0 if success else 1)
