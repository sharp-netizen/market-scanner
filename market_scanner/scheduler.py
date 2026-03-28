#!/usr/bin/env python3
"""
Market Scanner Scheduler
Starts and stops the scanner based on market hours
"""

import subprocess
import sys
import os
from datetime import datetime

SCRIPT_DIR = "/Users/clawdbotagent/workspace/market_scanner"
VENV_PYTHON = f"{SCRIPT_DIR}/venv/bin/python3"
MAIN_SCRIPT = f"{SCRIPT_DIR}/main_async.py"
LOG_FILE = f"{SCRIPT_DIR}/logs/scheduler.log"


def log(message: str):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


def start():
    """Start the market scanner"""
    if is_running():
        log("Scanner already running")
        return False
    
    log("Starting market scanner...")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = SCRIPT_DIR
    
    # Start in background
    with open(f"{SCRIPT_DIR}/logs/scanner.pid", "w") as f:
        subprocess.Popen(
            [VENV_PYTHON, MAIN_SCRIPT, "--mtf"],
            cwd=SCRIPT_DIR,
            env=env,
            stdout=open(f"{SCRIPT_DIR}/logs/scanner.log", "a"),
            stderr=open(f"{SCRIPT_DIR}/logs/scanner_error.log", "a")
        )
    
    log("Market scanner started")
    return True


def stop():
    """Stop the market scanner"""
    if not is_running():
        log("Scanner not running")
        return False
    
    log("Stopping market scanner...")
    
    # Read PID
    pid_file = f"{SCRIPT_DIR}/logs/scanner.pid"
    if os.path.exists(pid_file):
        with open(pid_file) as f:
            pid = int(f.read().strip())
        
        # Kill process
        try:
            subprocess.run(["kill", str(pid)], check=False)
            os.remove(pid_file)
            log(f"Stopped process {pid}")
        except Exception as e:
            log(f"Error stopping process: {e}")
    
    return True


def is_running():
    """Check if scanner is running"""
    pid_file = f"{SCRIPT_DIR}/logs/scanner.pid"
    if not os.path.exists(pid_file):
        return False
    
    with open(pid_file) as f:
        pid = int(f.read().strip())
    
    try:
        os.kill(pid, 0)  # Signal 0 checks if process exists
        return True
    except OSError:
        os.remove(pid_file)  # Clean up stale PID file
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: scheduler.py [start|stop|status]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "start":
        start()
    elif action == "stop":
        stop()
    elif action == "status":
        print(f"Running: {is_running()}")
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
