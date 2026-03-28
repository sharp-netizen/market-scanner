# Strategy Backtesting Framework

## Backtesting Tools
- **backtesting.py** - kernc/backtesting.py (recommended)
- **Backtrader** - feature-rich, older
- **vectorbt** - vectorized, fast

## Data Sources
- yfinance (free, Yahoo Finance)
- alpaca-market-data (paper trading)
- polygon.io (free tier)

## Initial Strategies to Test

### Momentum Strategies
1. RSI Oversold/Overbought
2. MACD Crossover
3. Moving Average Golden Cross/Death Cross
4. Price Momentum
5. Volume Spike

### Mean Reversion
6. Bollinger Bands Bounce
7. RSI Mean Reversion
8. Gap Fill Strategy
9. Pullback to EMA

### Breakout Strategies
10. Channel Breakout
11. Support/Resistance Break
12. High/Low Breakout
13. Volume-Price Breakout

### Trend Following
14. ADX Trend Strength
15. Parabolic SAR
16. Ichimoku Cloud
17. Donchian Channels

### Patterns
18. Head & Shoulders
19. Double Top/Bottom
20. Flag & Pennant

### Machine Learning
21. LSTM Price Prediction
22. Random Forest Classifier
23. Logistic Regression
24. SVM Momentum

### Sentiment
25. News Sentiment (API based)
26. Social Sentiment (Twitter)

## Reporting
- Generate performance reports in `/results`
- Track Sharpe ratio, max drawdown, win rate, profit factor
