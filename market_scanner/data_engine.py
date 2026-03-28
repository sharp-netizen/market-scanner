"""
Dynamic Data Engine - NumPy-based Rolling Window
Automatically scales row-count based on active tickers
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading
from collections import deque


@dataclass
class TickerData:
    """Data structure for a single ticker's window"""
    symbol: str
    prices: deque = field(default_factory=lambda: deque(maxlen=100))
    sizes: deque = field(default_factory=lambda: deque(maxlen=100))
    timestamps: deque = field(default_factory=lambda: deque(maxlen=100))
    last_update: datetime = field(default_factory=datetime.now)
    cumulative_volume: int = 0  # NEW: Track cumulative daily volume
    volume_deltas: deque = field(default_factory=lambda: deque(maxlen=100))  # NEW: Volume deltas for surge detection
    
    def add_trade(self, price: float, size: int, timestamp: int, cumulative_vol: int = None) -> None:
        """Add new trade to window"""
        # Calculate volume delta if cumulative provided
        if cumulative_vol is not None and cumulative_vol > self.cumulative_volume:
            delta = cumulative_vol - self.cumulative_volume
            self.volume_deltas.append(delta)
            self.cumulative_volume = cumulative_vol
        
        self.prices.append(price)
        self.sizes.append(size)
        self.timestamps.append(timestamp)
        self.last_update = datetime.now()
    
    def get_price_array(self) -> np.ndarray:
        """Get prices as numpy array"""
        return np.array(self.prices, dtype=np.float64)
    
    def get_size_array(self) -> np.ndarray:
        """Get sizes as numpy array"""
        return np.array(self.sizes, dtype=np.int32)
    
    def get_volume_delta_array(self) -> np.ndarray:  # NEW
        """Get volume deltas as numpy array"""
        return np.array(self.volume_deltas, dtype=np.float64)
    
    def get_cumulative_volume(self) -> int:  # NEW
        """Get current cumulative volume"""
        return self.cumulative_volume
    
    def get_matrix(self) -> np.ndarray:
        """Get combined data matrix [prices, sizes]"""
        prices = np.array(self.prices, dtype=np.float64).reshape(-1, 1)
        sizes = np.array(self.sizes, dtype=np.int32).reshape(-1, 1)
        return np.hstack([prices, sizes])
    
    def count(self) -> int:
        return len(self.prices)


class DataEngine:
    """
    NumPy-based Rolling Window Data Engine
    
    Manages real-time ticker data with:
    - Dynamic scaling based on active tickers
    - Thread-safe operations
    - Efficient NumPy operations
    """
    
    def __init__(
        self,
        window_size: int = 100,
        max_tickers: int = 100,
        on_update: Optional[Callable[[str, np.ndarray], None]] = None
    ):
        self.window_size = window_size
        self.max_tickers = max_tickers
        self.on_update = on_update
        
        # Thread-safe ticker storage
        self._lock = threading.Lock()
        self._tickers: Dict[str, TickerData] = {}
        self._active_symbols: List[str] = []
        
        # Statistics
        self._total_trades = 0
        self._last_update_time = datetime.now()
        
        # Performance tracking
        self._processing_times: deque = deque(maxlen=1000)
    
    def add_ticker(self, symbol: str) -> TickerData:
        """Add a new ticker to track"""
        with self._lock:
            if symbol not in self._tickers:
                self._tickers[symbol] = TickerData(symbol=symbol)
                self._active_symbols.append(symbol)
            return self._tickers[symbol]
    
    def remove_ticker(self, symbol: str) -> None:
        """Remove a ticker"""
        with self._lock:
            if symbol in self._tickers:
                del self._tickers[symbol]
                self._active_symbols.remove(symbol)
    
    def update(
        self,
        symbol: str,
        price: float,
        size: int,
        timestamp: int,
        cumulative_volume: int = None  # NEW
    ) -> Optional[np.ndarray]:
        """Update ticker with new trade data"""
        start = __import__('time').time()
        
        with self._lock:
            # Auto-add ticker if not exists
            if symbol not in self._tickers:
                self.add_ticker(symbol)
            
            # Add trade data (pass cumulative_volume)
            self._tickers[symbol].add_trade(price, size, timestamp, cumulative_volume)
            self._total_trades += 1
            self._last_update_time = datetime.now()
            
            # Get matrix for callback
            matrix = self._tickers[symbol].get_matrix()
        
        # Track processing time
        elapsed = (__import__('time').time() - start) * 1000
        self._processing_times.append(elapsed)
        
        # Callback
        if self.on_update:
            try:
                self.on_update(symbol, matrix)
            except Exception as e:
                print(f"[DataEngine] Callback error: {e}")
        
        return matrix
    
    def get_ticker_matrix(self, symbol: str) -> Optional[np.ndarray]:
        """Get current matrix for a specific ticker"""
        with self._lock:
            if symbol in self._tickers:
                return self._tickers[symbol].get_matrix()
            return None
    
    def get_all_matrices(self) -> Dict[str, np.ndarray]:
        """Get matrices for all active tickers"""
        with self._lock:
            return {
                symbol: ticker.get_matrix()
                for symbol, ticker in self._tickers.items()
                if ticker.count() > 0
            }
    
    def get_price_array(self, symbol: str) -> Optional[np.ndarray]:
        """Get price array for a ticker"""
        with self._lock:
            if symbol in self._tickers:
                return self._tickers[symbol].get_price_array()
            return None
    
    def get_all_prices(self) -> Dict[str, np.ndarray]:
        """Get price arrays for all tickers"""
        with self._lock:
            return {
                symbol: ticker.get_price_array()
                for symbol, ticker in self._tickers.items()
                if ticker.count() > 0
            }
    
    def get_cumulative_volume(self, symbol: str) -> Optional[int]:  # NEW
        """Get cumulative daily volume for a ticker"""
        with self._lock:
            if symbol in self._tickers:
                return self._tickers[symbol].get_cumulative_volume()
            return None
    
    def get_volume_delta_array(self, symbol: str) -> Optional[np.ndarray]:  # NEW
        """Get volume delta array for a ticker (for surge detection)"""
        with self._lock:
            if symbol in self._tickers:
                return self._tickers[symbol].get_volume_delta_array()
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        with self._lock:
            processing_times = list(self._processing_times)
            return {
                "active_tickers": len(self._active_symbols),
                "total_trades": self._total_trades,
                "avg_processing_ms": np.mean(processing_times) if processing_times else 0,
                "max_processing_ms": np.max(processing_times) if processing_times else 0,
                "last_update": self._last_update_time.isoformat(),
                "window_size": self.window_size,
                "symbols": list(self._active_symbols)
            }
    
    def get_ticker_count(self) -> int:
        """Get number of active tickers"""
        with self._lock:
            return len(self._active_symbols)
    
    def clear(self) -> None:
        """Clear all data"""
        with self._lock:
            self._tickers.clear()
            self._active_symbols.clear()
            self._total_trades = 0
            self._processing_times.clear()
    
    def get_numpy_matrix(self) -> np.ndarray:
        """
        Get combined NumPy matrix for all tickers
        Shape: (num_tickers * window_size, 3)
        Columns: [symbol_idx, price, size]
        """
        with self._lock:
            matrices = []
            symbol_indices = []
            
            for idx, (symbol, ticker) in enumerate(self._tickers.items()):
                if ticker.count() > 0:
                    price_arr = ticker.get_price_array().reshape(-1, 1)
                    size_arr = ticker.get_size_array().reshape(-1, 1)
                    idx_arr = np.full((ticker.count(), 1), idx)
                    
                    matrices.append(np.hstack([idx_arr, price_arr, size_arr]))
                    symbol_indices.append(symbol)
            
            if matrices:
                return np.vstack(matrices), symbol_indices
            return np.array([]), []


