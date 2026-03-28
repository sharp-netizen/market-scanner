#!/usr/bin/env python3
"""
High-Frequency Market Scanner
Async-based architecture (no multiprocessing)

Usage:
    python3 main_async.py [--config config.yaml] [--mtf]

Features:
- Crypto: Coinbase Pro (real-time via REST polling)
- Stocks: Alpaca (free real-time via REST polling)
- Options: QuiverQuant (unusual activity, delayed)
- Patterns: GreenStreak, VolumeSurge, Momentum, RSI
- Multi-Timeframe: Alignment analysis across 1min-4hr
"""

import argparse
import asyncio
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

import yaml
import numpy as np

# Import our modules
from providers import ProviderFactory, TradeData, AbstractProvider
from data_engine import DataEngine
from patterns import PatternManager, Alert, GreenStreakPattern, VolumeSurgePattern, MomentumPattern, RSIDivergencePattern
from output import OutputManager, ConsoleOutput, LogFileOutput, MockExecutorOutput, TelegramOutput, DiscordWebhookOutput

# Multi-Timeframe modules
try:
    from multi_timeframe_engine import MultiTimeframeEngine, Candle
    from mtf_patterns import MultiTimeframeAnalyzer, MultiTimeframeAlert
    MTF_AVAILABLE = True
except ImportError as e:
    print(f"[Scanner] MTF modules not available: {e}")
    MTF_AVAILABLE = False

# Options modules
try:
    from quiverquant import QuiverQuantProvider, OptionData
    from options_patterns import OptionsPatternManager, OptionAlert
    OPTIONS_QUIVER_AVAILABLE = True
except ImportError:
    OPTIONS_QUIVER_AVAILABLE = False

try:
    from yahoo_options import YahooOptionsProvider, YahooOption
    YAHOO_OPTIONS_AVAILABLE = True
except ImportError:
    YAHOO_OPTIONS_AVAILABLE = False


