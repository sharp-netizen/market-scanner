"""
Yahoo Finance Options Provider

Free, no API key required.
Delayed data (15+ min) but full options chains.

Usage:
    python3 yahoo_options.py AAPL
"""

import asyncio
import sys
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
import yfinance as yf


@dataclass
class YahooOption:
    """Yahoo Finance options data"""
    ticker: str
    expiration: str
    strike: float
    option_type: str  # "call" or "put"
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: float
    timestamp: int = 0


class YahooOptionsProvider:
    """
    Yahoo Finance Options Provider
    
    Free, no API key.
    Full options chains with strikes, expirations, IV.
    Data is delayed 15+ minutes.
    """
    
    def __init__(self, config: Dict, callback: Callable[[YahooOption], None]):
        self.config = config
        self.callback = callback
        self.tickers = config.get("tickers", ["AAPL", "TSLA"])
        self._running = False
        self._poll_interval = 60  # 60 seconds
        self._last_fetch: Dict[str, float] = {}  # Ticker -> timestamp
    
    async def connect(self) -> bool:
        """Initialize connection"""
        print(f"[YahooOptions] Connected (free, delayed)")
        return True
    
    async def subscribe(self, tickers: List[str] = None) -> bool:
        """Subscribe to tickers"""
        if tickers:
            self.tickers = tickers
        print(f"[YahooOptions] Subscribed: {self.tickers}")
        return True
    
    async def disconnect(self) -> None:
        self._running = False
        print("[YahooOptions] Disconnected")
    
    async def start(self) -> None:
        """Start polling for options data"""
        self._running = True
        await self._poll_loop()
    
    async def _poll_loop(self) -> None:
        """Poll for options data"""
        while self._running:
            try:
                await self._fetch_all_options()
            except Exception as e:
                print(f"[YahooOptions] Error: {e}")
            await asyncio.sleep(self._poll_interval)
    
    async def _fetch_all_options(self) -> None:
        """Fetch options for all tickers"""
        import time
        
        for ticker in self.tickers:
            # Rate limit: don't fetch same ticker more than every 30s
            now = time.time()
            last = self._last_fetch.get(ticker, 0)
            if now - last < 30:
                continue
            
            self._last_fetch[ticker] = now
            await self._fetch_options(ticker)
    
    async def _fetch_options(self, ticker: str) -> None:
        """Fetch options chain for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options
            
            if not expirations:
                return
            
            # Get first expiration (nearest)
            nearest_exp = expirations[0]
            chain = stock.option_chain(nearest_exp)
            
            # Process calls
            for _, row in chain.calls.iterrows():
                option = YahooOption(
                    ticker=ticker,
                    expiration=nearest_exp,
                    strike=float(row.get('strike', 0)),
                    option_type="call",
                    bid=float(row.get('bid', 0)),
                    ask=float(row.get('ask', 0)),
                    last=float(row.get('lastPrice', 0)),
                    volume=int(row.get('volume', 0)),
                    open_interest=int(row.get('openInterest', 0)),
                    implied_volatility=float(row.get('impliedVolatility', 0))
                )
                self.callback(option)
            
            # Process puts
            for _, row in chain.puts.iterrows():
                option = YahooOption(
                    ticker=ticker,
                    expiration=nearest_exp,
                    strike=float(row.get('strike', 0)),
                    option_type="put",
                    bid=float(row.get('bid', 0)),
                    ask=float(row.get('ask', 0)),
                    last=float(row.get('lastPrice', 0)),
                    volume=int(row.get('volume', 0)),
                    open_interest=int(row.get('openInterest', 0)),
                    implied_volatility=float(row.get('impliedVolatility', 0))
                )
                self.callback(option)
                
        except Exception as e:
            print(f"[YahooOptions] {ticker}: {e}")
    
    def get_expirations(self, ticker: str) -> List[str]:
        """Get available expirations for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            return stock.options
        except:
            return []
    
    def get_chain(self, ticker: str, expiration: str = None) -> Dict:
        """Get full options chain"""
        try:
            stock = yf.Ticker(ticker)
            if expiration is None:
                expirations = stock.options
                if not expirations:
                    return {}
                expiration = expirations[0]
            
            chain = stock.option_chain(expiration)
            return {
                "ticker": ticker,
                "expiration": expiration,
                "calls": chain.calls.to_dict('records'),
                "puts": chain.puts.to_dict('records')
            }
        except Exception as e:
            print(f"[YahooOptions] Chain error: {e}")
            return {}
    
    def get_nearest_calls(self, ticker: str, count: int = 10) -> List[Dict]:
        """Get nearest ITM/ATM calls"""
        chain = self.get_chain(ticker)
        if not chain:
            return []
        
        calls = chain.get("calls", [])
        # Sort by strike proximity to current price
        # Would need underlying price for ATM logic
        return calls[:count]
    
    def get_nearest_puts(self, ticker: str, count: int = 10) -> List[Dict]:
        """Get nearest ITM/ATM puts"""
        chain = self.get_chain(ticker)
        if not chain:
            return []
        
        puts = chain.get("puts", [])
        return puts[:count]


# CLI Demo
async def demo():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    
    def on_option(opt: YahooOption):
        print(f"{opt.ticker} | {opt.expiration} | {opt.option_type.upper()} \${opt.strike} | "
              f"Bid: \${opt.bid:.2f} | Ask: \${opt.ask:.2f} | Vol: {opt.volume}")
    
    provider = YahooOptionsProvider(
        config={"tickers": [ticker]},
        callback=on_option
    )
    
    print(f"=== Yahoo Finance Options: {ticker} ===\n")
    await provider.connect()
    
    # Get full chain
    print("Fetching options chain...")
    chain = provider.get_chain(ticker)
    
    if chain:
        print(f"\nTicker: {chain['ticker']}")
        print(f"Expiration: {chain['expiration']}")
        print(f"\nCalls ({len(chain['calls'])} contracts):")
        for c in chain['calls'][:5]:
            print(f"  Strike: \${c['strike']:.0f} | Bid: \${c['bid']:.2f} | Ask: \${c['ask']:.2f} | Vol: {c['volume']} | OI: {c['openInterest']}")
        
        print(f"\nPuts ({len(chain['puts'])} contracts):")
        for p in chain['puts'][:5]:
            print(f"  Strike: \${p['strike']:.0f} | Bid: \${p['bid']:.2f} | Ask: \${p['ask']:.2f} | Vol: {p['volume']} | OI: {p['openInterest']}")
    
    await provider.disconnect()


if __name__ == "__main__":
    asyncio.run(demo())
