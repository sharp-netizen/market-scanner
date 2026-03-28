#!/usr/bin/env python3
"""
Multi-Timeframe Data Engine

Stores tick data and aggregates candles for multiple timeframes:
- 1 minute
- 5 minutes
- 15 minutes
- 1 hour
- 4 hours

Enables multi-timeframe pattern analysis and aligned signal detection.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Deque
import json


@dataclass
class Candle:
    """OHLCV candle data"""
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
    tick_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timestamp": self.timestamp.isoformat(),
            "tick_count": self.tick_count
        }
    
    @property
    def is_green(self) -> bool:
        """Bullish candle (close > open)"""
        return self.close > self.open
    
    @property
    def body_pct(self) -> float:
        """Body size as percentage of open"""
        if self.open == 0:
            return 0
        return abs(self.close - self.open) / self.open * 100
    
    @property
    def range_pct(self) -> float:
        """Range (high-low) as percentage of open"""
        if self.open == 0 or self.high == self.low:
            return 0
        return (self.high - self.low) / self.open * 100


@dataclass
class Tick:
    """Individual trade tick"""
    symbol: str
    price: float
    size: int
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "size": self.size,
            "timestamp": self.timestamp.isoformat()
        }


class MultiTimeframeEngine:
    """
    Multi-timeframe data storage and aggregation engine.
    
    Stores tick data and builds candles for multiple timeframes.
    Enables pattern analysis across timeframes.
    """
    
    # Timeframe configurations
    TIMEFRAMES = {
        "1min": {"seconds": 60, "keep": 1440},      # 1 day
        "5min": {"seconds": 300, "keep": 288},       # 1 day
        "15min": {"seconds": 900, "keep": 96},       # 1 day
        "1hr": {"seconds": 3600, "keep": 168},       # 7 days
        "4hr": {"seconds": 14400, "keep": 168},      # 28 days
    }
    
    # Aggregation mapping: source -> [(target, ticks_per_candle)]
    AGGREGATION_MAP = {
        "1min": [
            ("5min", 5),      # 5 × 1min = 5min
            ("15min", 15),    # 15 × 1min = 15min
            ("1hr", 60),      # 60 × 1min = 1hr
            ("4hr", 240),     # 240 × 1min = 4hr
        ],
        "5min": [
            ("15min", 3),     # 3 × 5min = 15min
            ("1hr", 12),      # 12 × 5min = 1hr
            ("4hr", 48),      # 48 × 5min = 4hr
        ],
        "15min": [
            ("1hr", 4),       # 4 × 15min = 1hr
            ("4hr", 16),      # 16 × 15min = 4hr
        ],
        "1hr": [
            ("4hr", 4),       # 4 × 1hr = 4hr
        ],
    }
    
    def __init__(self, tickers: List[str], config: Dict = None):
        self.tickers = tickers
        self.config = config or {}
        
        # Storage per ticker
        self._data: Dict[str, Dict[str, Deque[Candle]]] = {}
        self._raw_ticks: Dict[str, Deque[Tick]] = {}
        self._current_candles: Dict[str, Dict[str, Candle]] = {}
        
        # Track candle boundaries
        self._last_aggregate: Dict[str, datetime] = {}
        
        # Initialize storage for each ticker
        self._init_storage()
        
        print(f"[MTFEngine] Initialized for {len(tickers)} tickers: {tickers}")
    
    def _init_storage(self):
        """Initialize data structures for each ticker"""
        for ticker in self.tickers:
            # Candles per timeframe
            self._data[ticker] = {}
            for tf, cfg in self.TIMEFRAMES.items():
                self._data[ticker][tf] = deque(maxlen=cfg["keep"])
            
            # Raw ticks (keep last 100 for debugging)
            self._raw_ticks[ticker] = deque(maxlen=100)
            
            # Current (building) candles
            self._current_candles[ticker] = {}
    
    def add_tick(self, symbol: str, price: float, size: int, timestamp: datetime = None):
        """
        Add a tick and update all timeframe candles.
        
        Args:
            symbol: Ticker symbol
            price: Trade price
            size: Trade size
            timestamp: Trade timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        tick = Tick(symbol, price, size, timestamp)
        self._raw_ticks[symbol].append(tick)
        
        # Update 1min candle (base timeframe) - this handles closing old candles
        self._update_candle(symbol, "1min", price, size, timestamp)
    
    def _update_candle(self, symbol: str, timeframe: str, price: float, 
                       size: int, timestamp: datetime) -> Candle:
        """Update or create current candle for a timeframe"""
        cfg = self.TIMEFRAMES[timeframe]
        period_start = self._get_period_start(timestamp, cfg["seconds"])
        
        current = self._current_candles[symbol].get(timeframe)
        
        # Check if we need to close the old candle first
        if current is not None and current.timestamp < period_start:
            # Close and store the old candle
            closed = self._close_candle(symbol, timeframe, timestamp)
            if closed:
                self._data[symbol][timeframe].append(closed)
                self._push_to_higher(symbol, timeframe, closed)
        
        # Get current candle (will be None or the one we just closed)
        current = self._current_candles[symbol].get(timeframe)
        
        # Create new candle if none exists
        if current is None or current.timestamp != period_start:
            new_candle = Candle(
                symbol=symbol,
                timeframe=timeframe,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=size,
                timestamp=period_start,
                tick_count=1
            )
            self._current_candles[symbol][timeframe] = new_candle
            return new_candle
        
        # Update existing candle
        current.high = max(current.high, price)
        current.low = min(current.low, price)
        current.close = price
        current.volume += size
        current.tick_count += 1
        
        return current
    
    def _get_period_start(self, timestamp: datetime, seconds: int) -> datetime:
        """Calculate the start of the period for a given timestamp"""
        epoch = datetime(1970, 1, 1)
        period_num = int(timestamp.timestamp() / seconds)
        period_start = epoch.fromtimestamp(period_num * seconds)
        return period_start
    
    def _aggregate_candles(self, symbol: str, timestamp: datetime):
        """Aggregate completed candles to higher timeframes"""
        # Check 1min candle
        if self._should_close(symbol, "1min", timestamp):
            closed = self._close_candle(symbol, "1min", timestamp)
            if closed:
                self._data[symbol]["1min"].append(closed)
                self._push_to_higher(symbol, "1min", closed)
        
        # Check 5min candle
        if self._should_close(symbol, "5min", timestamp):
            closed = self._close_candle(symbol, "5min", timestamp)
            if closed:
                self._data[symbol]["5min"].append(closed)
                self._push_to_higher(symbol, "5min", closed)
        
        # Check 15min candle
        if self._should_close(symbol, "15min", timestamp):
            closed = self._close_candle(symbol, "15min", timestamp)
            if closed:
                self._data[symbol]["15min"].append(closed)
                self._push_to_higher(symbol, "15min", closed)
        
        # Check 1hr candle
        if self._should_close(symbol, "1hr", timestamp):
            closed = self._close_candle(symbol, "1hr", timestamp)
            if closed:
                self._data[symbol]["1hr"].append(closed)
                self._push_to_higher(symbol, "1hr", closed)
        
        # Check 4hr candle
        if self._should_close(symbol, "4hr", timestamp):
            closed = self._close_candle(symbol, "4hr", timestamp)
            if closed:
                self._data[symbol]["4hr"].append(closed)
    
    def _should_close(self, symbol: str, timeframe: str, timestamp: datetime) -> bool:
        """Check if current candle should be closed"""
        cfg = self.TIMEFRAMES[timeframe]
        current = self._current_candles[symbol].get(timeframe)
        
        if current is None:
            return False
        
        period_start = self._get_period_start(timestamp, cfg["seconds"])
        
        # Close if we're in a new period
        return period_start > current.timestamp
    
    def _close_candle(self, symbol: str, timeframe: str, timestamp: datetime) -> Optional[Candle]:
        """Close and return the completed candle"""
        current = self._current_candles[symbol].get(timeframe)
        
        if current is None:
            return None
        
        # Create closed version
        closed = Candle(
            symbol=current.symbol,
            timeframe=current.timeframe,
            open=current.open,
            high=current.high,
            low=current.low,
            close=current.close,
            volume=current.volume,
            timestamp=current.timestamp,
            tick_count=current.tick_count
        )
        
        # Reset current candle for new period
        cfg = self.TIMEFRAMES[timeframe]
        new_period = self._get_period_start(timestamp, cfg["seconds"])
        self._current_candles[symbol][timeframe] = Candle(
            symbol=symbol,
            timeframe=timeframe,
            open=closed.close,  # Open at previous close
            high=closed.close,
            low=closed.close,
            close=closed.close,
            volume=0,
            timestamp=new_period,
            tick_count=0
        )
        
        return closed
    
    def _push_to_higher(self, symbol: str, source_tf: str, candle: Candle):
        """Push closed candle to higher timeframe"""
        aggregations = self.AGGREGATION_MAP.get(source_tf, [])
        
        for target_tf, count in aggregations:
            if target_tf not in self.TIMEFRAMES:
                continue
            
            # Add tick to the higher timeframe
            self._update_candle(symbol, target_tf, candle.close, candle.volume, candle.timestamp)
            
            # Check if we have enough source candles to close target
            target_cfg = self.TIMEFRAMES[target_tf]
            target = self._current_candles[symbol].get(target_tf)
            
            if target and target.tick_count >= count:
                # Close the target candle
                closed = self._close_candle(symbol, target_tf, candle.timestamp)
                if closed:
                    self._data[symbol][target_tf].append(closed)
    
    # Public API
    
    def get_candles(self, symbol: str, timeframe: str, count: int = None) -> List[Candle]:
        """Get candles for a symbol and timeframe"""
        if symbol not in self._data or timeframe not in self._data[symbol]:
            return []
        
        candles = list(self._data[symbol][timeframe])
        
        if count:
            return candles[-count:]
        return candles
    
    def get_current_candle(self, symbol: str, timeframe: str) -> Optional[Candle]:
        """Get the currently building candle"""
        return self._current_candles.get(symbol, {}).get(timeframe)
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a symbol"""
        ticks = list(self._raw_ticks.get(symbol, []))
        if ticks:
            return ticks[-1].price
        return None
    
    def get_summary(self, symbol: str) -> Dict[str, Any]:
        """Get summary of stored data for a symbol"""
        if symbol not in self._data:
            return {}
        
        summary = {
            "symbol": symbol,
            "ticker_count": len(self.tickers),
            "candles": {}
        }
        
        for tf in self.TIMEFRAMES:
            candles = self._data[symbol][tf]
            current = self._current_candles[symbol].get(tf)
            
            summary["candles"][tf] = {
                "stored": len(candles),
                "building": current.to_dict() if current else None
            }
        
        return summary
    
    def get_multi_timeframe_view(self, symbol: str) -> Dict[str, Any]:
        """Get view of all timeframes for analysis"""
        if symbol not in self._data:
            return {}
        
        view = {
            "symbol": symbol,
            "latest_price": self.get_latest_price(symbol),
            "timeframes": {}
        }
        
        for tf in self.TIMEFRAMES:
            candles = list(self._data[symbol][tf])
            current = self._current_candles[symbol].get(tf)
            
            # Get last few candles for pattern analysis
            recent = candles[-10:] if len(candles) >= 10 else candles
            if current:
                recent = recent + [current]
            
            view["timeframes"][tf] = {
                "candles": [c.to_dict() for c in recent],
                "current": current.to_dict() if current else None,
                "count": len(candles)
            }
        
        return view
    
    def get_alignment_score(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate alignment score across timeframes.
        
        Returns:
            Dict with:
            - score: 0-100 alignment percentage
            - direction: "up", "down", or "neutral"
            - timeframes: analysis per timeframe
        """
        if symbol not in self._data:
            return {"score": 0, "direction": "neutral", "timeframes": {}}
        
        directions = []
        analysis = {}
        
        for tf in ["1hr", "4hr", "15min", "5min"]:
            candles = list(self._data[symbol][tf])
            if len(candles) < 2:
                analysis[tf] = {"direction": "unknown", "score": 0}
                continue
            
            # Check if price is trending in this timeframe
            recent = candles[-5:] if len(candles) >= 5 else candles
            
            if len(recent) < 2:
                analysis[tf] = {"direction": "unknown", "score": 0}
                continue
            
            # Simple trend: compare recent closes
            closes = [c.close for c in recent]
            first, last = closes[0], closes[-1]
            pct_change = (last - first) / first * 100 if first > 0 else 0
            
            if pct_change > 0.5:
                direction = "up"
                tf_score = min(100, pct_change * 10)
            elif pct_change < -0.5:
                direction = "down"
                tf_score = min(100, abs(pct_change) * 10)
            else:
                direction = "neutral"
                tf_score = 50
            
            directions.append(direction)
            analysis[tf] = {
                "direction": direction,
                "pct_change": pct_change,
                "score": tf_score,
                "last_close": last,
                "candle_count": len(recent)
            }
        
        # Calculate alignment
        if not directions:
            return {"score": 0, "direction": "neutral", "timeframes": analysis}
        
        # Count aligned directions
        up_count = directions.count("up")
        down_count = directions.count("down")
        neutral_count = directions.count("neutral")
        
        if up_count >= down_count and up_count > neutral_count:
            overall = "up"
            score = int((up_count / len(directions)) * 100)
        elif down_count > up_count and down_count > neutral_count:
            overall = "down"
            score = int((down_count / len(directions)) * 100)
        else:
            overall = "neutral"
            score = 50
        
        return {
            "score": score,
            "direction": overall,
            "timeframes": analysis,
            "alignment": {
                "up": up_count,
                "down": down_count,
                "neutral": neutral_count
            }
        }


