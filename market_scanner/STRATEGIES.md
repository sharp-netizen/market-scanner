# 100+ Trading Strategies

## Overview
This document contains 100+ trading strategies for the market scanner.

---

## Moving Average Strategies (1-10)

| # | Strategy | Description |
|---|----------|-------------|
| 1 | SMA Crossover | Fast SMA crosses above Slow SMA |
| 2 | EMA Crossover | Exponential MA crossover |
| 3 | HMA Crossover | Hull Moving Average crossover |
| 4 | DEMA | Double Exponential MA |
| 5 | TEMA | Triple Exponential MA |
| 6 | T3 MA | Tillson T3 Moving Average |
| 7 | ZLEMA | Zero Lag EMA |
| 8 | LSMA | Least Squares MA |
| 9 | VAMA | Volume Adjusted MA |
| 10 | FRAMA | Fractal Adaptive MA |

---

## Momentum Indicators (11-30)

| # | Strategy | Description |
|---|----------|-------------|
| 11 | RSI Oversold | RSI below 30 |
| 12 | RSI Overbought | RSI above 70 |
| 13 | MACD Crossover | MACD crosses signal line |
| 14 | Stochastic | Stochastic oscillator |
| 15 | Williams %R | Williams percent range |
| 16 | Price Momentum | Rate of change |
| 17 | PPO | Percent Price Oscillator |
| 18 | CCI | Commodity Channel Index |
| 19 | Ultimate Osc | Williams Ultimate Oscillator |
| 20 | TRIX | Triple exponential average |
| 21 | ATR Volatility | Average True Range |
| 22 | Bollinger Bands | Price at band edges |
| 23 | Keltner Channel | Channel breakout |
| 24 | Donchian Channel | Channel breakout |
| 25 | Historical Vol | Statistical volatility |
| 26 | Ulcer Index | Downside volatility |
| 27 | Mass Index | Volatility expansion |
| 28 | DPO | Detrended Price Oscillator |
| 29 | KST | Know Sure Thing |
| 30 | Chaikin Osc | Chaikin oscillator |

---

## Trend Indicators (31-50)

| # | Strategy | Description |
|---|----------|-------------|
| 31 | ADX Trend | Average Directional Index > 25 |
| 32 | Supertrend | Trend direction indicator |
| 33 | Parabolic SAR | Stop and reverse |
| 34 | Ichimoku Cloud | Cloud analysis |
| 35 | Aroon | Aroon up/down |
| 36 | Aroon Oscillator | Aroon oscillator |
| 37 | Vortex | Vortex indicator |
| 38 | QStick | Trend strength |
| 39 | Trend Intensity | Trend intensity index |
| 40 | Volume Spike | Unusual volume |

---

## Volume Strategies (41-60)

| # | Strategy | Description |
|---|----------|-------------|
| 41 | OBV Divergence | Price vs volume divergence |
| 42 | VWAP | Volume weighted average price |
| 43 | MFI | Money Flow Index |
| 44 | EOM | Ease of Movement |
| 45 | VPCI | Volume Price Confirmation |
| 46 | VZO | Volume Zone Oscillator |
| 47 | PVO | Percent Volume Oscillator |
| 48 | Force Index | Force of movement |
| 49 | Demand Index | Buying/selling pressure |
| 50 | Gap Up | Price gap higher |

---

## Price Patterns (51-70)

| # | Strategy | Description |
|---|----------|-------------|
| 51 | Gap Down | Price gap lower |
| 52 | Doji | Indecision candle |
| 53 | Hammer | Bullish reversal |
| 54 | Shooting Star | Bearish reversal |
| 55 | Bullish Engulfing | Pattern reversal |
| 56 | Bearish Engulfing | Pattern reversal |
| 57 | Morning Star | Bullish 3-candle pattern |
| 58 | Evening Star | Bearish 3-candle pattern |
| 59 | Piercing Line | Bullish pattern |
| 60 | Three White Soldiers | Strong uptrend |
| 61 | Three Black Crows | Strong downtrend |
| 62 | Double Top | Resistance pattern |
| 63 | Double Bottom | Support pattern |
| 64 | Head & Shoulders | Reversal pattern |
| 65 | Inv Head & Shoulders | Bullish reversal |
| 66 | Rising Wedge | Bearish pattern |
| 67 | Falling Wedge | Bullish pattern |
| 68 | Ascending Triangle | Bullish pattern |
| 69 | Descending Triangle | Bearish pattern |
| 70 | Bull Flag | Continuation up |

---

## Continuation Patterns (71-80)

| # | Strategy | Description |
|---|----------|-------------|
| 71 | Bear Flag | Continuation down |
| 72 | Bullish Channel | Price channel up |
| 73 | Bearish Channel | Price channel down |
| 74 | Rectangle | Consolidation |
| 75 | Cup and Handle | Bullish continuation |
| 76 | Rounding Bottom | Bullish reversal |
| 77 | Bump and Run | Momentum pattern |
| 78 | Three Drives | Reversal pattern |
| 79 | Iso Reversal | Isolation reversal |
| 80 | Tweezer Top | Reversal pattern |

---

## Advanced Patterns (81-90)

| # | Strategy | Description |
|---|----------|-------------|
| 81 | Tweezer Bottom | Reversal pattern |
| 82 | Dark Cloud Cover | Bearish pattern |
| 83 | Belt Hold | Trend start |
| 84 | Marubozu | Strong trend candle |
| 85 | Stalled Pattern | Weakness signal |
| 86 | Island Reversal | Gap reversal |
| 87 | Kicker | Strong reversal |
| 88 | Thrusting | Continuation |
| 89 | Hikkake | Pattern trap |
| 90 | Nader | Indecision pattern |

---

## Specialized Strategies (91-100)

| # | Strategy | Description |
|---|----------|-------------|
| 91 | TD Sequential | Count-based signals |
| 92 | TD Combo | Count-based signals |
| 93 | Wave Trend | WaveTrend indicator |
| 94 | Elder-Ray | Bull/bear power |
| 95 | EWO | Elliott Wave Oscillator |
| 96 | VPT | Volume Price Trend |
| 97 | NVT | Network Value to Transactions |
| 98 | Hull Suite | Hull MA variations |
| 99 | JMA | Jurik Moving Average |
| 100 | Ehlers Supertrend | Cybernetics-based |

---

## Strategy Implementation

Each strategy implements the `BaseStrategy` interface:

```python
class BaseStrategy(ABC):
    def __init__(self, name, config=None)
    def analyze(self, symbol, data) -> Optional[StrategyAlert]
```

### Usage Example

```python
from strategies_100 import get_all_strategies, STRATEGY_REGISTRY

# Get all strategies
strategies = get_all_strategies()

# Run analysis
for strategy in strategies:
    alert = strategy.analyze("AAPL", {"close": [...], "volume": [...]})
    if alert:
        print(alert.message)
```

---

## Alert Severity Levels

| Level | Value | Description |
|-------|-------|-------------|
| LOW | 1 | Informational |
| MEDIUM | 2 | Minor signals |
| HIGH | 3 | Important signals |
| CRITICAL | 4 | Urgent alerts |

---

*Generated: March 28, 2026*
*Total Strategies: 100*