class MarketScanner:
    """
    Async Market Scanner
    
    Uses asyncio for concurrent operations instead of multiprocessing.
    Better for I/O-bound tasks (WebSocket, HTTP).
    """
    
    def __init__(self, config_path: str = "config.yaml", mtf_mode: bool = False):
        self.config_path = config_path
        self.config: Dict = {}
        self.mtf_mode = mtf_mode
        
        # Core components
        self.data_engine: Optional[DataEngine] = None
        self.pattern_manager: Optional[PatternManager] = None
        self.output_manager: Optional[OutputManager] = None
        self.provider: Optional[AbstractProvider] = None
        
        # Multi-Timeframe components
        self.mtf_engine: Optional[MultiTimeframeEngine] = None
        self.mtf_analyzer: Optional[MultiTimeframeAnalyzer] = None
        self._mtf_task: Optional[asyncio.Task] = None
        
        # State
        self._running = False
        self._trades_processed = 0
        self._alerts_processed = 0
        self._mtf_alerts_processed = 0
        
        # Setup
        self._load_config()
        self._setup_components()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            config_file = Path(__file__).parent / "config.yaml"
        
        if config_file.exists():
            with open(config_file) as f:
                self.config = yaml.safe_load(f)
            print(f"[Scanner] Loaded config from {config_file}")
        else:
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "provider": "alpaca",
            "tickers": ["AAPL", "TSLA", "NVDA", "AMD"],
            "data_engine": {"window_size": 100, "max_tickers": 100},
            "patterns": {
                "green_streak": {"enabled": True, "streak_length": 5},
                "volume_surge": {"enabled": True, "surge_multiplier": 2.0},
                "momentum": {"enabled": True, "lookback": 10, "threshold": 2.0},
                "rsi_divergence": {"enabled": True, "period": 14, "overbought": 70, "oversold": 30}
            },
            "output": {
                "console": {"enabled": True, "rich_dashboard": False},
                "log_file": {"enabled": True, "path": "logs/scanner.log"},
                "mock_executor": {"enabled": True},
                "telegram": {"enabled": True, "token": "8503878440:AAEa2RlNR4Q-Q1oW-IXRHm-9J0BJT3LfyoU", "chat_id": "6975285448", "parse_mode": "HTML"}
            }
        }
    
    def _setup_components(self) -> None:
        """Initialize all components"""
        print("[Scanner] Setting up components...")
        
        # Data Engine
        de_config = self.config.get("data_engine", {})
        self.data_engine = DataEngine(
            window_size=de_config.get("window_size", 100),
            max_tickers=de_config.get("max_tickers", 100)
        )
        
        # Pattern Manager
        self.pattern_manager = PatternManager()
        pattern_configs = self.config.get("patterns", {})
        
        if pattern_configs.get("green_streak", {}).get("enabled"):
            self.pattern_manager.register(GreenStreakPattern(pattern_configs.get("green_streak")))
        if pattern_configs.get("volume_surge", {}).get("enabled"):
            self.pattern_manager.register(VolumeSurgePattern(pattern_configs.get("volume_surge")))
        if pattern_configs.get("momentum", {}).get("enabled"):
            self.pattern_manager.register(MomentumPattern(pattern_configs.get("momentum")))
        if pattern_configs.get("rsi_divergence", {}).get("enabled"):
            self.pattern_manager.register(RSIDivergencePattern(pattern_configs.get("rsi_divergence")))
        
        # Output Manager
        self.output_manager = OutputManager()
        output_configs = self.config.get("output", {})
        
        if output_configs.get("console", {}).get("enabled"):
            self.output_manager.register(ConsoleOutput(output_configs.get("console")))
        if output_configs.get("log_file", {}).get("enabled"):
            self.output_manager.register(LogFileOutput(output_configs.get("log_file")))
        if output_configs.get("mock_executor", {}).get("enabled"):
            self.output_manager.register(MockExecutorOutput(output_configs.get("mock_executor")))
        if output_configs.get("telegram", {}).get("enabled"):
            self.output_manager.register(TelegramOutput(output_configs.get("telegram")))
        if output_configs.get("discord", {}).get("enabled"):
            self.output_manager.register(DiscordWebhookOutput(output_configs.get("discord")))
        
        # Multi-Timeframe Engine (if enabled and available)
        if self.mtf_mode and MTF_AVAILABLE:
            self._setup_mtf_components()
        elif self.mtf_mode and not MTF_AVAILABLE:
            print("[Scanner] WARNING: MTF mode enabled but modules not available")
        
        print("[Scanner] Components initialized")
    
    def _setup_mtf_components(self) -> None:
        """Initialize Multi-Timeframe components"""
        print("[Scanner] Setting up MTF components...")
        
        mtf_config = self.config.get("multi_timeframe", {})
        
        if not mtf_config.get("enabled", False):
            print("[Scanner] MTF disabled in config")
            self.mtf_mode = False
            return
        
        tickers = self.config.get("tickers", [])
        
        # Create MTF engine
        self.mtf_engine = MultiTimeframeEngine(tickers)
        
        # Create MTF analyzer with config
        analyzer_config = mtf_config.get("patterns", {})
        self.mtf_analyzer = MultiTimeframeAnalyzer(
            self.mtf_engine,
            config={
                "trend_threshold": analyzer_config.get("trend", {}).get("threshold", 0.5),
                "alignment_threshold": analyzer_config.get("alignment", {}).get("threshold", 60),
                "volume_surge_threshold": analyzer_config.get("smart_money", {}).get("volume_surge_threshold", 3.0)
            }
        )
        
        print(f"[Scanner] MTF Engine initialized for {len(tickers)} tickers")
    
    def _on_trade(self, trade: TradeData) -> None:
        """Handle incoming trade"""
        self._trades_processed += 1
        
        # Update data engine (pass cumulative_volume)
        self.data_engine.update(trade.symbol, trade.price, trade.size, trade.timestamp, trade.cumulative_volume)
        
        # Update MTF engine (if enabled)
        if self.mtf_mode and self.mtf_engine:
            self.mtf_engine.add_tick(
                symbol=trade.symbol,
                price=trade.price,
                size=trade.size,
                timestamp=trade.timestamp
            )
        
        # Get data for analysis
        prices = self.data_engine.get_price_array(trade.symbol)
        sizes = self.data_engine.get_size_array(trade.symbol)
        cumulative_volume = self.data_engine.get_cumulative_volume(trade.symbol)  # NEW
        
        if prices is not None and len(prices) >= 15:
            # Run patterns (pass cumulative_volume)
            alerts = self.pattern_manager.analyze_all(trade.symbol, prices, sizes, cumulative_volume=cumulative_volume)
            
            for alert in alerts:
                self.output_manager.send(alert)
                self._alerts_processed += 1
    
    async def _run_mtf_analysis(self) -> None:
        """Run periodic MTF analysis"""
        print("[Scanner] MTF analysis loop started")
        
        while self._running:
            try:
                if self.mtf_analyzer and self.mtf_engine:
                    tickers = self.config.get("tickers", [])
                    
                    for symbol in tickers:
                        alerts = self.mtf_analyzer.analyze_symbol(symbol)
                        
                        for alert in alerts:
                            self.output_manager.send(alert)
                            self._mtf_alerts_processed += 1
                
                await asyncio.sleep(30)  # Analyze every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Scanner] MTF analysis error: {e}")
                await asyncio.sleep(5)
    
    async def _run_async(self) -> None:
        """Main async run loop"""
        mode = self.config.get("mode", "single")
        
        if mode == "aggregator":
            await self._run_aggregator()
        else:
            await self._run_single()
    
    async def _run_single(self) -> None:
        """Run single provider"""
        provider_type = self.config.get("provider", "alpaca")
        provider_config = self.config.get(provider_type, {})
        tickers = self.config.get("tickers", [])
        
        self.provider = ProviderFactory.create(provider_type, provider_config, self._on_trade)
        
        print(f"[Scanner] Starting {provider_type}...")
        print(f"[Scanner] Tickers: {tickers}")
        print(f"[Scanner] Patterns: {self.pattern_manager.get_enabled_patterns()}")
        
        if self.mtf_mode:
            print(f"[Scanner] MTF Mode: ENABLED (1min-4hr alignment)")
        
        await self.provider.connect()
        await self.provider.subscribe(tickers)
        
        # Start MTF analysis loop
        if self.mtf_mode and self.mtf_analyzer:
            self._mtf_task = asyncio.create_task(self._run_mtf_analysis())
        
        print(f"\n[Scanner] Running... Press Ctrl+C to stop\n")
        
        await self.provider.start()
        
        while self._running:
            await asyncio.sleep(1)
        
        # Cancel MTF task
        if self._mtf_task:
            self._mtf_task.cancel()
            try:
                await self._mtf_task
            except asyncio.CancelledError:
                pass
    
    async def _run_aggregator(self) -> None:
        """Run aggregator with multiple providers"""
        aggregator_config = self.config.get("aggregator", {})
        
        # Create aggregator
        self.provider = ProviderFactory.create(
            "aggregator",
            aggregator_config,
            self._on_trade
        )
        
        # Get all tickers from providers
        all_tickers = set()
        for p_config in aggregator_config.get("providers", []):
            all_tickers.update(p_config.get("tickers", []))
        
        print(f"[Scanner] Starting Aggregator...")
        print(f"[Scanner] Tickers: {list(all_tickers)}")
        print(f"[Scanner] Providers: {len(aggregator_config.get('providers', []))}")
        print(f"[Scanner] Patterns: {self.pattern_manager.get_enabled_patterns()}")
        
        if self.mtf_mode:
            print(f"[Scanner] MTF Mode: ENABLED")
        
        await self.provider.connect()
        await self.provider.subscribe()
        
        # Start MTF analysis loop
        if self.mtf_mode and self.mtf_analyzer:
            self._mtf_task = asyncio.create_task(self._run_mtf_analysis())
        
        print(f"\n[Scanner] Running... Press Ctrl+C to stop\n")
        
        await self.provider.start()
        
        while self._running:
            await asyncio.sleep(1)
        
        # Cancel MTF task
        if self._mtf_task:
            self._mtf_task.cancel()
            try:
                await self._mtf_task
            except asyncio.CancelledError:
                pass
    
    def start(self) -> None:
        """Start the scanner"""
        self._running = True
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            asyncio.run(self._run_async())
        except KeyboardInterrupt:
            print("\n[Scanner] Interrupted")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the scanner"""
        print("\n[Scanner] Stopping...")
        self._running = False
        
        if self.provider:
            try:
                asyncio.run(self.provider.disconnect())
            except:
                pass
        
        if self.output_manager:
            self.output_manager.close()
        
        stats = self.get_stats()
        print(f"\n[Scanner] Final Stats:")
        print(f"  Trades: {stats['trades_processed']}")
        print(f"  Alerts: {stats['alerts_processed']}")
        print(f"  MTF Alerts: {stats.get('mtf_alerts_processed', 0)}")
        if self.mtf_mode:
            print(f"  MTF Status: Engine running={self.mtf_engine is not None}")
        print("[Scanner] Stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n[Scanner] Received signal {signum}")
        self.stop()
        sys.exit(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scanner statistics"""
        stats = {
            "running": self._running,
            "trades_processed": self._trades_processed,
            "alerts_processed": self._alerts_processed,
            "mtf_alerts_processed": self._mtf_alerts_processed,
            "data_engine": self.data_engine.get_stats() if self.data_engine else {},
            "patterns_enabled": self.pattern_manager.get_enabled_patterns() if self.pattern_manager else [],
            "outputs_enabled": self.output_manager.get_enabled_outputs() if self.output_manager else [],
            "mtf_mode": self.mtf_mode,
            "mtf_engine_running": self.mtf_engine is not None
        }
        return stats


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="High-Frequency Market Scanner")
    parser.add_argument("--config", "-c", default="config.yaml", help="Path to config file")
    parser.add_argument("--mtf", action="store_true", help="Enable multi-timeframe analysis")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    
    print("=" * 60)
    print("High-Frequency Market Scanner")
    print("Async Architecture + Multi-Timeframe Analysis")
    print("=" * 60)
    
    # Create scanner
    scanner = MarketScanner(config_path=args.config, mtf_mode=args.mtf)
    
    # Print initial stats
    print("\nConfiguration:")
    print(f"  Provider: {scanner.config.get('provider', 'alpaca')}")
    print(f"  Tickers: {scanner.config.get('tickers', [])}")
    print(f"  Patterns: {scanner.pattern_manager.get_enabled_patterns()}")
    
    if args.mtf:
        print(f"  MTF Mode: ENABLED")
        mtf_config = scanner.config.get("multi_timeframe", {})
        if mtf_config.get("enabled", False):
            print(f"  MTF Analysis: Every 30 seconds")
        else:
            print(f"  ⚠️ MTF enabled but not configured in config.yaml")
    else:
        print(f"  MTF Mode: DISABLED (use --mtf to enable)")
    
    print("\nStarting scanner...")
    print("Press Ctrl+C to stop\n")
    
    try:
        scanner.start()
    except KeyboardInterrupt:
        print("\nInterrupted by user")


if __name__ == "__main__":
    main()
