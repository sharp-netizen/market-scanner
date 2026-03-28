#!/usr/bin/env python3
"""
Automated Strategy Discovery and Backtesting Pipeline v2
Fixed for backtesting.py compatibility
"""

import subprocess
import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
WORKSPACE = "/Users/clawdbotagent/workspace/strategy_tester"
STRATEGIES_DIR = f"{WORKSPACE}/strategies"
RESULTS_DIR = f"{WORKSPACE}/results"
DATA_DIR = f"{WORKSPACE}/data"
REPORTS_DIR = f"{WORKSPACE}/reports"

os.makedirs(STRATEGIES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

print("=" * 60)
print("AUTOMATED STRATEGY DISCOVERY & BACKTESTING PIPELINE v2")
print("=" * 60)

# Install required packages
print("\n[1/5] Installing dependencies...")
packages = ["yfinance", "backtesting", "pandas", "numpy"]
for pkg in packages:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)

print("[✓] Dependencies installed")

# Download stock data
print("\n[2/5] Downloading market data...")
import yfinance as yf

TICKERS = ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]

def download_data(ticker, period="5y"):
    try:
        data = yf.download(ticker, period=period, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        if len(data) > 100:
            data.to_csv(f"{DATA_DIR}/{ticker}.csv")
            print(f"  [✓] {ticker}: {len(data)} days")
            return True
    except Exception as e:
        print(f"  [✗] {ticker}: {e}")
    return False

for ticker in TICKERS:
    download_data(ticker)

print(f"[✓] Downloaded data for {len([f for f in os.listdir(DATA_DIR) if f.endswith('.csv')])} stocks")

# Strategy implementations
print("\n[3/5] Implementing trading strategies...")

from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# ============================================================================
# CUSTOM INDICATORS (compatible with backtesting.py)
# ============================================================================

def SMA(close, period):
    """Simple Moving Average"""
    return pd.Series(close).rolling(period).mean().values

def EMA(close, period):
    """Exponential Moving Average"""
    return pd.Series(close).ewm(span=period, adjust=False).mean().values

def RSI(close, period=14):
    """Relative Strength Index"""
    delta = pd.Series(close).diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return (100 - (100 / (1 + rs))).values

def MACD(close, fast=12, slow=26, signal=9):
    """MACD - returns (macd_line, signal_line, histogram)"""
    ema_fast = pd.Series(close).ewm(span=fast, adjust=False).mean()
    ema_slow = pd.Series(close).ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd.values, signal_line.values, (macd - signal_line).values

def BB(close, period=20, std_dev=2):
    """Bollinger Bands - returns (upper, middle, lower)"""
    sma = pd.Series(close).rolling(period).mean()
    std = pd.Series(close).rolling(period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper.values, sma.values, lower.values

def ATR(high, low, close, period=14):
    """Average True Range"""
    tr1 = pd.Series(high) - pd.Series(low)
    tr2 = abs(pd.Series(high) - pd.Series(close).shift(1))
    tr3 = abs(pd.Series(low) - pd.Series(close).shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean().values

def Stochastic(high, low, close, period=14, smooth=3):
    """Stochastic Oscillator - returns (%K, %D)"""
    lowest = pd.Series(low).rolling(period).min()
    highest = pd.Series(high).rolling(period).max()
    k = 100 * (pd.Series(close) - lowest) / (highest - lowest)
    d = k.rolling(smooth).mean()
    return k.values, d.values

def ROC(close, period=12):
    """Rate of Change"""
    return (pd.Series(close).pct_change(period) * 100).values

def ADX(high, low, close, period=14):
    """Average Directional Index"""
    plus_dm = pd.Series(high).diff()
    minus_dm = -pd.Series(low).diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    tr = ATR(high, low, close, period)
    plus_di = 100 * (pd.Series(plus_dm).rolling(period).mean() / tr)
    minus_di = 100 * (pd.Series(minus_dm).rolling(period).mean() / tr)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()
    return adx.values

# ============================================================================
# STRATEGY CLASSES
# ============================================================================

class RSIReversal(Strategy):
    """Buy when RSI < oversold, sell when RSI > overbought"""
    def init(self):
        self.rsi = self.I(RSI, self.data.Close, 14)
    
    def next(self):
        if self.rsi[-1] < 30 and not self.position:
            self.buy(size=0.1)
        elif self.rsi[-1] > 70 and self.position:
            self.sell(size=0.1)

class RSIMomentum(Strategy):
    """Buy when RSI crosses above 30, sell when crosses below 70"""
    def init(self):
        self.rsi = self.I(RSI, self.data.Close, 14)
    
    def next(self):
        if self.rsi[-1] >= 30 and self.rsi[-2] < 30 and not self.position:
            self.buy(size=0.1)
        elif self.rsi[-1] <= 70 and self.rsi[-2] > 70 and self.position:
            self.sell(size=0.1)

class GoldenCross(Strategy):
    """Buy when 50 SMA crosses above 200 SMA"""
    def init(self):
        self.sma50 = self.I(SMA, self.data.Close, 50)
        self.sma200 = self.I(SMA, self.data.Close, 200)
    
    def next(self):
        if crossover(self.sma50, self.sma200) and not self.position:
            self.buy(size=0.1)
        elif crossover(self.sma200, self.sma50) and self.position:
            self.sell(size=0.1)

class DeathCross(Strategy):
    """Buy when 50 SMA crosses below 200 SMA"""
    def init(self):
        self.sma50 = self.I(SMA, self.data.Close, 50)
        self.sma200 = self.I(SMA, self.data.Close, 200)
    
    def next(self):
        if crossover(self.sma200, self.sma50) and not self.position:
            self.buy(size=0.1)
        elif crossover(self.sma50, self.sma200) and self.position:
            self.sell(size=0.1)

class MACDCrossover(Strategy):
    """Buy when MACD crosses above signal"""
    def init(self):
        self.macd, self.signal, _ = self.I(MACD, self.data.Close)
    
    def next(self):
        if crossover(self.macd, self.signal) and not self.position:
            self.buy(size=0.1)
        elif crossover(self.signal, self.macd) and self.position:
            self.sell(size=0.1)

class BollingerBounce(Strategy):
    """Buy when price hits lower Bollinger Band"""
    def init(self):
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(BB, self.data.Close)
    
    def next(self):
        if self.data.Close[-1] < self.bb_lower[-1] and not self.position:
            self.buy(size=0.1)
        elif self.position and self.data.Close[-1] > self.bb_upper[-1]:
            self.sell(size=0.1)

class EMAPullback(Strategy):
    """Buy on pullback to EMA"""
    def init(self):
        self.ema20 = self.I(EMA, self.data.Close, 20)
        self.ema50 = self.I(EMA, self.data.Close, 50)
    
    def next(self):
        if self.data.Close[-1] > self.ema20[-1] and self.data.Close[-1] > self.ema50[-1]:
            if not self.position:
                self.buy(size=0.1)
        elif self.position and self.data.Close[-1] < self.ema20[-1]:
            self.sell(size=0.1)

class VolumeSpike(Strategy):
    """Buy when volume spikes"""
    def init(self):
        self.volume = self.data.Volume
        self.avg_volume = self.I(SMA, self.data.Volume, 20)
    
    def next(self):
        if self.volume[-1] > 2 * self.avg_volume[-1] and not self.position:
            self.buy(size=0.1)
        elif self.position and len(self.position) > 10:
            self.sell(size=0.1)

class ADXTrend(Strategy):
    """Buy when ADX indicates strong trend"""
    def init(self):
        self.adx = self.I(ADX, self.data.High, self.data.Low, self.data.Close)
    
    def next(self):
        if self.adx[-1] > 25 and not self.position:
            self.buy(size=0.1)
        elif self.position and self.adx[-1] < 20:
            self.sell(size=0.1)

class StochasticCross(Strategy):
    """Buy when Stochastic crosses above"""
    def init(self):
        self.stoch_k, self.stoch_d = self.I(Stochastic, self.data.High, self.data.Low, self.data.Close)
    
    def next(self):
        if crossover(self.stoch_k, self.stoch_d) and self.stoch_k[-1] < 80 and not self.position:
            self.buy(size=0.1)
        elif crossover(self.stoch_d, self.stoch_k) and self.stoch_k[-1] > 20 and self.position:
            self.sell(size=0.1)

class DualEMA(Strategy):
    """9/21 EMA crossover"""
    def init(self):
        self.ema9 = self.I(EMA, self.data.Close, 9)
        self.ema21 = self.I(EMA, self.data.Close, 21)
    
    def next(self):
        if crossover(self.ema9, self.ema21) and not self.position:
            self.buy(size=0.1)
        elif crossover(self.ema21, self.ema9) and self.position:
            self.sell(size=0.1)

class TripleEMA(Strategy):
    """4/9/18 EMA triple crossover"""
    def init(self):
        self.ema4 = self.I(EMA, self.data.Close, 4)
        self.ema9 = self.I(EMA, self.data.Close, 9)
        self.ema18 = self.I(EMA, self.data.Close, 18)
    
    def next(self):
        if crossover(self.ema4, self.ema9) and self.ema4[-1] > self.ema18[-1] and not self.position:
            self.buy(size=0.1)
        elif crossover(self.ema9, self.ema4) and self.position:
            self.sell(size=0.1)

class ATRTrailingStop(Strategy):
    """ATR-based trailing stop"""
    def init(self):
        self.atr = self.I(ATR, self.data.High, self.data.Low, self.data.Close)
        self.sma = self.I(SMA, self.data.Close, 20)
    
    def next(self):
        if not self.position:
            if self.data.Close[-1] > self.sma[-1]:
                self.buy(sl=self.data.Close[-1] - 2 * self.atr[-1])
        else:
            if self.data.Close[-1] < self.sma[-1]:
                self.sell(size=0.1)

class ROCMomentum(Strategy):
    """Rate of Change momentum"""
    def init(self):
        self.roc = self.I(ROC, self.data.Close, 12)
    
    def next(self):
        if self.roc[-1] > 5 and not self.position:
            self.buy(size=0.1)
        elif self.position and self.roc[-1] < 0:
            self.sell(size=0.1)

class Breakout(Strategy):
    """20-day high breakout"""
    def init(self):
        self.high20 = self.I(lambda x: pd.Series(x).rolling(20).max().values, self.data.High)
    
    def next(self):
        if self.data.Close[-1] > self.high20[-1] and not self.position:
            self.buy(size=0.1)
        elif self.position:
            self.sell(size=0.1)

class SupportBounce(Strategy):
    """Buy near support levels"""
    def init(self):
        self.low20 = self.I(lambda x: pd.Series(x).rolling(20).min().values, self.data.Low)
    
    def next(self):
        price = self.data.Close[-1]
        support = self.low20[-1]
        if price < support * 1.02 and not self.position:
            self.buy(size=0.1)
        elif self.position and price > support * 1.10:
            self.sell(size=0.1)

class GapFill(Strategy):
    """Buy on gap down, sell on fill"""
    def init(self):
        pass
    
    def next(self):
        if len(self.data.Close) < 2:
            return
        gap = (self.data.Open[-1] - self.data.Close[-2]) / self.data.Close[-2]
        if gap < -0.02 and not self.position:
            self.buy(size=0.1)
        elif self.position and self.data.Close[-1] > self.data.Open[-2]:
            self.sell(size=0.1)

class DonchianChannel(Strategy):
    """Donchian Channel breakout"""
    def init(self):
        self.donchian_high = self.I(lambda x: pd.Series(x).rolling(20).max().values, self.data.High)
        self.donchian_low = self.I(lambda x: pd.Series(x).rolling(20).min().values, self.data.Low)
    
    def next(self):
        if self.data.Close[-1] > self.donchian_high[-1] and not self.position:
            self.buy(size=0.1)
        elif self.position and self.data.Close[-1] < self.donchian_low[-1]:
            self.sell(size=0.1)

class MeanReversion(Strategy):
    """Mean reversion to 20-day SMA"""
    def init(self):
        self.sma20 = self.I(SMA, self.data.Close, 20)
    
    def next(self):
        deviation = (self.data.Close[-1] - self.sma20[-1]) / self.sma20[-1]
        if deviation < -0.03 and not self.position:
            self.buy(size=0.1)
        elif self.position and deviation > 0.02:
            self.sell(size=0.1)

class TurtleTrading(Strategy):
    """Turtle trading strategy"""
    def init(self):
        self.high20 = self.I(lambda x: pd.Series(x).rolling(20).max().values, self.data.High)
        self.low20 = self.I(lambda x: pd.Series(x).rolling(20).min().values, self.data.Low)
    
    def next(self):
        if self.data.Close[-1] > self.high20[-1] and not self.position:
            self.buy(size=0.1)
        elif self.position and self.data.Close[-1] < self.low20[-1]:
            self.sell(size=0.1)

class ChannelBreakout(Strategy):
    """20-day channel breakout"""
    def init(self):
        self.channel_high = self.I(lambda x: pd.Series(x).rolling(20).max().values, self.data.High)
        self.channel_low = self.I(lambda x: pd.Series(x).rolling(20).min().values, self.data.Low)
    
    def next(self):
        if self.data.Close[-1] > self.channel_high[-1] and not self.position:
            self.buy(size=0.1)
        elif self.position and self.data.Close[-1] < self.channel_low[-1]:
            self.sell(size=0.1)

class VWAPTrend(Strategy):
    """VWAP-based trend following"""
    def init(self):
        typical = (self.data.High + self.data.Low + self.data.Close) / 3
        self.vwap = self.I(lambda x: pd.Series(x).expanding().mean().values, 
                          typical * self.data.Volume) / self.I(lambda x: pd.Series(x).expanding().sum().values, self.data.Volume)
    
    def next(self):
        if self.data.Close[-1] > self.vwap[-1] and not self.position:
            self.buy(size=0.1)
        elif self.position and self.data.Close[-1] < self.vwap[-1]:
            self.sell(size=0.1)

class EMACross(Strategy):
    """EMA 12/26 crossover"""
    def init(self):
        self.ema12 = self.I(EMA, self.data.Close, 12)
        self.ema26 = self.I(EMA, self.data.Close, 26)
    
    def next(self):
        if crossover(self.ema12, self.ema26) and not self.position:
            self.buy(size=0.1)
        elif crossover(self.ema26, self.ema12) and self.position:
            self.sell(size=0.1)

class DMA50(Strategy):
    """50-day moving average trend"""
    def init(self):
        self.sma50 = self.I(SMA, self.data.Close, 50)
    
    def next(self):
        if self.data.Close[-1] > self.sma50[-1] and not self.position:
            self.buy(size=0.1)
        elif self.position and self.data.Close[-1] < self.sma50[-1]:
            self.sell(size=0.1)

class SupportResistance(Strategy):
    """Buy at support, sell at resistance"""
    def init(self):
        self.high10 = self.I(lambda x: pd.Series(x).rolling(10).max().values, self.data.High)
        self.low10 = self.I(lambda x: pd.Series(x).rolling(10).min().values, self.data.Low)
    
    def next(self):
        if self.data.Close[-1] < self.low10[-1] * 1.01 and not self.position:
            self.buy(size=0.1)
        elif self.position and self.data.Close[-1] > self.high10[-1] * 0.99:
            self.sell(size=0.1)

class TrendPullback(Strategy):
    """Buy on trend pullback to SMA"""
    def init(self):
        self.sma20 = self.I(SMA, self.data.Close, 20)
        self.sma50 = self.I(SMA, self.data.Close, 50)
    
    def next(self):
        trend_up = self.sma20[-1] > self.sma50[-1]
        pullback = self.data.Close[-1] < self.sma20[-1] * 0.98
        if trend_up and pullback and not self.position:
            self.buy(size=0.1)
        elif self.position:
            if self.data.Close[-1] > self.sma20[-1] * 1.02:
                self.sell(size=0.1)

# Register all strategies
STRATEGIES = {
    "RSIReversal": RSIReversal,
    "RSIMomentum": RSIMomentum,
    "GoldenCross": GoldenCross,
    "DeathCross": DeathCross,
    "MACDCrossover": MACDCrossover,
    "BollingerBounce": BollingerBounce,
    "EMAPullback": EMAPullback,
    "VolumeSpike": VolumeSpike,
    "ADXTrend": ADXTrend,
    "StochasticCross": StochasticCross,
    "DualEMA": DualEMA,
    "TripleEMA": TripleEMA,
    "ATRTrailingStop": ATRTrailingStop,
    "ROCMomentum": ROCMomentum,
    "Breakout": Breakout,
    "SupportBounce": SupportBounce,
    "GapFill": GapFill,
    "DonchianChannel": DonchianChannel,
    "MeanReversion": MeanReversion,
    "TurtleTrading": TurtleTrading,
    "ChannelBreakout": ChannelBreakout,
    "VWAPTrend": VWAPTrend,
    "EMACross": EMACross,
    "DMA50": DMA50,
    "SupportResistance": SupportResistance,
    "TrendPullback": TrendPullback,
}

print(f"[✓] Implemented {len(STRATEGIES)} strategies")

# ============================================================================
# BACKTESTING ENGINE
# ============================================================================

print("\n[4/5] Running backtests...")

def run_backtest(strategy_class, ticker, cash=10000, commission=0.001):
    """Run backtest for a strategy on a ticker"""
    try:
        data = pd.read_csv(f"{DATA_DIR}/{ticker}.csv", parse_dates=True, index_col=0)
        if len(data) < 100:
            return None
        
        bt = Backtest(data, strategy_class, cash=cash, commission=commission)
        result = bt.run()
        
        return {
            "strategy": strategy_class.__name__,
            "ticker": ticker,
            "return": result["Return [%]"],
            "max_drawdown": result["Max. Drawdown [%]"],
            "sharpe": result.get("Sharpe Ratio", 0) or 0,
            "win_rate": result.get("Win Rate [%]", 0) or 0,
            "trades": result["# Trades"],
            "profit_factor": result.get("Profit Factor", 0) or 0,
            "avg_trade": result.get("Avg. Trade [%]", 0) or 0,
        }
    except Exception as e:
        print(f"    Error: {e}")
        return None

results = []
test_tickers = [f.replace('.csv', '') for f in os.listdir(DATA_DIR) if f.endswith('.csv')]

for strategy_name, strategy_class in STRATEGIES.items():
    for ticker in test_tickers:
        result = run_backtest(strategy_class, ticker)
        if result:
            results.append(result)
            print(f"  {strategy_name} on {ticker}: Return {result['return']:.2f}%")

print(f"[✓] Completed {len(results)} backtest runs")

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv(f"{RESULTS_DIR}/all_results.csv", index=False)

# Aggregate by strategy
if len(results_df) > 0:
    strategy_summary = results_df.groupby("strategy").agg({
        "return": "mean",
        "max_drawdown": "mean",
        "sharpe": "mean",
        "win_rate": "mean",
        "trades": "sum"
    }).round(2)
    strategy_summary = strategy_summary.sort_values("return", ascending=False)
    strategy_summary.to_csv(f"{RESULTS_DIR}/strategy_summary.csv")
    
    print("\n" + "=" * 60)
    print("TOP 10 STRATEGIES BY AVERAGE RETURN")
    print("=" * 60)
    print(strategy_summary.head(10).to_string())

# ============================================================================
# GENERATE REPORT
# ============================================================================

print("\n[5/5] Generating final report...")

report = f"""# STOCK TRADING STRATEGY BACKTEST REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Strategies Tested:** {len(STRATEGIES)}
- **Total Backtest Runs:** {len(results)}
- **Tickers Tested:** {', '.join(test_tickers)}
- **Time Period:** 5 years

## Top Performing Strategies

{strategy_summary.head(20).to_string() if len(results_df) > 0 else "No results yet"}

## Methodology

All strategies were backtested using:
- **Framework:** backtesting.py
- **Initial Capital:** $10,000
- **Commission:** 0.1%
- **Data Source:** Yahoo Finance

## Detailed Results

See: {RESULTS_DIR}/all_results.csv

## Recommendations

Based on the backtest results, the following strategies show the most promise:
1. Highest average returns
2. Positive Sharpe ratio
3. Reasonable drawdown
4. Sufficient number of trades

---

*This is a preliminary report. Further analysis and optimization needed.*
"""

with open(f"{REPORTS_DIR}/strategy_report.md", "w") as f:
    f.write(report)

print(f"[✓] Report saved to {REPORTS_DIR}/strategy_report.md")
print("\n" + "=" * 60)
print("PIPELINE COMPLETE")
print("=" * 60)

# Save state
state = {
    "strategies_implemented": len(STRATEGIES),
    "backtests_run": len(results),
    "last_updated": datetime.now().isoformat(),
    "target": 100
}

with open(f"{WORKSPACE}/pipeline_state.json", "w") as f:
    json.dump(state, f, indent=2)

print(f"\nProgress: {len(STRATEGIES)}/100 strategies implemented")
