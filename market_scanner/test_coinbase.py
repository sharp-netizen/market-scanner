from providers import CoinbaseProProvider
import asyncio
import websockets

print('=== Testing Coinbase WebSocket ===\n')

received = []

def on_trade(trade):
    received.append(trade)
    print(f'{trade.symbol}: ${trade.price:,.2f}')

async def test():
    provider = CoinbaseProProvider(
        config={'tickers': ['BTC', 'ETH', 'SOL']},
        callback=on_trade
    )
    
    await provider.connect()
    await provider.subscribe(['BTC', 'ETH', 'SOL'])
    provider._running = True
    
    # Start in background
    task = asyncio.create_task(provider._run())
    
    await asyncio.sleep(3)
    
    provider._running = False
    await task
    await provider.disconnect()
    
    print(f'\nTotal: {len(received)} trades')

asyncio.run(test())
