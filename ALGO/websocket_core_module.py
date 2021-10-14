import websocket
from json import loads
import datetime as dt


class WebsocketBootStrapper:
    def __init__(self, stock_tickers, trade_data):
        token_file = open("finnhub_key.txt")
        lines = token_file.readlines()
        self.token = lines[0].rstrip('\n')

        self.socket = websocket.WebSocketApp("wss://ws.finnhub.io?token={}".format(self.token),
                                             on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        self.socket.on_open = self.on_open
        self.stock_tickers = stock_tickers
        self.trade_data = trade_data

    def start_ws(self):
        self.socket.run_forever()

    def return_data(self):
        print(self.trade_data)
        return self.trade_data

    def close_ws(self):
        self.socket.keep_running = False
        self.socket.close()

    def on_message(self, ws, message):
        if message == '{"type":"ping"}':
            return
        data = loads(message)
        stock_fundamentals = data['data'][0]
        time_integer = stock_fundamentals['t']
        timestamp = dt.datetime.fromtimestamp(time_integer / 1e3)
        timestamp = str("{}.{:03d}".format(timestamp.strftime('%Y-%m-%d %H:%M:%S'), timestamp.microsecond // 1000))
        stock_fundamentals['t'] = timestamp
        s = stock_fundamentals['s']
        stock_fundamentals['time'] = stock_fundamentals.pop('t')
        stock_fundamentals['price'] = stock_fundamentals.pop('p')
        stock_fundamentals['stock'] = stock_fundamentals.pop('s')
        stock_fundamentals['volume'] = stock_fundamentals.pop('v')
        print(stock_fundamentals)
        self.trade_data[s].append(stock_fundamentals)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### websocket closed ###")

    def on_open(self, ws):
        for stock_ticker in self.stock_tickers:
            custom_call = str('{"type":"subscribe","symbol":"') + stock_ticker + str('"}')
            print(custom_call)
            ws.send(custom_call)
