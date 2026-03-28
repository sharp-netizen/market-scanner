"""
Data Provider Interface - Abstract Base Class and Implementations
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Any
import asyncio
import json
import random
import time
import websockets
import aiohttp
import requests
from datetime import datetime


class TradeData:
    """Standardized trade data structure"""
    def __init__(
        self,
        symbol: str,
        price: float,
        size: int,
        timestamp: int,
        exchange: int = 0,
        conditions: List[int] = None,
        cumulative_volume: int = None  # NEW: cumulative daily volume
    ):
        self.symbol = symbol
        self.price = price
        self.size = size
        self.timestamp = timestamp
        self.exchange = exchange
        self.conditions = conditions or []
        self.cumulative_volume = cumulative_volume  # NEW
        self.datetime = datetime.fromtimestamp(timestamp / 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "size": self.size,
            "timestamp": self.timestamp,
            "exchange": self.exchange,
            "conditions": self.conditions,
            "cumulative_volume": self.cumulative_volume,  # NEW
            "datetime": self.datetime.isoformat()
        }


class AbstractProvider(ABC):
    """Abstract Base Class for data providers"""
    
    def __init__(self, config: dict, callback: Callable[[TradeData], None]):
        self.config = config
        self.callback = callback
        self._running = False
        self.subscribed_tickers: List[str] = []
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    async def subscribe(self, tickers: List[str]) -> bool:
        """Subscribe to specific tickers"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, tickers: List[str]) -> bool:
        """Unsubscribe from tickers"""
        pass
    
    @abstractmethod
    async def on_message(self, message: Any) -> None:
        """Handle incoming message"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up connection"""
        pass
    
    async def start(self) -> None:
        """Start the provider"""
        self._running = True
        await self._run()
    
    async def _run(self) -> None:
        """Main loop - override in subclasses"""
        pass
    
    def is_running(self) -> bool:
        return self._running


class PolygonProvider(AbstractProvider):
    """
    Polygon.io WebSocket Provider
    Docs: https://polygon.io/docs/websocket/stocks/trades
    """
    
    def __init__(self, config: dict, callback: Callable[[TradeData], None]):
        super().__init__(config, callback)
        self.api_key = config.get("api_key", "")
        self.ws_url = config.get("ws_url", "wss://socket.polygon.io/stocks")
        self._websocket = None
        self._reconnect_delay = 1
        self._max_reconnect_delay = 30
    
    async def connect(self) -> bool:
        """Connect to Polygon WebSocket"""
        try:
            self._websocket = await websockets.connect(self.ws_url)
            # Authenticate
            auth_msg = json.dumps({"action": "auth", "params": self.api_key})
            await self._websocket.send(auth_msg)
            auth_response = await self._websocket.recv()
            print(f"[Polygon] Connected: {auth_response}")
            return True
        except Exception as e:
            print(f"[Polygon] Connection failed: {e}")
            return False
    
    async def subscribe(self, tickers: List[str]) -> bool:
        """Subscribe to ticker trades"""
        if not self._websocket:
            return False
        
        try:
            # Subscribe to trades (T prefix)
            for ticker in tickers:
                sub_msg = json.dumps({"action": "subscribe", "params": f"T.{ticker}"})
                await self._websocket.send(sub_msg)
                self.subscribed_tickers.append(ticker)
            print(f"[Polygon] Subscribed to: {tickers}")
            return True
        except Exception as e:
            print(f"[Polygon] Subscribe failed: {e}")
            return False
    
    async def unsubscribe(self, tickers: List[str]) -> bool:
        """Unsubscribe from tickers"""
        if not self._websocket:
            return False
        
        try:
            for ticker in tickers:
                unsub_msg = json.dumps({"action": "unsubscribe", "params": f"T.{ticker}"})
                await self._websocket.send(unsub_msg)
                if ticker in self.subscribed_tickers:
                    self.subscribed_tickers.remove(ticker)
            return True
        except Exception as e:
            print(f"[Polygon] Unsubscribe failed: {e}")
            return False
    
    async def on_message(self, message: str) -> Optional[TradeData]:
        """Parse Polygon trade message"""
        try:
            data = json.loads(message)
            
            # Polygon sends: { "ev": "T", "sym": "AAPL", "p": 150.25, "s": 100, ... }
            if data.get("ev") == "T":  # Trade event
                trade = TradeData(
                    symbol=data.get("sym", ""),
                    price=float(data.get("p", 0)),
                    size=int(data.get("s", 0)),
                    timestamp=int(data.get("t", 0)),
                    exchange=int(data.get("x", 0)),
                    conditions=data.get("c", [])
                )
                self.callback(trade)
                return trade
            return None
        except Exception as e:
            print(f"[Polygon] Parse error: {e}")
            return None
    
    async def disconnect(self) -> None:
        """Close WebSocket connection"""
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        print("[Polygon] Disconnected")
    
    async def _run(self) -> None:
        """Main WebSocket loop"""
        while self._running and self._websocket:
            try:
                message = await self._websocket.recv()
                await self.on_message(message)
            except websockets.ConnectionClosed:
                print("[Polygon] Connection closed, attempting reconnect...")
                await self._reconnect()
            except Exception as e:
                print(f"[Polygon] Error: {e}")
                await asyncio.sleep(1)
    
    async def _reconnect(self) -> None:
        """Reconnect with exponential backoff"""
        await asyncio.sleep(min(self._reconnect_delay, self._max_reconnect_delay))
        self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
        if await self.connect():
            await self.subscribe(self.subscribed_tickers)
            self._reconnect_delay = 1


