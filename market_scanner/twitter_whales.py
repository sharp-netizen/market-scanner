"""
Twitter/X Whale Tracker

Track unusual options activity from popular whale accounts.

Free sources:
- @unusualwhales
- @whale_alerts
- @options_wizard
- @larrywilliams1

Usage:
    python3 twitter_whales.py
"""

import asyncio
import os
from typing import Callable, List, Dict
from dataclasses import dataclass
from datetime import datetime


# Whale tracking accounts (free on Twitter/X)
WHALE_ACCOUNTS = [
    "unusualwhales",
    "whale_alerts", 
    "options_wizard",
    "maxjuli",
    "stonexwolf",
]

@dataclass
class WhaleTweet:
    """Whale tweet data"""
    author: str
    content: str
    ticker: str
    option_type: str  # "call" or "put"
    strike: float
    expiration: str
    size: int
    premium: float
    url: str
    timestamp: datetime


class TwitterWhaleTracker:
    """
    Track unusual options from Twitter/X accounts
    
    Note: Requires Twitter/X cookies for API access.
    This is a placeholder - actual implementation needs
    Twitter API or cookie-based scraping.
    
    Free alternative: Manual monitoring of whale accounts
    """
    
    def __init__(self, config: Dict, callback: Callable[[WhaleTweet], None]):
        self.config = config
        self.callback = callback
        self.accounts = config.get("accounts", WHALE_ACCOUNTS)
        self._running = False
    
    async def start(self) -> None:
        """Start tracking whale tweets"""
        self._running = True
        
        # Note: Twitter/X API requires authentication
        # Free alternative: Manual account monitoring
        print("[TwitterWhales] Note: Twitter API requires authentication")
        print(f"[TwitterWhales] Tracking: {', '.join(self.accounts)}")
        print("[TwitterWhales] Free alternative: Check these accounts manually")
        
        while self._running:
            await asyncio.sleep(3600)  # Check every hour
            # Would need Twitter API or cookies for automation
    
    def stop(self) -> None:
        self._running = False


class RedditOptionsTracker:
    """
    Track unusual options from Reddit communities
    
    Free sources:
    - r/options
    - r/wallstreetbets
    - r/options_flow
    """
    
    def __init__(self, config: Dict, callback: Callable[[Dict], None]):
        self.config = config
        self.callback = callback
        self.subreddits = config.get("subreddits", ["options", "wallstreetbets"])
    
    async def fetch_recent(self, subreddit: str = "options", limit: int = 10) -> List[Dict]:
        """Fetch recent posts about unusual options"""
        # Would use Reddit API (free, no auth for public data)
        return []
    
    def parse_post(self, post: Dict) -> Dict:
        """Parse Reddit post for options data"""
        # Extract ticker, strike, expiration from post title
        return {}


class TelegramWhaleChannels:
    """
    Free Telegram channels for whale options alerts
    
    Channels:
    - @unusualwhales (free tier)
    - @whale_trades
    - @options_flow
    """
    
    def __init__(self, config: Dict, callback: Callable[[Dict], None]):
        self.config = config
        self.callback = callback
        self.channels = config.get("channels", ["unusualwhales"])
    
    async def start(self) -> None:
        """Monitor Telegram channels"""
        print("[TelegramWhales] Note: Requires Telegram account")
        print(f"[TelegramWhales] Channels: {', '.join(self.channels)}")


# ============================================================
# MOCK WHALE DATA - Simulate what real data looks like
# ============================================================

def get_mock_whale_data(days: int = 1) -> List[Dict]:
    """Generate mock whale data for demonstration"""
    import random
    from datetime import datetime, timedelta
    
    data = []
    tickers = ["AAPL", "TSLA", "NVDA", "AMD", "SPY", "META", "GOOGL", "AMZN"]
    accounts = ["@unusualwhales", "@whale_alerts", "@options_wizard"]
    
    for _ in range(days * 24):  # Per hour
        if random.random() > 0.7:  # 30% chance of whale
            for _ in range(random.randint(1, 5)):
                ticker = random.choice(tickers)
                option_type = random.choice(["call", "put"])
                strike = random.randint(100, 500)
                size = random.randint(100, 5000)
                price = random.uniform(1, 20)
                
                data.append({
                    "source": random.choice(accounts),
                    "ticker": ticker,
                    "type": option_type,
                    "strike": strike,
                    "expiration": (datetime.now() + timedelta(days=random.randint(7, 30))).strftime("%Y-%m-%d"),
                    "size": size,
                    "price": round(price, 2),
                    "premium": round(size * price * 100, 2),
                    "timestamp": datetime.now().isoformat(),
                    "signal": random.choice(["sweep", "whale", "unusual", "block"]),
                })
    
    return data


async def demo():
    """Demo showing whale tracking"""
    print("=== Free Whale Tracking Options ===\n")
    
    print("1. Twitter/X Accounts (Free, Manual):")
    for acc in WHALE_ACCOUNTS:
        print(f"   - {acc}")
    
    print("\n2. Reddit Communities (Free, Public):")
    print("   - r/options")
    print("   - r/wallstreetbets")
    print("   - r/options_flow")
    
    print("\n3. Telegram Channels (Free):")
    print("   - @unusualwhales")
    print("   - @whale_trades")
    
    print("\n=== Mock Whale Data ===")
    print("(Simulated data - represents what real sources provide)\n")
    
    whale_data = get_mock_whale_data(days=1)
    
    # Aggregate by ticker
    by_ticker = {}
    for w in whale_data:
        t = w["ticker"]
        if t not in by_ticker:
            by_ticker[t] = {"calls": 0, "puts": 0, "premium": 0}
        if w["type"] == "call":
            by_ticker[t]["calls"] += w["size"]
        else:
            by_ticker[t]["puts"] += w["size"]
        by_ticker[t]["premium"] += w["premium"]
    
    print(f"Found {len(whale_data)} whale orders\n")
    print("By Ticker:")
    print("-" * 60)
    for ticker, stats in sorted(by_ticker.items(), key=lambda x: x[1]["premium"], reverse=True):
        print(f"{ticker:6} | Calls: {stats['calls']:5} | Puts: {stats['puts']:5} | Premium: ${stats['premium']/1000:.1f}K")
    
    print("\n=== Sample Whale Alerts ===")
    for w in whale_data[:10]:
        print(f"{w['source']:15} | {w['ticker']:5} | {w['type'].upper():4} ${w['strike']:3} | "
              f"x{w['size']:4} | ${w['premium']/1000:.1f}K | [{w['signal']}]")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
