import pandas as pd
import datetime as dt
import numpy as np
import time
import os

from ALGO.stock_data_module import stockDataEngine, spy_returns
from ALGO.bond_yield_fetch_module import treasuryYields
from ALGO.excel_formatting_module import ExcelFormatting


def data_to_excel(data, sheet_name):
    cwd = os.getcwd()
    path = cwd + r"\Portfolio-Analysis\Portfolio Data.xlsx"
    metrics = pd.DataFrame(data, columns=['Performance Summary', 'All Trades', 'Long Trades', 'Short Trades'])

    with pd.ExcelWriter(path) as writer:
        metrics.to_excel(writer, sheet_name=sheet_name)

    formatter = ExcelFormatting(file_path=path, worksheet_name=sheet_name)
    formatter.formatting()

    print("Data table of portfolio performance metrics has been exported to Microsoft Excel")


class portfolioAnalysis:
    def __init__(self, api=None):
        pd.options.mode.chained_assignment = None
        self.days = 0
        self.activities_df = None
        self.open_tickers = None
        self.open_position_catalog = None
        self.api = api

    def main(self):
        while True:
            try:
                spec_date = dt.datetime.today() - dt.timedelta(days=self.days)
                date = spec_date.strftime('%Y-%m-%d')
                # print('Attempting to analyze portfolio on {}'.format(date))
                activities = self.api.get_activities(activity_types='FILL', date=date)
                activities_df = pd.DataFrame([activity._raw for activity in activities])
                if not len(activities_df) > 10:
                    raise Exception("Not enough trades for analysis")

                print("Analyzing portfolio activities on {}".format(date))
                activities_df = pd.DataFrame([activity._raw for activity in activities])
                activities_df = activities_df.iloc[::-1]
                activities_df[['price', 'qty']] = activities_df[['price', 'qty']].apply(pd.to_numeric)
                activities_df['net_qty'] = np.where(activities_df.side == 'buy', activities_df.qty, -activities_df.qty)
                activities_df['net_trade'] = -activities_df.net_qty * activities_df.price
                activities_df['cumulative_sum'] = activities_df.groupby('symbol')['net_qty'].apply(lambda g: g.cumsum())
                activities_df.to_excel("Portfolio Activities, {}.xlsx".format(date))
                self.stock_tickers = list(activities_df.symbol.unique())

                # check if there were any open positions on the previous day
                try:
                    prev_day_spec_date = dt.datetime.today() - dt.timedelta(days=(self.days + 1))
                    prev_day_date = prev_day_spec_date.strftime('%Y-%m-%d')
                    prev_day_activities = self.api.get_activities(activity_types='FILL', date=prev_day_date)
                    prev_days_activities_df = pd.DataFrame([activity._raw for activity in prev_day_activities])
                    prev_days_activities_df = prev_days_activities_df.iloc[::-1]
                    prev_days_activities_df[['price', 'qty']] = \
                        prev_days_activities_df[['price', 'qty']].apply(pd.to_numeric)
                    prev_days_activities_df['net_qty'] = \
                        np.where(prev_days_activities_df.side == 'buy', prev_days_activities_df.qty,
                                 -prev_days_activities_df.qty)
                    prev_days_activities_df['net_trade'] = \
                        -prev_days_activities_df.net_qty * prev_days_activities_df.price
                    prev_days_activities_df['cumulative_sum'] = \
                        prev_days_activities_df.groupby('symbol')['net_qty'].apply(lambda h: h.cumsum())
                    prev_days_activities_df.to_excel("Portfolio Activities, {}.xlsx".format(prev_day_date))

                    nonzero_trades = \
                        prev_days_activities_df.groupby('symbol').filter(lambda trade: sum(trade.net_qty) != 0)
                    open_position_catalog = {}
                    open_tickers = nonzero_trades.symbol.unique()
                    # print(open_tickers)

                    nonzero_trades = nonzero_trades.iloc[::-1]
                    for stock in open_tickers:
                        boolean_rectified_open_position = False
                        open_position_catalog[stock] = []
                        open_position_qty = nonzero_trades.iloc[0]['cumulative_sum']
                        for index, row in nonzero_trades.copy().iterrows():
                            if boolean_rectified_open_position:
                                break
                            if row.symbol == stock:
                                if row.net_qty == open_position_qty:
                                    open_position_catalog[stock].append(row)
                                    nonzero_trades = nonzero_trades[nonzero_trades['symbol'] != stock]
                                    boolean_rectified_open_position = True
                                else:
                                    open_position_qty -= row.net_qty
                                    open_position_catalog[stock].append(row)

                    for stock in open_tickers:
                        open_position_catalog[stock] = reversed(open_position_catalog[stock])
                        activities_df = pd.concat([pd.DataFrame(open_position_catalog[stock]), activities_df],
                                                  ignore_index=True)
                except Exception as e:
                    print("Based on the lack of previous days trades, there is probably not an open position")
                break
            except Exception as e:
                if str(e) == str('Not enough trades for analysis'):
                    self.days += 1
                else:
                    print('Program ran into the following error while trying to analyze portfolio data:')
                    print(e)
                    return

        self.date = date
        self.purchasing_filter(activities_df)

    def purchasing_filter(self, purchases_df):
        long_purchases_df = purchases_df.loc[(purchases_df['side'] == 'buy') & (purchases_df['cumulative_sum'] > 0)]
        total_long_purchases = round(long_purchases_df['net_trade'].sum(), 2)
        print("Gross cost of long positions:", total_long_purchases)

        short_purchases_df = purchases_df.loc[(purchases_df['side'] == 'buy') & (purchases_df['cumulative_sum'] <= 0)]
        total_short_purchases = round(short_purchases_df['net_trade'].sum(), 2)
        print("Gross cost of short positions:", total_short_purchases)

        long_sales_df = purchases_df.loc[purchases_df['side'] == 'sell']
        total_long_sells = round(long_sales_df['net_trade'].sum(), 2)
        print("Gross profit of long positions:", total_long_sells)

        short_sales_df = purchases_df.loc[purchases_df['side'] == 'sell_short']
        total_short_sells = round(short_sales_df['net_trade'].sum(), 2)
        print("Gross profit of short positions:", total_short_sells)

        self.trade_settlement(purchases_df)

    def trade_settlement(self, activities_df):
        trade_book = {}
        short_trade_book = {}
        short_order_time_held = {}
        long_order_time_held = {}
        for stock in self.stock_tickers:
            trade_book[stock] = []
            short_trade_book[stock] = []
            short_order_time_held[stock] = []
            long_order_time_held[stock] = []
            trades_list = []
            for index, row in activities_df.iterrows():
                grouped_trades = {}
                if row['symbol'] == stock:
                    grouped_trades.update(row)
                    trades_list.append(grouped_trades)

            grouped_trades_df = pd.DataFrame(trades_list)
            # excel_title = str(stock) + str(' Trades for ') + str(dt.date.today()) + str('.xlsx')
            grouped_trades_df['cumulative_sum'] = grouped_trades_df.groupby('symbol')['net_qty'].apply(
                lambda h: h.cumsum())
            # grouped_trades_df.to_excel(excel_title)

            # here is where the trades will be settled
            rows_to_drop = []
            length_of_df = grouped_trades_df.index
            for index, row in grouped_trades_df.copy().iterrows():
                if grouped_trades_df['type'][index] == 'partial_fill':
                    # noinspection PyTypeChecker
                    for i in range((index + 1), (len(length_of_df) - 1)):
                        if grouped_trades_df['side'][index] == grouped_trades_df['side'][i]:
                            grouped_trades_df['qty'][i] += grouped_trades_df['qty'][index]
                            grouped_trades_df['net_qty'][i] += grouped_trades_df['net_qty'][index]
                            grouped_trades_df['net_trade'][i] += grouped_trades_df['net_trade'][index]
                            rows_to_drop.append(index)
                            break
            for rowtodrop in rows_to_drop:
                grouped_trades_df = grouped_trades_df.drop(rowtodrop)

            same_side_orders = []
            txn_time1 = None
            # net_trade1 = None
            side1 = None
            qty1 = None
            reset_flag = True
            for index, row in grouped_trades_df.copy().iterrows():
                if reset_flag:
                    txn_time1 = dt.datetime.strptime(grouped_trades_df['transaction_time'][index],
                                                     "%Y-%m-%dT%H:%M:%S.%fZ")
                    net_trade1 = grouped_trades_df['net_trade'][index]
                    side1 = grouped_trades_df['side'][index]
                    qty1 = grouped_trades_df['qty'][index]
                    same_side_orders.append([txn_time1, net_trade1, qty1, side1])
                    reset_flag = False
                    continue

                txn_time2 = dt.datetime.strptime(grouped_trades_df['transaction_time'][index], "%Y-%m-%dT%H:%M:%S.%fZ")
                net_trade2 = grouped_trades_df['net_trade'][index]
                side2 = grouped_trades_df['side'][index]
                qty2 = grouped_trades_df['qty'][index]

                if side2 == side1:
                    same_side_orders.append([txn_time2, net_trade2, qty2, side2])
                elif side1 == 'sell_short' and side2 == 'buy':
                    if qty2 > qty1:
                        for i in range(len(same_side_orders)):
                            profitloss = round(same_side_orders[0][1] + ((net_trade2 / qty2) * same_side_orders[0][2]),
                                               2)
                            short_trade_book[stock].append(profitloss)
                            time_held = (txn_time2 - same_side_orders[0][0]).total_seconds()
                            short_order_time_held[stock].append((time_held, same_side_orders[0][2]))
                            same_side_orders.pop(0)
                    else:
                        profitloss = round(same_side_orders[0][1] + net_trade2, 2)
                        short_trade_book[stock].append(profitloss)
                        time_held = (txn_time2 - txn_time1).total_seconds()
                        short_order_time_held[stock].append((time_held, qty2))
                        same_side_orders.pop(0)
                elif side1 == 'buy' and side2 == 'sell':
                    if qty2 > qty1:
                        for i in range(len(same_side_orders)):
                            profitloss = round(same_side_orders[0][1] + ((net_trade2 / qty2) * same_side_orders[0][2]),
                                               2)
                            short_trade_book[stock].append(profitloss)
                            time_held = (txn_time2 - same_side_orders[0][0]).total_seconds()
                            long_order_time_held[stock].append((time_held, same_side_orders[0][2]))
                            same_side_orders.pop(0)
                    else:
                        profitloss = round(same_side_orders[0][1] + net_trade2, 2)
                        trade_book[stock].append(profitloss)
                        time_held = (txn_time2 - txn_time1).total_seconds()
                        long_order_time_held[stock].append((time_held, qty2))
                        same_side_orders.pop(0)
                if len(same_side_orders) == 0:
                    reset_flag = True

        # print(trade_book)
        # print(short_trade_book)
        # print(long_order_time_held)
        # print(short_order_time_held)

        total_profit = 0
        profit_per_symbol = {}
        for stock in trade_book:
            profit_per_symbol[stock] = 0
            for element in trade_book[stock]:
                total_profit += float(element)
                profit_per_symbol[stock] += float(element)
            for element in short_trade_book[stock]:
                total_profit += float(element)
                profit_per_symbol[stock] += float(element)
        # print(round(total_profit, 2))
        # print("Note that there may be a slight discrepancy in calculated prices vs what alpaca's interface shows, \n"
        #       "This is simply due to the fact this calculation concerns CLOSED trades, and doesnt consider the \n"
        #       "changing value of stock(s) held")

        self.trade_calculations(trade_book, short_trade_book, long_order_time_held, short_order_time_held,
                                profit_per_symbol)

    def trade_calculations(self, trade_book, short_trade_book, long_order_time_held, short_order_time_held,
                           profit_per_symbol):
        longtime = 0
        longquantity = 0
        long_length = 0
        shorttime = 0
        shortquantity = 0
        short_length = 0

        for stock in self.stock_tickers:
            for i in range(len(long_order_time_held[stock])):
                longtime += long_order_time_held[stock][i][0]
                longquantity += long_order_time_held[stock][i][1]
                long_length += 1
            for i in range(len(short_order_time_held[stock])):
                shorttime += short_order_time_held[stock][i][0]
                shortquantity += short_order_time_held[stock][i][1]
                short_length += 1

        # avg_long_stock_hold_time = round(longtime / longquantity, 2)
        # avg_short_stock_hold_time = round(shorttime / shortquantity, 2)
        avg_long_trade_hold_time = round(longtime / long_length, 2)
        avg_short_trade_hold_time = round(shorttime / short_length, 2)
        # print("Average stock held for:", round(avg_long_stock_hold_time, 2), 'seconds')
        # print("Average short stock held for:", round(avg_short_stock_hold_time, 2), 'seconds')

        avg_ttl_trade_time = time.strftime("%#M:%S", time.gmtime((avg_short_trade_hold_time +
                                                                      avg_long_trade_hold_time)))
        avg_short_trade_time = time.strftime("%#M:%S", time.gmtime(avg_short_trade_hold_time))
        avg_long_trade_time = time.strftime("%#M:%S", time.gmtime(avg_long_trade_hold_time))

        # print("Average long trade held for:", avg_long_trade_time)
        # print("Average short trade held for:", avg_short_trade_time)
        ##################################################################
        total_gross_profit = 0
        total_gross_loss = 0
        short_gross_profit = 0
        short_gross_loss = 0
        net_short_profit = 0
        total_short_trades = 0
        short_winning_trades = 0
        short_even_trades = 0
        short_losing_trades = 0

        for stock in short_trade_book:
            for i in range(len(short_trade_book[stock])):
                if short_trade_book[stock][i] > 0:
                    short_winning_trades += 1
                    short_gross_profit += short_trade_book[stock][i]
                    total_gross_profit += short_trade_book[stock][i]
                elif short_trade_book[stock][i] < 0:
                    short_losing_trades += 1
                    short_gross_loss += short_trade_book[stock][i]
                    total_gross_loss += short_trade_book[stock][i]
                else:
                    short_even_trades += 1
                total_short_trades += 1
                net_short_profit += short_trade_book[stock][i]

        net_short_profit = round(net_short_profit, 2)
        # print("Short-side net profit:", net_short_profit)
        # print("Short-side profitable trades:", short_winning_trades)
        # print("Short-side even trades:", short_even_trades)
        # print("Short-side Losing trades:", short_losing_trades)
        # print("Total short-side trades:", total_short_trades)

        # initialization of long variables
        long_gross_profit = 0
        long_gross_loss = 0
        net_long_profit = 0
        total_long_trades = 0
        long_winning_trades = 0
        long_even_trades = 0
        long_losing_trades = 0
        for stock in trade_book:
            for i in range(len(trade_book[stock])):
                if trade_book[stock][i] > 0:
                    long_winning_trades += 1
                    long_gross_profit += trade_book[stock][i]
                    total_gross_profit += trade_book[stock][i]
                elif trade_book[stock][i] < 0:
                    long_losing_trades += 1
                    long_gross_loss += trade_book[stock][i]
                    total_gross_loss += trade_book[stock][i]
                else:
                    long_even_trades += 1
                total_long_trades += 1
                net_long_profit += trade_book[stock][i]

        net_long_profit = round(net_long_profit, 4)
        # print("\nLong-side net profit:", net_long_profit)
        # print("Long-side profitable trades:", long_winning_trades)
        # print("Long-side even trades:", long_even_trades)
        # print("Long-side losing trades:", long_losing_trades)
        # print("Total long-side trades", total_long_trades)

        avg_winning_trade = round((total_gross_profit / (long_winning_trades + short_winning_trades)), 4)
        avg_losing_trade = round((total_gross_loss / (total_long_trades + short_losing_trades)), 4)
        avg_long_winning_trade = round(long_gross_profit / long_winning_trades, 4)
        avg_long_losing_trade = round(long_gross_loss / long_losing_trades, 4)
        avg_short_winning_trade = round(short_gross_profit / short_winning_trades, 4)
        avg_short_losing_trade = round(short_gross_loss / short_losing_trades, 4)

        todays_profit_and_loss = round(total_gross_profit + total_gross_loss, 4)
        total_gross_profit = round(total_gross_profit, 4)
        total_gross_loss = round(total_gross_loss, 4)

        # print("\nProfit Metrics:")
        # print("Gross Profit:", total_gross_profit)
        # print("Average Winning Trade:", avg_winning_trade)
        # print("Gross Loss:", total_gross_loss)
        # print("Average Losing Trade:", avg_losing_trade)
        # print("Total Net Profit:", todays_profit_and_loss)

        pd.options.display.float_format = '{:.0f}'.format
        data_engine = stockDataEngine(self.stock_tickers)
        init_data = data_engine.initial_quote_data_fetch()
        quote_data = data_engine.quote_data_processor()
        spyreturn = float(spy_returns())
        bond_object = treasuryYields()
        bond_yields = bond_object.treasury_bond_yields()
        riskfreerate = float(bond_yields[0])

        stock_metrics = [['' for m in range(1)] for i in range(len(self.stock_tickers) * 3)]
        spdr_string = str(spyreturn) + str('%')
        spdr_list = ["Daily return of $SPY", spdr_string]

        stock_index = 0
        account = self.api.get_account()
        for stock in self.stock_tickers:
            print(stock)
            # init data is a list of dicts
            # quote data is just a dict
            # the average max holdings of each stock is limited at 10% of the portfolio
            print(init_data)
            print(quote_data)
            trade_size_relative_to_portfolio = 0.1
            beta = trade_size_relative_to_portfolio * float(init_data[stock][0]['beta'])
            buying_power = float(account.buying_power) / 4
            stock_profit_pct = round((profit_per_symbol[stock] / buying_power) * 100, 4)
            market_returns_pct = round((quote_data[stock]['current price'] - float(init_data[stock][0]['open'])) / 100, 4)
            # divide the 1 month risk free rate by 30 to approximate the rate of bond return for 1 day
            alpha = round((stock_profit_pct - (riskfreerate / 30)) - (beta * (spyreturn - (riskfreerate / 30))), 4)

            list1 = ["Performance of {}:".format(stock), str(market_returns_pct) + str('%')]
            list2 = ["Performance of {} relative to $SPY:".format(stock),
                     str(round(market_returns_pct - spyreturn, 4)) + str('%')]
            list3 = ["\"Alpha\" trading performance of {}:".format(stock), str(alpha) + str('%')]

            stock_metrics[stock_index] = list1
            stock_metrics[stock_index + 1] = list2
            stock_metrics[stock_index + 2] = list3
            stock_index += 3

        if total_gross_profit > -total_gross_loss:
            total_profit_factor = round((total_gross_profit / -total_gross_loss), 4)
        else:
            total_profit_factor = round((total_gross_profit / total_gross_loss), 4)

        if long_gross_profit > -long_gross_loss:
            long_profit_factor = round((long_gross_profit / -long_gross_loss), 4)
        else:
            long_profit_factor = round((long_gross_profit / long_gross_loss), 4)

        if short_gross_profit > -short_gross_loss:
            short_profit_factor = round((short_gross_profit / -short_gross_loss), 4)
        else:
            short_profit_factor = round((short_gross_profit / short_gross_loss), 4)

        ttl_pct_pftability = round(((long_winning_trades + short_winning_trades) /
                                          (total_long_trades + total_short_trades)) * 100, 4)
        long_pct_pftability = round((long_winning_trades / total_long_trades) * 100, 4)
        short_pct_pftability = round((short_winning_trades / total_short_trades) * 100, 4)

        # this is the 2d list used to convert into a pandas dataframe for easy transcription onto an excel document
        data = [['Profit Metrics', '', '', ''],
                ['Total Net Profit:', todays_profit_and_loss, net_long_profit, net_short_profit],
                ['Gross Profit:', total_gross_profit, long_gross_profit, short_gross_profit],
                ['Gross Loss:', total_gross_loss, long_gross_loss, short_gross_loss],
                ['Profit Factor:', total_profit_factor, long_profit_factor, short_profit_factor],
                ['', '', '', ''],
                ['Trade Metrics', '', '', ''],
                ['Total Number of Trades:', int(total_long_trades + total_short_trades), total_long_trades,
                 total_short_trades],
                ['Percent Profitable:', f'{ttl_pct_pftability}%', f'{long_pct_pftability}%',
                 f'{short_pct_pftability}%'],
                ['Average Stock Held Time (Seconds):', avg_ttl_trade_time, avg_long_trade_time, avg_short_trade_time],
                ['Winning Trades:', long_winning_trades + short_winning_trades, long_winning_trades,
                 short_winning_trades],
                ['Average Winning Trade:', avg_winning_trade, avg_long_winning_trade, avg_short_winning_trade],
                ['Losing Trades:', long_losing_trades + short_losing_trades, long_losing_trades, short_losing_trades],
                ['Average Losing Trade:', avg_losing_trade, avg_long_losing_trade, avg_short_losing_trade],
                ['Even Trades', long_even_trades + short_even_trades, long_even_trades, short_even_trades],
                ['', '', '', ''],
                ['Stock Metrics', '', '', ''],
                spdr_list] + stock_metrics

        sheet_name = str('Performance on ' + self.date)
        data_to_excel(data, sheet_name)
