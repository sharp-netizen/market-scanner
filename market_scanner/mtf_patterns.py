#!/usr/bin/env python3
"""
Multi-Timeframe Pattern Analyzer

Analyzes patterns across multiple timeframes and generates aligned signals.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from multi_timeframe_engine import Candle, MultiTimeframeEngine


@dataclass
class MultiTimeframeAlert:
    """Alert with multi-timeframe context"""
    symbol: str
    pattern_name: str
    score: int  # 0-100 confidence
    direction: str  # "up", "down", "neutral"
    message: str
    timeframes: Dict[str, Dict] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "pattern": self.pattern_name,
            "score": self.score,
            "direction": self.direction,
            "message": self.message,
            "timeframes": self.timeframes,
            "timestamp": self.timestamp.isoformat()
        }


class MultiTimeframeAnalyzer:
    """
    Analyzes patterns across multiple timeframes.
    
    Generates alerts when:
    - Multiple timeframes align in the same direction
    - Specific patterns trigger on higher timeframes
    - Smart money accumulation detected
    """
    
    def __init__(self, engine: MultiTimeframeEngine, config: Dict = None):
        self.engine = engine
        self.config = config or {}
        
        # Pattern thresholds
        self.trend_threshold = self.config.get("trend_threshold", 0.5)  # % change
        self.alignment_threshold = self.config.get("alignment_threshold", 60)  # % aligned
        self.volume_surge_threshold = self.config.get("volume_surge_threshold", 3.0)
        
        print(f"[MTFAnalyzer] Initialized")
    
    def analyze_symbol(self, symbol: str) -> List[MultiTimeframeAlert]:
        """
        Analyze a symbol across all timeframes.
        
        Returns:
            List of alerts (may be empty if no signals)
        """
        alerts = []
        
        # Get alignment analysis
        alignment = self.engine.get_alignment_score(symbol)
        
        # Generate aligned signal if all timeframes agree
        aligned_alert = self._check_alignment(symbol, alignment)
        if aligned_alert:
            alerts.append(aligned_alert)
        
        # Check for smart money accumulation (volume + price)
        sm_alert = self._check_smart_money(symbol)
        if sm_alert:
            alerts.append(sm_alert)
        
        # Check for higher timeframe trends
        ht_alert = self._check_higher_timeframe_trend(symbol)
        if ht_alert:
            alerts.append(ht_alert)
        
        return alerts
    
    def _check_alignment(self, symbol: str, alignment: Dict) -> Optional[MultiTimeframeAlert]:
        """Check if all timeframes are aligned"""
        score = alignment.get("score", 0)
        direction = alignment.get("direction", "neutral")
        
        if score >= self.alignment_threshold and direction != "neutral":
            timeframes = alignment.get("timeframes", {})
            
            # Build message
            tf_details = []
            for tf, data in timeframes.items():
                if data.get("direction") == direction:
                    tf_details.append(f"{tf}({data['direction']}:{data['pct_change']:.2f}%)")
            
            message = f"🎯 MULTI-TIMEFRAME ALIGNMENT: {direction.upper()}"
            message += f"\n  {' | '.join(tf_details)}"
            message += f"\n  Confidence: {score}%"
            
            return MultiTimeframeAlert(
                symbol=symbol,
                pattern_name="multi_timeframe_alignment",
                score=score,
                direction=direction,
                message=message,
                timeframes=timeframes
            )
        
        return None
    
    def _check_smart_money(self, symbol: str) -> Optional[MultiTimeframeAlert]:
        """Check for smart money accumulation (high volume + price up)"""
        candles = self.engine.get_candles(symbol, "15min", count=10)
        
        if len(candles) < 2:
            return None
        
        # Check for volume surge + price increase
        recent = candles[-1]
        previous = candles[-2]
        
        # Calculate volume surge
        vol_avg = sum(c.volume for c in candles[:-1]) / len(candles[:-1])
        vol_surge = recent.volume / vol_avg if vol_avg > 0 else 0
        
        # Calculate price change
        price_change = (recent.close - previous.close) / previous.close * 100
        
        # Check for accumulation (up + high volume)
        if vol_surge >= self.volume_surge_threshold and price_change > 0:
            timeframes = {}
            for tf in ["15min", "5min", "1min"]:
                c = self.engine.get_candles(symbol, tf, count=3)
                if len(c) >= 2:
                    tf_vol = c[-1].volume / (sum(x.volume for x in c[:-1]) / len(c[:-1])) if len(c) > 1 else 1
                    tf_change = (c[-1].close - c[-2].close) / c[-2].close * 100 if len(c) > 1 else 0
                    timeframes[tf] = {
                        "volume_surge": tf_vol,
                        "price_change": tf_change,
                        "direction": "up" if tf_change > 0 else "down"
                    }
            
            message = f"📈 SMART MONEY ACCUMULATION"
            message += f"\n  Volume: {vol_surge:.1f}x average"
            message += f"\n  Price: +{price_change:.2f}%"
            message += f"\n  Confidence: {min(100, int(vol_surge * 20))}%"
            
            return MultiTimeframeAlert(
                symbol=symbol,
                pattern_name="smart_money_accumulation",
                score=min(100, int(vol_surge * 20)),
                direction="up",
                message=message,
                timeframes=timeframes
            )
        
        # Check for distribution (down + high volume)
        if vol_surge >= self.volume_surge_threshold and price_change < -0.2:
            message = f"📉 SMART MONEY DISTRIBUTION"
            message += f"\n  Volume: {vol_surge:.1f}x average"
            message += f"\n  Price: {price_change:.2f}%"
            message += f"\n  Confidence: {min(100, int(vol_surge * 20))}%"
            
            return MultiTimeframeAlert(
                symbol=symbol,
                pattern_name="smart_money_distribution",
                score=min(100, int(vol_surge * 20)),
                direction="down",
                message=message,
                timeframes={}
            )
        
        return None
    
    def _check_higher_timeframe_trend(self, symbol: str) -> Optional[MultiTimeframeAlert]:
        """Check for trend on higher timeframes (4hr, 1hr)"""
        alerts = []
        
        # Check 4hr timeframe
        candles_4h = self.engine.get_candles(symbol, "4hr", count=5)
        if len(candles_4h) >= 2:
            alert = self._check_tf_trend(symbol, "4hr", candles_4h)
            if alert:
                alerts.append(alert)
        
        # Check 1hr timeframe
        candles_1h = self.engine.get_candles(symbol, "1hr", count=10)
        if len(candles_1h) >= 2:
            alert = self._check_tf_trend(symbol, "1hr", candles_1h)
            if alert:
                alerts.append(alert)
        
        # Return the strongest signal
        if alerts:
            return max(alerts, key=lambda x: x.score)
        
        return None
    
    def _check_tf_trend(self, symbol: str, timeframe: str, candles: List[Candle]) -> Optional[MultiTimeframeAlert]:
        """Check for trend in a specific timeframe"""
        if len(candles) < 2:
            return None
        
        closes = [c.close for c in candles]
        pct_change = (closes[-1] - closes[0]) / closes[0] * 100
        
        if pct_change > 1:  # Strong up trend
            last_candle = candles[-1]
            message = f"📊 {timeframe.upper()} TREND: UP"
            message += f"\n  Change: +{pct_change:.2f}%"
            message += f"\n  Current: ${last_candle.close:.2f}"
            
            return MultiTimeframeAlert(
                symbol=symbol,
                pattern_name=f"{timeframe}_trend_up",
                score=min(100, int(pct_change * 10)),
                direction="up",
                message=message,
                timeframes={timeframe: {
                    "pct_change": pct_change,
                    "direction": "up",
                    "candle_count": len(candles)
                }}
            )
        
        elif pct_change < -1:  # Strong down trend
            last_candle = candles[-1]
            message = f"📊 {timeframe.upper()} TREND: DOWN"
            message += f"\n  Change: {pct_change:.2f}%"
            message += f"\n  Current: ${last_candle.close:.2f}"
            
            return MultiTimeframeAlert(
                symbol=symbol,
                pattern_name=f"{timeframe}_trend_down",
                score=min(100, int(abs(pct_change) * 10)),
                direction="down",
                message=message,
                timeframes={timeframe: {
                    "pct_change": pct_change,
                    "direction": "down",
                    "candle_count": len(candles)
                }}
            )
        
        return None
    
    def analyze_all(self, symbols: List[str] = None) -> Dict[str, List[MultiTimeframeAlert]]:
        """
        Analyze all symbols and return alerts grouped by symbol.
        
        Args:
            symbols: List of symbols to analyze (defaults to all in engine)
        
        Returns:
            Dict mapping symbol -> list of alerts
        """
        if symbols is None:
            symbols = self.engine.tickers
        
        results = {}
        
        for symbol in symbols:
            alerts = self.analyze_symbol(symbol)
            if alerts:
                results[symbol] = alerts
        
        return results


# Simple test
if __name__ == "__main__":
    from multi_timeframe_engine import MultiTimeframeEngine
    
    # Create engine and analyzer
    engine = MultiTimeframeEngine(["AAPL", "TSLA"])
    analyzer = MultiTimeframeAnalyzer(engine)
    
    # Simulate ticks
    base_time = datetime.now()
    
    print("Adding simulated ticks...")
    for i in range(300):  # 25 minutes of data
        for symbol in ["AAPL", "TSLA"]:
            # Simulate upward trend with volume
            trend = i * 0.005
            noise = (hash(f"{symbol}{i}") % 100) * 0.0001
            price = 277.50 + trend + noise
            size = 100 + (i * 5) + (hash(symbol) % 50) * 10
            timestamp = base_time + timedelta(seconds=i * 5)
            
            engine.add_tick(symbol, price, size, timestamp)
    
    print("\n" + "="*60)
    print("MULTI-TIMEFRAME ANALYSIS RESULTS")
    print("="*60)
    
    # Analyze all symbols
    results = analyzer.analyze_all()
    
    for symbol, alerts in results.items():
        print(f"\n📊 {symbol}")
        print("-" * 40)
        
        for alert in alerts:
            print(f"\n{alert.pattern_name}: {alert.direction} (score: {alert.score})")
            print(alert.message)
    
    # Show alignment for all symbols
    print("\n" + "="*60)
    print("ALIGNMENT SUMMARY")
    print("="*60)
    
    for symbol in ["AAPL", "TSLA"]:
        alignment = engine.get_alignment_score(symbol)
        print(f"\n{symbol}:")
        print(f"  Direction: {alignment['direction']}")
        print(f"  Score: {alignment['score']}%")
        print(f"  Alignment: {alignment.get('alignment', {})}")