class MockDataProvider(AbstractProvider):
    """
    Mock Data Provider for testing and development
    Generates realistic-looking trade data
    """
    
    def __init__(self, config: dict, callback: Callable[[TradeData], None]):
        super().__init__(config, callback)
        self.tickers = config.get("tickers", ["AAPL", "TSLA"])
        self._task = None
        self._base_prices: Dict[str, float] = {}
        self._volatilities: Dict[str, float] = {}
        
        # Initialize prices based on realistic values
        realistic_prices = {
            "AAPL": 185.50,
            "TSLA": 245.30,
            "NVDA": 495.20,
            "AMD": 145.80,
            "MSFT": 378.90,
            "GOOGL": 141.25,
            "AMZN": 178.50,
            "META": 485.60
        }
        
        for ticker in self.tickers:
            self._base_prices[ticker] = realistic_prices.get(ticker, 100.0)
            self._volatilities[ticker] = random.uniform(0.001, 0.005)
    
    async def connect(self) -> bool:
        """Mock connection always succeeds"""
        print(f"[Mock] Connected (simulating {len(self.tickers)} tickers)")
        return True
    
    async def subscribe(self, tickers: List[str]) -> bool:
        """Mock subscription"""
        for ticker in tickers:
            if ticker not in self.subscribed_tickers:
                self.subscribed_tickers.append(ticker)
        print(f"[Mock] Subscribed to: {tickers}")
        return True
    
    async def unsubscribe(self, tickers: List[str]) -> bool:
        """Mock unsubscription"""
        for ticker in tickers:
            if ticker in self.subscribed_tickers:
                self.subscribed_tickers.remove(ticker)
        return True
    
    async def on_message(self, message: str = None) -> Optional[TradeData]:
        """Generate mock trade data"""
        if not self.subscribed_tickers:
            return None
        
        # Pick random ticker
        symbol = random.choice(self.subscribed_tickers)
        
        # Generate realistic price movement
        base = self._base_prices[symbol]
        vol = self._volatilities[symbol]
        change = random.gauss(0, vol)
        price = base * (1 + change)
        price = round(price, 2)
        
        # Update base price for next iteration
        self._base_prices[symbol] = price
        
        # Random trade size
        size = random.randint(1, 1000)
        
        trade = TradeData(
            symbol=symbol,
            price=price,
            size=size,
            timestamp=int(time.time() * 1000)
        )
        
        self.callback(trade)
        return trade
    
    async def disconnect(self) -> None:
        """Mock disconnect"""
        self._running = False
        print("[Mock] Disconnected")
    
    async def _run(self) -> None:
        """Generate trades at high frequency"""
        while self._running:
            # Simulate 10-50 trades per second across all tickers
            num_trades = random.randint(10, 50)
            for _ in range(num_trades):
                if not self._running:
                    break
                await self.on_message()
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.001)  # 1ms between trades
            # Slightly longer pause between batches
            await asyncio.sleep(random.uniform(0.01, 0.05))


