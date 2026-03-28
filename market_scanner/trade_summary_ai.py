"""
AI Trade Summary System
Correlates pattern triggers with news for enriched trade ideas.

Architecture:
    Pattern Trigger → NewsFetcher → LLMProcessor → EnrichedTradeIdea
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PatternContext:
    """Context when a pattern triggers."""
    ticker: str
    pattern_name: str
    pattern_type: str  # bullish / bearish / neutral
    price_change: float
    volume_change: float
    timeframe: str
    additional_data: Dict[str, Any]  # RSI, momentum, etc.


@dataclass
class NewsResult:
    """News article or result."""
    title: str
    url: str
    source: str
    published_at: str
    snippet: Optional[str] = None


@dataclass
class EnrichedTradeIdea:
    """Final output: pattern + news + trade recommendation."""
    ticker: str
    pattern_name: str
    news_summary: str
    trade_idea: str
    catalyst: str  # earnings, product, analyst, deal, etc.
    confidence: str  # high / medium / low
    risk_level: str  # high / medium / low
    entry_suggestion: Optional[str] = None
    exit_suggestion: Optional[str] = None
    generated_at: datetime = None


# =============================================================================
# NEWS FETCHERS (Pluggable)
# =============================================================================

class NewsFetcher(ABC):
    """Abstract base for news sources."""
    
    @abstractmethod
    async def fetch(self, ticker: str, hours_back: int = 24) -> List[NewsResult]:
        pass


class GoogleNewsFetcher(NewsFetcher):
    """Fetch news via web search."""
    
    async def fetch(self, ticker: str, hours_back: int = 24) -> List[NewsResult]:
        # Uses web_search tool
        from web_search import web_search
        query = f"{ticker} stock news today"
        results = await web_search(query=query, count=5)
        # Parse and return NewsResult objects
        ...


class TwitterFetcher(NewsFetcher):
    """Fetch tweets via Twitter/X API."""
    
    async def fetch(self, ticker: str, hours_back: int = 24) -> List[NewsResult]:
        # Would use Twitter API or wacli
        ...


class FinvizFetcher(NewsFetcher):
    """Fetch from Finviz (free, no API key)."""
    
    async def fetch(self, ticker: str, hours_back: int = 24) -> List[NewsResult]:
        # Use web_fetch to scrape finviz.com/quote.ashx?t={ticker}
        ...


# =============================================================================
# LLM PROCESSORS
# =============================================================================

class LLMProcessor(ABC):
    """Abstract base for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass


class OllamaProcessor(LLMProcessor):
    """Local Ollama (Llama3/Mistral)."""
    
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    async def generate(self, prompt: str) -> str:
        # Call Ollama API
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt}
            )
            return response.json()["response"]


class OpenAIProcessor(LLMProcessor):
    """OpenAI API (GPT-4o-mini for speed/cost)."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
    
    async def generate(self, prompt: str) -> str:
        # Call OpenAI API
        ...


# =============================================================================
# TRADE IDEA GENERATOR (Orchestrator)
# =============================================================================

class TradeIdeaGenerator:
    """
    Main orchestrator:
    1. Receives pattern trigger
    2. Fetches news from multiple sources
    3. Sends to LLM for analysis
    4. Returns enriched trade idea
    """
    
    def __init__(
        self,
        news_fetchers: List[NewsFetcher],
        llm_processor: LLMProcessor,
        max_news_items: int = 10
    ):
        self.news_fetchers = news_fetchers
        self.llm = llm_processor
        self.max_news_items = max_news_items
    
    async def generate(self, context: PatternContext) -> EnrichedTradeIdea:
        # Step 1: Fetch news concurrently
        news_results = await self._fetch_news(context.ticker)
        
        # Step 2: Build prompt
        prompt = self._build_prompt(context, news_results)
        
        # Step 3: Send to LLM
        raw_response = await self.llm.generate(prompt)
        
        # Step 4: Parse response
        trade_idea = self._parse_response(context, news_results, raw_response)
        
        return trade_idea
    
    async def _fetch_news(self, ticker: str) -> List[NewsResult]:
        """Fetch news from all sources concurrently."""
        tasks = [fetcher.fetch(ticker) for fetcher in self.news_fetchers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and dedupe
        all_news = []
        for r in results:
            if isinstance(r, list):
                all_news.extend(r)
        
        return all_news[:self.max_news_items]
    
    def _build_prompt(self, context: PatternContext, news: List[NewsResult]) -> str:
        """Build the LLM prompt."""
        
        news_text = "\n".join([
            f"- {n.title} ({n.source})" for n in news[:5]
        ]) or "No recent news found."
        
        prompt = f"""
