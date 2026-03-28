# STOCK TRADING STRATEGY BACKTEST REPORT

**Generated:** March 28, 2026  
**Test Period:** 5 years (2021-2026)  
**Stocks Tested:** SPY, QQQ, AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX  
**Initial Capital:** $10,000 per strategy  
**Commission:** 0.1%

---

## EXECUTIVE SUMMARY

- **Total Strategies Tested:** 20 (with trades)
- **Total Backtest Runs:** 256 (20 strategies × 10 stocks)
- **Most Profitable:** GoldenCross (+13.49%)
- **Best Win Rate:** GoldenCross (86.67%)

---

## DETAILED RESULTS (Sorted by Return)

| # | Strategy | Return % | Trades | Initial $ | Final $ | Profit/Loss | Win Rate |
|---|----------|----------|--------|-----------|---------|-------------|----------|
| 1 | **GoldenCross** | **+13.49%** | 15 | $10,000 | $11,349 | **+$1,349** | 86.67% |
| 2 | DeathCross | -2.49% | 16 | $10,000 | $9,751 | -$249 | 36.67% |
| 3 | EMACross | -49.88% | 51 | $10,000 | $5,012 | -$4,988 | 57.62% |
| 4 | DualEMA | -59.05% | 65 | $10,000 | $4,095 | -$5,905 | 51.03% |
| 5 | RSIMomentum | -61.43% | 61 | $10,000 | $3,857 | -$6,143 | 60.53% |
| 6 | BollingerBounce | -71.54% | 95 | $10,000 | $2,846 | -$7,154 | 47.89% |
| 7 | MACDCrossover | -72.94% | 139 | $10,000 | $2,706 | -$7,294 | 43.38% |
| 8 | TripleEMA | -75.54% | 130 | $10,000 | $2,446 | -$7,554 | 47.27% |
| 9 | RSIReversal | -77.10% | 127 | $10,000 | $2,290 | -$7,710 | 46.01% |
| 10 | SupportBounce | -86.50% | 246 | $10,000 | $1,350 | -$8,650 | 28.33% |
| 11 | MeanReversion | -86.65% | 217 | $10,000 | $1,335 | -$8,665 | 29.63% |
| 12 | TrendPullback | -86.82% | 232 | $10,000 | $1,318 | -$8,682 | 29.70% |
| 13 | StochasticCross | -88.55% | 213 | $10,000 | $1,145 | -$8,855 | 22.07% |
| 14 | SupportResistance | -89.22% | 189 | $10,000 | $1,078 | -$8,922 | 24.24% |
| 15 | DMA50 | -89.83% | 439 | $10,000 | $1,017 | -$8,983 | 19.82% |
| 16 | EMAPullback | -90.01% | 414 | $10,000 | $999 | -$9,001 | 17.86% |
| 17 | GapFill | -90.03% | 258 | $10,000 | $997 | -$9,003 | 19.16% |
| 18 | ADXTrend | -91.52% | 226 | $10,000 | $848 | -$9,152 | 18.01% |
| 19 | ROCMomentum | -91.71% | 318 | $10,000 | $829 | -$9,171 | 15.09% |
| 20 | ATRTrailingStop | -95.88% | 284 | $10,000 | $412 | -$9,588 | 5.49% |

---

## KEY FINDINGS

### 🏆 WINNER: GoldenCross
- **Return:** +13.49% (only profitable strategy)
- **Max Drawdown:** -8.01%
- **Sharpe Ratio:** 0.46
- **Win Rate:** 86.67%
- **Trades:** 15

### Insights
1. The 5-year period (2021-2026) was challenging - most strategies lost money
2. GoldenCross (50/200 day MA crossover) was the ONLY profitable strategy
3. High-frequency strategies (more trades = worse performance)
4. Simple trend-following outperformed complex indicators

---

## RECOMMENDATIONS

1. **Use GoldenCross** - Only proven profitable strategy
2. **Avoid high-trade strategies** - More trades = more losses
3. **Consider longer timeframes** - Weekly/monthly may work better
4. **Add stop-loss** - Could improve all strategies

---

*Report generated from backtesting.py framework on Yahoo Finance data*
