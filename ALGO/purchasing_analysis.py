import datetime as dt
import sqlite3
import logging

logger = logging.getLogger(__name__)


# WIP
# NEEDS TO BE TESTED
class purchasingAnalysis:
    def __init__(self, stock_tickers, volume_terms_dict, buy_list, short_list, cwd):
        self.path = fr'{cwd}\Databases\\'
        self.stock_tickers = stock_tickers
        self.volume_dict = volume_terms_dict
        self.buy_list = buy_list
        self.short_list = short_list

    def analysis_operations(self):
        quote_data = {}
        weak_buy = []
        buy = []
        strong_buy = []
        weak_sell = []
        sell = []
        strong_sell = []
        with sqlite3.connect(self.path + 'quotes.db', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as db:
            five_minutes_ago = dt.datetime.now() - dt.timedelta(minutes=5)
            for stock in self.stock_tickers:
                cur = db.execute(f"select * from quotes_{stock} where time > (?)", (five_minutes_ago,))
                quote_data[stock] = cur.fetchall()

        for stock in self.stock_tickers:
            print(stock)
            print(self.volume_dict[stock])
            try:
                order_flow = round(self.volume_dict[stock]['30_s']['buys'] /
                                   (self.volume_dict[stock]['30_s']['buys'] +
                                    self.volume_dict[stock]['30_s']['sells']), 2)
            except ZeroDivisionError:
                continue

            print(order_flow)
            print(self.short_list[stock])
            print(self.buy_list[stock])

            try:
                short_indicator = self.short_list[stock][-1]

                if order_flow < 0.5 and (short_indicator == 'Bearish' and quote_data[stock] == 'Bearish') or \
                        (short_indicator == 'Neutral' or quote_data[stock] == 'Bearish') or \
                        (short_indicator == 'Bearish' or quote_data[stock] == 'Neutral'):
                    weak_sell.append(f'SELL 1 LOT OF {stock}')
                elif order_flow < 0.5 and short_indicator == 'Bearish' and quote_data[stock] == 'Bearish':
                    sell.append(f'SHORT SELL 1 LOT OF {stock}')
                elif order_flow < 0.5 and short_indicator == 'Very Bearish' and (quote_data[stock] == 'Very Bearish' or
                                                                                 quote_data[stock] == 'Bearish'):
                    strong_sell.append(f'SELL LONG POSITION AND SHORT SELL {stock}')
            except IndexError:
                pass

            try:
                long_indicator = self.buy_list[stock][-1]
                # add a clause that if we get the same bullish and very bullish indicators, we make the trade regardless
                # of what yahoo finance rates the stock

                if order_flow > 0.5 and (long_indicator == 'Bullish' and quote_data[stock] == 'Bullish') or \
                        (long_indicator == 'Neutral' or quote_data[stock] == 'Bullish') or \
                        (long_indicator == 'Bullish' or quote_data[stock] == 'Neutral'):
                    weak_buy.append(f'COVER 1 LOT OF {stock}')
                elif order_flow > 0.5 and long_indicator == 'Bullish' and quote_data[stock] == 'Bullish':
                    buy.append(f'BUY 1 LOT OF {stock}')
                elif order_flow > 0.5 and long_indicator == 'Very Bullish' and (quote_data[stock] == 'Very Bullish' or
                                                                                quote_data[stock] == 'Bullish'):
                    strong_buy.append(f'COVER SHORT POSITION AND GO LONG {stock}')
            except IndexError:
                pass

        if len(strong_buy) > 0:
            print('Stock Strong Buy List:', strong_buy)
        if len(buy) > 0:
            print('Stock Buy List:', buy)
        if len(weak_buy) > 0:
            print('Stock Weak Buy List:', weak_buy)
        if len(strong_sell) > 0:
            print('Stock Strong Sell List:', strong_sell)
        if len(sell) > 0:
            print('Stock Sell List:', sell)
        if len(weak_sell) > 0:
            print('Stock Weak Sell List:', weak_sell)

        return strong_buy, buy, weak_buy, strong_sell, sell, weak_sell
