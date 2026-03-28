#!/usr/bin/env python3
"""Test Aggregator Provider - Debug Version"""

import asyncio
import sys
sys.path.insert(0, '.')
from providers import AggregatorProvider

print('=== TESTING AGGREGATOR ===')

received = {}
trade_count = 0

def on_trade(trade):
    global trade_count
    trade_count += 1
    if trade.symbol not in received:
        received[trade.symbol] = 0
    received[trade.symbol] += 1
    print(f'[{trade_count}] {trade.symbol}: ${trade.price}', flush=True)

async def test():
    config = {
        'providers': [
            {'type': 'mock', 'tickers': ['AAPL', 'TSLA']},
        ]
    }
    
    agg = AggregatorProvider(config, on_trade)
    
    print('1. Creating aggregator...', flush=True)
    
    print('2. Connecting...', flush=True)
    await agg.connect()
    
    # Manually subscribe to verify
    mock = agg.providers[0]
    print(f'3. Before subscribe - subscribed_tickers: {mock.subscribed_tickers}', flush=True)
    
    print('4. Subscribing...', flush=True)
    await agg.subscribe()
    
    print(f'5. After subscribe - subscribed_tickers: {mock.subscribed_tickers}', flush=True)
    
    print('6. Starting...', flush=True)
    
    # Start aggregator in background
    agg._running = True
    task = asyncio.create_task(agg.start())
    
    # Give it time to start
    await asyncio.sleep(0.5)
    
    print(f'\\n7. Checking...', flush=True)
    print(f'   mock._running: {mock._running}', flush=True)
    print(f'   mock.subscribed_tickers: {mock.subscribed_tickers}', flush=True)
    
    await asyncio.sleep(1)
    
    print('\\n8. Stopping...', flush=True)
    agg._running = False
    await agg.disconnect()
    await task
    
    print('\\n=== RESULTS ===', flush=True)
    for symbol, count in sorted(received.items()):
        print(f'{symbol}: {count} trades')
    
    print(f'\\nTotal trades: {trade_count}')

if __name__ == '__main__':
    asyncio.run(test())
