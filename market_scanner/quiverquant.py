"""
QuiverQuant Provider for Options Data

Free API for unusual options activity, whale trades, and institutional flow.

API Docs: https://api.quiverquant.com/docs
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp


@dataclass
class OptionData:
    """Options trade data structure"""
    symbol: str          # AAPL240119C00150000
    ticker: str          # AAPL
    strike: float        # 150.0
    expiration: str      # 2024-01-19
    option_type: str     # "call" or "put"
    price: float         # Option price
    size: int           # Number of contracts
    premium: float       # Total premium (price * size * 100)
    timestamp: int       # Unix timestamp
    exchange: str        # Exchange
    conditions: List[str] # Special conditions
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "ticker": self.ticker,
            "strike": self.strike,
            "expiration": self.expiration,
            "type": self.option_type,
            "price": self.price,
            "size": self.size,
            "premium": self.premium,
            "timestamp": self.timestamp,
            "exchange": self.exchange,
            "conditions": self.conditions
        }


class QuiverQuantProvider:
    """
    QuiverQuant API Provider for Options Data
    
    Provides:
    - Unusual options activity
    - Whale trades
    - Sweeps
    - Historical data
    
    Note: Data is delayed (15+ min), not real-time.
    """
    
    BASE_URL = "https://api.quiverquant.com/beta"
    
    def __init__(self, config: dict, callback: Callable[[OptionData], None]):
        self.config = config
        self.callback = callback
        self.api_key = config.get("api_key", "")
        self.tickers = config.get("tickers", ["AAPL", "TSLA", "SPY"])
        self._running = False
        self._session = None
        self._poll_interval = 60  # Poll every 60 seconds
    
    async def connect(self) -> bool:
        """Initialize HTTP session"""
        self._session = aiohttp.ClientSession()
        print(f"[QuiverQuant] Connected (REST API)")
        return True
    
    async def subscribe(self, tickers: List[str] = None) -> bool:
        """Subscribe to tickers (for polling)"""
        if tickers:
            self.tickers = tickers
        print(f"[QuiverQuant] Subscribed to: {self.tickers}")
        return True
    
    async def unsubscribe(self, tickers: List[str]) -> bool:
        return True
    
    async def on_message(self, message: str) -> Optional[OptionData]:
        return None
    
    async def disconnect(self) -> None:
        self._running = False
        if self._session:
            await self._session.close()
        print("[QuiverQuant] Disconnected")
    
    async def start(self) -> None:
        """Start polling for options data"""
        self._running = True
        await self._poll_loop()
    
    async def _poll_loop(self) -> None:
        """Poll for options data"""
        while self._running:
            try:
                await self._fetch_unusual_activity()
            except Exception as e:
                print(f"[QuiverQuant] Error: {e}")
            
            await asyncio.sleep(self._poll_interval)
    
    async def _fetch_unusual_activity(self) -> None:
        """Fetch unusual options activity"""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        async with self._session.get(
            f"{self.BASE_URL}/historical/live",
            headers=headers
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                await self._parse_unusual_activity(data)
            else:
                print(f"[QuiverQuant] API error: {resp.status}")
    
    async def _parse_unusual_activity(self, data: List[Dict]) -> None:
        """Parse API response into OptionData"""
        for item in data:
            try:
                option = self._parse_item(item)
                if option:
                    self.callback(option)
            except Exception as e:
                print(f"[QuiverQuant] Parse error: {e}")
    
    def _parse_item(self, item: Dict) -> Optional[OptionData]:
        """Parse single item into OptionData"""
        ticker = item.get("Ticker", "")
        if ticker not in self.tickers:
            return None
        
        # Parse option symbol (AAPL240119C00150000)
        symbol = item.get("Ticker", "")
        strike = item.get("Strike", 0)
        expiration = item.get("Expiration", "")
        option_type = item.get("Type", "").lower()  # "call" or "put"
        price = item.get("Price", 0)
        size = item.get("Size", 0)
        
        # Calculate premium
        premium = price * size * 100 if price and size else 0
        
        # Parse timestamp
        timestamp = int(time.time() * 1000)
        
        return OptionData(
            symbol=symbol,
            ticker=ticker,
            strike=float(strike) if strike else 0,
            expiration=expiration,
            option_type=option_type,
            price=float(price) if price else 0,
            size=int(size) if size else 0,
            premium=premium,
            timestamp=timestamp,
            exchange=item.get("Exchange", ""),
            conditions=[]
        )
    
    async def fetch_historical(self, days: int = 7) -> List[Dict]:
        """Fetch historical unusual activity
        
        Args:
            days: Number of days back to fetch (1-30)
        
        Returns:
            List of historical options data
        """
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        async with self._session.get(
            f"{self.BASE_URL}/historical/options",
            params={"days": days},
            headers=headers
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return []
    
    async def fetch_sweeps(self, ticker: str = None) -> List[Dict]:
        """Fetch sweep orders
        
        Sweeps are large orders broken into smaller parts.
        Often indicate institutional activity.
        """
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        params = {"ticker": ticker} if ticker else {}
        
        async with self._session.get(
            f"{self.BASE_URL}/historical/sweeps",
            params=params,
            headers=headers
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return []
    
    async def fetch_flow(self, ticker: str = None) -> List[Dict]:
        """Fetch institutional flow data"""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        params = {"ticker": ticker} if ticker else {}
        
        async with self._session.get(
            f"{self.BASE_URL}/historical/flow",
            params=params,
            headers=headers
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return []
    
    async def analyze_sentiment(self, ticker: str) -> Dict:
        """Get options sentiment for a ticker
        
        Returns:
            {
                "call_put_ratio": float,
                "total_calls": int,
                "total_puts": int,
                "unusual_activity": List
            }
        """
        data = await self.fetch_historical(days=7)
        
        calls = [d for d in data if d.get("Type", "").lower() == "call"]
        puts = [d for d in data if d.get("Type", "").lower() == "put"]
        
        total_calls = sum(d.get("Size", 0) for d in calls)
        total_puts = sum(d.get("Size", 0) for d in puts)
        
        return {
            "ticker": ticker,
            "call_put_ratio": total_calls / total_puts if total_puts else 0,
            "total_calls": total_calls,
            "total_puts": total_puts,
            "unusual_activity": data[:10]  # Top 10 unusual
        }


# Example usage
async def example():
    def on_option(option: OptionData):
        print(f"{option.ticker} {option.expiration} {option.option_type.upper()} "
              f"${option.strike} x {option.size} @ ${option.price}")
    
    provider = QuiverQuantProvider(
        config={"tickers": ["AAPL", "TSLA"]},
        callback=on_option
    )
    
    await provider.connect()
    await provider.subscribe(["AAPL", "TSLA"])
    
    # Fetch historical data
    print("\n=== Last 7 Days ===")
    historical = await provider.fetch_historical(days=7)
    print(f"Found {len(historical)} unusual options")
    
    # Analyze sentiment
    sentiment = await provider.analyze_sentiment("AAPL")
    print(f"\n=== AAPL Sentiment ===")
    print(f"Call/Put Ratio: {sentiment['call_put_ratio']:.2f}")
    print(f"Total Calls: {sentiment['total_calls']}")
    print(f"Total Puts: {sentiment['total_puts']}")
    
    await provider.disconnect()


if __name__ == "__main__":
    asyncio.run(example())