# Multiprocessing-safe Shared Buffer
class SharedBuffer:
    """
    Thread-safe shared buffer for multiprocessing
    Uses numpy memory-mapped arrays for efficient IPC
    """
    
    def __init__(self, max_tickers: int = 100, window_size: int = 100):
        self.max_tickers = max_tickers
        self.window_size = window_size
        
        # Pre-allocate arrays
        self._prices = np.zeros((max_tickers, window_size), dtype=np.float64)
        self._sizes = np.zeros((max_tickers, window_size), dtype=np.int32)
        self._timestamps = np.zeros((max_tickers, window_size), dtype=np.int64)
        self._indices = np.zeros(max_tickers, dtype=np.int32)  # Current position per ticker
        self._active = np.zeros(max_tickers, dtype=np.bool_)
        
        self._lock = threading.Lock()
        self._symbol_to_idx: Dict[str, int] = {}
        self._idx_to_symbol: Dict[int, str] = {}
    
    def register_symbol(self, symbol: str) -> int:
        """Register a symbol and get its index"""
        with self._lock:
            if symbol in self._symbol_to_idx:
                return self._symbol_to_idx[symbol]
            
            if len(self._symbol_to_idx) >= self.max_tickers:
                raise ValueError("Max tickers reached")
            
            idx = len(self._symbol_to_idx)
            self._symbol_to_idx[symbol] = idx
            self._idx_to_symbol[idx] = symbol
            self._active[idx] = True
            return idx
    
    def add_trade(self, symbol: str, price: float, size: int, timestamp: int) -> None:
        """Add trade to buffer"""
        with self._lock:
            if symbol not in self._symbol_to_idx:
                idx = self.register_symbol(symbol)
            else:
                idx = self._symbol_to_idx[symbol]
            
            pos = self._indices[idx] % self.window_size
            
            self._prices[idx, pos] = price
            self._sizes[idx, pos] = size
            self._timestamps[idx, pos] = timestamp
            self._indices[idx] += 1
    
    def get_ticker_window(self, symbol: str) -> Optional[np.ndarray]:
        """Get full window for a symbol"""
        with self._lock:
            if symbol not in self._symbol_to_idx:
                return None
            
            idx = self._symbol_to_idx[symbol]
            count = min(self._indices[idx], self.window_size)
            
            if count == 0:
                return None
            
            pos = (self._indices[idx] - count) % self.window_size
            
            prices = self._prices[idx, pos:pos + count]
            sizes = self._sizes[idx, pos:pos + count]
            
            return np.hstack([prices.reshape(-1, 1), sizes.reshape(-1, 1)])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics"""
        with self._lock:
            return {
                "registered_symbols": len(self._symbol_to_idx),
                "max_tickers": self.max_tickers,
                "window_size": self.window_size,
                "symbols": list(self._symbol_to_idx.keys())
            }
