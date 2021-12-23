# updated to full functionality

import concurrent.futures
import datetime as dt
import time
import threading as th
import http.client as httplib
import sys
import logging
import logging.handlers
from pandas.tseries.offsets import BDay
import os
import glob
import sqlite3
import pandas as pd


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
from ALGO.verify_file_integrity import verifyFileIntegrity


# threaded method that allows an input timeout
class inputWithTimeout:
    _input = None

    def override(self):
        get_input_thread = th.Thread(target=self.get_input)
        get_input_thread.start()
        get_input_thread.join(timeout=5)

        if self._input is None or self._input == 'n':
            print("\nProgram executing automatically")
            manual_override_bool = False
            choice = 1
        else:
            manual_override_bool = True
            choice = None
        return manual_override_bool, choice

    def get_input(self):
        self._input = str(input("Manual override? (y/n)"))
        return


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
    # check and see if we dont already have the information
    # make a list with 4 of the initial fetches in there (I plan to add more)
    # append to the list if the system detects we have already gathered that information
    bdays = BDay()
    is_business_day = bdays.is_on_offset(dt.datetime.today())
    if is_business_day and market_closed_bool:
        last_business_day = dt.datetime.today()
    else:
        last_business_day = dt.datetime.today() - BDay(1)
    # reason for this confusingness is because the us treasury department puts out new rates at 3pm CST every day,
    # libor does not update todays rates until the next day
    tbond_business_day = dt.datetime.strftime(last_business_day, '%Y-%m-%d')
    libor_business_day = dt.datetime.strftime(dt.datetime.today() - BDay(1), '%Y-%m-%d')

    cwd = os.getcwd()
    fetched_information = []
    libor_yields = None

    libor_files = glob.glob(cwd + r"\Daily Stock Analysis\Bonds\LIBOR Yields (last updated *).xlsx")
    if len(libor_files) > 0:
        for file in libor_files:
            try:
                libor_df = pd.read_excel(cwd + fr"\Daily Stock Analysis\Bonds\LIBOR Yields "
                                               fr"(last updated {libor_business_day}).xlsx")
                libor_list = libor_df[libor_business_day].tolist()
                libor_yields = []
                for element in libor_list:
                    if element == '-':
                        continue
                    libor_yields.append(element[:-2])
                fetched_information.append('LIBOR')
            except FileNotFoundError:
                os.remove(file)

    bond_files = glob.glob(cwd + r"\Daily Stock Analysis\Bonds\US T-Bond Yields (last updated *).xlsx")
    if len(bond_files) > 0:
        for file in bond_files:
            try:
                bond_df = pd.read_excel(cwd + f"\\Daily Stock Analysis\\Bonds\\US T-Bond Yields "
                                              f"(last updated {tbond_business_day}).xlsx")

                bond_df = bond_df.set_index(['Unnamed: 0'])
                bond_list = bond_df.loc[tbond_business_day, ['1 Mo', '2 Mo', '3 Mo', '6 Mo', '1 Yr', '2 Yr']].tolist()
                fetched_information.append('T-Bond')
            except FileNotFoundError:
                os.remove(file)

    with sqlite3.connect(cwd + r'\Databases\quotes.db') as db:
        cursor = db.cursor()
        initial_quote_fetch = {}
        for stock in stock_tickers:
            # check if initial quotes exist
            cursor.execute(f"select name from sqlite_master where type = 'table' and name = 'initial_quote_{stock}'")
            table_name = cursor.fetchall()
            if len(table_name) == 1:
                cursor.execute(f"select * from initial_quote_{stock}")
                initial_data = cursor.fetchall()[0]
                if len(initial_data) > 0:
                    quote = {'time': initial_data[0], 'beta': initial_data[1], 'dividend': initial_data[2],
                             "day's range": initial_data[3], '52 week range': initial_data[4],
                             'one year target': initial_data[5], 'previous close': initial_data[6],
                             'open': initial_data[7], 'P/E ratio': initial_data[8], 'average volume': initial_data[9]}
                    initial_quote_fetch[stock] = [quote]

        if len(initial_quote_fetch) == len(stock_tickers):
            fetched_information.append(f'Initial Quote')

    logging.debug(f"information already fetched: {fetched_information}")
    # initial fetches
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        if 'Initial Quote' not in fetched_information:
            initial_quote_fetch = executor.submit(stock_data_bootstrap.initial_quote_data_fetch).result()
        else:
            logging.debug(f"Initial Quote information for {dt.date.today()} already exists")

        stock_quotes = executor.submit(stock_data_bootstrap.quote_data_processor).result()

        if 'T-Bond' not in fetched_information:
            t_bond_yields = executor.submit(bond_bootstrap.treasury_bond_yields).result()
        else:
            logging.debug(f"T-bond information for {tbond_business_day} already exists")

        if 'LIBOR' not in fetched_information:
            libor_yields = executor.submit(bond_bootstrap.LIBOR_yields).result()
        else:
            logging.debug(f"LIBOR information for the previous business day {libor_business_day} already exists")

        ti_fetch = executor.submit(finnhub_tech_bootstrap.tech_indicator).result()

    try:
        if 'Initial Quote' not in fetched_information:
            db_bootstrap.initial_quote_insertion(file='quotes.db', initial_data=initial_quote_fetch)

        logging.debug("Options gathering started")
        options_bootstrapper = Options(stock_tickers=stock_tickers, initial_data=initial_quote_fetch,
                                       quote_data=stock_quotes, rate=libor_yields, bbond=bond_bootstrap)
        # function changed to a yield from in order to wait and make sure everything is done and priced
        options_bootstrapper.thread_marshaller()
        logging.debug("Options gathering completed")

        return options_bootstrapper, initial_quote_fetch, stock_quotes, libor_yields, ti_fetch
    except Exception as error:
        logging.error(f"Exception occurred {error}", exc_info=True)


