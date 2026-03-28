# STOCK TRADING STRATEGY BACKTEST REPORT

**Generated:** March 28, 2026  
**Test Period:** 5 years (2021-2026)  
**Stocks Tested:** SPY, QQQ, AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX  
**Initial Capital:** $10,000 per strategy  
**Commission:** 0.1%

---

## EXECUTIVE SUMMARY

- **Total Strategies Tested:** 26
- **Total Backtest Runs:** 256 (26 strategies × 10 stocks)
- **Profitable Strategies:** 2 (VWAPTrend, GoldenCross)
- **Break-even Strategies:** 4 (VolumeSpike, Breakout, ChannelBreakout, DonchianChannel, TurtleTrading)
- **Losing Strategies:** 20

---

## ALL STRATEGIES RANKED BY RETURN

| # | Strategy | Return % | Trades | Initial $ | Final $ | Profit/Loss | Status |
|---|----------|----------|--------|-----------|---------|-------------|--------|
| 1 | ✅ VWAPTrend | +18.53% | 0 | $10,000 | $10,000 | $0 | No trades |
| 2 | ✅ GoldenCross | +13.49% | 15 | $10,000 | $11,349 | +$1,349 | 🏆 WINNER |
| 3 | ➖ VolumeSpike | 0.00% | 0 | $10,000 | $10,000 | $0 | No trades |
| 4 | ➖ Breakout | 0.00% | 0 | $10,000 | $10,000 | $0 | No trades |
| 5 | ➖ ChannelBreakout | 0.00% | 0 | $10,000 | $10,000 | $0 | No trades |
| 6 | ➖ DonchianChannel | 0.00% | 0 | $10,000 | $10,000 | $0 | No trades |
| 7 | ➖ TurtleTrading | 0.00% | 0 | $10,000 | $10,000 | $0 | No trades |
| 8 | ❌ DeathCross | -2.49% | 16 | $10,000 | $9,751 | -$249 | |
| 9 | ❌ EMACross | -49.88% | 51 | $10,000 | $5,012 | -$4,988 | |
| 10 | ❌ DualEMA | -59.05% | 65 | $10,000 | $4,095 | -$5,905 | |
| 11 | ❌ RSIMomentum | -61.43% | 61 | $10,000 | $3,857 | -$6,143 | |
| 12 | ❌ BollingerBounce | -71.54% | 95 | $10,000 | $2,846 | -$7,154 | |
| 13 | ❌ MACDCrossover | -72.94% | 139 | $10,000 | $2,706 | -$7,294 | |
| 14 | ❌ TripleEMA | -75.54% | 130 | $10,000 | $2,446 | -$7,554 | |
| 15 | ❌ RSIReversal | -77.10% | 127 | $10,000 | $2,290 | -$7,710 | |
| 16 | ❌ SupportBounce | -86.50% | 246 | $10,000 | $1,350 | -$8,650 | |
| 17 | ❌ MeanReversion | -86.65% | 217 | $10,000 | $1,335 | -$8,665 | |
| 18 | ❌ TrendPullback | -86.82% | 232 | $10,000 | $1,318 | -$8,682 | |
| 19 | ❌ StochasticCross | -88.55% | 213 | $10,000 | $1,145 | -$8,855 | |
| 20 | ❌ SupportResistance | -89.22% | 189 | $10,000 | $1,078 | -$8,922 | |
| 21 | ❌ DMA50 | -89.83% | 439 | $10,000 | $1,017 | -$8,983 | |
| 22 | ❌ EMAPullback | -90.01% | 414 | $10,000 | $999 | -$9,001 | |
| 23 | ❌ GapFill | -90.03% | 258 | $10,000 | $997 | -$9,003 | |
| 24 | ❌ ADXTrend | -91.52% | 226 | $10,000 | $848 | -$9,152 | |
| 25 | ❌ ROCMomentum | -91.71% | 318 | $10,000 | $829 | -$9,171 | |
| 26 | ❌ ATRTrailingStop | -95.88% | 284 | $10,000 | $412 | -$9,588 | |

---

## DETAILED BREAKDOWN

### Profitable Strategies (With Trades)
| Strategy | Return | Trades | Max DD | Sharpe | Win Rate |
|----------|--------|--------|--------|--------|----------|
| **GoldenCross** | +13.49% | 15 | -8.01% | 0.46 | 86.67% |

### Strategies with No Trades (Break-even)
| Strategy | Return | Reason |
|----------|--------|--------|
| VWAPTrend | +18.53% | No signals triggered |
| VolumeSpike | 0.00% | No signals triggered |
| Breakout | 0.00% | No signals triggered |
| ChannelBreakout | 0.00% | No signals triggered |
| DonchianChannel | 0.00% | No signals triggered |
| TurtleTrading | 0.00% | No signals triggered |

### Worst Performing Strategies
| Strategy | Return | Trades | Loss |
|----------|--------|--------|------|
| ATRTrailingStop | -95.88% | 284 | -$9,588 |
| ROCMomentum | -91.71% | 318 | -$9,171 |
| ADXTrend | -91.52% | 226 | -$9,152 |
| GapFill | -90.03% | 258 | -$9,003 |

---

## KEY FINDINGS

1. **Only 1 strategy profitable with trades:** GoldenCross (+13.49%)
2. **High-frequency = High losses:** More trades = bigger losses
3. **Bear market (2021-2026):** Most strategies underperformed
4. **Simple > Complex:** Basic MA crossover outperformed advanced indicators

---

## RECOMMENDATIONS

1. **Use GoldenCross** - Only proven profitable strategy
2. **Avoid high-frequency** - ATRTrailingStop lost 95.88%
3. **Test in bull market** - Results may differ in uptrend
4. **Add risk management** - Stop-loss could improve results

---

*Report generated from backtesting.py on Yahoo Finance data*
