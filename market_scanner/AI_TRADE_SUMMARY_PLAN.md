# Market Scanner - AI Trade Summary Feature

**Date:** Tue 2026-02-10

## Status: Parked

## Where We Left Off

### Idea
Enrich pattern triggers with news correlation using LLM:
- Pattern fires → Search news → LLM analyzes → Trade idea with catalyst

### Files Created
- `/Users/clawdbotagent/workspace/market_scanner/trade_summary_ai.py` — Full prototype architecture

### Architecture
```
PatternContext → [NewsFetcher × N] → LLMProcessor → EnrichedTradeIdea
```

### Key Components
- `PatternContext` — wraps alert data
- `NewsFetcher` — pluggable (Google News, Finviz, Twitter)
- `LLMProcessor` — pluggable (Ollama local, OpenAI API)
- `TradeIdeaGenerator` — orchestrator

### Output Fields
- `news_summary`, `trade_idea`, `catalyst`, `confidence`, `risk_level`, `entry/exit`

## Next Steps
1. Test with one ticker
2. Hook into `main_async.py` pattern triggers
3. Add actual web search/fetch calls
4. Configure LLM (Ollama vs OpenAI)

## Ref
Original brainstorm in `trade_summary_ai.py` comments.
