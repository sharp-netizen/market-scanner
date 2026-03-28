#!/usr/bin/env python3
"""Debug Aggregator"""

import asyncio
import sys
sys.path.insert(0, '.')
from providers import AggregatorProvider, MockDataProvider

print('=== DEBUGGING ===')

received = []

def on_trade(trade):
    received.append(trade.symbol)
    print(f'Got: {trade.symbol}', flush=True)

async def test():
    # Test mock directly first
    print('\\n--- Testing Mock Directly ---')
    mock = MockDataProvider({'tickers': ['AAPL']}, on_trade)
    await mock.connect()
    await mock.subscribe(['AAPL'])
    
    print(f'mock._running before: {mock._running}')
    mock._running = True
    print(f'mock._running after: {mock._running}')
    
    # Just call _run() once
    print('Calling mock._run()...', flush=True)
    await mock._run()
    print(f'mock._run() returned')
    
    print(f'Received: {len(received)}')
    
    await mock.disconnect()
    
    print('\\n--- Testing Aggregator ---')
    config = {
        'providers': [
            {'type': 'mock', 'tickers': ['TSLA']}
        ]
    }
    
    agg = AggregatorProvider(config, on_trade)
    await agg.connect()
    await agg.subscribe()
    
    mock2 = agg.providers[0]
    print(f'mock2._running: {mock2._running}')
    
    # Set running and start
    agg._running = True
    mock2._running = True
    
    print('Starting task...', flush=True)
    task = asyncio.create_task(agg._run_provider(mock2))
    
    await asyncio.sleep(1)
    
    mock2._running = False
    agg._running = False
    
    await task
    await agg.disconnect()
    
    print(f'\\nTotal received: {len(received)}')

if __name__ == '__main__':
    asyncio.run(test())
