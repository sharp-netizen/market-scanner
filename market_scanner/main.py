#!/usr/bin/env python3
"""
High-Frequency Market Scanner
Modular architecture with multiprocessing for M4 optimization

Usage:
    python3 main.py [--config config.yaml]
"""

import argparse
import asyncio
import json
import logging
import multiprocessing as mp
import os
import signal
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml
import numpy as np

# Import our modules
from providers import ProviderFactory, TradeData, AbstractProvider
from data_engine import DataEngine, SharedBuffer
from patterns import PatternManager, Alert, GreenStreakPattern, VolumeSurgePattern, MomentumPattern, RSIDivergencePattern
from output import OutputManager, ConsoleOutput, LogFileOutput, MockExecutorOutput, TelegramOutput, DiscordWebhookOutput


class IngestionProcess(mp.Process):
    """
    Ingestion Process - Runs on separate CPU core
    Receives data from provider and updates shared buffer
    """
    
    def __init__(self, config: Dict, buffer: SharedBuffer):
        super().__init__()
        self.config = config
        self.buffer = buffer
        self.provider: Optional[AbstractProvider] = None
        self._running = False
    
    def run(self):
        """Main loop for ingestion process"""
        self._running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        try:
            # Create provider
            provider_config = self.config.get(self.config.get("provider", "mock"), {})
            self.provider = ProviderFactory.create(
                self.config.get("provider", "mock"),
                provider_config,
                self._on_trade
            )
            
            # Connect and subscribe
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(self.provider.connect())
            loop.run_until_complete(self.provider.subscribe(self.config.get("tickers", [])))
            
            print(f"[IngestionProcess] Started on PID {os.getpid()}")
            
            # Run provider
            loop.run_until_complete(self.provider.start())
            
        except Exception as e:
            print(f"[IngestionProcess] Error: {e}")
        finally:
            self._running = False
    
    def _on_trade(self, trade: TradeData):
        """Callback for new trades"""
        self.buffer.add_trade(trade.symbol, trade.price, trade.size, trade.timestamp)
    
    def _signal_handler(self, signum, frame):
        print(f"[IngestionProcess] Received signal {signum}")
        self._running = False
        if self.provider:
            asyncio.create_task(self.provider.disconnect())


def analyze_patterns_wrapper(args: tuple) -> List[Dict]:
    """
    Worker function for pattern analysis (runs in process pool)
    
    Args:
        args: (symbol, prices_array, sizes_array, patterns_config)
        
    Returns:
        List of alert dicts
    """
    symbol, prices_json, sizes_json, patterns_config = args
    
    prices = np.array(json.loads(prices_json))
    sizes = np.array(json.loads(sizes_json))
    
    alerts = []
    
    # Create pattern manager
    manager = PatternManager()
    
    # Register patterns from config
    if patterns_config.get("green_streak", {}).get("enabled"):
        manager.register(GreenStreakPattern(patterns_config.get("green_streak")))
    
    if patterns_config.get("volume_surge", {}).get("enabled"):
        manager.register(VolumeSurgePattern(patterns_config.get("volume_surge")))
    
    # Run analysis
    pattern_alerts = manager.analyze_all(symbol, prices, sizes)
    
    for alert in pattern_alerts:
        alerts.append(alert.to_dict())
    
    return alerts