class BinanceProvider(AbstractProvider):
    """
    Binance WebSocket + REST Provider for Crypto Data
    
    Free real-time crypto data via Binance WebSocket streams.
    Falls back to REST API if WebSocket is unavailable.
    Supports: BTCUSDT, ETHUSDT, SOLUSDT, and 1000+ pairs.
    """
    
    def __init__(self, config: dict, callback: Callable[[TradeData], None]):
        super().__init__(config, callback)
        self.api_key = config.get("api_key", "")
        self.ws_url = "wss://stream.binance.com:9443/ws"
        self.rest_url = "https://api.binance.com/api/v3"
        self._websocket = None
        self._reconnect_delay = 1
        self._max_reconnect_delay = 30
        self._streams: List[str] = []
        self._use_rest = False
        self._rest_task = None
    
    async def connect(self) -> bool:
        """Try WebSocket first, fallback to REST"""
        try:
            self._websocket = await websockets.connect(self.ws_url, open_timeout=5)
            print(f"[Binance] Connected to WebSocket")
            return True
        except Exception as e:
            print(f"[Binance] WebSocket failed ({e}), using REST API fallback")
            self._use_rest = True
            return True  # REST always works
    
    async def subscribe(self, tickers: List[str]) -> bool:
        """Subscribe to streams (WebSocket) or prepare for REST polling"""
        for ticker in tickers:
            symbol = ticker.replace("/", "").upper()
            if not self._use_rest:
                stream = f"{symbol.lower()}@trade"
                self._streams.append(stream)
            self.subscribed_tickers.append(ticker)
        
        if self._use_rest:
            print(f"[Binance] REST mode: will poll for {tickers}")
            # Start REST polling task
            self._rest_task = asyncio.create_task(self._rest_poll())
        else:
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": self._streams,
                "id": int(time.time() * 1000)
            }
            await self._websocket.send(json.dumps(subscribe_msg))
            response = await self._websocket.recv()
            print(f"[Binance] Subscribed to {tickers}")
        
        return True
    
    async def _rest_poll(self) -> None:
        """REST API fallback - poll for prices"""
        while self._running:
            try:
                for ticker in self.subscribed_tickers:
                    symbol = ticker.replace("/", "").upper()
                    url = f"{self.rest_url}/ticker/24hr?symbol={symbol}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            data = await resp.json()
                            trade = TradeData(
                                symbol=data.get("symbol", ""),
                                price=float(data.get("lastPrice", 0)),
                                size=float(data.get("quoteVolume", 0)),
                                timestamp=int(time.time() * 1000)
                            )
                            self.callback(trade)
                    await asyncio.sleep(0.5)  # Rate limit
            except Exception as e:
                print(f"[Binance] REST poll error: {e}")
                await asyncio.sleep(1)
    
    async def unsubscribe(self, tickers: List[str]) -> bool:
        """Unsubscribe from tickers"""
        if self._use_rest and self._rest_task:
            self._rest_task.cancel()
        
        for ticker in tickers:
            if ticker in self.subscribed_tickers:
                self.subscribed_tickers.remove(ticker)
        return True
    
    async def on_message(self, message: str) -> Optional[TradeData]:
        """Parse Binance WebSocket trade message"""
        try:
            data = json.loads(message)
            if data.get("e") == "trade":
                trade = TradeData(
                    symbol=data.get("s", ""),
                    price=float(data.get("p", 0)),
                    size=float(data.get("q", 0)),
                    timestamp=int(data.get("T", 0))
                )
                self.callback(trade)
                return trade
            return None
        except Exception as e:
            print(f"[Binance] Parse error: {e}")
            return None
    
    async def disconnect(self) -> None:
        """Close connections"""
        self._running = False
        if self._websocket:
            await self._websocket.close()
        if self._rest_task:
            self._rest_task.cancel()
        print("[Binance] Disconnected")
    
    async def _run(self) -> None:
        """Main loop"""
        if self._use_rest:
            return  # REST uses _rest_poll
        
        while self._running and self._websocket:
            try:
                message = await self._websocket.recv()
                await self.on_message(message)
            except websockets.ConnectionClosed:
                self._running = False
            except Exception as e:
                await asyncio.sleep(1)


