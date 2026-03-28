#!/usr/bin/env python3
"""Test Aggregator Provider - Multi-provider demo"""

import asyncio
import sys
sys.path.insert(0, '.')
from providers import AggregatorProvider

print('=== AGGREGATOR TEST ===')

received = {}

def on_trade(trade):
    if trade.symbol not in received:
        received[trade.symbol] = 0
    received[trade.symbol] += 1

async def test():
    config = {
        'providers': [
            {'type': 'mock', 'tickers': ['AAPL', 'TSLA', 'NVDA']},
        ]
    }
    
    agg = AggregatorProvider(config, on_trade)
    
    print('Connecting...')
    await agg.connect()
    
    print('Subscribing...')
    await agg.subscribe()
    
    print('Starting...')
    agg._running = True
    task = asyncio.create_task(agg.start())
    
    await asyncio.sleep(3)
    
    print('Stopping...')
    agg._running = False
    await agg.disconnect()
    await task
    
    print('\n=== RESULTS ===')
    for symbol, count in sorted(received.items()):
        print(f'{symbol}: {count} trades')

if __name__ == '__main__':
    asyncio.run(test())
