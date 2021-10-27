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
