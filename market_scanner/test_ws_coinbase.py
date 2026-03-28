#!/usr/bin/env python3
"""Test Coinbase WebSocket Provider"""

import asyncio
import json

async def test():
    print('=== Coinbase WebSocket Test ===\n')
    
    import websockets
    
    received = []
    
    async with websockets.connect('wss://ws-feed.exchange.coinbase.com') as ws:
        # Subscribe
        msg = {
            'type': 'subscribe',
            'product_ids': ['BTC-USD', 'ETH-USD', 'SOL-USD'],
            'channels': ['ticker']
        }
        await ws.send(json.dumps(msg))
        print('Subscribed to BTC, ETH, SOL\n')
        
        # Receive messages
        for i in range(5):
            data = await asyncio.wait_for(ws.recv(), timeout=5)
            parsed = json.loads(data)
            
            if parsed.get('type') == 'ticker':
                symbol = parsed.get('product_id', '').replace('-USD', '')
                price = parsed.get('price', 0)
                received.append((symbol, price))
                print(f'{symbol}: ${price}')
        
        # Unsubscribe
        unsub = {'type': 'unsubscribe', 'product_ids': ['BTC-USD'], 'channels': ['ticker']}
        await ws.send(json.dumps(unsub))
        print('\nUnsubscribed')
    
    print(f'\nTotal: {len(received)} trades')

if __name__ == '__main__':
    asyncio.run(test())
