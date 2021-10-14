import pandas as pd
import requests
from win10toast import ToastNotifier
from requests import get
import websocket
from json import loads
import threading as th
import alpaca_trade_api as trade_api
import datetime as dt
from clr import AddReference
from pandas import DataFrame
import openpyxl
import win32com.client as win32
import os
from bs4 import BeautifulSoup
import numpy as np
import time
import sys


def ticker_operations():
    for STOCK_TICKER in stock_tickers:
        timestamp = dt.datetime.strptime(quote_data[STOCK_TICKER][-1]['time'][11::], '%H:%M:%S').time()
        indicator = quote_data[STOCK_TICKER][-1]['indicator']
        if len(ti_data) > 0:
            buy_votes = int(ti_data[STOCK_TICKER][-1]['buy'])
            sell_votes = int(ti_data[STOCK_TICKER][-1]['sell'])
            neutral_votes = int(ti_data[STOCK_TICKER][-1]['neutral'])
            indicator_votes[STOCK_TICKER]['Bullish Votes'] += buy_votes
            indicator_votes[STOCK_TICKER]['Bearish Votes'] += sell_votes
            indicator_votes[STOCK_TICKER]['Neutral Votes'] += neutral_votes

        if indicator == 'Bullish':
            indicator_votes[STOCK_TICKER]['Bullish Votes'] += 1
        if indicator == 'Bearish':
            indicator_votes[STOCK_TICKER]['Bearish Votes'] += 1

        if indicator_votes[STOCK_TICKER]['Bullish Votes'] > indicator_votes[STOCK_TICKER]['Bearish Votes'] and \
                indicator_votes[STOCK_TICKER]['Bullish Votes'] > indicator_votes[STOCK_TICKER]['Neutral Votes']:
            stock_buylist[STOCK_TICKER].append('Very Bullish at: ' + str(timestamp))
        elif indicator_votes[STOCK_TICKER]['Bullish Votes'] > indicator_votes[STOCK_TICKER]['Bearish Votes']:
            stock_buylist[STOCK_TICKER].append('Bullish at: ' + str(timestamp))

        if indicator_votes[STOCK_TICKER]['Bearish Votes'] > indicator_votes[STOCK_TICKER]['Bullish Votes'] and \
                indicator_votes[STOCK_TICKER]['Bearish Votes'] > indicator_votes[STOCK_TICKER]['Neutral Votes']:
            stock_shortlist[STOCK_TICKER].append('Very Bearish at: ' + str(timestamp))
        elif indicator_votes[STOCK_TICKER]['Bearish Votes'] > indicator_votes[STOCK_TICKER]['Bullish Votes']:
            stock_shortlist[STOCK_TICKER].append('Bearish at: ' + str(timestamp))

    print('Stocks of interest:', stock_tickers)
    print('Buy Side Stocklist:', stock_buylist)
    print('Sell Side Stocklist:', stock_shortlist)
    print('------------------------------------------------------------------------')


def volume_operations():
    for STOCK_TICKER in stock_tickers:
        volume_past_30sec = 0
        volume_past_min = 0
        volume_past_2min = 0
        volume_past_5min = 0
        stock_price = 0
        stock_list_length[STOCK_TICKER] = 0
        length = []
        stock_prices[STOCK_TICKER] = []
        for pos, ite in enumerate(trade_data[STOCK_TICKER]):
            if pos >= int(len(trade_data[STOCK_TICKER]) - 25):
                stock_price += ite['price']
                length.append(ite)
                stock_list_length[STOCK_TICKER] = int(len(length))
            ##############################################################################
            tradetime = dt.datetime.strptime(ite['time'], "%Y-%m-%d %H:%M:%S.%f")
            if tradetime > dt.datetime.now() - dt.timedelta(seconds=30):
                volume_past_30sec += int(ite['volume'])
            if tradetime > dt.datetime.now() - dt.timedelta(seconds=60):
                volume_past_min += int(ite['volume'])
            if tradetime > dt.datetime.now() - dt.timedelta(seconds=120):
                volume_past_2min += int(ite['volume'])
            if tradetime > dt.datetime.now() - dt.timedelta(seconds=300):
                volume_past_5min += int(ite['volume'])
        ##############################################################################
        try:
            stock_prices[STOCK_TICKER] = float("{:.3f}".format(stock_price / stock_list_length[STOCK_TICKER]))
        except ZeroDivisionError:
            stock_prices[STOCK_TICKER] = quote_data[STOCK_TICKER][-1]['current price']
            pass
        volume_terms[STOCK_TICKER] = volume_past_30sec, volume_past_min, volume_past_2min, volume_past_5min
        ##############################################################################
    print('volume by stock ordered 30sec, 1min, 2min and 5min:', volume_terms)
    print('stock prices:', stock_prices)


