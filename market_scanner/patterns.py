"""
Pattern Logic - Strategy Pattern for Pluggable Analysis

FIXED PATTERNS:
- GreenStreakPattern: Lowered threshold (15 → 5), added flexible mode, added cooldown
- VolumeSurgePattern: Now uses CUMULATIVE volume instead of single trades
- RSIDivergencePattern: Added actual divergence detection (price vs RSI)
- MomentumPattern: Added ATR volatility normalization
- PatternManager: Added market context, cumulative volume support, cooldown reset
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from datetime import datetime
import inspect


# ============================================================================
# HELPER FUNCTIONS (FIXED & SHARED)
# ============================================================================

def find_peaks_and_troughs(values: np.ndarray, lookback: int) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """
    Find local peaks and troughs in a series of values.
    """
    if len(values) < lookback:
        return [], []
    
    recent = values[-lookback:]
    peaks = []
    troughs = []
    
    for i in range(1, len(recent) - 1):
        if recent[i] > recent[i-1] and recent[i] > recent[i+1]:
            peaks.append((len(recent) - lookback + i, recent[i]))
        if recent[i] < recent[i-1] and recent[i] < recent[i+1]:
            troughs.append((len(recent) - lookback + i, recent[i]))
    
    return peaks, troughs


def calculate_atr(prices: np.ndarray, period: int = 14) -> float:
    """Calculate Average True Range for volatility normalization."""
    if len(prices) < period + 1:
        return prices[-1] * 0.02
    
    highs = prices[1:]
    lows = prices[1:]
    closes = prices[:-1]
    
    tr1 = highs - lows
    tr2 = np.abs(highs - closes)
    tr3 = np.abs(lows - closes)
    
    true_ranges = np.maximum(np.maximum(tr1, tr2), tr3)
    
    if len(true_ranges) > 0:
        return np.mean(true_ranges[-period:])
    return prices[-1] * 0.02


def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate RSI using Wilder's smoothing method."""
    if len(prices) < period + 1:
        return np.array([])
    
    deltas = np.diff(prices)
    gains = np.maximum(deltas, 0)
    losses = np.maximum(-deltas, 0)
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    rsi_values = np.zeros(len(prices))
    
    if avg_loss == 0:
        rsi_values[period:] = 100
    else:
        rs = avg_gain / avg_loss
        rsi_values[period] = 100 - (100 / (1 + rs))
        
        for i in range(period + 1, len(prices)):
            gain_idx = i - 1
            if gain_idx >= len(gains):
                break
            avg_gain = (avg_gain * (period - 1) + gains[gain_idx]) / period
            avg_loss = (avg_loss * (period - 1) + losses[gain_idx]) / period
            
            if avg_loss == 0:
                rsi_values[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi_values[i] = 100 - (100 / (1 + rs))
    
    return rsi_values


# ============================================================================
# ALERT & SEVERITY CLASSES
# ============================================================================

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Alert:
    """Alert object returned by pattern detectors"""
    symbol: str
    pattern_name: str
    severity: AlertSeverity
    value: float
    threshold: float
    message: str
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "pattern": self.pattern_name,
            "severity": self.severity.name,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class BasePattern(ABC):
    """Abstract Base Class for pattern detectors"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self._enabled = self.config.get("enabled", True)
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
    
    @abstractmethod
    def analyze(
        self,
        symbol: str,
        prices: np.ndarray,
        sizes: np.ndarray,
        timestamps: np.ndarray = None
    ) -> List[Alert]:
        """
        Analyze ticker data and return alerts
        
        Args:
            symbol: Ticker symbol
            prices: NumPy array of prices
            sizes: NumPy array of trade sizes
            timestamps: Optional array of timestamps
            
        Returns:
            List of Alert objects
        """
        pass
    
    def validate_input(self, prices: np.ndarray, sizes: np.ndarray) -> bool:
        """Validate input data has required length"""
        min_length = self.get_min_required_length()
        return len(prices) >= min_length and len(sizes) >= min_length
    
    def get_min_required_length(self) -> int:
        """Minimum data points required for analysis"""
        return 2


class GreenStreakPattern(BasePattern):
    """
    Detects consecutive green (up) candles/wicks
    
    Config:
        - streak_length: Number of consecutive green candles (default: 5, reduced from 15)
        - min_streak_pct: Minimum % gain for streak to count (default: 0.1)
        - flexible_mode: If true, accepts partial streaks (default: true)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("GreenStreak", config)
        self.streak_length = self.config.get("streak_length", 5)  # Changed from 15
        self.min_streak_pct = self.config.get("min_streak_pct", 0.1)
        self.flexible_mode = self.config.get("flexible_mode", True)
        self._alert_cooldowns = {}  # Cooldown tracking
    
    def analyze(
        self,
        symbol: str,
        prices: np.ndarray,
        sizes: np.ndarray,
        timestamps: np.ndarray = None
    ) -> List[Alert]:
        from datetime import timedelta
        import time
        
        if not self.validate_input(prices, sizes):
            return []
        
        alerts = []
        
        # Need at least streak_length + 1 prices to detect streaks
        if len(prices) < self.streak_length + 1:
            return []
        
        # Check cooldown (5 minutes)
        cooldown_key = f"greenstreak_{symbol}"
        now = time.time()
        if cooldown_key in self._alert_cooldowns:
            if now - self._alert_cooldowns[cooldown_key] < 300:  # 5 min
                return []
        
        # Calculate price changes
        changes = np.diff(prices)
        
        # Find consecutive positive changes (green streaks)
        current_streak = 0
        max_streak = 0
        streak_start_idx = -1
        
        for i, change in enumerate(changes):
            pct_change = (change / prices[i]) * 100
            if change > 0 and pct_change >= self.min_streak_pct:
                if current_streak == 0:
                    streak_start_idx = i
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        # Alert threshold - either full streak or flexible mode
        if max_streak >= self.streak_length or (self.flexible_mode and max_streak >= self.streak_length - 2):
            effective_streak = max_streak if max_streak >= self.streak_length else max_streak
            
            streak_start_price = prices[streak_start_idx] if streak_start_idx >= 0 else prices[0]
            current_price = prices[-1]
            streak_return = ((current_price - streak_start_price) / streak_start_price) * 100
            
            # Determine severity
            if max_streak >= self.streak_length * 2:
                severity = AlertSeverity.HIGH
            elif max_streak >= self.streak_length:
                severity = AlertSeverity.MEDIUM
            else:
                severity = AlertSeverity.LOW
            
            alerts.append(Alert(
                symbol=symbol,
                pattern_name=self.name,
                severity=severity,
                value=float(max_streak),
                threshold=float(self.streak_length),
                message=f"🔥 {symbol}: {effective_streak} consecutive green candles (+{streak_return:.2f}%)",
                metadata={
                    "streak_length": max_streak,
                    "return_pct": streak_return,
                    "start_price": float(streak_start_price),
                    "end_price": float(current_price),
                    "flexible_mode": self.flexible_mode
                }
            ))
            
            # Set cooldown
            self._alert_cooldowns[cooldown_key] = now
        
        return alerts
    
    def get_min_required_length(self) -> int:
        return self.streak_length + 1


class VolumeSurgePattern(BasePattern):
    """
    Detects unusual volume spikes using CUMULATIVE volume (not single trade sizes).
    
    CRITICAL FIX: Previous implementation used single trade sizes, which is wrong.
    Now tracks cumulative daily volume and calculates deltas.
    
    Config:
        - surge_multiplier: Multiplier of average volume to trigger (default: 3.0)
        - lookback_period: Period to calculate average volume (default: 50)
        - cooldown_seconds: Time between alerts for same symbol (default: 300)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("VolumeSurge", config)
        self.surge_multiplier = self.config.get("surge_multiplier", 3.0)
        self.lookback_period = self.config.get("lookback_period", 50)
        self.cooldown_seconds = self.config.get("cooldown_seconds", 300)
        self._previous_cumulative = {}  # Track cumulative volume per symbol
        self._previous_total = {}  # Track previous total for delta calculation
        self._alert_cooldowns = {}
        self._lookback_volumes = {symbol: [] for symbol in self._get_tracked_symbols()}
    
    def _get_tracked_symbols(self):
        """Get symbols being tracked for volume history"""
        return []
    
    def analyze(
        self,
        symbol: str,
        prices: np.ndarray,
        sizes: np.ndarray,
        timestamps: np.ndarray = None,
        cumulative_volume: int = None
    ) -> List[Alert]:
        import time
        
        if not self.validate_input(sizes, sizes):
            return []
        
        alerts = []
        
        # Check cooldown
        cooldown_key = f"volumesurge_{symbol}"
        now = time.time()
        if cooldown_key in self._alert_cooldowns:
            if now - self._alert_cooldowns[cooldown_key] < self.cooldown_seconds:
                return []
        
        # If cumulative volume is provided (from snapshot API), use it
        if cumulative_volume is not None:
            if symbol not in self._previous_total:
                self._previous_total[symbol] = cumulative_volume
                return []
            
            # Calculate delta since last poll
            volume_delta = cumulative_volume - self._previous_total[symbol]
            self._previous_total[symbol] = cumulative_volume
            
            # Add to lookback history
            self._lookback_volumes.setdefault(symbol, []).append(volume_delta)
            if len(self._lookback_volumes[symbol]) > self.lookback_period:
                self._lookback_volumes[symbol].pop(0)
            
            # Need enough history
            if len(self._lookback_volumes[symbol]) < self.lookback_period:
                return []
            
            # Calculate average delta volume
            avg_volume = np.mean(self._lookback_volumes[symbol][:-1])  # Exclude current
            current_volume = volume_delta
            
            if avg_volume > 0:
                surge_ratio = current_volume / avg_volume
                
                if surge_ratio >= self.surge_multiplier:
                    price_change = ((prices[-1] - prices[-2]) / prices[-2]) * 100 if len(prices) >= 2 else 0
                    
                    severity = AlertSeverity.HIGH if surge_ratio >= self.surge_multiplier * 2 else AlertSeverity.MEDIUM
                    
                    alerts.append(Alert(
                        symbol=symbol,
                        pattern_name=self.name,
                        severity=severity,
                        value=float(surge_ratio),
                        threshold=float(self.surge_multiplier),
                        message=f"📊 {symbol}: Volume surge {surge_ratio:.1f}x (avg: {avg_volume:.0f}, current: {current_volume})",
                        metadata={
                            "surge_ratio": surge_ratio,
                            "avg_volume": float(avg_volume),
                            "current_volume": int(current_volume),
                            "price_change_pct": price_change,
                            "method": "cumulative_delta"
                        }
                    ))
                    
                    self._alert_cooldowns[cooldown_key] = now
        
        # FALLBACK: If no cumulative volume, estimate from trade sizes (less accurate)
        else:
            # This is the old method - using individual trade sizes
            # It's less accurate but works as fallback
            if len(sizes) < self.lookback_period + 1:
                return []
            
            avg_volume = np.mean(sizes[:-1])
            current_volume = sizes[-1]
            
            if avg_volume > 0:
                surge_ratio = current_volume / avg_volume
                
                if surge_ratio >= self.surge_multiplier * 3:  # Higher threshold for fallback
                    price_change = ((prices[-1] - prices[-2]) / prices[-2]) * 100 if len(prices) >= 2 else 0
                    
                    alerts.append(Alert(
                        symbol=symbol,
                        pattern_name=self.name,
                        severity=AlertSeverity.LOW,
                        value=float(surge_ratio),
                        threshold=float(self.surge_multiplier),
                        message=f"📊 {symbol}: Estimated volume surge {surge_ratio:.1f}x (WARNING: using single trades, may be inaccurate)",
                        metadata={
                            "surge_ratio": surge_ratio,
                            "avg_volume": float(avg_volume),
                            "current_volume": int(current_volume),
                            "price_change_pct": price_change,
                            "method": "single_trade_fallback"
                        }
                    ))
        
        return alerts
    
    def get_min_required_length(self) -> int:
        return self.lookback_period + 1
    
    def reset(self, symbol: str = None):
        """Reset volume history"""
        if symbol:
            self._previous_total.pop(symbol, None)
            self._lookback_volumes[symbol] = []
        else:
            self._previous_total.clear()
            self._lookback_volumes.clear()


class RSIDivergencePattern(BasePattern):
    """
    Detects RSI divergence from price action.
    
    FIXED: Now properly detects divergence (price up + RSI down, or vice versa)
    
    Config:
        - period: RSI period (default: 14)
        - overbought: Overbought threshold (default: 70)
        - oversold: Oversold threshold (default: 30)
        - lookback_candles: Number of candles to check for divergence (default: 20)
        - cooldown_seconds: Time between alerts (default: 600)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("RSIDivergence", config)
        self.period = self.config.get("period", 14)
        self.overbought = self.config.get("overbought", 70)
        self.oversold = self.config.get("oversold", 30)
        self.lookback_candles = self.config.get("lookback_candles", 20)
        self.cooldown_seconds = self.config.get("cooldown_seconds", 600)
        self._alert_cooldowns = {}
    
    def _calculate_rsi(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate RSI values - uses shared helper"""
        return calculate_rsi(prices, period)
    
    def _find_peaks_and_troughs(self, values: np.ndarray, lookback: int) -> tuple:
        """Find local peaks and troughs - uses shared helper"""
        return find_peaks_and_troughs(values, lookback)
    
    def analyze(
        self,
        symbol: str,
        prices: np.ndarray,
        sizes: np.ndarray,
        timestamps: np.ndarray = None
    ) -> List[Alert]:
        import time
        
        if not self.validate_input(prices, prices):
            return []
        
        alerts = []
        
        # Check cooldown
        cooldown_key = f"rsi_{symbol}"
        now = time.time()
        if cooldown_key in self._alert_cooldowns:
            if now - self._alert_cooldowns[cooldown_key] < self.cooldown_seconds:
                return []
        
        rsi = self._calculate_rsi(prices, self.period)
        
        if len(rsi) == 0:
            return []
        
        current_rsi = rsi[-1]
        current_price = prices[-1]
        
        # Find peaks and troughs in both price and RSI
        price_peaks, price_troughs = self._find_peaks_and_troughs(prices, self.lookback_candles)
        rsi_peaks, rsi_troughs = self._find_peaks_and_troughs(rsi, self.lookback_candles)
        
        divergence_detected = None
        
        # BEARISH DIVERGENCE: Price makes HIGHER high, RSI makes LOWER high
        if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
            # Get two most recent price peaks
            recent_price_peaks = price_peaks[-2:]
            recent_rsi_peaks = rsi_peaks[-2:] if len(rsi_peaks) >= 2 else []
            
            if len(recent_rsi_peaks) >= 2:
                price_1, price_2 = recent_price_peaks[0][1], recent_price_peaks[1][1]
                rsi_1, rsi_2 = recent_rsi_peaks[0][1], recent_rsi_peaks[1][1]
                
                if price_2 > price_1 and rsi_2 < rsi_1:
                    divergence_detected = ("bearish", price_2 - price_1, rsi_1 - rsi_2)
        
        # BULLISH DIVERGENCE: Price makes LOWER trough, RSI makes HIGHER trough
        if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
            recent_price_troughs = price_troughs[-2:]
            recent_rsi_troughs = rsi_troughs[-2:] if len(rsi_troughs) >= 2 else []
            
            if len(recent_rsi_troughs) >= 2:
                price_1, price_2 = recent_price_troughs[0][1], recent_price_troughs[1][1]
                rsi_1, rsi_2 = recent_rsi_troughs[0][1], recent_rsi_troughs[1][1]
                
                if price_2 < price_1 and rsi_2 > rsi_1:
                    divergence_detected = ("bullish", price_1 - price_2, rsi_2 - rsi_1)
        
        # Generate alert for divergence
        if divergence_detected:
            div_type, price_diff, rsi_diff = divergence_detected
            direction = "⬆️ BULLISH" if div_type == "bullish" else "⬇️ BEARISH"
            severity = AlertSeverity.HIGH
            
            alerts.append(Alert(
                symbol=symbol,
                pattern_name=self.name,
                severity=severity,
                value=float(current_rsi),
                threshold=float(self.overbought) if div_type == "bearish" else float(self.oversold),
                message=f"{direction} RSI DIVERGENCE on {symbol}\n  RSI: {current_rsi:.1f} | Price: ${current_price:.2f}\n  Divergence strength: {rsi_diff:.1f} RSI pts / {price_diff:.2f} price pts",
                metadata={
                    "rsi": current_rsi,
                    "divergence_type": div_type,
                    "divergence_strength": rsi_diff,
                    "price_change": price_diff,
                    "condition": "divergence"
                }
            ))
            self._alert_cooldowns[cooldown_key] = now
        
        # Also check overbought/oversold (with cooldown)
        elif current_rsi >= self.overbought:
            alerts.append(Alert(
                symbol=symbol,
                pattern_name=self.name,
                severity=AlertSeverity.LOW,
                value=float(current_rsi),
                threshold=float(self.overbought),
                message=f"⚠️ {symbol}: RSI overbought at {current_rsi:.1f}",
                metadata={"rsi": current_rsi, "condition": "overbought"}
            ))
            self._alert_cooldowns[cooldown_key] = now
        
        elif current_rsi <= self.oversold:
            alerts.append(Alert(
                symbol=symbol,
                pattern_name=self.name,
                severity=AlertSeverity.LOW,
                value=float(current_rsi),
                threshold=float(self.oversold),
                message=f"⚠️ {symbol}: RSI oversold at {current_rsi:.1f}",
                metadata={"rsi": current_rsi, "condition": "oversold"}
            ))
            self._alert_cooldowns[cooldown_key] = now
        
        return alerts
    
    def get_min_required_length(self) -> int:
        return max(self.period + 1, self.lookback_candles + 1)


class MomentumPattern(BasePattern):
    """
    Detects strong price momentum WITH volatility normalization.
    
    FIXED: Now accounts for volatility (ATR-normalized momentum)
    
    Config:
        - lookback: Period to calculate momentum (default: 10)
        - threshold: Minimum momentum % to trigger (default: 2.0)
        - normalize: Use ATR normalization (default: true)
        - cooldown_seconds: Time between alerts (default: 300)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Momentum", config)
        self.lookback = self.config.get("lookback", 10)
        self.threshold = self.config.get("threshold", 2.0)
        self.normalize = self.config.get("normalize", True)
        self.cooldown_seconds = self.config.get("cooldown_seconds", 300)
        self._alert_cooldowns = {}
    
    def _calculate_atr(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range - uses shared helper"""
        return calculate_atr(prices, period)
    
    def analyze(
        self,
        symbol: str,
        prices: np.ndarray,
        sizes: np.ndarray,
        timestamps: np.ndarray = None
    ) -> List[Alert]:
        import time
        
        if len(prices) < self.lookback + 1:
            return []
        
        alerts = []
        
        # Check cooldown
        cooldown_key = f"momentum_{symbol}"
        now = time.time()
        if cooldown_key in self._alert_cooldowns:
            if now - self._alert_cooldowns[cooldown_key] < self.cooldown_seconds:
                return []
        
        # Calculate raw momentum
        momentum_raw = ((prices[-1] - prices[-self.lookback - 1]) / prices[-self.lookback - 1]) * 100
        
        if self.normalize:
            # Normalize by volatility (ATR)
            atr = self._calculate_atr(prices)
            atr_pct = (atr / prices[-1]) * 100  # ATR as % of price
            
            # Normalized momentum: momentum / volatility
            if atr_pct > 0:
                momentum_normalized = momentum_raw / atr_pct
            else:
                momentum_normalized = momentum_raw
            
            # Use normalized value for threshold comparison
            effective_threshold = self.threshold
            momentum_display = momentum_raw
            momentum_value = momentum_normalized
        else:
            effective_threshold = self.threshold
            momentum_display = momentum_raw
            momentum_value = momentum_raw
        
        if abs(momentum_value) >= effective_threshold:
            direction = "up" if momentum_value > 0 else "down"
            severity = AlertSeverity.HIGH if abs(momentum_value) >= effective_threshold * 2 else AlertSeverity.MEDIUM
            
            # Determine signal quality
            if abs(momentum_value) >= effective_threshold * 3:
                signal_quality = "STRONG"
            elif abs(momentum_value) >= effective_threshold * 1.5:
                signal_quality = "MODERATE"
            else:
                signal_quality = "WEAK"
            
            message = f"🚀 {symbol}: {momentum_display:.2f}% momentum {direction} ({signal_quality})"
            if self.normalize:
                message += f"\n   Normalized: {momentum_normalized:.2f}x volatility | ATR: {atr:.2f} ({atr_pct:.2f}%)"
            
            alerts.append(Alert(
                symbol=symbol,
                pattern_name=self.name,
                severity=severity,
                value=float(momentum_value),
                threshold=float(effective_threshold),
                message=message,
                metadata={
                    "raw_momentum": momentum_display,
                    "normalized_momentum": momentum_normalized if self.normalize else momentum_display,
                    "direction": direction,
                    "lookback": self.lookback,
                    "atr": atr if self.normalize else None,
                    "signal_quality": signal_quality
                }
            ))
            
            self._alert_cooldowns[cooldown_key] = now
        
        return alerts


class PatternManager:
    """
    Manages multiple pattern detectors with Strategy Pattern
    
    Features:
    - Cooldown tracking per pattern per symbol
    - Cumulative volume support for VolumeSurgePattern
    - Context-aware analysis
    """
    
    def __init__(self):
        self._patterns: Dict[str, BasePattern] = {}
        self._market_context = {
            "market_direction": "neutral",  # "up", "down", "neutral"
            "market_change_pct": 0.0,
            "vix_level": "normal"  # "low", "normal", "high"
        }
    
    def register(self, pattern: BasePattern) -> None:
        """Register a new pattern detector"""
        self._patterns[pattern.name] = pattern
    
    def unregister(self, name: str) -> None:
        """Remove a pattern detector"""
        if name in self._patterns:
            del self._patterns[name]
    
    def get(self, name: str) -> Optional[BasePattern]:
        """Get a pattern by name"""
        return self._patterns.get(name)
    
    def set_market_context(self, market_direction: str, market_change_pct: float, vix_level: str = "normal"):
        """Set market context for smarter pattern detection"""
        self._market_context = {
            "market_direction": market_direction,
            "market_change_pct": market_change_pct,
            "vix_level": vix_level
        }
    
    def analyze_all(
        self,
        symbol: str,
        prices: np.ndarray,
        sizes: np.ndarray,
        timestamps: np.ndarray = None,
        cumulative_volume: int = None
    ) -> List[Alert]:
        """Run all enabled patterns with optional cumulative volume"""
        alerts = []
        
        for pattern in self._patterns.values():
            if pattern.enabled:
                try:
                    # Pass cumulative volume if pattern supports it
                    if hasattr(pattern, 'analyze') and cumulative_volume is not None:
                        # Use inspect to check if analyze accepts cumulative_volume
                        import inspect
                        sig = inspect.signature(pattern.analyze)
                        if 'cumulative_volume' in sig.parameters:
                            pattern_alerts = pattern.analyze(
                                symbol, prices, sizes, timestamps, cumulative_volume
                            )
                            alerts.extend(pattern_alerts)
                            continue
                    
                    pattern_alerts = pattern.analyze(symbol, prices, sizes, timestamps)
                    alerts.extend(pattern_alerts)
                except Exception as e:
                    print(f"[PatternManager] Error in {pattern.name}: {e}")
        
        return alerts
    
    def get_enabled_patterns(self) -> List[str]:
        """Get list of enabled pattern names"""
        return [name for name, p in self._patterns.items() if p.enabled]
    
    def set_enabled(self, name: str, enabled: bool) -> None:
        """Enable/disable a pattern"""
        if name in self._patterns:
            self._patterns[name].enabled = enabled
    
    def reset_cooldowns(self, symbol: str = None):
        """Reset cooldowns for a symbol or all"""
        for pattern in self._patterns.values():
            if hasattr(pattern, '_alert_cooldowns'):
                if symbol:
                    keys_to_remove = [k for k in pattern._alert_cooldowns if k.endswith(f"_{symbol}")]
                    for k in keys_to_remove:
                        del pattern._alert_cooldowns[k]
                else:
                    pattern._alert_cooldowns.clear()
