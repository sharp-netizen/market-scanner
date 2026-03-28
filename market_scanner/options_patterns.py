"""
Options Patterns - Detect unusual options activity

Patterns:
- Unusual Volume (large purchases)
- Sweeps (aggressive buying)
- Call/Put Sentiment
- Large Premium Orders (whale activity)
- Unusual Activity Score
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import statistics


class AlertSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class OptionAlert:
    """Alert from options patterns"""
    ticker: str
    pattern_name: str
    severity: AlertSeverity
    value: float
    threshold: float
    message: str
    timestamp: datetime = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        return {
            "ticker": self.ticker,
            "pattern": self.pattern_name,
            "severity": self.severity.name,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class BaseOptionPattern(ABC):
    """Base class for options patterns"""
    
    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
    
    @abstractmethod
    def analyze(self, option_data: Dict) -> List[OptionAlert]:
        pass
    
    def get_min_required(self) -> int:
        return 2


class UnusualVolumePattern(BaseOptionPattern):
    """Detect unusual volume spikes in options"""
    
    def __init__(self, config: Dict = None):
        super().__init__("UnusualVolume", config)
        self.multiplier = self.config.get("multiplier", 5.0)  # 5x average = unusual
        self.size_threshold = self.config.get("size_threshold", 100)  # Min contracts
        self._history: Dict[str, List[int]] = {}  # Ticker -> sizes
    
    def analyze(self, option: Dict) -> List[OptionAlert]:
        alerts = []
        ticker = option.get("Ticker", "")
        size = option.get("Size", 0)
        
        if size < self.size_threshold:
            return alerts
        
        # Track history
        if ticker not in self._history:
            self._history[ticker] = []
        self._history[ticker].append(size)
        
        # Keep last 100
        if len(self._history[ticker]) > 100:
            self._history[ticker] = self._history[ticker][-100:]
        
        # Check if unusual
        if len(self._history[ticker]) >= 10:
            avg = statistics.mean(self._history[ticker][:-1])
            if size > avg * self.multiplier:
                alerts.append(OptionAlert(
                    ticker=ticker,
                    pattern_name=self.name,
                    severity=AlertSeverity.HIGH,
                    value=size / avg if avg else 0,
                    threshold=self.multiplier,
                    message=f"📊 {ticker}: Unusual volume {size} contracts "
                           f"({size/avg:.1f}x average)",
                    metadata={
                        "size": size,
                        "average": avg,
                        "multiplier": size/avg,
                        "strike": option.get("Strike"),
                        "expiration": option.get("Expiration"),
                        "type": option.get("Type"),
                        "premium": option.get("Price", 0) * size * 100
                    }
                ))
        
        return alerts


class SweepPattern(BaseOptionPattern):
    """Detect sweep orders (aggressive large purchases)"""
    
    def __init__(self, config: Dict = None):
        super().__init__("Sweep", config)
        self.sweep_threshold = self.config.get("sweep_threshold", 500)  # 500+ contracts
        self._sweep_count: Dict[str, int] = {}
    
    def analyze(self, option: Dict) -> List[OptionAlert]:
        alerts = []
        ticker = option.get("Ticker", "")
        size = option.get("Size", 0)
        
        if size >= self.sweep_threshold:
            alerts.append(OptionAlert(
                ticker=ticker,
                pattern_name=self.name,
                severity=AlertSeverity.CRITICAL,
                value=size,
                threshold=self.sweep_threshold,
                message=f"🔔 {ticker}: SWEEP DETECTED! {size} contracts "
                       f"{option.get('Type', '').upper()} ${option.get('Strike')}",
                metadata={
                    "size": size,
                    "strike": option.get("Strike"),
                    "expiration": option.get("Expiration"),
                    "type": option.get("Type"),
                    "premium": option.get("Price", 0) * size * 100,
                    "exchange": option.get("Exchange")
                }
            ))
        
        return alerts


class WhalePattern(BaseOptionPattern):
    """Detect whale activity (large premium orders)"""
    
    def __init__(self, config: Dict = None):
        super().__init__("Whale", config)
        self.premium_threshold = self.config.get("premium_threshold", 100000)  # $100K+
    
    def analyze(self, option: Dict) -> List[OptionAlert]:
        alerts = []
        
        price = option.get("Price", 0)
        size = option.get("Size", 0)
        premium = price * size * 100
        
        if premium >= self.premium_threshold:
            ticker = option.get("Ticker", "")
            alerts.append(OptionAlert(
                ticker=ticker,
                pattern_name=self.name,
                severity=AlertSeverity.HIGH,
                value=premium,
                threshold=self.premium_threshold,
                message=f"🐋 {ticker}: WHALE ALERT! ${premium/1000:.1f}K premium "
                       f"{option.get('Type', '').upper()} ${option.get('Strike')}",
                metadata={
                    "premium": premium,
                    "strike": option.get("Strike"),
                    "expiration": option.get("Expiration"),
                    "type": option.get("Type"),
                    "size": size,
                    "price": price
                }
            ))
        
        return alerts


class CallPutRatioPattern(BaseOptionPattern):
    """Analyze call/put ratio sentiment"""
    
    def __init__(self, config: Dict = None):
        super().__init__("CallPutRatio", config)
        self.call_threshold = self.config.get("call_threshold", 2.0)  # 2:1 ratio
        self.put_threshold = self.config.get("put_threshold", 2.0)
        self._ticker_stats: Dict[str, Dict] = {}
    
    def analyze(self, option: Dict) -> List[OptionAlert]:
        alerts = []
        ticker = option.get("Ticker", "")
        option_type = option.get("Type", "").lower()
        size = option.get("Size", 0)
        
        # Track stats
        if ticker not in self._ticker_stats:
            self._ticker_stats[ticker] = {"calls": 0, "puts": 0, "total_premium": 0}
        
        stats = self._ticker_stats[ticker]
        if option_type == "call":
            stats["calls"] += size
        elif option_type == "put":
            stats["puts"] += size
        
        stats["total_premium"] += option.get("Price", 0) * size * 100
        
        # Only alert every 20 trades
        total = stats["calls"] + stats["puts"]
        if total % 20 != 0:
            return alerts
        
        # Check ratios
        if stats["puts"] > 0:
            ratio = stats["calls"] / stats["puts"]
            if ratio >= self.call_threshold:
                alerts.append(OptionAlert(
                    ticker=ticker,
                    pattern_name=self.name,
                    severity=AlertSeverity.MEDIUM,
                    value=ratio,
                    threshold=self.call_threshold,
                    message=f"📈 {ticker}: BULLISH! Call/Put ratio {ratio:.1f}:1",
                    metadata=dict(stats)
                ))
            elif ratio <= 1 / self.put_threshold:
                alerts.append(OptionAlert(
                    ticker=ticker,
                    pattern_name=self.name,
                    severity=AlertSeverity.MEDIUM,
                    value=ratio,
                    threshold=1 / self.put_threshold,
                    message=f"📉 {ticker}: BEARISH! Call/Put ratio {ratio:.1f}:1",
                    metadata=dict(stats)
                ))
        
        return alerts


class OptionsPatternManager:
    """Manage multiple options patterns"""
    
    def __init__(self):
        self._patterns: List[BaseOptionPattern] = []
        self.register(UnusualVolumePattern({"enabled": True, "multiplier": 5.0, "size_threshold": 100}))
        self.register(SweepPattern({"enabled": True, "sweep_threshold": 500}))
        self.register(WhalePattern({"enabled": True, "premium_threshold": 100000}))
        self.register(CallPutRatioPattern({"enabled": True, "call_threshold": 2.0, "put_threshold": 2.0}))
    
    def register(self, pattern: BaseOptionPattern) -> None:
        self._patterns.append(pattern)
    
    def analyze(self, option_data: Dict) -> List[OptionAlert]:
        alerts = []
        for pattern in self._patterns:
            if pattern.enabled:
                alerts.extend(pattern.analyze(option_data))
        return alerts
    
    def get_enabled(self) -> List[str]:
        return [p.name for p in self._patterns if p.enabled]


# Example usage
async def example():
    from quiverquant import QuiverQuantProvider
    
    print("=== Options Patterns Demo ===\n")
    
    # Create pattern manager
    manager = OptionsPatternManager()
    print(f"Enabled patterns: {manager.get_enabled()}\n")
    
    # Sample options data
    sample_options = [
        {"Ticker": "AAPL", "Size": 100, "Price": 5.50, "Strike": 180, "Expiration": "2024-01-19", "Type": "call", "Exchange": "NYSE"},
        {"Ticker": "AAPL", "Size": 1000, "Price": 5.50, "Strike": 180, "Expiration": "2024-01-19", "Type": "call", "Exchange": "NYSE"},
        {"Ticker": "TSLA", "Size": 50, "Price": 250, "Strike": 250, "Expiration": "2024-01-19", "Type": "put", "Exchange": "CBOE"},
        {"Ticker": "AAPL", "Size": 5000, "Price": 3.25, "Strike": 185, "Expiration": "2024-01-19", "Type": "put", "Exchange": "NYSE"},
    ]
    
    print("=== Analyzing Sample Options ===")
    for option in sample_options:
        alerts = manager.analyze(option)
        for alert in alerts:
            print(f"  {alert.message}")
    
    # Connect to QuiverQuant for real data
    print("\n=== Real Data ===")
    provider = QuiverQuantProvider(
        config={"tickers": ["AAPL", "TSLA"]},
        callback=lambda o: print(f"  {o.ticker}: {o.size} {o.option_type} @ ${o.strike}")
    )
    
    await provider.connect()
    await provider.subscribe(["AAPL", "TSLA"])
    
    # Get sentiment
    sentiment = await provider.analyze_sentiment("AAPL")
    print(f"\nAAPL Sentiment:")
    print(f"  Call/Put Ratio: {sentiment['call_put_ratio']:.2f}")
    
    await provider.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example())
