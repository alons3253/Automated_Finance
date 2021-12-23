from clr import AddReference
import datetime as dt
import logging

from ALGO.stock_data_module import stockDataEngine

logger = logging.getLogger(__name__)


def order_checker(api, analysis, current_stock_position):
    try:
        # for an element in the strong_buy indicator list, if it is equal to the current stock position,
        # then we wont liquidate, if not then we will liquidate
        if analysis in current_stock_position:
            return
        else:
            # if we have an indicator that is different that we just calculated, we need to remove
            # the old position and use the new analysis as it is more up to date on the strength of the stock
            check_orders = api.list_orders(status='open')
            for order in check_orders:
                api.cancel_order(order.id)
            api.close_position(analysis)
    except Exception as problem:
        print(problem)
        return


# not 100% to my liking and needs to be tested
class tradeExecution:
    def __init__(self, api, tickers):
        self.api = api
        self.stock_tickers = tickers
        AddReference(r"C:\Users\fabio\source\repos\Main Trade Executor Class Library\Main Trade Executor Class Lib"
                     r"rary\bin\Release\Main Trade Executor Class Library.dll")
        import CSharpTradeExecutor
        self.trader = CSharpTradeExecutor.BracketOrders()

    def trade_execution(self, account_balance, strong_buy, buy, weak_buy, strong_sell, sell, weak_sell):
        self.api.list_orders()
        block_purchases = []
        current_stock_position = []
        if len(self.api.list_positions()) > 0:
            for stock in self.stock_tickers:
                try:
                    stock_position = self.api.get_position(stock)
                    print(stock_position)
                    position_value = getattr(stock_position, "market_value")
                    position_value = abs(float(position_value))
                    if position_value >= (0.10 * account_balance):
                        block_purchases.append('block ' + stock)
                except Exception as problem:
                    print(problem)
                    continue

            for analysis in strong_buy:
                print(analysis)
                order_checker(self.api, analysis, current_stock_position)
            for analysis in buy:
                order_checker(self.api, analysis, current_stock_position)
            for analysis in weak_buy:
                order_checker(self.api, analysis, current_stock_position)
            for analysis in strong_sell:
                order_checker(self.api, analysis, current_stock_position)
            for analysis in sell:
                order_checker(self.api, analysis, current_stock_position)
            for analysis in weak_sell:
                order_checker(self.api, analysis, current_stock_position)

        quote_data = {}
        for stock in self.stock_tickers:
            quote_data[stock] = []

        quote_data = stockDataEngine(self.stock_tickers, quote_data).quote_data_processor()

        for analysis in strong_buy:
            try:
                for position, item in enumerate(block_purchases):
                    if analysis in block_purchases[position]:
                        raise Exception('{} Position has exceeded 10% of the portfolio value'.format(analysis))
                # replace this with the stock fetch module to get as accurate of a stock price as possible
                stock = analysis.split()[-1]
                price = quote_data[stock]['current price']
                account_percentage = (account_balance * 0.04) // price
                round_lot = int(account_percentage)
                if round_lot == 0:
                    round_lot += 1
                stop_loss = 0.9985 * price
                stoplosslimitprice = .9980 * price
                limit_price = 1.002 * price
                args = [stock, 'buy', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                        str(round(stoplosslimitprice, 2))]
                self.trader.Trader(args)
                print(f"Program executed strongbuy trade of {stock} at {dt.datetime.now()}")
                pos = str(stock + ' strongbuy')
                current_stock_position.append(pos)
            except Exception as error:
                print('The following error occurred during trade execution:\'{}\''.format(error))
                continue

        for analysis in buy:
            try:
                for position, item in enumerate(block_purchases):
                    if analysis in block_purchases[position]:
                        raise Exception('{} Position has exceeded 10% of the portfolio value'.format(analysis))
                # replace this with the stock fetch module to get as accurate of a stock price as possible
                stock = analysis.split()[-1]
                price = quote_data[stock]['current price']
                account_percentage = (account_balance * 0.03) // price
                round_lot = int(account_percentage)
                if round_lot == 0:
                    round_lot += 1
                limit_price = 1.0016 * price
                stop_loss = 0.9986 * price
                stoplosslimitprice = 0.9984 * price
                args = [stock, 'buy', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                        str(round(stoplosslimitprice, 2))]
                self.trader.Trader(args)
                print(f"Program executed buy trade of {stock} at {dt.datetime.now()}")
                pos = str(stock + ' buy')
                current_stock_position.append(pos)
            except Exception as error:
                print('The following error occurred during trade execution:\'{}\''.format(error))
                continue

        for analysis in weak_buy:
            try:
                for position, item in enumerate(block_purchases):
                    if analysis in block_purchases[position]:
                        raise Exception('{} Position has exceeded 10% of the portfolio value'.format(analysis))
                # replace this with the stock fetch module to get as accurate of a stock price as possible
                stock = analysis.split()[-1]
                price = quote_data[stock]['current price']
                account_percentage = (account_balance * 0.025) // price
                round_lot = int(account_percentage)
                if round_lot == 0:
                    round_lot += 1
                limit_price = 1.0012 * price
                stop_loss = 0.9988 * price
                stoplosslimitprice = 0.9986 * price
                args = [stock, 'buy', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                        str(round(stoplosslimitprice, 2))]
                self.trader.Trader(args)
                print(f"Program executed weakbuy trade of {stock} at {dt.datetime.now()}")
                pos = str(stock + ' weakbuy')
                current_stock_position.append(pos)
            except Exception as error:
                print('The following error occurred during trade execution:\'{}\''.format(error))
                continue

        # short trades
        for analysis in strong_sell:
            try:
                for position, item in enumerate(block_purchases):
                    if analysis in block_purchases[position]:
                        raise Exception('{} Position has exceeded 10% of the portfolio value'.format(analysis))
                # replace this with the stock fetch module to get as accurate of a stock price as possible
                stock = analysis.split()[-1]
                price = quote_data[stock]['current price']
                account_percentage = (account_balance * 0.04) // price
                round_lot = int(account_percentage)
                if round_lot == 0:
                    round_lot += 1
                limit_price = .998 * price
                stop_loss = 1.0015 * price
                stoplosslimitprice = 1.0020 * price
                args = [stock, 'sell', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                        str(round(stoplosslimitprice, 2))]
                self.trader.Trader(args)
                print(f"Program executed strongsell trade of {stock} at {dt.datetime.now()}")
                pos = str(stock + ' strongsell')
                current_stock_position.append(pos)
            except Exception as error:
                print('The following error occurred during trade execution:\'{}\''.format(error))
                continue

        for analysis in sell:
            try:
                for position, item in enumerate(block_purchases):
                    if analysis in block_purchases[position]:
                        raise Exception('{} Position has exceeded 10% of the portfolio value'.format(analysis))
                # replace this with the stock fetch module to get as accurate of a stock price as possible
                stock = analysis.split()[-1]
                price = quote_data[stock]['current price']
                account_percentage = (account_balance * 0.03) // price
                round_lot = int(account_percentage)
                if round_lot == 0:
                    round_lot += 1
                limit_price = .9984 * price
                stop_loss = 1.0012 * price
                stoplosslimitprice = 1.0016 * price
                args = [stock, 'sell', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                        str(round(stoplosslimitprice, 2))]
                self.trader.Trader(args)
                print(f"Program executed sell trade of {stock} at {dt.datetime.now()}")
                pos = str(stock + ' sell')
                current_stock_position.append(pos)
            except Exception as error:
                print('The following error occurred during trade execution:\'{}\''.format(error))
                continue

        for analysis in weak_sell:
            try:
                for position, item in enumerate(block_purchases):
                    if analysis in block_purchases[position]:
                        raise Exception('{} Position has exceeded 10% of the portfolio value'.format(analysis))
                # replace this with the stock fetch module to get as accurate of a stock price as possible
                stock = analysis.split()[-1]
                price = quote_data[stock]['current price']
                account_percentage = (account_balance * 0.025) // price
                round_lot = int(account_percentage)
                if round_lot == 0:
                    round_lot += 1
                limit_price = .9988 * price
                stop_loss = 1.0010 * price
                stoplosslimitprice = 1.0012 * price
                args = [stock, 'sell', str(round_lot), str(round(stop_loss, 2)), str(round(limit_price, 2)),
                        str(round(stoplosslimitprice, 2))]
                self.trader.Trader(args)
                print(f"Program executed sell trade of {stock} at {dt.datetime.now()}")
                pos = str(stock + ' weaksell')
                current_stock_position.append(pos)
            except Exception as error:
                print('The following error occurred during trade execution:\'{}\''.format(error))
                continue

"""
def trade_execution_operations():
    #################################################################################################################
    # check orders and see if they should be sold, if we have idle bracket orders with a small fluctuating profit/loss
    # just close them out
    for element in stock_tickers:
        api.list_positions()
        for stockposition in api.list_positions():
            if float(getattr(stockposition, "unrealized_intraday_plpc")) > 0.001:
                check_orders = api.list_orders(status='open')
                for order in check_orders:
                    api.cancel_order(order.id)
                api.close_position(element)
"""