class CoinbaseProProvider(AbstractProvider):
    """
    Coinbase Pro WebSocket + REST Provider for Crypto Data
    
    Free crypto data via Coinbase Pro WebSocket (real-time).
    Falls back to REST API if WebSocket is unavailable.
    Supports: BTC-USD, ETH-USD, SOL-USD, +100+ pairs.
    
    WebSocket: wss://ws-feed.exchange.coinbase.com
    REST: https://api.exchange.coinbase.com
    """
    
    def __init__(self, config: dict, callback: Callable[[TradeData], None]):
        super().__init__(config, callback)
        self.ws_url = "wss://ws-feed.exchange.coinbase.com"
        self.rest_url = "https://api.exchange.coinbase.com"
        self._products: List[str] = []
        self._websocket = None
        self._use_rest = False
        self._running = False
        self._session = None
    
    async def connect(self) -> bool:
        """Try WebSocket first, fallback to REST"""
        # Try WebSocket first
        try:
            import websockets
            self._websocket = await websockets.connect(self.ws_url, open_timeout=5)
            print(f"[CoinbasePro] Connected to WebSocket")
            
            # Subscribe to channels
            subscribe_msg = {
                "type": "subscribe",
                "product_ids": ["BTC-USD", "ETH-USD", "SOL-USD"],
                "channels": ["ticker"]
            }
            await self._websocket.send(json.dumps(subscribe_msg))
            
            # Wait for subscription confirmation
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            print(f"[CoinbasePro] WebSocket failed ({e}), using REST fallback")
            self._use_rest = True
            self._session = aiohttp.ClientSession()
            return True
    
    async def subscribe(self, tickers: List[str]) -> bool:
        """Prepare ticker list"""
        for ticker in tickers:
            base = ticker.replace("USDT", "").replace("USD", "").upper()
            if base not in ["USD", "USDT"]:
                product_id = f"{base}-USD"
            else:
                product_id = ticker.replace("/", "-").upper()
            
            if product_id not in self._products:
                self._products.append(product_id)
            
            self.subscribed_tickers.append(ticker)
        
        if self._use_rest:
            print(f"[CoinbasePro] REST polling: {self._products}")
        else:
            print(f"[CoinbasePro] WebSocket subscribed: {self._products}")
        return True
    
    async def unsubscribe(self, tickers: List[str]) -> bool:
        """Unsubscribe from tickers"""
        self._running = False
        return True
    
    async def _ws_listen(self) -> None:
        """Listen for WebSocket messages"""
        try:
            async for message in self._websocket:
                await self.on_message(message)
        except websockets.ConnectionClosed:
            print("[CoinbasePro] WebSocket closed")
            self._use_rest = True
        except Exception as e:
            print(f"[CoinbasePro] WS Error: {e}")
            self._use_rest = True
    
    async def _rest_poll(self) -> None:
        """REST fallback polling"""
        for product_id in self._products:
            if not self._running:
                break
            
            url = f"{self.rest_url}/products/{product_id}/ticker"
            try:
                async with self._session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        symbol = product_id.replace("-USD", "")
                        trade = TradeData(
                            symbol=symbol,
                            price=float(data.get("price", 0)),
                            size=float(data.get("size", 0)),
                            timestamp=int(time.time() * 1000)
                        )
                        self.callback(trade)
            except:
                pass
    
    async def on_message(self, message: str) -> Optional[TradeData]:
        """Parse WebSocket message"""
        try:
            data = json.loads(message)
            
            # Check if ticker data
            if data.get("type") == "ticker":
                product_id = data.get("product_id", "")
                symbol = product_id.replace("-USD", "")
                
                trade = TradeData(
                    symbol=symbol,
                    price=float(data.get("price", 0)),
                    size=float(data.get("last_size", 0)),
                    timestamp=int(time.time() * 1000)
                )
                self.callback(trade)
                return trade
        except:
            pass
        return None
    
    async def _run(self) -> None:
        """Main loop - WebSocket or REST"""
        self._running = True
        
        if not self._use_rest:
            # WebSocket mode - listen for messages
            await self._ws_listen()
        else:
            # REST mode - poll every second
            while self._running:
                await self._rest_poll()
                await asyncio.sleep(1.0)
    
    async def disconnect(self) -> None:
        self._running = False
        if self._websocket:
            await self._websocket.close()
        if self._session:
            await self._session.close()
        print("[CoinbasePro] Disconnected")
    
    async def start(self) -> None:
        """Start the provider"""
        await self._run()


