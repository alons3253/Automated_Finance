# updated to full functionality

import concurrent.futures
import datetime as dt
import time
import threading as th
import http.client as httplib
import sys
import logging

from ALGO.stock_init_fetch_module import APIbootstrap
from ALGO.websocket_core_module import WebsocketBootStrapper
from ALGO.stock_data_module import stockDataEngine
from ALGO.technical_indicators_core import technicalIndicators
from ALGO.bond_yield_fetch_module import bondYields
from ALGO.options_module import Options
from ALGO.portfolio_analysis_module import portfolioAnalysis
from ALGO.file_handling_module import filePruning
from ALGO.stock_and_option_analysis_module import stockAnalysis
from ALGO.db_initializer import databaseInitializer
from ALGO.purchasing_analysis import purchasingAnalysis
from ALGO.trade_executor_module import tradeExecution


# minor date functions
def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def custom_strftime(time_format, t):
    return t.strftime(time_format).replace('{S}', str(t.day) + suffix(t.day))


def time_initialization():
    fulltimezone = str(dt.datetime.now(dt.timezone.utc).astimezone().tzinfo)
    local_timezone = ''.join([c for c in fulltimezone if c.isupper()])
    proper_date = custom_strftime('%B {S}, %Y', dt.datetime.now())
    print('Today\'s date:', proper_date)
    proper_time = dt.datetime.strftime(dt.datetime.now(), "%I:%M:%S %p")
    print('The time is:', proper_time, local_timezone)

    cstdelta = dt.timedelta(hours=1)
    mkt_close = (clock.next_close - cstdelta).time()
    mkt_close_time_ampm = mkt_close.strftime("%#I:%M %p")

    mkt_open_date = custom_strftime('%B {S}, %Y', clock.next_open)
    mkt_open_time = (clock.next_open - cstdelta).time()
    market_open_time_ampm = mkt_open_time.strftime("%#I:%M %p")

    market_closed_boolean = False
    if not clock.is_open:
        print('The stock market is currently closed, but will reopen on:')
        print(mkt_open_date + ' at ' + market_open_time_ampm + ' ' + local_timezone)
        market_closed_boolean = True
    else:
        print('The stock market closes at ' + mkt_close_time_ampm + ' today')

    return mkt_close, market_closed_boolean


# disabled for now
def check_for_market_close():
    if not clock.is_open:
        raise Exception('The market is currently closed')

    tmp_fivemintime = dt.datetime.combine(dt.date(1, 1, 1), market_close)
    fiveminfromclose = (tmp_fivemintime - dt.timedelta(minutes=5)).time()
    if dt.datetime.now().time() > fiveminfromclose:
        raise Exception('The market is closing in 5 minutes, all positions have been closed')


# working
def websocket_boot():
    try:
        socket_th = th.Thread(target=websocket_bootstrap.start_ws)
        socket_th.daemon = True
        socket_th.start()
    except Exception as error:
        print(error)
        websocket_bootstrap.close_ws()


# working
def data_thread_marshaller():
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(stock_data_bootstrap.quote_data_processor).result()
        executor.submit(finnhub_tech_bootstrap.tech_indicator).result()


# working
def initial_fetch():
    # initial fetches
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        initial_quote_fetch = executor.submit(stock_data_bootstrap.initial_quote_data_fetch).result()
        stock_quotes = executor.submit(stock_data_bootstrap.quote_data_processor).result()
        treasury_yields = executor.submit(bond_bootstrap.treasury_bond_yields).result()
        libor_yields = executor.submit(bond_bootstrap.LIBOR_yields).result()
        ti_fetch = executor.submit(finnhub_tech_bootstrap.tech_indicator).result()

    print("T-Bond Yields:", treasury_yields)
    print("LIBOR Yields:", libor_yields)
    print(initial_quote_fetch)
    print(stock_quotes)
    print(ti_fetch)

    try:
        options_bootstrapper = Options(stock_tickers=stock_tickers, initial_data=initial_quote_fetch,
                                       quote_data=stock_quotes, rate=libor_yields)
        options_pricing = options_bootstrapper.thread_marshaller()

        return options_pricing
    except Exception as error:
        logging.error(f"Exception occurred {error}", exc_info=True)


