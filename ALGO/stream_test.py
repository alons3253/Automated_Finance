import asyncio
import logging
import json
import re
import websockets
import queue
from alpaca_trade_api.entity import Entity
import alpaca_trade_api
import alpaca_trade_api as tradeapi
from alpaca_trade_api.stream2 import StreamConn


async def trade_callback(t):
    logging.debug(t)
    print('trade', t)


async def quote_callback(q):
    print('quote', q)


# Initiate Class Instance
def main():
    stream = alpaca_trade_api.stream.Stream(key_id="PK0QPQZ255LO6DW35GF2",
                    secret_key="q6pbl9uKwkk7qvcNZHQqRbsN9NkQwdKZaHfogNNf",
                    base_url=alpaca_trade_api.stream2.URL('https://paper-api.alpaca.markets'),
                    data_feed='iex')  # <- replace to 'sip' if you have PRO subscription

    # subscribing to event
    stream.subscribe_trades(trade_callback, 'AAPL')
    stream.subscribe_quotes(quote_callback, 'IBM')

    stream.run()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s  %(levelname)s %(message)s',
                        level=logging.INFO)

    endpoint = alpaca_trade_api.stream.URL("wss://data.alpaca.markets/stream")
    key_id = "PK0QPQZ255LO6DW35GF2"
    secret_key = "q6pbl9uKwkk7qvcNZHQqRbsN9NkQwdKZaHfogNNf"
    WEBSOCKET_DEFAULTS = {"ping_interval": 10, "ping_timeout": 180, "max_queue": 1024}
    stock = 'AAPL'
    #ws = Websocket(endpoint, key_id, secret_key, WEBSOCKET_DEFAULTS, stock)
    #ws._run_forever()

    main()

    #ws = alpaca_trade_api.stream.TradingStream(key_id, secret_key, endpoint)
    #ws.subscribe_trade_updates(handler)