class AggregatorProvider(AbstractProvider):
    """
    Aggregator Provider - Runs multiple providers simultaneously
    
    Example:
        - Coinbase for crypto (BTC, ETH, SOL)
        - Mock for stocks (AAPL, TSLA)
    
    Usage:
        agg = AggregatorProvider(config, callback)
        await agg.connect()
        await agg.subscribe()
        await agg.start()
        
        # To stop:
        agg._running = False
        await agg.disconnect()
    """
    
    def __init__(self, config: dict, callback: Callable[[TradeData], None]):
        super().__init__(config, callback)
        self.providers: List[AbstractProvider] = []
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Provider configurations
        provider_configs = config.get("providers", [])
        
        # Create providers
        for p_config in provider_configs:
            p_type = p_config.get("type", "mock")
            p_callback = self._forward_trade
            provider = ProviderFactory.create(p_type, p_config, p_callback)
            self.providers.append(provider)
            
            # Track tickers
            for ticker in p_config.get("tickers", []):
                if ticker not in self.subscribed_tickers:
                    self.subscribed_tickers.append(ticker)
    
    def _forward_trade(self, trade: TradeData) -> None:
        """Forward trade from any provider to main callback"""
        self.callback(trade)
    
    async def connect(self) -> bool:
        """Connect all providers"""
        results = []
        for provider in self.providers:
            result = await provider.connect()
            results.append(result)
        print(f"[Aggregator] Connected {len(self.providers)} providers")
        return all(results)
    
    async def subscribe(self, tickers: List[str] = None) -> bool:
        """Subscribe all providers to their respective tickers"""
        for provider in self.providers:
            # Get the tickers for this provider from config
            provider_tickers = []
            provider_type = type(provider).__name__.lower().replace("provider", "")
            for p_config in self.config.get("providers", []):
                config_type = p_config.get("type", "").lower()
                if provider_type in config_type or config_type in provider_type:
                    provider_tickers = p_config.get("tickers", [])
                    break
            
            # Subscribe the provider
            if hasattr(provider, 'subscribe') and provider_tickers:
                await provider.subscribe(provider_tickers)
        
        return True
    
    async def unsubscribe(self, tickers: List[str]) -> bool:
        """Unsubscribe from tickers"""
        for provider in self.providers:
            await provider.unsubscribe(tickers)
        return True
    
    async def on_message(self, message: str) -> Optional[TradeData]:
        """Not used - trades come via callbacks"""
        return None
    
    async def disconnect(self) -> None:
        """Disconnect all providers"""
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to finish
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Disconnect all providers
        for provider in self.providers:
            await provider.disconnect()
        
        print("[Aggregator] All providers disconnected")
    
    async def start(self) -> None:
        """Start all providers concurrently"""
        self._running = True
        
        # Start each provider in a background task
        for provider in self.providers:
            # Set running flag
            provider._running = True
            
            # Create task for this provider
            task = asyncio.create_task(self._run_provider(provider))
            self._tasks.append(task)
        
        print(f"[Aggregator] Started {len(self._tasks)} provider tasks")
        
        # Wait for stop signal
        try:
            while self._running:
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
    
    async def _run_provider(self, provider: AbstractProvider) -> None:
        """Run a single provider's _run method"""
        try:
            await provider._run()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[Aggregator] Provider error: {e}")
    
    def is_running(self) -> bool:
        return self._running


