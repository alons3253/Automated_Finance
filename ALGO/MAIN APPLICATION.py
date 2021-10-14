# updated to full functionality

from win10toast import ToastNotifier
import alpaca_trade_api as trade_api
from alpaca_trade_api.stream import URL
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
from ALGO.bond_yield_fetch_module import treasuryYields
from ALGO.options_module import Options
from ALGO.portfolio_analysis_module import portfolioAnalysis
from ALGO.file_handling_module import filePruning
from ALGO.stock_and_option_analysis_module import stockAnalysis
from ALGO.db_initializer import databaseInitializer


# minor date functions
def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def custom_strftime(time_format, t):
    return t.strftime(time_format).replace('{S}', str(t.day) + suffix(t.day))


def alpaca_bootstrapper():
    # Alpaca API Bootstrap
    alpaca_api = None
    try:
        with open("alpaca_keys.txt") as f:
            keys = f.readlines()
            key = keys[0].rstrip('\n')
            sec_key = keys[1].rstrip('\n')
        alpaca_api = trade_api.REST(key, sec_key, URL("https://paper-api.alpaca.markets"), api_version='v2')
        alpaca_api.get_account()
    except:
        while True:
            logging.warning("Alpaca account credentials were not found!")
            logging.warning("Please input the Alpaca API key:")
            key = str(input())
            logging.warning("Please input the Alpaca API security key:")
            sec_key = str(input())
            try:
                alpaca_api = trade_api.REST(key, sec_key, URL("https://paper-api.alpaca.markets"), api_version='v2')
                alpaca_api.get_account()
            except Exception:
                continue
            with open("alpaca_keys.txt", 'w') as f:
                f.write(key + '\n')
                f.write(sec_key + '\n')
                break

    logging.debug("A valid Alpaca trading account was found")
    return alpaca_api


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
        stock_quotes = executor.submit(stock_data_bootstrap.quote_data_processor).result()
        technical_indicators = executor.submit(finnhub_tech_bootstrap.tech_indicator).result()

    print(stock_quotes)
    print(technical_indicators)
    print('------------------------------------------------------------------')


# working
def initial_fetch():
    # initial fetches
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        initial_quote_fetch = executor.submit(stock_data_bootstrap.initial_quote_data_fetch).result()
        stock_quotes = executor.submit(stock_data_bootstrap.quote_data_processor).result()
        initial_bond_fetch = executor.submit(bond_bootstrap.treasury_bond_yields).result()
        ti_fetch = executor.submit(finnhub_tech_bootstrap.tech_indicator).result()
    print(initial_bond_fetch)
    print(initial_quote_fetch)
    print(stock_quotes)
    print(ti_fetch)

    try:
        options_bootstrapper = Options(stock_tickers=stock_tickers, initial_data=initial_quote_fetch,
                                       quote_data=stock_quotes, rate=initial_bond_fetch)
        options_pricing = options_bootstrapper.thread_marshaller()

        return options_pricing
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)


# WIP
def initial_analysis(options_pricing):
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
    # get rid of elements in lists that are dated 5 minutes and beyond to save memory
    # this is a temporary solution, i want to store all information instead of deleting it but not sure yet how i want
    # to do this in a fast and low computational cost method
    if (time.time() - program_start) > 300:
        print('Data Culling')
        for STOCK in stock_tickers:
            for p, it1 in enumerate(trade_data[STOCK].copy()):
                for key, value in it1.items():
                    if key == 'time':
                        if dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f") < dt.datetime.now() - dt.timedelta(
                                seconds=300):
                            trade_data[STOCK].remove(it1)
            for p, it2 in enumerate(stock_quote_data[STOCK].copy()):
                for key, value in it2.items():
                    if key == 'time':
                        if dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S") < dt.datetime.now() - dt.timedelta(
                                seconds=300):
                            stock_quote_data[STOCK].remove(it2)
            for p, it3 in enumerate(ti_data[STOCK].copy()):
                for key, value in it3.items():
                    if key == 'time':
                        if dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S") < dt.datetime.now() - dt.timedelta(
                                seconds=300):
                            ti_data[STOCK].remove(it3)


def data_analysis():
    analysis_module = stockAnalysis(stock_tickers, stock_quote_data, ti_data, trade_data, indicator_votes)

    analysis_module.indicator_analysis(stock_shortlist, stock_buylist)
    analysis_module.volume_analysis(volume_terms)


if __name__ == '__main__':
    # check for an internet connection
    conn = httplib.HTTPConnection(r"www.google.com", timeout=5)
    try:
        conn.request("HEAD", "/")
        conn.close()
    except Exception as e:
        conn.close()
        logging.critical("You need to have an internet connection!")
        sys.exit(0)

    # error handling
    logger = logging.getLogger(__name__)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('debug.log')
    c_handler.setLevel(logging.WARNING)
    f_handler.setLevel(logging.ERROR)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    file_handler_module = filePruning()
    file_handler_module.initialize_files()
    file_handler_module.prune_files()

    notification = ToastNotifier()
    api = alpaca_bootstrapper()
    account = api.get_account()
    clock = api.get_clock()

    account_balance = float(account.buying_power) / 4
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
                volume_terms = {}
                stock_buylist = {}
                stock_shortlist = {}
                for stock in stock_tickers:
                    stock_buylist[stock] = []
                    stock_shortlist[stock] = []
                    trade_data[stock] = []
                    stock_quote_data[stock] = []
                    ti_data[stock] = []
                    volume_terms[stock] = (0, 0, 0, 0)
                    indicator_votes[stock] = {'Bullish Votes': 0, 'Bearish Votes': 0, 'Neutral Votes': 0}

                stock_data_bootstrap = stockDataEngine(stock_tickers=stock_tickers, quote_data=stock_quote_data)
                websocket_bootstrap = WebsocketBootStrapper(stock_tickers=stock_tickers, trade_data=trade_data)
                finnhub_tech_bootstrap = technicalIndicators(stock_tickers=stock_tickers, ti_data=ti_data)
                bond_bootstrap = treasuryYields()
                db_bootstrap = databaseInitializer(stock_tickers=stock_tickers, path='trade_db.db')

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
                db_bootstrap.generation_of_trade_database()
                program_start = time.time()
                while True:
                    data_thread_marshaller()
                    trade_data = websocket_bootstrap.return_data()
                    db_bootstrap.insertion_into_database(trade_data)
                    data_analysis()

                    cleanup()
                    # check_for_market_close()
                    time.sleep(10)

    # START OF PORTFOLIO ANALYSIS
    portfolio_bootstrap = portfolioAnalysis(api=api)
    portfolio_bootstrap.main()