# WIP
def initial_analysis(options_pricing):
    # note as of 10/20, i am ignoring the options for now while i rebuild the analysis and trading modules

    """
    for the initial analysis function, we want to take a look at the options we just gathered and take a note
    of a couple of things, namely how large is the open interest?

    also take a look at the technical indicators that we have gathered, and the price and its change from the previous
    trading day, if there was a big move premarket compared to yesterdays close then we want to buy that stock
    """
    # first lets look at early opex and check to make sure it's well priced
    print('---------------------------------------------')
    print('Options Analysis')
    for opex in options_pricing:
        print(opex)
        print(options_pricing[opex])


# needs fixing
def cleanup():
    # needs to remove the far dated elements in the sql databases
    db_bootstrap.cleanup_of_trade_database('trades.db')
    db_bootstrap.cleanup_of_quote_database('quotes.db')
    db_bootstrap.cleanup_of_indicators_database('indicators.db')


def data_analysis():
    analysis_module = stockAnalysis(stock_tickers, stock_quote_data, ti_data, indicator_votes)
    buy_list, short_list = analysis_module.indicator_analysis(stock_shortlist, stock_buylist, 'indicators.db')
    volume_terms_dict = analysis_module.volume_analysis(tick_test, 'trades.db')

    # WIP
    for st in stock_tickers:
        if volume_terms_dict[st]['30_seconds']['shares_bought'] == \
                volume_terms_dict[st]['1_minute']['shares_bought'] or \
                volume_terms_dict[st]['1_minute']['shares_bought'] == \
                volume_terms_dict[st]['2_minutes']['shares_bought']:
            continue
        else:
            strong_buy, buy, weak_buy, strong_sell, sell, weak_sell = \
                purchasingAnalysis([st], volume_terms_dict, buy_list, short_list).analysis_operations(stock_quote_data)

            trade_bootstrap.trade_execution(account_balance, strong_buy, buy, weak_buy, strong_sell, sell, weak_sell)

        stock_quote_data[st] = []


