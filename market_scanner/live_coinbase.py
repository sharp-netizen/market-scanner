#!/usr/bin/env python3
"""Live Coinbase WebSocket Stream - See incoming data in real-time"""

import asyncio
import websockets
import json
import sys

async def stream():
    print("=" * 60)
    print("  LIVE COINBASE WEBSOCKET STREAM")
    print("  BTC-USD | ETH-USD | SOL-USD")
    print("=" * 60)
    print()
    print("Press Ctrl+C to stop")
    print("-" * 60)
    print()
    
    try:
        async with websockets.connect('wss://ws-feed.exchange.coinbase.com') as ws:
            # Subscribe
            msg = {
                'type': 'subscribe',
                'product_ids': ['BTC-USD', 'ETH-USD', 'SOL-USD'],
                'channels': ['ticker']
            }
            await ws.send(json.dumps(msg))
            
            # Count messages
            count = 0
            
            while True:
                data = await ws.recv()
                parsed = json.loads(data)
                
                count += 1
                
                # Show all messages
                msg_type = parsed.get('type', 'unknown')
                
                if msg_type == 'ticker':
                    product = parsed.get('product_id', '')
                    symbol = product.replace('-USD', '')
                    price = parsed.get('price', '0')
                    size = parsed.get('last_size', '0')
                    side = parsed.get('side', '')
                    
                    print(f"[{count:4}] 📊 {symbol:4} | ${price:>12} | Vol: {size:>8} | {side}")
                
                elif msg_type == 'subscriptions':
                    print(f"[{count:4}] ✅ Subscribed to channels")
                
                else:
                    print(f"[{count:4}] 🔧 {msg_type}")
    
    except websockets.ConnectionClosed:
        print("\n❌ Connection closed")
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    print("Starting WebSocket stream...")
    print()
    asyncio.run(stream())