class MarketScanner:
    """
    Main Market Scanner Orchestrator
    
    Coordinates:
    - Data ingestion (via provider)
    - Data storage (via DataEngine)
    - Pattern analysis (via PatternManager)
    - Output dispatch (via OutputManager)
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Dict = {}
        
        # Core components
        self.data_engine: Optional[DataEngine] = None
        self.pattern_manager: Optional[PatternManager] = None
        self.output_manager: Optional[OutputManager] = None
        
        # Multiprocessing
        self.ingestion_process: Optional[IngestionProcess] = None
        self.analysis_executor: Optional[ProcessPoolExecutor] = None
        
        # State
        self._running = False
        self._last_stats_time = time.time()
        self._alerts_processed = 0
        self._trades_processed = 0
        
        # Setup
        self._load_config()
        self._setup_components()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            print(f"[Scanner] Config file not found: {self.config_path}")
            # Try default location
            config_file = Path(__file__).parent / "config.yaml"
        
        if config_file.exists():
            with open(config_file) as f:
                self.config = yaml.safe_load(f)
            print(f"[Scanner] Loaded config from {config_file}")
        else:
            print("[Scanner] Using default config")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "provider": "mock",
            "tickers": ["AAPL", "TSLA", "NVDA", "AMD", "MSFT", "GOOGL", "AMZN", "META"],
            "data_engine": {"window_size": 100, "max_tickers": 100},
            "patterns": {
                "green_streak": {"enabled": True, "streak_length": 15},
                "volume_surge": {"enabled": True, "surge_multiplier": 3.0}
            },
            "output": {
                "console": {"enabled": True, "rich_dashboard": True},
                "log_file": {"enabled": True, "path": "logs/scanner.log"},
                "mock_executor": {"enabled": True}
            },
            "performance": {"multiprocessing": True}
        }
    
    def _setup_components(self) -> None:
        """Initialize all components"""
        print("[Scanner] Setting up components...")
        
        # Data Engine
        de_config = self.config.get("data_engine", {})
        self.data_engine = DataEngine(
            window_size=de_config.get("window_size", 100),
            max_tickers=de_config.get("max_tickers", 100),
            on_update=self._on_data_update
        )
        
        # Pattern Manager
        self.pattern_manager = PatternManager()
        
        pattern_configs = self.config.get("patterns", {})
        
        if pattern_configs.get("green_streak", {}).get("enabled"):
            self.pattern_manager.register(
                GreenStreakPattern(pattern_configs.get("green_streak"))
            )
        
        if pattern_configs.get("volume_surge", {}).get("enabled"):
            self.pattern_manager.register(
                VolumeSurgePattern(pattern_configs.get("volume_surge"))
            )
        
        if pattern_configs.get("momentum", {}).get("enabled"):
            self.pattern_manager.register(
                MomentumPattern(pattern_configs.get("momentum"))
            )
        
        if pattern_configs.get("rsi_divergence", {}).get("enabled"):
            self.pattern_manager.register(
                RSIDivergencePattern(pattern_configs.get("rsi_divergence"))
            )
        
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
        
        print("[Scanner] Components initialized")
    
    def _on_data_update(self, symbol: str, matrix: np.ndarray) -> None:
        """Callback when data engine receives update"""
        # This runs in the ingestion thread/process
        pass
    
    async def _run_async(self) -> None:
        """Main async run loop"""
        print("[Scanner] Starting...")
        
        if self.config.get("performance", {}).get("multiprocessing"):
            await self._run_with_multiprocessing()
        else:
            await self._run_embedded()
    
    async def _run_with_multiprocessing(self) -> None:
        """Run with separate ingestion process"""
        # Create shared buffer
        de_config = self.config.get("data_engine", {})
        buffer = SharedBuffer(
            max_tickers=de_config.get("max_tickers", 100),
            window_size=de_config.get("window_size", 100)
        )
        
        # Start ingestion process
        self.ingestion_process = IngestionProcess(self.config, buffer)
        self.ingestion_process.start()
        
        # Create analysis executor
        self.analysis_executor = ProcessPoolExecutor(max_workers=2)
        
        print("[Scanner] Running with multiprocessing...")
        
        # Main analysis loop
        while self._running:
            try:
                # Check for new data
                stats = buffer.get_stats()
                
                if stats["registered_symbols"] > 0:
                    # Analyze each ticker
                    for symbol in stats["symbols"]:
                        try:
                            window = buffer.get_ticker_window(symbol)
                            
                            if window is not None and len(window) >= 15:
                                prices = window[:, 0]
                                sizes = window[:, 1]
                                
                                # Run pattern analysis in separate process
                                prices_json = json.dumps(prices.tolist())
                                sizes_json = json.dumps(sizes.tolist())
                                patterns_config = self.config.get("patterns", {})
                                
                                future = self.analysis_executor.submit(
                                    analyze_patterns_wrapper,
                                    (symbol, prices_json, sizes_json, patterns_config)
                                )
                                
                                # Process results
                                alerts_data = future.result(timeout=1.0)
                                
                                for alert_dict in alerts_data:
                                    alert = Alert(**alert_dict)
                                    self.output_manager.send(alert)
                                    self._alerts_processed += 1
                        
                        except Exception as e:
                            pass  # Skip errors for individual tickers
                
                await asyncio.sleep(0.01)  # 10ms loop
            
            except Exception as e:
                print(f"[Scanner] Error in main loop: {e}")
                await asyncio.sleep(1)
        
        # Cleanup
        if self.ingestion_process:
            self.ingestion_process.terminate()
            self.ingestion_process.join()
        
        if self.analysis_executor:
            self.analysis_executor.shutdown(wait=True)
    
    async def _run_embedded(self) -> None:
        """Run without multiprocessing (embedded mode)"""
        print("[Scanner] Running in embedded mode...")
        
        # Create provider
        provider_type = self.config.get("provider", "mock")
        provider_config = self.config.get(provider_type, {})
        
        provider = ProviderFactory.create(
            provider_type,
            provider_config,
            self._on_trade
        )
        
        await provider.connect()
        await provider.subscribe(self.config.get("tickers", []))
        
        # Main loop
        while self._running:
            await asyncio.sleep(0.01)
            # Processing happens in callbacks
    
    def _on_trade(self, trade):
        """Handle incoming trade"""
        self._trades_processed += 1
        
        # Update data engine
        self.data_engine.update(
            trade.symbol,
            trade.price,
            trade.size,
            trade.timestamp
        )
        
        # Check if we have enough data for analysis
        prices = self.data_engine.get_price_array(trade.symbol)
        sizes = self.data_engine.get_size_array(trade.symbol)
        
        if prices is not None and len(prices) >= 15:
            alerts = self.pattern_manager.analyze_all(trade.symbol, prices, sizes)
            
            for alert in alerts:
                self.output_manager.send(alert)
                self._alerts_processed += 1
    
    def start(self) -> None:
        """Start the scanner"""
        self._running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Run
        asyncio.run(self._run_async())
    
    def stop(self) -> None:
        """Stop the scanner"""
        print("[Scanner] Stopping...")
        self._running = False
        
        # Cleanup
        if self.output_manager:
            self.output_manager.close()
        
        if self.ingestion_process:
            self.ingestion_process.terminate()
        
        print("[Scanner] Stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"[Scanner] Received signal {signum}")
        self.stop()
        sys.exit(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scanner statistics"""
        stats = {
            "running": self._running,
            "trades_processed": self._trades_processed,
            "alerts_processed": self._alerts_processed,
            "data_engine": self.data_engine.get_stats() if self.data_engine else {},
            "patterns_enabled": self.pattern_manager.get_enabled_patterns() if self.pattern_manager else [],
            "outputs_enabled": self.output_manager.get_enabled_outputs() if self.output_manager else []
        }
        return stats


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="High-Frequency Market Scanner")
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to config file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    
    print("=" * 50)
    print("High-Frequency Market Scanner")
    print("=" * 50)
    
    # Create scanner
    scanner = MarketScanner(config_path=args.config)
    
    # Print initial stats
    print("\nConfiguration:")
    print(f"  Provider: {scanner.config.get('provider', 'mock')}")
    print(f"  Tickers: {scanner.config.get('tickers', [])}")
    print(f"  Patterns: {scanner.pattern_manager.get_enabled_patterns()}")
    print(f"  Multiprocessing: {scanner.config.get('performance', {}).get('multiprocessing', True)}")
    print("\nStarting scanner...")
    print("Press Ctrl+C to stop\n")
    
    try:
        scanner.start()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        scanner.stop()


if __name__ == "__main__":
    main()