if __name__ == '__main__':
    # error handling
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # create file handler which logs even debug messages
    fh = logging.FileHandler('tmp.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    # check for an internet connection
    conn = httplib.HTTPConnection(r"www.google.com", timeout=5)
    try:
        conn.request("HEAD", "/")
        conn.close()
    except Exception as e:
        conn.close()
        logging.critical("You need to have an internet connection!")
        sys.exit(0)

    file_handler_module = filePruning()
    file_handler_module.initialize_directories()
    file_handler_module.prune_files()

    api, alpaca_data_keys, finnhub_token, brokerage_keys = databaseInitializer().check_for_account_details()

    account = api.get_account()
    clock = api.get_clock()

    account_balance = float(account.buying_power) / 2
    print('Trading account status:', account.status)
    print('Current account balance (without margin) is: $' + str(round(account_balance, 2)))

    market_close, market_closed_bool = time_initialization()

    manual_override_bool = False
    if input("Manual override? (y/n)") == 'y':
        manual_override_bool = True

    # if market_closed_bool is False and manual_override_bool is True:
    if manual_override_bool is True:
        print("Select from one of the following choices:")
        print('Press 1 for Automated Stock Fetch and Trading')
        print('Press 2 for Manual Stock Fetch and Automated Trading')
        print('Press 3 for Portfolio Analysis')
        print('This program is developed solely by Anthony M. Lonsdale')
        print('Contact Information:')
        print('E-mail: alons3253@gmail.com')
        print('Cell: 816-872-7762')

        choice = None
        while True:
            try:
                choice = int(input('Enter: '))
                if choice > 3:
                    raise ValueError
            except ValueError:
                print('Invalid input')
                continue
            else:
                break

        stock_tickers = []
        if choice == 1:
            stock_tickers = APIbootstrap(_api=api).get_tickers()
        if choice == 2:
            print("Input stock tickers separated by a space, the quotes and trades for each stock will be streamed")
            print("When you are done entering tickers, press Enter to show the quotes for each stock in order")
            print("Type 'close' in order to close all current positions")
            stock_tickers = input('Enter Ticker(s): ').upper().split()

            while True:
                try:
                    if stock_tickers == ['CLOSE']:
                        api.cancel_all_orders()
                        api.close_all_positions()
                        stock_tickers = input('Positions have been closed, Enter Ticker(s): ').upper().split()

                    for position, item in enumerate(stock_tickers):
                        try:
                            asset = api.get_asset(item)
                            if not asset.tradable:
                                print(item, 'is not available to trade on Alpaca!')
                                stock_tickers[position] = input('Enter different ticker: ').upper()
                            continue
                        except Exception as e:
                            print(e)
                            print(stock_tickers[position], 'is not a valid ticker!')
                            stock_tickers[position] = input('Enter a different ticker: ').upper()

                    for stock in stock_tickers:
                        try:
                            asset = api.get_asset(stock)
                            if not asset.tradable:
                                raise Exception("Not Tradable")
                        except Exception:
                            raise Exception("Not Tradable")
                    break
                except Exception as stockinputerror:
                    print(stockinputerror)
                    print("There was a problem with the ticker(s) that you entered")
                    continue

        # Start of main program
        # if not choice == 3 and not market_closed_bool:
        if not choice == 3:
            # bootstrappers
            while True:
                trade_data = {}
                stock_quote_data = {}
                ti_data = {}
                indicator_votes = {}
                stock_buylist = {}
                stock_shortlist = {}
                tick_test = {}
                for stock in stock_tickers:
                    stock_buylist[stock] = []
                    stock_shortlist[stock] = []
                    trade_data[stock] = []
                    stock_quote_data[stock] = []
                    ti_data[stock] = []
                    indicator_votes[stock] = {'Bullish Votes': 0, 'Bearish Votes': 0, 'Neutral Votes': 0}
                    uptick = False
                    downtick = False
                    zerotick = False
                    tick_test[stock] = [uptick, downtick, zerotick]

                stock_data_bootstrap = stockDataEngine(stock_tickers, stock_quote_data)
                websocket_bootstrap = WebsocketBootStrapper(stock_tickers, trade_data, finnhub_token)
                finnhub_tech_bootstrap = technicalIndicators(stock_tickers, ti_data)
                bond_bootstrap = bondYields()
                db_bootstrap = databaseInitializer(stock_tickers)
                trade_bootstrap = tradeExecution(api, stock_tickers)

                errormessage_market_close = 'The market is currently closed'
                errormessage_5min_to_close = 'The market is closing in 5 minutes, be warned that any new positions ' \
                                             'may be held until the next trading day'
                errormessage_trade_fetch = 'No trades gathered'
                cutoff_bool = False
                #######################################################################################################
                print("Starting Initial Fetch, this may take several minutes")
                options_pricing = initial_fetch()
                websocket_boot()
                initial_analysis(options_pricing)
                db_bootstrap.generation_of_trade_database('trades.db')
                db_bootstrap.generation_of_quote_database('quotes.db')
                db_bootstrap.generation_of_indicators_database('indicators.db')
                while True:
                    """
                    works well as of 10/28/2021
                    want to optimize the data i am pulling, do not want to take the entire chain of intraday data
                    when i am doing minute by minute updates, also that should probably go to a db
                    
                    ideally i will want to get rid of the 10 second time.sleep at the end of this loop
                    
                    the options pricing analysis will be added in the end once i figure out what to do with it
                    """
                    data_thread_marshaller()
                    # we have the trade data information loaded into the sql database and i want to also do this
                    # for the quote and technical indicator data because its better and more memory efficient
                    trade_data = websocket_bootstrap.return_data()
                    print(trade_data)
                    print(stock_quote_data)
                    print(ti_data)
                    trade_data = db_bootstrap.insertion_into_database(trade_data, 'trades.db')
                    stock_quote_data = db_bootstrap.insertion_into_quote_database(stock_quote_data, 'quotes.db')
                    ti_data = db_bootstrap.insertion_into_indicators_database(ti_data, 'indicators.db')

                    data_analysis()
                    cleanup()
                    # check_for_market_close()
                    time.sleep(5)

    # START OF PORTFOLIO ANALYSIS
    portfolio_bootstrap = portfolioAnalysis(api=api)
    portfolio_bootstrap.main()