# WIP
def initial_analysis():
    print("LIBOR Yields:", libor_yields)
    print("Initial Quote Fetch:", initial_quote_fetch)
    print("Stock Quote Fetch:", stock_quote_data)
    print("Technical Indicators:", ti_data)

    logging.debug("initial analysis function is entered")

    """
    for the initial analysis function, we want to take a look at the options we just gathered and take a note
    of a couple of things, namely how large is the open interest?

    also take a look at the technical indicators that we have gathered, and the price and its change from the previous
    trading day, if there was a big move premarket compared to yesterdays close then we want to buy that stock
    
    look at the trading range of the stock price, both for yesterdays and the yearly range, if its close to the top
    of the range and the indicators are bullish, this is a good sign of a breakout
    
    All of these factors should go into projecting a position size using the size of our account and the technical
    indicators, we should implement a internet search function on the stock and see if we retrieve any important or up
    to date news that will indicate volatility, which would be pretty cool
    """

    # first look at the options open interest and look at the max pain (only considering the options we have priced)
    print('---------------------------------------------')
    print('Options Analysis')
    print(stock_tickers)
    max_pain = options_bootstrapper.options_fetch(initial_quote_fetch)
    print(max_pain)

    # we want to project a position size over the course of the day


def cleanup():
    # needs to remove the far dated elements in the sql databases
    db_bootstrap.cleanup_of_trade_database('trades.db')
    db_bootstrap.cleanup_of_quote_database('quotes.db')
    db_bootstrap.cleanup_of_indicators_database('indicators.db')


def data_analysis():
    analysis_module = stockAnalysis(stock_tickers, stock_quote_data, ti_data, indicator_votes)
    b_l, s_l = analysis_module.indicator_analysis(stock_shortlist, stock_buylist, 'indicators.db')
    volume_dict = analysis_module.trade_analysis(tick_test, 'trades.db')
    option_analysis = analysis_module.option_analysis()
    print('change in options volume:')
    print(option_analysis)

    # WIP
    for stock in stock_tickers:
        if volume_dict[stock]['30_seconds']['shares_bought'] == volume_dict[stock]['1_minute']['shares_bought'] or \
                volume_dict[stock]['1_minute']['shares_bought'] == volume_dict[stock]['2_minutes']['shares_bought']:
            continue
        else:
            s_b, b, w_b, s_s, s, w_s = purchasingAnalysis([stock], volume_dict, b_l, s_l).analysis_operations(stock_quote_data)
            trade_bootstrap.trade_execution(account_balance, s_b, b, w_b, s_s, s, w_s)
        stock_quote_data[stock] = []