class ProviderFactory:
    """Factory for creating provider instances"""
    
    @staticmethod
    def create(provider_type: str, config: dict, callback: Callable[[TradeData], None]) -> AbstractProvider:
        """Create provider based on type"""
        providers = {
            "polygon": PolygonProvider,
            "mock": MockDataProvider,
            "binance": BinanceProvider,
            "coinbase": CoinbaseProProvider,
            "aggregator": AggregatorProvider,
            "alpaca": AlpacaProvider,
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        return providers[provider_type](config, callback)


class AlpacaProvider(AbstractProvider):
    """
    Alpaca Market Data Provider
    
    Free real-time stock data via Alpaca's REST API.
    Docs: https://alpaca.markets/docs/market-data/
    
    Note: Requires API key for market data. Paper trading keys work.
    """
    
    def __init__(self, config: dict, callback: Callable[[TradeData], None]):
        super().__init__(config, callback)
        self.api_key = config.get("api_key", "")
        self.secret_key = config.get("secret_key", "")
        self.paper = config.get("paper", True)
        self.endpoint = config.get("endpoint", "https://paper-api.alpaca.markets")
        self._session = None
        self._rest_task = None
        
        # Alpaca REST endpoints (Data API - for market data)
        if self.paper:
            self._data_url = "https://data.alpaca.markets"
        else:
            self._data_url = "https://data.alpaca.markets"
        
        self._headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }
    
    async def connect(self) -> bool:
        """Initialize session"""
        import aiohttp
        self._session = aiohttp.ClientSession()
        print(f"[Alpaca] Connected (REST API)")
        return True
    
    async def subscribe(self, tickers: List[str]) -> bool:
        """Start polling for trades"""
        for ticker in tickers:
            self.subscribed_tickers.append(ticker)
        
        # Start REST polling task
        self._rest_task = asyncio.create_task(self._rest_poll())
        print(f"[Alpaca] Subscribed to: {tickers}")
        return True
    
    async def _rest_poll(self) -> None:
        """Poll for latest price using snapshots (works when market is closed)"""
        import aiohttp
        import json
        
        while self._running:
            try:
                async with self._session.get(
                    f"{self._data_url}/v2/stocks/snapshots",
                    params={"symbols": ",".join(self.subscribed_tickers)},
                    headers=self._headers
                ) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        snapshots = json.loads(text)
                        
                        for symbol, snapshot in snapshots.items():
                            if "latestTrade" in snapshot and snapshot["latestTrade"]:
                                trade_data = snapshot["latestTrade"]
                                ts_str = trade_data.get("t", "")
                                
                                # Extract cumulative daily volume from dailyBar
                                daily_bar = snapshot.get("dailyBar", {})
                                cumulative_volume = daily_bar.get("v", None)  # NEW
                                
                                # Parse ISO timestamp: "2026-02-06T21:15:24.622568784Z"
                                try:
                                    from datetime import datetime
                                    ts_str = ts_str.replace('Z', '').replace('+00:00', '')
                                    dt = datetime.fromisoformat(ts_str)
                                    timestamp = int(dt.timestamp() * 1000)
                                except:
                                    timestamp = int(time.time() * 1000)
                                
                                trade = TradeData(
                                    symbol=symbol,
                                    price=float(trade_data.get("p", 0)),
                                    size=int(trade_data.get("s", 0)),
                                    timestamp=timestamp,
                                    cumulative_volume=cumulative_volume  # NEW
                                )
                                self.callback(trade)
                    else:
                        error_text = await resp.text()
                        print(f"[Alpaca] Error {resp.status}: {error_text[:200]}")
                    
            except Exception as e:
                print(f"[Alpaca] REST poll error: {e}")
            
            await asyncio.sleep(5)
    
    async def unsubscribe(self, tickers: List[str]) -> bool:
        """Unsubscribe from tickers"""
        if self._rest_task:
            self._rest_task.cancel()
        for ticker in tickers:
            if ticker in self.subscribed_tickers:
                self.subscribed_tickers.remove(ticker)
        return True
    
    async def on_message(self, message: str) -> Optional[TradeData]:
        """Not used in REST mode"""
        return None
    
    async def disconnect(self) -> None:
        """Disconnect"""
        self._running = False
        if self._rest_task:
            self._rest_task.cancel()
        if self._session:
            await self._session.close()
        print("[Alpaca] Disconnected")
    
    async def _run(self) -> None:
        """Main loop - keep alive"""
        while self._running:
            await asyncio.sleep(1)
