# STOCK TRADING STRATEGY BACKTEST REPORT
Generated: 2026-03-28 08:46:38

## Executive Summary

- **Total Strategies Tested:** 26
- **Total Backtest Runs:** 256
- **Tickers Tested:** QQQ, AMZN, MSFT, NVDA, NFLX, TSLA, SPY, GOOGL, META, AAPL
- **Time Period:** 5 years

## Top Performing Strategies

                   return  max_drawdown  sharpe  win_rate  trades
strategy                                                         
VWAPTrend           18.53         -8.07    0.46       NaN       0
GoldenCross         13.49         -8.01    0.46     86.67      15
VolumeSpike          0.00          0.00     NaN       NaN       0
Breakout             0.00          0.00     NaN       NaN       0
ChannelBreakout      0.00          0.00     NaN       NaN       0
DonchianChannel      0.00          0.00     NaN       NaN       0
TurtleTrading        0.00          0.00     NaN       NaN       0
DeathCross          -2.49         -6.39   -0.22     36.67      16
EMACross           -49.88        -69.52   -0.08     57.62      51
DualEMA            -59.05        -76.38   -0.08     51.03      65
RSIMomentum        -61.43        -79.80   -0.11     60.53      61
BollingerBounce    -71.54        -81.33   -0.06     47.89      95
MACDCrossover      -72.94        -83.16   -0.09     43.38     139
TripleEMA          -75.54        -86.69   -0.03     47.27     130
RSIReversal        -77.10        -88.17   -0.04     46.01     127
SupportBounce      -86.50        -89.39    0.02     28.33     246
MeanReversion      -86.65        -89.48    0.01     29.63     217
TrendPullback      -86.82        -89.52   -0.03     29.70     232
StochasticCross    -88.55        -91.62   -0.08     22.07     213
SupportResistance  -89.22        -92.29   -0.08     24.24     189

## Methodology

All strategies were backtested using:
- **Framework:** backtesting.py
- **Initial Capital:** $10,000
- **Commission:** 0.1%
- **Data Source:** Yahoo Finance

## Detailed Results

See: /Users/clawdbotagent/workspace/strategy_tester/results/all_results.csv

## Recommendations

Based on the backtest results, the following strategies show the most promise:
1. Highest average returns
2. Positive Sharpe ratio
3. Reasonable drawdown
4. Sufficient number of trades

---

*This is a preliminary report. Further analysis and optimization needed.*