if __name__ == '__main__':
    # Change root logger level from WARNING (default) to NOTSET in order for all messages to be delegated.
    logging.getLogger().setLevel(logging.NOTSET)

    # Add stdout handler, with level INFO
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formater = logging.Formatter('%(name)-13s: %(levelname)-8s %(message)s')
    console.setFormatter(formater)
    logging.getLogger().addHandler(console)

    # Add file rotating handler, with level DEBUG
    if os.path.exists('temp.log'):
        os.remove('temp.log')
    rotatingHandler = logging.handlers.RotatingFileHandler(filename='temp.log', maxBytes=(50*1024*1024),
                                                           backupCount=5, mode='w')
    rotatingHandler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    rotatingHandler.setFormatter(formatter)
    logging.getLogger().addHandler(rotatingHandler)

    log = logging.getLogger("app." + __name__)

    # log.debug('Debug message, should only appear in the file.')
    # log.info('Info message, should appear in file and stdout.')
    # log.warning('Warning message, should appear in file and stdout.')
    # log.error('Error message, should appear in file and stdout.')

    # check google for an internet connection
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
    file_handler_module.excel_handler()

    verifyFileIntegrity().check_files()

    api, alpaca_data_keys, finnhub_token, brokerage_keys = databaseInitializer().check_for_account_details()

    account = api.get_account()
    clock = api.get_clock()

    account_balance = float(account.buying_power) / 2
    print('Trading account status:', account.status)
    print('Current account balance (without margin) is: $' + str(round(account_balance, 2)))

    market_close, market_closed_bool = time_initialization()
    manual_override_bool, choice = inputWithTimeout().override()

    # if market_closed_bool is False and manual_override_bool is True:
    if manual_override_bool is True:
        print("Select from one of the following choices:")
        print("Press 1 for Automated Stock Fetch and Trading")
        print("Press 2 for Manual Stock Fetch and Automated Trading")
        print("Press 3 for Portfolio Analysis")

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
        # initialization of variables
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

            errormessage_market_close = 'The market is currently closed'
            errormessage_5min_to_close = 'The market is closing in 5 minutes, be warned that any new positions ' \
                                         'may be held until the next trading day'
            errormessage_trade_fetch = 'No trades gathered'
            cutoff_bool = False
            # end initialization of variables

            # boot-strappers, these serve the purpose of initializing classes so the multi-threading works fine
            stock_data_bootstrap = stockDataEngine(stock_tickers, stock_quote_data)
            websocket_bootstrap = WebsocketBootStrapper(stock_tickers, trade_data, finnhub_token)
            finnhub_tech_bootstrap = technicalIndicators(stock_tickers, ti_data)
            bond_bootstrap = bondYields()
            db_bootstrap = databaseInitializer(stock_tickers)
            db_bootstrap.cleanup_options_database('options.db')
            trade_bootstrap = tradeExecution(api, stock_tickers)
            # end boot-strappers
            #######################################################################################################
            print("Starting Initial Fetch, this may take several minutes")
            # initial fetch and db creation
            options_bootstrapper, initial_quote_fetch, stock_quote_data, libor_yields, ti_data = initial_fetch()
            websocket_boot()
            # important function
            initial_analysis()

            while True:
                db_bootstrap.generation_of_trade_database('trades.db')
                db_bootstrap.generation_of_quote_database('quotes.db')
                db_bootstrap.generation_of_indicators_database('indicators.db')

                troublesome_dbs = db_bootstrap.verify_db_integrity()
                if len(troublesome_dbs) > 0:
                    if ('trades.db' not in troublesome_dbs) and ('quotes.db' not in troublesome_dbs) and \
                            ('indicators.db' not in troublesome_dbs):
                        break
                else:
                    break

            # end initialization and start main loop
            while True:
                """
                works well as of 12/17/2021
                everything works okay, there are still issues with the options chain storage and pulling from dbs
                I have not been able to test the trade executor module and think that is a priority (in order to make
                sure we can trade and perform all the functions we were able to just a few months ago)
                all of the technical analysis has been offloaded from finnhub and is a bit more rigorous since all the
                data is stored in-house and calculated client side instead of relying on finnhub to do it
                
                I fixed the logging which means we can see what requests get made before the program terminates
                
                / old notes
                want to optimize the data i am pulling, do not want to take the entire chain of intraday data
                when i am doing minute by minute updates, also that should probably go to a db
                
                ideally i will want to get rid of the 10 second time.sleep at the end of this loop
                
                the options pricing analysis will be added in the end once i figure out what to do with it
                /
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

                # commented out for now as we focus on the initial function
                # data_analysis()
                cleanup()
                # check_for_market_close()
                time.sleep(5)

    # START OF PORTFOLIO ANALYSIS
    portfolio_bootstrap = portfolioAnalysis(api=api)
    portfolio_bootstrap.main()
    # end of program