Ticker: {context.ticker}
Pattern: {context.pattern_name} ({context.pattern_type})
Price Change: {context.price_change:+.2f}%
Volume Change: {context.volume_change:+.2f}x
Timeframe: {context.timeframe}

Recent News:
{news_text}

Analyze and output JSON with:
- news_summary (2-3 sentences)
- trade_idea (concise recommendation)
- catalyst (earnings/product/analyst/deal/sentiment/unknown)
- confidence (high/medium/low)
- risk_level (high/medium/low)
- entry_suggestion (optional)
- exit_suggestion (optional)

JSON:
"""
        return prompt
    
    def _parse_response(
        self,
        context: PatternContext,
        news: List[NewsResult],
        raw_response: str
    ) -> EnrichedTradeIdea:
        """Parse LLM response into EnrichedTradeIdea."""
        import json
        
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError:
            # Fallback: try to extract from text
            data = {"trade_idea": raw_response, "confidence": "low"}
        
        return EnrichedTradeIdea(
            ticker=context.ticker,
            pattern_name=context.pattern_name,
            news_summary=data.get("news_summary", "Analysis unavailable"),
            trade_idea=data.get("trade_idea", "No clear setup"),
            catalyst=data.get("catalyst", "unknown"),
            confidence=data.get("confidence", "medium"),
            risk_level=data.get("risk_level", "medium"),
            entry_suggestion=data.get("entry_suggestion"),
            exit_suggestion=data.get("exit_suggestion"),
            generated_at=datetime.now()
        )


# =============================================================================
# INTEGRATION WITH EXISTING SCANNER
# =============================================================================

# In your main_async.py, when a pattern triggers:

async def on_pattern_trigger(alert: Alert, scanner: MarketScanner):
    """Hook into existing pattern detection."""
    
    # 1. Create context
    context = PatternContext(
        ticker=alert.ticker,
        pattern_name=alert.pattern_name,
        pattern_type=alert.pattern_type,
        price_change=alert.price_change,
        volume_change=alert.volume_multiplier,
        timeframe="1min",  # or current TF
        additional_data={"rsi": alert.rsi, "momentum": alert.momentum}
    )
    
    # 2. Generate enriched trade idea
    trade_idea = await trade_generator.generate(context)
    
    # 3. Output with enhanced info
    output_manager.output({
        "type": "enriched_alert",
        "ticker": trade_idea.ticker,
        "pattern": trade_idea.pattern_name,
        "trade_idea": trade_idea.trade_idea,
        "news_summary": trade_idea.news_summary,
        "catalyst": trade_idea.catalyst,
        "confidence": trade_idea.confidence,
        "risk": trade_idea.risk_level
    })


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

async def main():
    """Demo the trade idea generator."""
    
    # Setup components
    news_fetchers = [
        GoogleNewsFetcher(),
        FinvizFetcher(),
    ]
    
    llm = OllamaProcessor(model="llama3")
    
    generator = TradeIdeaGenerator(
        news_fetchers=news_fetchers,
        llm_processor=llm
    )
    
    # Simulate pattern trigger
    context = PatternContext(
        ticker="META",
        pattern_name="GreenStreak + VolumeSurge",
        pattern_type="bullish",
        price_change=5.2,
        volume_change=2.8,
        timeframe="15min",
        additional_data={"rsi": 68, "momentum": 0.75}
    )
    
    result = await generator.generate(context)
    
    print(f"\n{'='*60}")
    print(f"TICKER: {result.ticker}")
    print(f"PATTERN: {result.pattern_name}")
    print(f"\n📰 NEWS SUMMARY:")
    print(f"{result.news_summary}")
    print(f"\n💡 TRADE IDEA:")
    print(f"{result.trade_idea}")
    print(f"\n⚡ CATALYST: {result.catalyst.upper()}")
    print(f"📊 CONFIDENCE: {result.confidence.upper()}")
    print(f"⚠️ RISK: {result.risk_level.upper()}")


if __name__ == "__main__":
    asyncio.run(main())
