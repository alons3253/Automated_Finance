import datetime as dt
import sqlite3
import os


# WIP
class purchasingAnalysis:
    def __init__(self, stock_tickers, volume_terms_dict, buy_list, short_list):
        cwd = os.getcwd()
        self.path = fr'{cwd}\Databases\\'
        self.stock_tickers = stock_tickers
        self.volume_dict = volume_terms_dict
        self.buy_list = buy_list
        self.short_list = short_list

    def analysis_operations(self):
        print(self.stock_tickers)
        print(self.volume_dict)
        print(self.buy_list)
        print(self.short_list)
"""

    def analysis_operations():
        # this block is only to see if the stock has had an increase or decrease in short term price respectively
        # if the following conditions are met, then this represents a good trade opportunity
        # this portion works
        for sto in stock_buylist:
            for pos, Item in enumerate(quote_data[sto]):
                if dt.datetime.strptime(quote_data[sto][pos]['time'], "%Y-%m-%d %H:%M:%S") > \
                        (dt.datetime.now() - dt.timedelta(minutes=5)):
                    if pos == (len(quote_data[sto]) - 1) and quote_data[sto][pos]['current price'] < \
                            stock_prices[sto]:
                        stock_price_movement[sto] = 'short-term increase in price'
        for sto in stock_shortlist:
            for pos, Item in enumerate(quote_data[sto]):
                if dt.datetime.strptime(quote_data[sto][pos]['time'], "%Y-%m-%d %H:%M:%S") > \
                        (dt.datetime.now() - dt.timedelta(minutes=5)):
                    # if current price is lower than quote price
                    if pos == (len(quote_data[sto]) - 1) and quote_data[sto][pos]['current price'] > \
                            stock_prices[sto]:
                        stock_price_movement[sto] = 'short-term decrease in price'
        print(stock_price_movement)
        ##############################################################################
        for STOCK_QUOTE in stock_price_movement:
            if 'increase' in stock_price_movement[STOCK_QUOTE]:
                if len(stock_buylist[STOCK_QUOTE]) > 2:
                    if quote_data[STOCK_QUOTE][-1]['current price'] > quote_data[STOCK_QUOTE][-2]['current price'] > \
                            quote_data[STOCK_QUOTE][-3]['current price']:
                        if 'Very Bullish' in stock_buylist[STOCK_QUOTE][-1] and 'Very Bullish' in \
                                stock_buylist[STOCK_QUOTE][-2]:
                            strong_buy.append(STOCK_QUOTE)
                    elif quote_data[STOCK_QUOTE][-1]['current price'] > quote_data[STOCK_QUOTE][-2]['current price']:
                        if 'Bullish' in stock_buylist[STOCK_QUOTE][-1] and 'Bullish' in stock_buylist[STOCK_QUOTE][-2]:
                            buy.append(STOCK_QUOTE)
                    else:
                        weak_buy.append(STOCK_QUOTE)
            if 'decrease' in stock_price_movement[STOCK_QUOTE]:
                if len(stock_shortlist[STOCK_QUOTE]) > 2:
                    if quote_data[STOCK_QUOTE][-1]['current price'] < quote_data[STOCK_QUOTE][-2]['current price'] < \
                            quote_data[STOCK_QUOTE][-3]['current price']:
                        if 'Very Bearish' in stock_shortlist[STOCK_QUOTE][-1] and 'Very Bearish' in STOCK_QUOTE:
                            strong_sell.append(STOCK_QUOTE)
                    elif quote_data[STOCK_QUOTE][-1]['current price'] < quote_data[STOCK_QUOTE][-2]['current price']:
                        if 'Bearish' in stock_shortlist[STOCK_QUOTE][-1] and 'Bearish' in stock_shortlist[STOCK_QUOTE][-2]:
                            sell.append(STOCK_QUOTE)
                    else:
                        weak_sell.append(STOCK_QUOTE)
        ####################################################################################################################
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
"""