"""
Output Manager - Observer Pattern for Multi-Channel Output
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import os
import json
from pathlib import Path


class OutputChannel(Enum):
    """Output channel types"""
    CONSOLE = "console"
    LOG_FILE = "log_file"
    MOCK_EXECUTOR = "mock_executor"
    TELEGRAM = "telegram"
    DISCORD = "discord"


@dataclass
class Alert:
    """Alert object"""
    symbol: str
    pattern_name: str
    severity: str
    value: float
    threshold: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "pattern": self.pattern_name,
            "severity": self.severity,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class BaseOutput(ABC):
    """Abstract Base Class for output handlers"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self._enabled = self.config.get("enabled", True)
        self._lock = threading.Lock()
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
    
    @abstractmethod
    def send(self, alert: Alert) -> None:
        """Send alert to output channel"""
        pass
    
    @abstractmethod
    def send_batch(self, alerts: List[Alert]) -> None:
        """Send multiple alerts"""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush any pending output"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Clean up resources"""
        pass


class ConsoleOutput(BaseOutput):
    """
    Rich-based Terminal Dashboard Output
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Console", config)
        self.use_rich = self.config.get("rich_dashboard", True)
        self._last_stats_time = datetime.now()
        self._stats_interval = self.config.get("stats_interval", 5.0)
        
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            self.console = Console()
            self._rich_available = True
        except ImportError:
            self._rich_available = False
            print("[ConsoleOutput] Rich not available, using plain print")
    
    def send(self, alert: Alert) -> None:
        if not self._enabled:
            return
        
        with self._lock:
            if self._rich_available:
                self._send_rich(alert)
            else:
                print(f"[{alert.timestamp.strftime('%H:%M:%S')}] {alert.message}")
    
    def send_batch(self, alerts: List[Alert]) -> None:
        if not self._enabled or not alerts:
            return
        
        with self._lock:
            for alert in alerts:
                if self._rich_available:
                    self._send_rich(alert)
                else:
                    print(f"[{alert.timestamp.strftime('%H:%M:%S')}] {alert.message}")
    
    def _send_rich(self, alert: Alert) -> None:
        """Send with Rich formatting"""
        from rich.text import Text
        from rich.style import Style
        
        # Color by severity
        colors = {
            "LOW": "green",
            "MEDIUM": "yellow",
            "HIGH": "red",
            "CRITICAL": "bright_red"
        }
        color = colors.get(alert.severity, "white")
        
        text = Text()
        text.append(f"[{alert.timestamp.strftime('%H:%M:%S')}] ", style="dim")
        text.append(alert.message, style=f"bold {color}")
        
        self.console.print(text)
    
    def flush(self) -> None:
        if self._rich_available:
            self.console.clear()
    
    def close(self) -> None:
        pass


class LogFileOutput(BaseOutput):
    """
    File-based logging output
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("LogFile", config)
        self.log_path = self.config.get("path", "logs/scanner.log")
        self._ensure_log_dir()
        self._current_date = datetime.now().date()
        self._file = None
    
    def _ensure_log_dir(self) -> None:
        """Create log directory if needed"""
        log_dir = Path(self.log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file(self):
        """Get or create log file handle"""
        today = datetime.now().date()
        
        if self._file is None or today != self._current_date:
            if self._file:
                self._file.close()
            
            date_str = today.strftime("%Y-%m-%d")
            log_name = f"scanner_{date_str}.log"
            log_file_path = Path(self.log_path).parent / log_name
            
            self._file = open(log_file_path, "a")
            self._current_date = today
    
    def send(self, alert: Alert) -> None:
        if not self._enabled:
            return
        
        try:
            self._get_file()
            log_entry = json.dumps(alert.to_dict())
            self._file.write(log_entry + "\n")
            self._file.flush()
        except Exception as e:
            print(f"[LogFileOutput] Error writing log: {e}")
    
    def send_batch(self, alerts: List[Alert]) -> None:
        if not self._enabled or not alerts:
            return
        
        try:
            self._get_file()
            for alert in alerts:
                log_entry = json.dumps(alert.to_dict())
                self._file.write(log_entry + "\n")
            self._file.flush()
        except Exception as e:
            print(f"[LogFileOutput] Error writing logs: {e}")
    
    def flush(self) -> None:
        if self._file:
            self._file.flush()
    
    def close(self) -> None:
        if self._file:
            self._file.close()
            self._file = None


class MockExecutorOutput(BaseOutput):
    """
    Mock Execution Output - Placeholder for real order execution
    
    Use this to test strategies without placing real orders.
    Later, you can replace this with real broker integration.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("MockExecutor", config)
        self._orders: List[Dict[str, Any]] = []
        self._order_count = 0
        self._lock = threading.Lock()
    
    def send(self, alert: Alert) -> None:
        if not self._enabled:
            return
        
        with self._lock:
            # Generate mock order
            order = {
                "id": f"mock_{self._order_count}",
                "symbol": alert.symbol,
                "side": "BUY" if "up" in alert.message.lower() or "+" in alert.message else "SELL",
                "quantity": self._calculate_quantity(alert),
                "price": None,  # Would be market price
                "type": "MARKET",
                "status": "PENDING",
                "alert": alert.to_dict(),
                "created_at": datetime.now().isoformat()
            }
            
            self._orders.append(order)
            self._order_count += 1
            
            print(f"[MockExecutor] Generated order: {order['symbol']} {order['side']} {order['quantity']} shares")
    
    def send_batch(self, alerts: List[Alert]) -> None:
        for alert in alerts:
            self.send(alert)
    
    def _calculate_quantity(self, alert: Alert) -> int:
        """Calculate mock order quantity based on alert severity"""
        severity_map = {
            "LOW": 10,
            "MEDIUM": 25,
            "HIGH": 50,
            "CRITICAL": 100
        }
        return severity_map.get(alert.severity, 10)
    
    def flush(self) -> None:
        """Process pending orders"""
        with self._lock:
            # In real implementation, this would submit orders
            for order in self._orders:
                if order["status"] == "PENDING":
                    order["status"] = "SIMULATED"
            self._orders = []
    
    def close(self) -> None:
        self.flush()
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Get all orders"""
        with self._lock:
            return list(self._orders)
    
    def clear_orders(self) -> None:
        """Clear order history"""
        with self._lock:
            self._orders.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        with self._lock:
            return {
                "total_orders": self._order_count,
                "pending_orders": len(self._orders),
                "buy_orders": len([o for o in self._orders if o["side"] == "BUY"]),
                "sell_orders": len([o for o in self._orders if o["side"] == "SELL"])
            }


class TelegramOutput(BaseOutput):
    """
    Telegram Bot Output
    Sends alerts to Telegram channel/chat
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Telegram", config)
        self.token = self.config.get("token", "")
        self.chat_id = self.config.get("chat_id", "")
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.parse_mode = self.config.get("parse_mode", "HTML")  # HTML or Markdown
    
    def send(self, alert: Alert) -> None:
        if not self._enabled:
            return
        
        try:
            # Format message
            message = self._format_message(alert)
            
            # Send to Telegram
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": self.parse_mode
            }
            
            import requests
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code != 200:
                print(f"[Telegram] Failed to send: {response.text}")
        
        except Exception as e:
            print(f"[Telegram] Error sending message: {e}")
    
    def _format_message(self, alert: Alert) -> str:
        """Format alert as Telegram message"""
        # Emoji by severity
        emojis = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🔴",
            "CRITICAL": "🚨"
        }
        emoji = emojis.get(alert.severity, "⚪")
        
        message = f"{emoji} <b>{alert.symbol}</b>\n"
        message += f"Pattern: {alert.pattern_name}\n"
        message += f"Severity: {alert.severity}\n"
        message += f"{alert.message}"
        
        return message
    
    def send_batch(self, alerts: List[Alert]) -> None:
        for alert in alerts:
            self.send(alert)
    
    def flush(self) -> None:
        pass
    
    def close(self) -> None:
        pass


class DiscordWebhookOutput(BaseOutput):
    """
    Discord Webhook Output
    Sends alerts to Discord via webhook
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Discord", config)
        self.webhook_url = self.config.get("webhook_url", "")
        self.username = self.config.get("username", "Market Scanner")
        self.avatar_url = self.config.get("avatar_url", "")
    
    def send(self, alert: Alert) -> None:
        if not self._enabled or not self.webhook_url:
            return
        
        try:
            import requests
            
            # Color by severity (Discord uses decimal color)
            colors = {
                "LOW": 5763714,      # Green
                "MEDIUM": 16776960,  # Yellow
                "HIGH": 15132390,    # Red
                "CRITICAL": 15631086 # Bright Red
            }
            color = colors.get(alert.severity, 5763714)
            
            # Build embed
            embed = {
                "title": f"{alert.symbol} - {alert.pattern_name}",
                "description": alert.message,
                "color": color,
                "fields": [
                    {"name": "Severity", "value": alert.severity, "inline": True},
                    {"name": "Value", "value": f"{alert.value:.2f}", "inline": True},
                    {"name": "Threshold", "value": f"{alert.threshold:.2f}", "inline": True}
                ],
                "timestamp": alert.timestamp.isoformat()
            }
            
            payload = {
                "username": self.username,
                "avatar_url": self.avatar_url,
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            
            if response.status_code not in [200, 204]:
                print(f"[Discord] Failed to send: {response.text}")
        
        except Exception as e:
            print(f"[Discord] Error sending message: {e}")
    
    def send_batch(self, alerts: List[Alert]) -> None:
        for alert in alerts:
            self.send(alert)
    
    def flush(self) -> None:
        pass
    
    def close(self) -> None:
        pass


class OutputManager:
    """
    Observer Pattern Implementation for Multi-Channel Output
    
    Manages multiple output channels and distributes alerts to all.
    """
    
    def __init__(self):
        self._outputs: Dict[str, BaseOutput] = {}
        self._lock = threading.Lock()
    
    def register(self, output: BaseOutput) -> None:
        """Register an output handler"""
        with self._lock:
            self._outputs[output.name] = output
    
    def unregister(self, name: str) -> None:
        """Remove an output handler"""
        with self._lock:
            if name in self._outputs:
                self._outputs[name].close()
                del self._outputs[name]
    
    def send(self, alert: Alert) -> None:
        """Send alert to all registered outputs"""
        with self._lock:
            for output in self._outputs.values():
                if output.enabled:
                    try:
                        output.send(alert)
                    except Exception as e:
                        print(f"[OutputManager] Error sending to {output.name}: {e}")
    
    def send_batch(self, alerts: List[Alert]) -> None:
        """Send multiple alerts to all outputs"""
        if not alerts:
            return
        
        with self._lock:
            for output in self._outputs.values():
                if output.enabled:
                    try:
                        output.send_batch(alerts)
                    except Exception as e:
                        print(f"[OutputManager] Error batch sending to {output.name}: {e}")
    
    def flush(self) -> None:
        """Flush all outputs"""
        with self._lock:
            for output in self._outputs.values():
                if output.enabled:
                    output.flush()
    
    def close(self) -> None:
        """Clean up all outputs"""
        with self._lock:
            for output in self._outputs.values():
                output.close()
            self._outputs.clear()
    
    def get_output(self, name: str) -> Optional[BaseOutput]:
        """Get a specific output handler"""
        return self._outputs.get(name)
    
    def get_all_outputs(self) -> Dict[str, BaseOutput]:
        """Get all registered outputs"""
        with self._lock:
            return dict(self._outputs)
    
    def get_enabled_outputs(self) -> List[str]:
        """Get list of enabled output names"""
        with self._lock:
            return [name for name, o in self._outputs.items() if o.enabled]
    
    def set_enabled(self, name: str, enabled: bool) -> None:
        """Enable/disable an output"""
        with self._lock:
            if name in self._outputs:
                self._outputs[name].enabled = enabled


# ============================================================
# MULTI-TIMEFRAME ALERT SUPPORT
# ============================================================

def format_mtf_alert(alert) -> str:
    """Format multi-timeframe alert for output channels"""
    direction_emoji = "📈" if alert.direction == "up" else "📉" if alert.direction == "down" else "⚪"
    
    lines = [
        f"{direction_emoji} MULTI-TIMEFRAME SIGNAL: {alert.symbol}",
        f"{'─' * 40}",
        alert.message,
        "",
        f"📊 Confidence: {alert.score}%",
        f"⏰ {alert.timestamp.strftime('%H:%M:%S')}",
    ]
    
    # Add timeframe details if available
    if hasattr(alert, 'timeframes') and alert.timeframes:
        lines.append("")
        lines.append("📊 Timeframe Analysis:")
        for tf, data in alert.timeframes.items():
            direction = data.get("direction", "?")
            pct = data.get("pct_change", 0)
            emoji = "🟢" if direction == "up" else "🔴" if direction == "down" else "⚪"
            lines.append(f"  {emoji} {tf}: {direction} ({pct:+.2f}%)")
    
    return "\n".join(lines)


def format_mtf_alert_telegram(alert) -> str:
    """Format MTF alert for Telegram (HTML)"""
    direction_emoji = "🟢" if alert.direction == "up" else "🔴" if alert.direction == "down" else "⚪"
    
    html = [
        f"<b>{direction_emoji} MULTI-TIMEFRAME SIGNAL: {alert.symbol}</b>",
        f"<code>{'─' * 40}</code>",
        f"<b>{alert.pattern_name.upper()}</b>",
        "",
        f"<i>{alert.message}</i>",
        "",
        f"📊 Confidence: <b>{alert.score}%</b>",
        f"⏰ {alert.timestamp.strftime('%H:%M:%S')}",
    ]
    
    # Add timeframe breakdown
    if hasattr(alert, 'timeframes') and alert.timeframes:
        html.append("")
        html.append("<b>Timeframe Analysis:</b>")
        for tf, data in alert.timeframes.items():
            direction = data.get("direction", "?")
            pct = data.get("pct_change", 0)
            emoji = "🟢" if direction == "up" else "🔴" if direction == "down" else "⚪"
            html.append(f"{emoji} <b>{tf}</b>: {direction} ({pct:+.2f}%)")
    
    return "\n".join(html)


# Extend ConsoleOutput to handle MTF alerts
def _console_send_mtf(self, alert) -> None:
    """Send MTF alert to console"""
    if not self._enabled:
        return
    
    with self._lock:
        print(f"\n{'=' * 50}")
        print(format_mtf_alert(alert))
        print(f"{'=' * 50}\n")


def _console_send_mtf_rich(self, alert) -> None:
    """Send MTF alert with Rich formatting"""
    if not self._enabled or not self._rich_available:
        return
    
    with self._lock:
        from rich.text import Text
        from rich.panel import Panel
        
        direction_color = "green" if alert.direction == "up" else "red" if alert.direction == "down" else "white"
        
        text = Text()
        text.append(f"🚨 MULTI-TIMEFRAME SIGNAL: {alert.symbol}\n", style=f"bold {direction_color}")
        text.append(f"{'─' * 40}\n")
        text.append(alert.message)
        text.append(f"\n\n📊 Confidence: {alert.score}%")
        
        # Add timeframe breakdown
        if hasattr(alert, 'timeframes') and alert.timeframes:
            text.append("\n\n📊 Timeframe Analysis:\n")
            for tf, data in alert.timeframes.items():
                direction = data.get("direction", "?")
                pct = data.get("pct_change", 0)
                emoji = "🟢" if direction == "up" else "🔴" if direction == "down" else "⚪"
                text.append(f"{emoji} {tf}: {direction} ({pct:+.2f}%)\n")
        
        panel = Panel(text, title=f"{alert.symbol}", expand=False)
        self.console.print(panel)


def _telegram_send_mtf(self, alert) -> None:
    """Send MTF alert to Telegram"""
    if not self._enabled:
        return
    
    try:
        message = format_mtf_alert_telegram(alert)
        
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": self.parse_mode,
            "disable_web_page_preview": True
        }
        
        response = requests.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json=payload,
            timeout=5
        )
        
        if response.status_code != 200:
            print(f"[Telegram] Failed to send: {response.text}")
    
    except Exception as e:
        print(f"[Telegram] Error sending message: {e}")