# Simple test
if __name__ == "__main__":
    engine = MultiTimeframeEngine(["AAPL", "TSLA"])
    
    # Simulate some ticks
    base_time = datetime.now()
    
    print("Adding simulated ticks...")
    for i in range(100):
        for symbol in ["AAPL", "TSLA"]:
            price = 277.50 + (i * 0.01) + (hash(symbol) % 100) * 0.001
            size = 100 + (i * 10)
            timestamp = base_time + timedelta(seconds=i * 5)
            
            engine.add_tick(symbol, price, size, timestamp)
    
    # Get summary
    for symbol in ["AAPL", "TSLA"]:
        print(f"\n{'='*50}")
        print(f"Symbol: {symbol}")
        print(f"{'='*50}")
        
        summary = engine.get_summary(symbol)
        print(f"\nCandles stored:")
        for tf, data in summary.get("candles", {}).items():
            print(f"  {tf}: {data['stored']} closed, building={data['building'] is not None}")
        
        alignment = engine.get_alignment_score(symbol)
        print(f"\nAlignment: {alignment['direction']} (score: {alignment['score']}%)")
        
        # Show latest candle for each timeframe
        print(f"\nLatest candles:")
        for tf in ["1min", "5min", "15min", "1hr"]:
            candles = engine.get_candles(symbol, tf, count=1)
            if candles:
                c = candles[-1]
                print(f"  {tf}: O=${c.open:.2f} H=${c.high:.2f} L=${c.low:.2f} C=${c.close:.2f} Vol={c.volume}")