# might need rework and additional analysis
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


def trade_execution_operations():
    global strong_buy, buy, weak_buy, strong_sell, sell, weak_sell, current_stock_position
    print(api.list_orders())
    block_purchase = []

    if len(api.list_positions()) > 0:
        for stockticker in stock_tickers:
            try:
                stock_position = api.get_position(stockticker)
                print(stock_position)
                position_value = getattr(stock_position, "market_value")
                position_value = abs(float(position_value))
                if position_value >= (0.10 * account_balance):
                    block_purchase.append('block ' + stockticker)
            except Exception as problem:
                print(problem)
                continue

        for opportunity in strong_buy:
            try:
                # for an element in the strong_buy indicator list, if it is equal to the current stock position,
                # then we wont liquidate, if not then we will liquidate
                if opportunity in current_stock_position:
                    continue
                else:
                    # if we have an indicator that is different that we just calculated, we need to remove
                    # the old position and use the new analysis as it is more up to date on the strength of the stock
                    check_orders = api.list_orders(status='open')
                    for order in check_orders:
                        api.cancel_order(order.id)
                    api.close_position(opportunity)
            except Exception as problem:
                print(problem)
                continue

        for opportunity in buy:
            try:
                if opportunity in current_stock_position:
                    continue
                else:
                    check_orders = api.list_orders(status='open')
                    for order in check_orders:
                        api.cancel_order(order.id)
                    api.close_position(opportunity)
            except Exception as problem:
                print(problem)
                continue

        for opportunity in weak_buy:
            try:
                if opportunity in current_stock_position:
                    continue
                else:
                    check_orders = api.list_orders(status='open')
                    for order in check_orders:
                        api.cancel_order(order.id)
                    api.close_position(opportunity)
            except Exception as problem:
                print(problem)
                continue

        for opportunity in strong_sell:
            try:
                if opportunity in current_stock_position:
                    continue
                else:
                    check_orders = api.list_orders(status='open')
                    for order in check_orders:
                        api.cancel_order(order.id)
                    api.close_position(opportunity)
            except Exception as problem:
                print(problem)
                continue

        for opportunity in sell:
            try:
                if opportunity in current_stock_position:
                    continue
                else:
                    check_orders = api.list_orders(status='open')
                    for order in check_orders:
                        api.cancel_order(order.id)
                    api.close_position(opportunity)
            except Exception as problem:
                print(problem)
                continue

        for opportunity in weak_sell:
            try:
                if opportunity in current_stock_position:
                    continue
                else:
                    check_orders = api.list_orders(status='open')
                    for order in check_orders:
                        api.cancel_order(order.id)
                    api.close_position(opportunity)
            except Exception as problem:
                print(problem)
                continue

    #################################################################################################################
    # check orders and see if they should be sold, if we have idle bracket orders with a small fluctuating profit/loss
    # just close them out
    """
    for element in stock_tickers:
        api.list_positions()
        for stockposition in api.list_positions():
            if float(getattr(stockposition, "unrealized_intraday_plpc")) > 0.001:
                check_orders = api.list_orders(status='open')
                for order in check_orders:
                    api.cancel_order(order.id)
                api.close_position(element)
    """

    #################################################################################################################
    AddReference(r"C:\Users\fabio\source\repos\Main Trade Executor Class Library\Main Trade Executor Class Lib"
                 r"rary\bin\Release\Main Trade Executor Class Library.dll")
    import CSharpTradeExecutor
    trader = CSharpTradeExecutor.BracketOrders()

    print(block_purchase)

    for opportunity in strong_buy:
        try:
            for pos, it in enumerate(block_purchase):
                if opportunity in block_purchase[pos]:
                    raise Exception('{} Position has exceeded 10% of the portfolio value'.format(opportunity))
            price = stock_prices[opportunity]
            account_percentage = (account_balance * 0.04) // price
            round_lot = int(account_percentage)
            if round_lot == 0:
                round_lot += 1
            stop_loss = 0.9985 * price
            stoplosslimitprice = .9980 * price
            limit_price = 1.002 * price
            args = [opportunity, 'buy', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                    str(round(stoplosslimitprice, 2))]
            trader.Trader(args)
            notification.show_toast("Program Trades Executed", "Program executed strongbuy trade of {} at {}".format(
                                    opportunity, time.strftime("%H:%M:%S")), duration=4)
            pos = str(opportunity + 'strongbuy')
            current_stock_position.append(pos)
        except Exception as error:
            print('The following error occurred during trade execution:\'{}\''.format(error))
            continue

    for opportunity in buy:
        try:
            for pos, it in enumerate(block_purchase):
                if opportunity in block_purchase[pos]:
                    raise Exception('{} Position has exceeded 10% of the portfolio value'.format(opportunity))
            price = stock_prices[opportunity]
            account_percentage = (account_balance * 0.03) // price
            round_lot = int(account_percentage)
            if round_lot == 0:
                round_lot += 1
            limit_price = 1.0016 * price
            stop_loss = 0.9986 * price
            stoplosslimitprice = 0.9984 * price
            args = [opportunity, 'buy', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                    str(round(stoplosslimitprice, 2))]
            trader.Trader(args)
            notification.show_toast("Program Trades Executed", "Program executed buy trade of {} at {}".format(
                                    opportunity, time.strftime("%H:%M:%S")), duration=4)
            pos = str(opportunity + 'buy')
            current_stock_position.append(pos)
        except Exception as error:
            print('The following error occurred during trade execution:\'{}\''.format(error))
            continue

    for opportunity in weak_buy:
        try:
            for pos, it in enumerate(block_purchase):
                if opportunity in block_purchase[pos]:
                    raise Exception('{} Position has exceeded 10% of the portfolio value'.format(opportunity))
            price = stock_prices[opportunity]
            account_percentage = (account_balance * 0.025) // price
            round_lot = int(account_percentage)
            if round_lot == 0:
                round_lot += 1
            limit_price = 1.0012 * price
            stop_loss = 0.9988 * price
            stoplosslimitprice = 0.9986 * price
            args = [opportunity, 'buy', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                    str(round(stoplosslimitprice, 2))]
            trader.Trader(args)
            notification.show_toast("Program Trades Executed", "Program executed weakbuy trade of {} at {}".format(
                                    opportunity, time.strftime("%H:%M:%S")), duration=4)
            pos = str(opportunity + 'weakbuy')
            current_stock_position.append(pos)
        except Exception as error:
            print('The following error occurred during trade execution:\'{}\''.format(error))
            continue

    # short trades
    for opportunity in strong_sell:
        try:
            for pos, it in enumerate(block_purchase):
                if opportunity in block_purchase[pos]:
                    raise Exception('{} Position has exceeded 10% of the portfolio value'.format(opportunity))
            price = stock_prices[opportunity]
            account_percentage = (account_balance * 0.04) // price
            round_lot = int(account_percentage)
            if round_lot == 0:
                round_lot += 1
            limit_price = .998 * price
            stop_loss = 1.0015 * price
            stoplosslimitprice = 1.0020 * price
            args = [opportunity, 'sell', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                    str(round(stoplosslimitprice, 2))]
            trader.Trader(args)
            notification.show_toast("Program Trades Executed", "Program executed strongsell trade of {} at {}".format(
                                    opportunity, time.strftime("%H:%M:%S")), duration=4)
            pos = str(opportunity + 'strongsell')
            current_stock_position.append(pos)
        except Exception as error:
            print('The following error occurred during trade execution:\'{}\''.format(error))
            continue

    for opportunity in sell:
        try:
            for pos, it in enumerate(block_purchase):
                if opportunity in block_purchase[pos]:
                    raise Exception('{} Position has exceeded 10% of the portfolio value'.format(opportunity))
            price = stock_prices[opportunity]
            account_percentage = (account_balance * 0.03) // price
            round_lot = int(account_percentage)
            if round_lot == 0:
                round_lot += 1
            limit_price = .9984 * price
            stop_loss = 1.0012 * price
            stoplosslimitprice = 1.0016 * price
            args = [opportunity, 'sell', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                    str(round(stoplosslimitprice, 2))]
            trader.Trader(args)
            notification.show_toast("Program Trades Executed", "Program executed sell trade of {} at {}".format(
                                    opportunity, time.strftime("%H:%M:%S")), duration=4)
            pos = str(opportunity + 'sell')
            current_stock_position.append(pos)
        except Exception as error:
            print('The following error occurred during trade execution:\'{}\''.format(error))
            continue

    for opportunity in weak_sell:
        try:
            for pos, it in enumerate(block_purchase):
                if opportunity in block_purchase[pos]:
                    raise Exception('{} Position has exceeded 10% of the portfolio value'.format(opportunity))
            price = stock_prices[opportunity]
            account_percentage = (account_balance * 0.025) // price
            round_lot = int(account_percentage)
            if round_lot == 0:
                round_lot += 1
            limit_price = .9988 * price
            stop_loss = 1.0010 * price
            stoplosslimitprice = 1.0012 * price
            args = [opportunity, 'sell', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                    str(round(stoplosslimitprice, 2))]
            trader.Trader(args)
            notification.show_toast("Program Trades Executed", "Program executed weaksell trade of {} at {}".format(
                                    opportunity, time.strftime("%H:%M:%S")), duration=4)
            pos = str(opportunity + 'weaksell')
            current_stock_position.append(pos)
        except Exception as error:
            print('The following error occurred during trade execution:\'{}\''.format(error))
            continue