# Monkey-patch output classes to handle MTF alerts
def _patch_outputs():
    """Patch output classes to support MTF alerts"""
    
    # ConsoleOutput
    ConsoleOutput.send_mtf = _console_send_mtf
    ConsoleOutput.send_mtf_rich = _console_send_mtf_rich
    
    # TelegramOutput  
    TelegramOutput.send_mtf = _telegram_send_mtf


# Call patch on import
_patch_outputs()


# Update OutputManager.send to handle both types
_original_send = None

def _patched_send(self, alert):
    """Patched send that handles both Alert and MTFAlert"""
    # Check if it's an MTF alert (has score attribute)
    if hasattr(alert, 'score') and hasattr(alert, 'direction'):
        for output in list(self._outputs.values()):
            if output.enabled:
                try:
                    if hasattr(output, 'send_mtf'):
                        output.send_mtf(alert)
                    else:
                        # Fallback: print as regular alert
                        print(format_mtf_alert(alert))
                except Exception as e:
                    print(f"[OutputManager] Error sending MTF to {output.name}: {e}")
    else:
        # Regular alert - use original method
        _original_send(self, alert)


# Apply patch after OutputManager is defined
import output as output_module
_original_send = output_module.OutputManager.send
output_module.OutputManager.send = _patched_send

