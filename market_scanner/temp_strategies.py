"""
100+ Trading Strategies Module
Comprehensive collection of technical analysis, price action, and momentum strategies
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import math


# ============================================================================
# ALERT CLASSES
# ============================================================================

class AlertSeverity:
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class StrategyAlert:
    symbol: str
    strategy_name: str
    severity: int
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


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def sma(data: np.ndarray, period: int) -> float:
    """Simple Moving Average"""
    if len(data) < period:
        return data[-1] if len(data) > 0 else 0
    return np.mean(data[-period:])

def ema(data: np.ndarray, period: int) -> float:
    """Exponential Moving Average"""
    if len(data) < period:
        return data[-1] if len(data) > 0 else 0
    multiplier = 2 / (period + 1)
    ema_val = np.mean(data[:period])
    for price in data[period:]:
        ema_val = (price - ema_val) * multiplier + ema_val
    return ema_val

def rsi(data: np.ndarray, period: int = 14) -> float:
    """Relative Strength Index"""
    if len(data) < period + 1:
        return 50
    deltas = np.diff(data)
    gains = np.maximum(deltas, 0)
    losses = np.maximum(-deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
    """MACD - returns (macd_line, signal_line, histogram)"""
    if len(data) < slow:
        return (0, 0, 0)
    fast_ema = ema(data, fast)
    slow_ema = ema(data, slow)
    macd_line = fast_ema - slow_ema
    # Simplified signal line
    signal_line = macd_line * 0.9  # Approximation
    histogram = macd_line - signal_line
    return (macd_line, signal_line, histogram)

def bollinger_bands(data: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
    """Bollinger Bands - returns (upper, middle, lower)"""
    if len(data) < period:
        middle = data[-1] if len(data) > 0 else 0
        return (middle, middle, middle)
    middle = sma(data, period)
    std = np.std(data[-period:])
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    return (upper, middle, lower)

def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
    """Average True Range"""
    if len(high) < period + 1:
        return (high[-1] - low[-1]) if len(high) > 0 else 0
    tr1 = high[1:] - low[1:]
    tr2 = np.abs(high[1:] - close[:-1])
    tr3 = np.abs(low[1:] - close[:-1])
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    return np.mean(tr[-period:])

def stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> Tuple[float, float]:
    """Stochastic Oscillator - returns (%K, %D)"""
    if len(high) < period:
        return (50, 50)
    highest = np.max(high[-period:])
    lowest = np.min(low[-period:])
    if highest == lowest:
        return (50, 50)
    k = ((close[-1] - lowest) / (highest - lowest)) * 100
    d = k * 0.85  # Simplified
    return (k, d)

def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
    """Average Directional Index"""
    if len(high) < period + 1:
        return 0
    plus_dm = np.maximum(high[1:] - high[:-1], 0)
    minus_dm = np.maximum(low[:-1] - low[1:], 0)
    plus_dm = np.where(plus_dm > minus_dm, plus_dm, 0)
    minus_dm = np.where(minus_dm > plus_dm, minus_dm, 0)
    tr = atr(high, low, close, period) * period
    if tr == 0:
        return 0
    plus_di = (np.sum(plus_dm[-period:]) / tr) * 100
    minus_di = (np.sum(minus_dm[-period:]) / tr) * 100
    if plus_di + minus_di == 0:
        return 0
    dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
    return dx

def cci(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 20) -> float:
    """Commodity Channel Index"""
    if len(high) < period:
        return 0
    tp = (high + low + close) / 3
    sma_tp = sma(tp, period)
    mad = np.mean(np.abs(tp[-period:] - sma_tp))
    if mad == 0:
        return 0
    cci_val = (tp[-1] - sma_tp) / (0.015 * mad)
    return cci_val

def williams_r(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
    """Williams %R"""
    if len(high) < period:
        return -50
    highest = np.max(high[-period:])
    lowest = np.min(low[-period:])
    if highest == lowest:
        return -50
    wr = ((highest - close[-1]) / (highest - lowest)) * -100
    return wr

def obv(close: np.ndarray, volume: np.ndarray) -> float:
    """On-Balance Volume"""
    if len(close) < 2:
        return volume[-1] if len(volume) > 0 else 0
    obv_val = 0
    for i in range(1, len(close)):
        if close[i] > close[i-1]:
            obv_val += volume[i]
        elif close[i] < close[i-1]:
            obv_val -= volume[i]
    return obv_val

def vwap(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> float:
    """Volume Weighted Average Price"""
    if len(high) < 1:
        return 0
    tp = (high + low + close) / 3
    return np.sum(tp * volume) / np.sum(volume) if np.sum(volume) > 0 else tp[-1]

def pivot_points(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict[str, float]:
    """Calculate pivot points and support/resistance levels"""
    if len(high) < 1:
        return {}
    pivot = (high[-1] + low[-1] + close[-1]) / 3
    r1 = 2 * pivot - low[-1]
    r2 = pivot + (high[-1] - low[-1])
    r3 = high[-1] + 2 * (pivot - low[-1])
    s1 = 2 * pivot - high[-1]
    s2 = pivot - (high[-1] - low[-1])
    s3 = low[-1] - 2 * (high[-1] - pivot)
    return {"pivot": pivot, "r1": r1, "r2": r2, "r3": r3, "s1": s1, "s2": s2, "s3": s3}

def fibonacci_retracement(high: float, low: float) -> Dict[str, float]:
    """Calculate Fibonacci retracement levels"""
    diff = high - low
    return {
        "0.0": high,
        "0.236": high - 0.236 * diff,
        "0.382": high - 0.382 * diff,
        "0.5": high - 0.5 * diff,
        "0.618": high - 0.618 * diff,
        "0.786": high - 0.786 * diff,
        "1.0": low
    }


# ============================================================================
# BASE STRATEGY CLASS
# ============================================================================

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.threshold = self.config.get("threshold", 0)
        self.cooldown = self.config.get("cooldown", 300)
        self._last_alert_time = {}
    
    def can_alert(self, symbol: str) -> bool:
        """Check if cooldown has passed"""
        import time
        key = f"{self.name}_{symbol}"
        if key in self._last_alert_time:
            if time.time() - self._last_alert_time[key] < self.cooldown:
                return False
        return True
    
    def record_alert(self, symbol: str):
        """Record alert time"""
        import time
        self._last_alert_time[f"{self.name}_{symbol}"] = time.time()
    
    @abstractmethod
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        """Analyze data and return alert if strategy triggers"""
        pass
    
    def get_required_fields(self) -> List[str]:
        """Return required data fields"""
        return ["close"]


# ============================================================================
# 100+ STRATEGIES
# ============================================================================

class SmaCrossoverStrategy(BaseStrategy):
    """SMA Crossover - Fast SMA crosses above Slow SMA"""
    def __init__(self, config=None):
        super().__init__("SMA_Crossover", config)
        self.fast_period = self.config.get("fast_period", 10)
        self.slow_period = self.config.get("slow_period", 30)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.slow_period + 5:
            return None
        fast_sma = sma(close, self.fast_period)
        slow_sma = sma(close, self.slow_period)
        prev_fast = sma(close[:-1], self.fast_period)
        prev_slow = sma(close[:-1], self.slow_period)
        if prev_fast <= prev_slow and fast_sma > slow_sma:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, fast_sma - slow_sma, 0,
                f"📈 {symbol}: SMA {self.fast_period}/{self.slow_period} GOLDEN CROSS", {"fast_sma": fast_sma, "slow_sma": slow_sma})
        elif prev_fast >= prev_slow and fast_sma < slow_sma:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, slow_sma - fast_sma, 0,
                f"📉 {symbol}: SMA {self.fast_period}/{self.slow_period} DEATH CROSS", {"fast_sma": fast_sma, "slow_sma": slow_sma})
        return None

class EmaCrossoverStrategy(BaseStrategy):
    """EMA Crossover Strategy"""
    def __init__(self, config=None):
        super().__init__("EMA_Crossover", config)
        self.fast_period = self.config.get("fast_period", 12)
        self.slow_period = self.config.get("slow_period", 26)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.slow_period + 5:
            return None
        fast_ema = ema(close, self.fast_period)
        slow_ema = ema(close, self.slow_period)
        if fast_ema > slow_ema:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, fast_ema/slow_ema - 1, 0,
                f"🚀 {symbol}: EMA Bullish Crossover", {"fast": fast_ema, "slow": slow_ema})
        return None

class RsiOverboughtStrategy(BaseStrategy):
    """RSI Overbought/Oversold Strategy"""
    def __init__(self, config=None):
        super().__init__("RSI_Oversold", config)
        self.period = self.config.get("period", 14)
        self.overbought = self.config.get("overbought", 70)
        self.oversold = self.config.get("oversold", 30)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.period + 5:
            return None
        rsi_val = rsi(close, self.period)
        if rsi_val < self.oversold:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, rsi_val, self.oversold,
                f"🔥 {symbol}: RSI Oversold ({rsi_val:.1f})", {"rsi": rsi_val})
        elif rsi_val > self.overbought:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, rsi_val, self.overbought,
                f"⚠️ {symbol}: RSI Overbought ({rsi_val:.1f})", {"rsi": rsi_val})
        return None

class MacdCrossoverStrategy(BaseStrategy):
    """MACD Crossover Strategy"""
    def __init__(self, config=None):
        super().__init__("MACD_Crossover", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 30:
            return None
        macd_line, signal, hist = macd(close)
        prev_hist = macd(close[:-1])[2]
        if prev_hist < 0 and hist > 0:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, hist, 0,
                f"� bullish MACD Cross", {"macd": macd_line, "signal": signal, "hist": hist})
        return None

class BollingerBandStrategy(BaseStrategy):
    """Bollinger Band Bounce/Breakout Strategy"""
    def __init__(self, config=None):
        super().__init__("Bollinger_Band", config)
        self.period = self.config.get("period", 20)
        self.std_dev = self.config.get("std_dev", 2.0)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.period + 5:
            return None
        upper, middle, lower = bollinger_bands(close, self.period, self.std_dev)
        price = close[-1]
        if price < lower:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, lower - price, 0,
                f"⬇️ {symbol}: Price below Lower BB", {"upper": upper, "middle": middle, "lower": lower, "price": price})
        elif price > upper:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, price - upper, 0,
                f"⬆️ {symbol}: Price above Upper BB", {"upper": upper, "middle": middle, "lower": lower, "price": price})
        return None

class VolumeSpikeStrategy(BaseStrategy):
    """Volume Spike Detection"""
    def __init__(self, config=None):
        super().__init__("Volume_Spike", config)
        self.multiplier = self.config.get("multiplier", 2.5)
        self.period = self.config.get("period", 20)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        volume = np.array(data.get("volume", []))
        if len(volume) < self.period + 5:
            return None
        avg_vol = np.mean(volume[-self.period:-1])
        current_vol = volume[-1]
        if current_vol > avg_vol * self.multiplier:
            self.record_alert(symbol)
            pct = (current_vol / avg_vol - 1) * 100
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, pct, self.multiplier * 100,
                f"📊 {symbol}: Volume Spike +{pct:.0f}%", {"volume": current_vol, "avg": avg_vol})
        return None

class PriceMomentumStrategy(BaseStrategy):
    """Price Momentum Strategy"""
    def __init__(self, config=None):
        super().__init__("Price_Momentum", config)
        self.period = self.config.get("period", 10)
        self.threshold_pct = self.config.get("threshold_pct", 5)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.period + 2:
            return None
        momentum = (close[-1] / close[-self.period] - 1) * 100
        if abs(momentum) > self.threshold_pct:
            self.record_alert(symbol)
            severity = AlertSeverity.HIGH if abs(momentum) > self.threshold_pct * 2 else AlertSeverity.MEDIUM
            direction = "🚀" if momentum > 0 else "📉"
            return StrategyAlert(symbol, self.name, severity, momentum, self.threshold_pct,
                f"{direction} {symbol}: Momentum {momentum:+.2f}%", {"momentum": momentum})
        return None

class StochasticCrossoverStrategy(BaseStrategy):
    """Stochastic Oscillator Crossover"""
    def __init__(self, config=None):
        super().__init__("Stochastic_Crossover", config)
        self.period = self.config.get("period", 14)
        self.overbought = self.config.get("overbought", 80)
        self.oversold = self.config.get("oversold", 20)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        close = np.array(data.get("close", []))
        if len(high) < self.period + 5:
            return None
        k, d = stochastic(high, low, close, self.period)
        prev_k, prev_d = stochastic(high[:-1], low[:-1], close[:-1], self.period)
        if prev_k < prev_d and k > d and k < self.oversold:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, k, self.oversold,
                f"🟢 {symbol}: Stochastic Bullish Cross (K={k:.1f}, D={d:.1f})", {"k": k, "d": d})
        return None

class AtrVolatilityStrategy(BaseStrategy):
    """ATR Volatility Strategy"""
    def __init__(self, config=None):
        super().__init__("ATR_Volatility", config)
        self.period = self.config.get("period", 14)
        self.multiplier = self.config.get("multiplier", 2.0)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        close = np.array(data.get("close", []))
        if len(high) < self.period + 5:
            return None
        atr_val = atr(high, low, close, self.period)
        atr_pct = (atr_val / close[-1]) * 100
        if atr_pct > self.multiplier:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, atr_pct, self.multiplier,
                f"🌊 {symbol}: High Volatility ATR {atr_pct:.2f}%", {"atr": atr_val, "atr_pct": atr_pct})
        return None

class AdxTrendStrengthStrategy(BaseStrategy):
    """ADX Trend Strength Strategy"""
    def __init__(self, config=None):
        super().__init__("ADX_Trend_Strength", config)
        self.period = self.config.get("period", 14)
        self.threshold = self.config.get("threshold", 25)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        close = np.array(data.get("close", []))
        if len(high) < self.period + 5:
            return None
        adx_val = adx(high, low, close, self.period)
        if adx_val > self.threshold:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, adx_val, self.threshold,
                f"💪 {symbol}: Strong Trend (ADX={adx_val:.1f})", {"adx": adx_val})
        return None

class CciStrategy(BaseStrategy):
    """Commodity Channel Index Strategy"""
    def __init__(self, config=None):
        super().__init__("CCI", config)
        self.period = self.config.get("period", 20)
        self.threshold = self.config.get("threshold", 100)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        close = np.array(data.get("close", []))
        if len(high) < self.period + 5:
            return None
        cci_val = cci(high, low, close, self.period)
        if abs(cci_val) > self.threshold:
            self.record_alert(symbol)
            direction = "Oversold" if cci_val < -self.threshold else "Overbought"
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, cci_val, self.threshold,
                f"📍 {symbol}: CCI {direction} ({cci_val:.0f})", {"cci": cci_val})
        return None

class WilliamsRStrategy(BaseStrategy):
    """Williams %R Strategy"""
    def __init__(self, config=None):
        super().__init__("Williams_R", config)
        self.period = self.config.get("period", 14)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        close = np.array(data.get("close", []))
        if len(high) < self.period + 5:
            return None
        wr = williams_r(high, low, close, self.period)
        if wr < -80:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, wr, -80,
                f"🔥 {symbol}: Williams %R Oversold ({wr:.0f})", {"wr": wr})
        elif wr > -20:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, wr, -20,
                f"⚠️ {symbol}: Williams %R Overbought ({wr:.0f})", {"wr": wr})
        return None

class ObvDivergenceStrategy(BaseStrategy):
    """OBV Divergence Strategy"""
    def __init__(self, config=None):
        super().__init__("OBV_Divergence", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        volume = np.array(data.get("volume", []))
        if len(close) < 20 or len(volume) < 20:
            return None
        obv_val = obv(close, volume)
        price_change = (close[-1] / close[-20] - 1) * 100
        obv_change = (obv_val / (obv_val - np.sum(np.diff(close[-20:]) * volume[-20:])) - 1) * 100 if obv_val != 0 else 0
        if price_change > 5 and obv_change < 0:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, price_change, 0,
                f"⚠️ {symbol}: Bearish OBV Divergence", {"price_change": price_change, "obv_change": obv_change})
        return None

class VwapStrategy(BaseStrategy):
    """VWAP Strategy"""
    def __init__(self, config=None):
        super().__init__("VWAP", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        close = np.array(data.get("close", []))
        volume = np.array(data.get("volume", []))
        if len(high) < 10 or len(volume) < 10:
            return None
        vwap_val = vwap(high, low, close, volume)
        price = close[-1]
        deviation = (price / vwap_val - 1) * 100
        if abs(deviation) > 1:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, deviation, 1,
                f"{'📈' if deviation > 0 else '📉'} {symbol}: VWAP Deviation {deviation:+.2f}%", {"vwap": vwap_val, "deviation": deviation})
        return None

class PivotPointStrategy(BaseStrategy):
    """Pivot Point Strategy"""
    def __init__(self, config=None):
        super().__init__("Pivot_Points", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        close = np.array(data.get("close", []))
        if len(high) < 2:
            return None
        pivots = pivot_points(high, low, close)
        price = close[-1]
        if abs(price - pivots.get("pivot", 0)) < pivots.get("pivot", 1) * 0.005:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, price, pivots["pivot"],
                f"🎯 {symbol}: Near Pivot Point", pivots)
        return None

class GapStrategy(BaseStrategy):
    """Gap Detection Strategy"""
    def __init__(self, config=None):
        super().__init__("Gap_Detection", config)
        self.min_gap_pct = self.config.get("min_gap_pct", 2)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 2:
            return None
        gap = (close[-1] / close[-2] - 1) * 100
        if abs(gap) > self.min_gap_pct:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, gap, self.min_gap_pct,
                f"⬛ {symbol}: Gap {'Up' if gap > 0 else 'Down'} {gap:+.2f}%", {"gap": gap})
        return None

class DojiStrategy(BaseStrategy):
    """Doji Candlestick Pattern"""
    def __init__(self, config=None):
        super().__init__("Doji", config)
        self.threshold = self.config.get("threshold", 0.1)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        if len(close) < 2:
            return None
        body = abs(close[-1] - close[-2])
        wick_high = high[-1] - max(close[-1], close[-2])
        wick_low = min(close[-1], close[-2]) - low[-1]
        range_val = high[-1] - low[-1]
        if range_val > 0 and body / range_val < self.threshold:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, body/range_val, self.threshold,
                f"⚖️ {symbol}: Doji Candle Formed", {"body_pct": body/range_val})
        return None

class HammerStrategy(BaseStrategy):
    """Hammer/Hanging Man Candlestick"""
    def __init__(self, config=None):
        super().__init__("Hammer", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        if len(close) < 2:
            return None
        body_top = max(close[-1], open_price[-1] if len(open_price) > 1 else close[-2])
        body_bottom = min(close[-1], open_price[-1] if len(open_price) > 1 else close[-2])
        body = body_top - body_bottom
        upper_wick = high[-1] - body_top
        lower_wick = body_bottom - low[-1]
        if lower_wick > body * 2 and upper_wick < body * 0.5:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, lower_wick/body, 2,
                f"🔨 {symbol}: Hammer Candle", {"lower_wick": lower_wick, "body": body})
        return None

class EngulfingStrategy(BaseStrategy):
    """Bullish/Bearish Engulfing Pattern"""
    def __init__(self, config=None):
        super().__init__("Engulfing", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 3 or len(open_price) < 3:
            return None
        prev_bearish = close[-2] < open_price[-2] if len(open_price) > 1 else True
        current_bullish = close[-1] > open_price[-1] if len(open_price) > 1 else False
        if prev_bearish and current_bullish and close[-1] > open_price[-2] and close[-2] > open_price[-1]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - open_price[-2], 0,
                f"🟢 {symbol}: Bullish Engulfing", {})
        return None

class MorningStarStrategy(BaseStrategy):
    """Morning Star Pattern"""
    def __init__(self, config=None):
        super().__init__("Morning_Star", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 4 or len(open_price) < 4:
            return None
        if close[-3] < open_price[-3] and abs(close[-2] - open_price[-2]) < abs(close[-3] - open_price[-3]) * 0.3 and close[-1] > (close[-3] + open_price[-3]) / 2:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - close[-3], 0,
                f"⭐ {symbol}: Morning Star Pattern", {})
        return None

class ThreeWhiteSoldiersStrategy(BaseStrategy):
    """Three White Soldiers Pattern"""
    def __init__(self, config=None):
        super().__init__("Three_White_Soldiers", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 4 or len(open_price) < 4:
            return None
        if close[-1] > close[-2] and close[-2] > close[-3] and close[-3] > close[-4]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - close[-4], 0,
                f"🕯️ {symbol}: Three White Soldiers", {})
        return None

class ThreeBlackCrowsStrategy(BaseStrategy):
    """Three Black Crows Pattern"""
    def __init__(self, config=None):
        super().__init__("Three_Black_Crows", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 4 or len(open_price) < 4:
            return None
        if close[-1] < close[-2] and close[-2] < close[-3] and close[-3] < close[-4]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - close[-4], 0,
                f"🐦‍⬛ {symbol}: Three Black Crows", {})
        return None

class DoubleTopStrategy(BaseStrategy):
    """Double Top Pattern"""
    def __init__(self, config=None):
        super().__init__("Double_Top", config)
        self.tolerance = self.config.get("tolerance", 0.02)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        if len(high) < 20:
            return None
        recent_highs = []
        for i in range(2, len(high)-2):
            if high[i] > high[i-1] and high[i] > high[i+1] and high[i] > high[i-2] and high[i] > high[i+2]:
                recent_highs.append(high[i])
        if len(recent_highs) >= 2:
            if abs(recent_highs[-1] - recent_highs[-2]) / recent_highs[-2] < self.tolerance:
                self.record_alert(symbol)
                return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, recent_highs[-1], 0,
                    f"⛔ {symbol}: Double Top Detected", {"highs": recent_highs[-2:]})
        return None

class DoubleBottomStrategy(BaseStrategy):
    """Double Bottom Pattern"""
    def __init__(self, config=None):
        super().__init__("Double_Bottom", config)
        self.tolerance = self.config.get("tolerance", 0.02)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        low = np.array(data.get("low", data.get("close", [])))
        if len(low) < 20:
            return None
        recent_lows = []
        for i in range(2, len(low)-2):
            if low[i] < low[i-1] and low[i] < low[i+1] and low[i] < low[i-2] and low[i] < low[i+2]:
                recent_lows.append(low[i])
        if len(recent_lows) >= 2:
            if abs(recent_lows[-1] - recent_lows[-2]) / recent_lows[-2] < self.tolerance:
                self.record_alert(symbol)
                return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, recent_lows[-1], 0,
                    f"🪝 {symbol}: Double Bottom Detected", {"lows": recent_lows[-2:]})
        return None

class HeadAndShouldersStrategy(BaseStrategy):
    """Head and Shoulders Pattern"""
    def __init__(self, config=None):
        super().__init__("Head_Shoulders", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        if len(high) < 30:
            return None
        peaks = []
        for i in range(2, len(high)-2):
            if high[i] > high[i-1] and high[i] > high[i+1] and high[i] > high[i-2] and high[i] > high[i+2]:
                peaks.append(high[i])
        if len(peaks) >= 3:
            if peaks[-2] > peaks[-1] and peaks[-2] > peaks[-3] and abs(peaks[-1] - peaks[-3]) / peaks[-2] < 0.03:
                self.record_alert(symbol)
                return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, peaks[-2], 0,
                    f"👤 {symbol}: Head and Shoulders", {"peaks": peaks[-3:]})
        return None

class FlagPatternStrategy(BaseStrategy):
    """Bull Flag / Bear Flag Pattern"""
    def __init__(self, config=None):
        super().__init__("Flag_Pattern", config)
        self.flag_pole_min = self.config.get("flag_pole_min", 0.05)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 20:
            return None
        pole = (close[-15] - close[-20]) / close[-20] if len(close) >= 20 else 0
        flag = (close[-1] - close[-5]) / close[-5] if len(close) >= 5 else 0
        if abs(pole) > self.flag_pole_min and abs(flag) < abs(pole) * 0.3:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, pole, self.flag_pole_min,
                f"🚩 {symbol}: {'Bull' if pole > 0 else 'Bear'} Flag", {"pole": pole, "flag": flag})
        return None

class WedgePatternStrategy(BaseStrategy):
    """Rising/Falling Wedge Pattern"""
    def __init__(self, config=None):
        super().__init__("Wedge_Pattern", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        if len(high) < 20:
            return None
        high_slope = (high[-1] - high[-10]) / 10
        low_slope = (low[-1] - low[-10]) / 10
        if high_slope > 0 and low_slope > 0 and high_slope < low_slope:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, high_slope - low_slope, 0,
                f"📐 {symbol}: Rising Wedge", {"high_slope": high_slope, "low_slope": low_slope})
        elif high_slope < 0 and low_slope < 0 and high_slope > low_slope:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, low_slope - high_slope, 0,
                f"📐 {symbol}: Falling Wedge", {"high_slope": high_slope, "low_slope": low_slope})
        return None

class TrianglePatternStrategy(BaseStrategy):
    """Ascending/Descending Triangle"""
    def __init__(self, config=None):
        super().__init__("Triangle_Pattern", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        if len(high) < 20:
            return None
        high_slope = (high[-1] - high[-10]) / 10
        low_slope = (low[-1] - low[-10]) / 10
        if abs(high_slope) < 0.001 and low_slope > 0:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, low_slope, 0,
                f"🔺 {symbol}: Ascending Triangle", {})
        elif abs(low_slope) < 0.001 and high_slope < 0:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, high_slope, 0,
                f"🔻 {symbol}: Descending Triangle", {})
        return None

class IchimokuCloudStrategy(BaseStrategy):
    """Ichimoku Cloud Signal"""
    def __init__(self, config=None):
        super().__init__("Ichimoku_Cloud", config)
        self.conversion_period = 9
        self.base_period = 26
        self.span_period = 52
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        close = np.array(data.get("close", []))
        if len(high) < 52:
            return None
        conversion = (max(high[-self.conversion_period:]) + min(low[-self.conversion_period:])) / 2
        base = (max(high[-self.base_period:]) + min(low[-self.base_period:])) / 2
        if conversion > base:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, conversion - base, 0,
                f"☁️ {symbol}: Ichimoku Bullish", {"conversion": conversion, "base": base})
        return None

class KeltnerChannelStrategy(BaseStrategy):
    """Keltner Channel Breakout"""
    def __init__(self, config=None):
        super().__init__("Keltner_Channel", config)
        self.multiplier = self.config.get("multiplier", 2.0)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 20:
            return None
        middle = ema(close, 20)
        k_atr = atr(high, low, close, 10) * self.multiplier
        upper = middle + k_atr
        lower = middle - k_atr
        if close[-1] > upper:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - upper, 0,
                f"📈 {symbol}: Keltner Upper Breakout", {"upper": upper, "lower": lower})
        elif close[-1] < lower:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, lower - close[-1], 0,
                f"📉 {symbol}: Keltner Lower Breakout", {"upper": upper, "lower": lower})
        return None

class DonchianChannelStrategy(BaseStrategy):
    """Donchian Channel Breakout"""
    def __init__(self, config=None):
        super().__init__("Donchian_Channel", config)
        self.period = self.config.get("period", 20)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        close = np.array(data.get("close", []))
        if len(high) < self.period + 5:
            return None
        upper = np.max(high[-self.period:])
        lower = np.min(low[-self.period:])
        if close[-1] >= upper:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - upper, 0,
                f"⬆️ {symbol}: Donchian Upper Breakout", {"upper": upper, "lower": lower})
        elif close[-1] <= lower:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, lower - close[-1], 0,
                f"⬇️ {symbol}: Donchian Lower Breakout", {"upper": upper, "lower": lower})
        return None

class ParabolicSarStrategy(BaseStrategy):
    """Parabolic SAR Trend Change"""
    def __init__(self, config=None):
        super().__init__("Parabolic_SAR", config)
        self.af = 0.02
        self.max_af = 0.2
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 20:
            return None
        sar = low[0]
        trend = 1
        for i in range(1, min(20, len(close))):
            sar = sar + self.af * (high[i] - sar) if trend == 1 else sar - self.af * (sar - low[i])
            if (trend == 1 and close[i] < sar) or (trend == -1 and close[i] > sar):
                self.record_alert(symbol)
                return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, sar - close[-1], 0,
                    f"🔄 {symbol}: Parabolic SAR Reversal", {"sar": sar, "trend": -trend})
        return None

class SupertrendStrategy(BaseStrategy):
    """Supertrend Indicator"""
    def __init__(self, config=None):
        super().__init__("Supertrend", config)
        self.multiplier = self.config.get("multiplier", 3.0)
        self.period = self.config.get("period", 10)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < self.period + 5:
            return None
        hl_avg = (high + low) / 2
        basic = hl_avg + atr(high, low, close, self.period) * self.multiplier
        if close[-1] < basic:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, basic - close[-1], 0,
                f"📉 {symbol}: Supertrend Bearish", {"basic": basic})
        return None

class AroonIndicatorStrategy(BaseStrategy):
    """Aroon Indicator"""
    def __init__(self, config=None):
        super().__init__("Aroon", config)
        self.period = self.config.get("period", 25)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.period + 5:
            return None
        periods_since_high = 0
        periods_since_low = 0
        for i in range(len(close)-1, len(close)-self.period-1, -1):
            if close[i] == max(close[i-max(0,i-self.period):i+1]):
                periods_since_high = len(close) - i
        for i in range(len(close)-1, len(close)-self.period-1, -1):
            if close[i] == min(close[i-max(0,i-self.period):i+1]):
                periods_since_low = len(close) - i
        aroon_up = ((self.period - periods_since_high) / self.period) * 100
        aroon_down = ((self.period - periods_since_low) / self.period) * 100
        if aroon_up > 70 and aroon_down < 30:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, aroon_up, 70,
                f"🆙 {symbol}: Aroon Bullish (Up={aroon_up:.0f})", {"aroon_up": aroon_up, "aroon_down": aroon_down})
        return None

class ChaikinOscillatorStrategy(BaseStrategy):
    """Chaikin Oscillator"""
    def __init__(self, config=None):
        super().__init__("Chaikin_Oscillator", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        volume = np.array(data.get("volume", []))
        if len(close) < 20 or len(volume) < 20:
            return None
        cum_acc = 0
        for i in range(-20, 0):
            if high[i] != low[i]:
                cum_acc += ((close[i] - low[i]) / (high[i] - low[i]) - 0.5) * 2 * volume[i]
        self.record_alert(symbol)
        return StrategyAlert(symbol, self.name, AlertSeverity.LOW, cum_acc, 0,
            f"📊 {symbol}: Chaikin {cum_acc:.0f}", {"cum_acc": cum_acc})

class MoneyFlowIndexStrategy(BaseStrategy):
    """Money Flow Index"""
    def __init__(self, config=None):
        super().__init__("Money_Flow_Index", config)
        self.period = self.config.get("period", 14)
        self.overbought = self.config.get("overbought", 80)
        self.oversold = self.config.get("oversold", 20)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        volume = np.array(data.get("volume", []))
        if len(close) < self.period + 5:
            return None
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        pos_flow = np.sum(money_flow[-self.period//2:][typical_price[-self.period//2:] > typical_price[-self.period:-self.period//2]])
        neg_flow = np.sum(money_flow[-self.period//2:][typical_price[-self.period//2:] < typical_price[-self.period:-self.period//2]])
        if neg_flow == 0:
            mfi = 100
        else:
            mfi = 100 - (100 / (1 + pos_flow / neg_flow))
        if mfi < self.oversold:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, mfi, self.oversold,
                f"💰 {symbol}: MFI Oversold ({mfi:.0f})", {"mfi": mfi})
        return None

class EaseOfMovementStrategy(BaseStrategy):
    """Ease of Movement"""
    def __init__(self, config=None):
        super().__init__("Ease_of_Movement", config)
        self.threshold = self.config.get("threshold", 1.0)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        volume = np.array(data.get("volume", []))
        if len(close) < 10:
            return None
        eom = ((high[-1] - low[-1]) / 2 - (high[-2] - low[-2]) / 2) / (volume[-1] / 1000000)
        if abs(eom) > self.threshold:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, eom, self.threshold,
                f"😌 {symbol}: Ease of Movement {eom:.2f}", {"eom": eom})
        return None

class MassIndexStrategy(BaseStrategy):
    """Mass Index"""
    def __init__(self, config=None):
        super().__init__("Mass_Index", config)
        self.period = self.config.get("period", 25)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        if len(high) < self.period + 5:
            return None
        range_val = high - low
        single_ema = ema(range_val, 9)
        double_ema = ema(single_ema, 9)
        mass_idx = np.sum(double_ema[-self.period:])
        if mass_idx > 27:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, mass_idx, 27,
                f"⚖️ {symbol}: Mass Index {mass_idx:.1f}", {"mass_idx": mass_idx})
        return None

class DpoStrategy(BaseStrategy):
    """Detrended Price Oscillator"""
    def __init__(self, config=None):
        super().__init__("DPO", config)
        self.period = self.config.get("period", 20)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.period + 5:
            return None
        sma_val = sma(close, self.period)
        shifted = close[-self.period//2 - 1] if len(close) > self.period//2 else close[-1]
        dpo = shifted - sma_val
        dpo_pct = (dpo / sma_val) * 100
        if abs(dpo_pct) > 2:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, dpo_pct, 2,
                f"📐 {symbol}: DPO {dpo_pct:.2f}%", {"dpo": dpo})
        return None

class KstStrategy(BaseStrategy):
    """Know Sure Thing (KST) Oscillator"""
    def __init__(self, config=None):
        super().__init__("KST", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 40:
            return None
        roc1 = ((close[-1] / close[-10]) - 1) * 100 if len(close) >= 10 else 0
        roc2 = ((close[-1] / close[-15]) - 1) * 100 if len(close) >= 15 else 0
        roc3 = ((close[-1] / close[-20]) - 1) * 100 if len(close) >= 20 else 0
        roc4 = ((close[-1] / close[-30]) - 1) * 100 if len(close) >= 30 else 0
        kst = (roc1 * 1) + (roc2 * 2) + (roc3 * 3) + (roc4 * 4)
        if abs(kst) > 20:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, kst, 20,
                f"🎯 {symbol}: KST {kst:.0f}", {"kst": kst})
        return None

class UlcerIndexStrategy(BaseStrategy):
    """Ulcer Index"""
    def __init__(self, config=None):
        super().__init__("Ulcer_Index", config)
        self.period = self.config.get("period", 14)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.period + 5:
            return None
        highest = np.max(close[-self.period:])
        squared = ((close[-self.period:] - highest) / highest) * 100
        ulcer = np.sqrt(np.mean(squared ** 2))
        if ulcer > 10:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, ulcer, 10,
                f"🤕 {symbol}: Ulcer Index {ulcer:.2f}", {"ulcer": ulcer})
        return None

class TrixStrategy(BaseStrategy):
    """TRIX Indicator"""
    def __init__(self, config=None):
        super().__init__("TRIX", config)
        self.period = self.config.get("period", 15)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.period * 3:
            return None
        ema1 = ema(close, self.period)
        ema2 = ema(close, self.period)
        ema3 = ema(close, self.period)
        trix = ((ema3 - ema3) / ema3) * 100 if ema3 != 0 else 0
        if abs(trix) > 1:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, trix, 1,
                f"🔄 {symbol}: TRIX {trix:.3f}", {"trix": trix})
        return None

class UltimateOscillatorStrategy(BaseStrategy):
    """Ultimate Oscillator"""
    def __init__(self, config=None):
        super().__init__("Ultimate_Oscillator", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 30:
            return None
        bp = close[-1] - min(low[-1], close[-2])
        if len(close) >= 7:
            bp7 = close[-1] - min(low[-7:])
        else:
            bp7 = bp
        if len(close) >= 14:
            bp14 = close[-1] - min(low[-14:])
        else:
            bp14 = bp7
        tr = max(high[-1], close[-2]) - min(low[-1], close[-2])
        if len(close) >= 7:
            tr7 = max(high[-7:]) - min(low[-7:])
        else:
            tr7 = tr
        if len(close) >= 14:
            tr14 = max(high[-14:]) - min(low[-14:])
        else:
            tr14 = tr7
        uo = 100 * ((4 * bp7 / tr7) + (2 * bp14 / tr14) + (bp / tr)) / 7
        if uo < 30:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, uo, 30,
                f"🎯 {symbol}: Ultimate Osc Oversold ({uo:.0f})", {"uo": uo})
        return None

class VortexIndicatorStrategy(BaseStrategy):
    """Vortex Indicator"""
    def __init__(self, config=None):
        super().__init__("Vortex_Indicator", config)
        self.period = self.config.get("period", 14)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < self.period + 5:
            return None
        vm_plus = abs(high[-1] - low[-2]) 
        vm_minus = abs(low[-1] - high[-2])
        tr = max(high[-1], close[-2]) - min(low[-1], close[-2])
        if abs(tr) > 0:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, abs(vm_plus - vm_minus) / tr, 0,
                f"🌀 {symbol}: Vortex", {"vi": abs(vm_plus - vm_minus) / tr})
        return None

# ============================================================================
# NEW STRATEGIES (25-50)
# ============================================================================

class PriceEfficiencyRatioStrategy(BaseStrategy):
    """Price Efficiency Ratio"""
    def __init__(self, config=None):
        super().__init__("PER", config)
        self.period = self.config.get("period", 20)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.period + 2:
            return None
        net_change = abs(close[-1] - close[-self.period])
        total_movement = np.sum(np.abs(np.diff(close[-self.period:])))
        per = net_change / total_movement if total_movement > 0 else 0
        if per > 0.5:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, per, 0.5,
                f"📊 {symbol}: Price Efficiency {per:.2f}", {"per": per})
        return None

class TrendIntensityStrategy(BaseStrategy):
    """Trend Intensity Index"""
    def __init__(self, config=None):
        super().__init__("Trend_Intensity", config)
        self.period = self.config.get("period", 30)
        self.threshold = self.config.get("threshold", 50)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.period + 2:
            return None
        sma_val = sma(close, self.period)
        std = np.std(close[-self.period:])
        if std > 0:
            ti = ((close[-1] - sma_val) / std) + 50
            if abs(ti - 50) > self.threshold:
                self.record_alert(symbol)
                return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, ti, 50 + self.threshold,
                    f"💨 {symbol}: Trend Intensity {ti:.0f}", {"ti": ti})
        return None

class QStickIndicatorStrategy(BaseStrategy):
    """Qstick Indicator"""
    def __init__(self, config=None):
        super().__init__("QStick", config)
        self.period = self.config.get("period", 14)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]] * len(close)))
        if len(close) < self.period + 2:
            return None
        qstick = np.mean(close[-self.period:] - open_price[-self.period:])
        if abs(qstick) > close[-1] * 0.01:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, qstick, close[-1] * 0.01,
                f"📈 {symbol}: QStick {qstick:.2f}", {"qstick": qstick})
        return None

class RandomWalkIndexStrategy(BaseStrategy):
    """Random Walk Index"""
    def __init__(self, config=None):
        super().__init__("Random_Walk_Index", config)
        self.period = self.config.get("period", 14)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < self.period + 2:
            return None
        rwi = np.random.random()  # Placeholder
        self.record_alert(symbol)
        return StrategyAlert(symbol, self.name, AlertSeverity.LOW, rwi, 0,
            f"🎲 {symbol}: Random Walk {rwi:.2f}", {"rwi": rwi})

class SwingIndexStrategy(BaseStrategy):
    """Swing Index"""
    def __init__(self, config=None):
        super().__init__("Swing_Index", config)
        self.limit = self.config.get("limit", 0.5)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 2:
            return None
        swing = 0.5 * ((close[-1] - close[-2]) + (close[-1] - open_price[-1])) / (high[-1] - low[-1]) if high[-1] != low[-1] else 0
        if abs(swing) > self.limit:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, swing, self.limit,
                f"↔️ {symbol}: Swing Index {swing:.3f}", {"swing": swing})
        return None

class AccumulativeSwingIndexStrategy(BaseStrategy):
    """Accumulative Swing Index"""
    def __init__(self, config=None):
        super().__init__("ASI", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 20:
            return None
        asi = 0
        for i in range(1, min(20, len(close))):
            swing = 0.5 * ((close[i] - close[i-1]) + (close[i] - open_price[i])) / (high[i] - low[i]) if high[i] != low[i] else 0
            asi += swing
        if abs(asi) > 5:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, asi, 5,
                f"📈 {symbol}: ASI {asi:.2f}", {"asi": asi})
        return
class DemandIndexStrategy(BaseStrategy):
    """Demand Index"""
    def __init__(self, config=None):
        super().__init__("Demand_Index", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        volume = np.array(data.get("volume", []))
        if len(close) < 20 or len(volume) < 20:
            return None
        di = np.sum(volume[-10:][close[-10:] > close[-20:-10]]) / np.sum(volume[-10:][close[-10:] < close[-20:-10]]) if np.sum(volume[-10:][close[-10:] < close[-20:-10]]) > 0 else 999
        if di > 2:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, di, 2,
                f"📊 {symbol}: Demand Index {di:.1f}", {"di": di})
        return None

class MarubozuStrategy(BaseStrategy):
    """Marubozu Candlestick Pattern"""
    def __init__(self, config=None):
        super().__init__("Marubozu", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 2:
            return None
        body = abs(close[-1] - open_price[-1])
        total_range = high[-1] - low[-1]
        if total_range > 0 and body / total_range > 0.9:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, body/total_range, 0.9,
                f"🕯️ {symbol}: Marubozu {'Bullish' if close[-1] > open_price[-1] else 'Bearish'}", {})
        return None

class ShootingStarStrategy(BaseStrategy):
    """Shooting Star Pattern"""
    def __init__(self, config=None):
        super().__init__("Shooting_Star", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 2:
            return None
        body_top = max(close[-1], open_price[-1])
        body_bottom = min(close[-1], open_price[-1])
        upper_wick = high[-1] - body_top
        lower_wick = body_bottom - low[-1]
        if upper_wick > body * 2 and lower_wick < body * 0.3:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, upper_wick/body, 2,
                f"⭐ {symbol}: Shooting Star", {"upper_wick": upper_wick, "body": body})
        return None

class InvertedHammerStrategy(BaseStrategy):
    """Inverted Hammer Pattern"""
    def __init__(self, config=None):
        super().__init__("Inverted_Hammer", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 2:
            return None
        body_top = max(close[-1], close[-2])
        body_bottom = min(close[-1], close[-2])
        body = body_top - body_bottom
        upper_wick = high[-1] - body_top
        lower_wick = body_bottom - low[-1]
        if upper_wick > body * 2 and lower_wick < body * 0.3:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, upper_wick/body, 2,
                f"🔨 {symbol}: Inverted Hammer", {"upper_wick": upper_wick, "body": body})
        return None

class PiercingLineStrategy(BaseStrategy):
    """Piercing Line Pattern"""
    def __init__(self, config=None):
        super().__init__("Piercing_Line", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 3 or len(open_price) < 3:
            return None
        if close[-2] < open_price[-2] and close[-1] > open_price[-1] and close[-1] < open_price[-2] and open_price[-1] < close[-2]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - close[-2], 0,
                f"🗡️ {symbol}: Piercing Line", {})
        return None

class DarkCloudCoverStrategy(BaseStrategy):
    """Dark Cloud Cover Pattern"""
    def __init__(self, config=None):
        super().__init__("Dark_Cloud_Cover", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 3 or len(open_price) < 3:
            return None
        if close[-2] > open_price[-2] and close[-1] < open_price[-1] and close[-1] > open_price[-2] and open_price[-1] < close[-2]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-2] - close[-1], 0,
                f"☁️ {symbol}: Dark Cloud Cover", {})
        return None

class TweezerTopStrategy(BaseStrategy):
    """Tweezer Top/Bottom Pattern"""
    def __init__(self, config=None):
        super().__init__("Tweezer", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        high = np.array(data.get("high", data.get("close", [])))
        low = np.array(data.get("low", data.get("close", [])))
        if len(high) < 3:
            return None
        if abs(high[-1] - high[-2]) / high[-1] < 0.002:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, high[-1] - high[-2], 0,
                f"🔝 {symbol}: Tweezer Top", {})
        elif abs(low[-1] - low[-2]) / low[-1] < 0.002:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, low[-2] - low[-1], 0,
                f"🔻 {symbol}: Tweezer Bottom", {})
        return None

class BeltHoldStrategy(BaseStrategy):
    """Belt Hold Pattern"""
    def __init__(self, config=None):
        super().__init__("Belt_Hold", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 2:
            return None
        if close[-1] > open_price[-1] and abs(close[-1] - high[-1]) / high[-1] < 0.001:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, 1, 0,
                f"🟢 {symbol}: Bullish Belt Hold", {})
        return None

class CounterAttackStrategy(BaseStrategy):
    """Counter Attack Pattern"""
    def __init__(self, config=None):
        super().__init__("Counter_Attack", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 3:
            return None
        gap = abs(close[-1] - close[-2]) / close[-2]
        if gap > 0.02:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, gap, 0.02,
                f"⚔️ {symbol}: Counter Attack", {"gap": gap})
        return None

class GappingStrategies(BaseStrategy):
    """Various Gap Types"""
    def __init__(self, config=None):
        super().__init__("Gap_Types", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 3:
            return None
        gap_up = (close[-1] - close[-2]) / close[-2]
        gap_down = (close[-2] - close[-3]) / close[-3]
        if gap_up > 0.03:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, gap_up, 0.03,
                f"⬆️ {symbol}: Gap Up +{gap_up*100:.1f}%", {"gap": gap_up})
        elif gap_down > 0.03:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, gap_down, 0.03,
                f"⬇️ {symbol}: Gap Down {gap_down*100:.1f}%", {"gap": gap_down})
        return None

class LadderBottomStrategy(BaseStrategy):
    """Ladder Bottom Pattern"""
    def __init__(self, config=None):
        super().__init__("Ladder_Bottom", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 5:
            return None
        if all(close[-i] < close[-i-1] for i in range(1, 4)) and close[-1] > close[-4]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - close[-4], 0,
                f"📶 {symbol}: Ladder Bottom", {})
        return None

class BreakawayStrategy(BaseStrategy):
    """Breakaway Pattern"""
    def __init__(self, config=None):
        super().__init__("Breakaway", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 6:
            return None
        if close[-1] > close[-5] * 1.05 and all(abs(close[-i] - close[-i-1]) / close[-i] < 0.01 for i in range(2, 5)):
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - close[-5], 0,
                f"🚀 {symbol}: Breakaway", {})
        return None

class RoundingBottomStrategy(BaseStrategy):
    """Rounding Bottom Pattern"""
    def __init__(self, config=None):
        super().__init__("Rounding_Bottom", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 20:
            return None
        mid = len(close) // 2
        if close[-1] > close[mid] and close[mid] < close[0]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, close[-1] - close[mid], 0,
                f"🥣 {symbol}: Rounding Bottom", {})
        return None

class IslandReversalStrategy(BaseStrategy):
    """Island Reversal Pattern"""
    def __init__(self, config=None):
        super().__init__("Island_Reversal", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 5:
            return None
        gap1 = close[-3] > close[-4] * 1.02
        gap2 = close[-1] < close[-2] * 0.98
        if gap1 and gap2:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - close[-4], 0,
                f"🏝️ {symbol}: Island Reversal", {})
        return None

class KickerStrategy(BaseStrategy):
    """Kicker Pattern"""
    def __init__(self, config=None):
        super().__init__("Kicker", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 3 or len(open_price) < 3:
            return None
        direction_change = (close[-1] > open_price[-1]) != (close[-2] > open_price[-2])
        gap = abs(open_price[-1] - close[-2]) / close[-2] if close[-2] != 0 else 0
        if direction_change and gap > 0.02:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, gap, 0.02,
                f"👟 {symbol}: Kicker", {"gap": gap})
        return None

class ThrustingStrategy(BaseStrategy):
    """Thrusting Pattern"""
    def __init__(self, config=None):
        super().__init__("Thrusting", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 3 or len(open_price) < 3:
            return None
        if close[-2] < open_price[-2] and close[-1] > open_price[-1] and open_price[-1] < (close[-2] + open_price[-2]) / 2:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, close[-1] - open_price[-1], 0,
                f"🔨 {symbol}: Thrusting", {})
        return None

class StalledPatternStrategy(BaseStrategy):
    """Stalled Pattern"""
    def __init__(self, config=None):
        super().__init__("Stalled_Pattern", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        if len(close) < 10:
            return None
        recent_range = max(close[-5:]) - min(close[-5:])
        early_range = max(close[-10:-5]) - min(close[-10:-5])
        if recent_range < early_range * 0.3:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, recent_range/early_range, 0.3,
                f"⏸️ {symbol}: Stalled Pattern", {"recent": recent_range, "early": early_range})
        return None

class UniqueThreeRiverStrategy(BaseStrategy):
    """Unique Three River Pattern"""
    def __init__(self, config=None):
        super().__init__("Unique_Three_River", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 4 or len(open_price) < 4:
            return None
        if close[-3] > open_price[-3] and close[-2] < open_price[-2] and close[-1] > open_price[-1]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, close[-1] - close[-3], 0,
                f"🌊 {symbol}: Unique Three River", {})
        return None

class TwoCrowsStrategy(BaseStrategy):
    """Two Crows Pattern"""
    def __init__(self, config=None):
        super().__init__("Two_Crows", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 4 or len(open_price) < 4:
            return None
        if close[-3] > open_price[-3] and close[-2] < open_price[-2] and close[-2] > close[-3] and close[-1] < open_price[-1] and close[-1] > close[-3]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, close[-1] - close[-3], 0,
                f"🐦🐦 {symbol}: Two Crows", {})
        return None

class ThreeLineStrikeStrategy(BaseStrategy):
    """Three Line Strike Pattern"""
    def __init__(self, config=None):
        super().__init__("Three_Line_Strike", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        open_price = np.array(data.get("open", [close[0]]))
        if len(close) < 5 or len(open_price) < 5:
            return None
        if all(close[-i] > open_price[-i] for i in range(2, 5)) and close[-1] < open_price[-4]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.HIGH, open_price[-4] - close[-1], 0,
                f"📈📉 {symbol}: Three Line Strike", {})
        return None

class FourPriceDojiStrategy(BaseStrategy):
    """Four Price Doji"""
    def __init__(self, config=None):
        super().__init__("Four_Price_Doji", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 1:
            return None
        if high[-1] == low[-1]:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, 0, 0,
                f"⚖️ {symbol}: Four Price Doji", {})
        return None

class LongLeggedDojiStrategy(BaseStrategy):
    """Long Legged Doji"""
    def __init__(self, config=None):
        super().__init__("Long_Legged_Doji", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 2:
            return None
        body = abs(close[-1] - close[-2])
        wicks = (high[-1] - low[-1]) - body
        if wicks > body * 3:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.LOW, wicks/body, 3,
                f"🦵 {symbol}: Long Legged Doji", {"wicks": wicks, "body": body})
        return None

class DragonflyDojiStrategy(BaseStrategy):
    """Dragonfly Doji"""
    def __init__(self, config=None):
        super().__init__("Dragonfly_Doji", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 2:
            return None
        open_price = close[-2]
        body = abs(close[-1] - open_price)
        upper_wick = high[-1] - max(close[-1], open_price)
        lower_wick = min(close[-1], open_price) - low[-1]
        if body < (high[-1] - low[-1]) * 0.1 and lower_wick > (high[-1] - low[-1]) * 0.6:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, lower_wick, (high[-1] - low[-1]) * 0.6,
                f"🪰 {symbol}: Dragonfly Doji", {})
        return None

class GravestoneDojiStrategy(BaseStrategy):
    """Gravestone Doji"""
    def __init__(self, config=None):
        super().__init__("Gravestone_Doji", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
            return None
        close = np.array(data.get("close", []))
        high = np.array(data.get("high", close))
        low = np.array(data.get("low", close))
        if len(close) < 2:
            return None
        open_price = close[-2]
        body = abs(close[-1] - open_price)
        upper_wick = high[-1] - max(close[-1], open_price)
        lower_wick = min(close[-1], open_price) - low[-1]
        if body < (high[-1] - low[-1]) * 0.1 and upper_wick > (high[-1] - low[-1]) * 0.6:
            self.record_alert(symbol)
            return StrategyAlert(symbol, self.name, AlertSeverity.MEDIUM, upper_wick, (high[-1] - low[-1]) * 0.6,
                f"🪦 {symbol}: Gravestone Doji", {})
        return None

# ============================================================================
# STRATEGY REGISTRY
# ============================================================================


    """Get instances of all strategies"""
    return [strategy_class() for strategy_class in STRATEGY_REGISTRY.values()]

    """Get total number of strategies"""
    return len(STRATEGY_REGISTRY)

# ============================================================================
# ADDITIONAL STRATEGIES (77-105)
# ============================================================================

class VpciStrategy(BaseStrategy):
    """Volume Price Confirmation Index"""
    def __init__(self, config=None):
        super().__init__("VPCI", config)
    
    def analyze(self, symbol: str, data: Dict) -> Optional[StrategyAlert]:
        if not self.can_alert(symbol):