def check_trades():
    if len(trade_data) == 0:
        print('No trades were gathered')
        return False
    return True




if __name__ == '__main__':
    while True:
        start = time.time()
        stock_buylist = {}
        stock_shortlist = {}
        stock_prices = {}
        volume_terms = {}
        trade_data = {}
        ti_data = {}
        quote_data = {}
        stock_list_length = {}
        indicator_votes = {}
        current_stock_position = []
        stock_price_movement = {}
        cutoff_bool = False
        errormessage_market_close = 'The market is currently closed'
        errormessage_5min_to_close = 'The market is closing in 5 minutes, be warned that any new positions ' \
                                     'may be held until the next trading day'
        errormessage_trade_fetch = 'No trades gathered'
        for ticker in stock_tickers:
            indicator_votes[ticker] = {'Bullish Votes': 0, 'Bearish Votes': 0, 'Neutral Votes': 0}
            trade_data[ticker] = []
            ti_data[ticker] = []
            quote_data[ticker] = []
            stock_buylist[ticker] = []
            stock_shortlist[ticker] = []
            stock_price_movement[ticker] = ''
        #######################################################################################################
        while True:
            try:
                strong_buy = []
                buy = []
                weak_buy = []
                weak_sell = []
                sell = []
                strong_sell = []
                tradethread = th.Thread(target=trade_execution_operations)
                tradethread.daemon = True
                check_for_market_close()
                main_data_engine()
                print('Trades:', trade_data)
                print('Quotes:', quote_data)
                print('Indicators:', ti_data)
                if not check_trades():
                    print('Warning, No trades gathered! Program terminating...')
                    raise Exception("No trades gathered")
                ##############################
                ticker_operations()
                volume_operations()
                tradethread.start()
                analysis_operations()
                end = time.time()
                print('Time Elapsed (in seconds):', int((end - start)))
                cleanup()
                tradethread.join()
            except Exception as e:
                e = str(e)
                print(e)
                time.sleep(0.5)
                if e == errormessage_market_close or e == errormessage_5min_to_close:
                    api.close_all_positions()
                    api.cancel_all_orders()
                    cutoff_bool = True
                    break
                if e == errormessage_trade_fetch or ZeroDivisionError:
                    break
                else:
                    notification.show_toast("Program Critical Error", "Program Raised Error {}".format(e),
                                            duration=5)
                    print('All pending orders will be cancelled and all positions will be liquidated')
                    api.cancel_all_orders()
                    api.close_all_positions()
        if cutoff_bool:
            break
