import numpy as np
import time

# --- CONFIGURATION ---
NUM_STOCKS = 7000
WICKS_TO_FIND = 15  # Consecutive green wicks
TIME_STEPS = 50  # Keep 50 seconds of history in RAM

def run_benchmark():
    print(f"🚀 Initializing M4 Benchmark for {NUM_STOCKS} stocks...")
    # Pre-allocate a 2D matrix (Stocks x Time)
    # 0 = Red, 1 = Green
    data = np.random.randint(0, 2, size=(NUM_STOCKS, TIME_STEPS))
    print(f"📈 Memory used: ~{data.nbytes / 1e6:.2f} MB")
    print("-" * 40)
    
    while True:
        start_time = time.perf_counter()
        
        # 1. SIMULATE FIREHOSE: Update data (Shift left and add new 1-second wick)
        new_wicks = np.random.randint(0, 2, size=(NUM_STOCKS, 1))
        data = np.hstack((data[:, 1:], new_wicks))
        
        # 2. PATTERN LOGIC: Find stocks with N consecutive green wicks
        # We look at the last 'WICKS_TO_FIND' columns
        recent_history = data[:, -WICKS_TO_FIND:]
        # SUM across the wicks. If sum == WICKS_TO_FIND, it's a perfect green streak.
        streak_counts = np.sum(recent_history, axis=1)
        winners = np.where(streak_counts == WICKS_TO_FIND)[0]
        
        end_time = time.perf_counter()
        processing_ms = (end_time - start_time) * 1000
        
        # 3. OUTPUT
        if len(winners) > 0:
            print(f"🔥 FOUND {len(winners)} RUNNERS | Time: {processing_ms:.2f}ms | Examples: {winners[:5]}")
        else:
            print(f"Scanning... Time: {processing_ms:.2f}ms")
        
        # Slow it down to 1 second intervals
        time.sleep(1)

if __name__ == "__main__":
    try:
        run_benchmark()
    except KeyboardInterrupt:
        print(" Stopping Scanner...")
