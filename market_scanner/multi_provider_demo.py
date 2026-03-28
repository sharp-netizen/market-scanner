#!/usr/bin/env python3
"""Simple Multi-Provider Demo"""

import asyncio
import sys
sys.path.insert(0, '.')

from providers import MockDataProvider, CoinbaseProProvider

print('=== MULTI-PROVIDER DEMO ===')
print()

received = {}

def on_trade(trade):
    if trade.symbol not in received:
        received[trade.symbol] = 0
    received[trade.symbol] += 1

async def main():
    # Provider 1: Mock (stocks)
    print('Starting Mock (AAPL, TSLA)...')
    mock = MockDataProvider({'tickers': ['AAPL', 'TSLA']}, on_trade)
    await mock.connect()
    await mock.subscribe(['AAPL', 'TSLA'])
    mock._running = True
    mock_task = asyncio.create_task(mock._run())
    
    # Provider 2: Coinbase (crypto)
    print('Starting Coinbase (BTC, ETH)...')
    coinbase = CoinbaseProProvider({'tickers': ['BTC', 'ETH']}, on_trade)
    await coinbase.connect()
    await coinbase.subscribe(['BTC', 'ETH'])
    coinbase._running = True
    coinbase_task = asyncio.create_task(coinbase._run())
    
    print()
    print('Running for 3 seconds...')
    print()
    
    await asyncio.sleep(3)
    
    # Stop
    mock._running = False
    coinbase._running = False
    
    await mock.disconnect()
    await coinbase.disconnect()
    
    await mock_task
    await coinbase_task
    
    print()
    print('=== RESULTS ===')
    for symbol, count in sorted(received.items()):
        print(f'{symbol}: {count} trades')

if __name__ == '__main__':
    asyncio.run(main())
