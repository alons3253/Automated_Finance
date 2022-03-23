import sqlite3
import os
import datetime as dt
import logging
import alpaca_trade_api as trade_api
from alpaca_trade_api.stream import URL
import websocket
import glob

logger = logging.getLogger(__name__)


class databaseInitializer:
    def __init__(self, stock_tickers=None, cwd=None):
        self.stock_tickers = stock_tickers
        self.cwd = cwd
        if not os.path.isdir(fr'{self.cwd}\Databases\\'):
            os.mkdir(fr'{self.cwd}\Databases')
        self.path = f'{self.cwd}\\Databases\\'
        logger.debug("Initialization of Databases")

    def check_for_account_details(self):
        with sqlite3.connect(self.path + 'accounts.db') as db:
            db.execute(f'''create table if not exists account_info (
                    alpaca_key TEXT NOT NULL UNIQUE,
                    alpaca_security_key TEXT NOT NULL UNIQUE,
                    finnhub_key TEXT NOT NULL UNIQUE,
                    alpaca_brokerage_key TEXT NOT NULL UNIQUE,
                    alpaca_brokerage_security_key TEXT NOT NULL UNIQUE
                    )''')
            db.commit()

        with sqlite3.connect(self.path + 'accounts.db') as db:
            try:
                cur = db.execute("select rowid, * from account_info")
                accounts = cur.fetchall()[0]
                try:
                    alpaca_api = trade_api.REST(accounts[1], accounts[2],
                                                URL("https://paper-api.alpaca.markets"), api_version='v2')
                    account_check = alpaca_api.get_account()
                    if float(account_check.buying_power) < 1.0:
                        raise ValueError
                except Exception as e:
                    logging.debug(e)
                    raise IndexError
            except ValueError:
                logging.warning("Alpaca Account is unfunded, re-enter keys and ensure there is a nonzero equity "
                                "in the account")
                logging.warning("Input Alpaca Trading Key:")
                alpaca_key = str(input())
                logging.warning("Input Alpaca Trading Security Key:")
                alpaca_sec_key = str(input())
                while True:
                    try:
                        alpaca_api = trade_api.REST(alpaca_key, alpaca_sec_key, URL("https://paper-api.alpaca.markets"),
                                                    api_version='v2')
                        alpaca_api.get_account()
                        break
                    except Exception:
                        logging.warning("Alpaca account credentials were not found!")
                        logging.warning("Input Alpaca Trading Key:")
                        alpaca_key = str(input())
                        logging.warning("Input Alpaca Trading Security Key:")
                        alpaca_sec_key = str(input())

                cursor = db.cursor()
                cursor.execute("update account_info set alpaca_key = (?), alpaca_security_key = (?) where rowid = (?)",
                               (alpaca_key, alpaca_sec_key, accounts[0]))
                db.commit()

            except IndexError:
                logging.warning("Account Information was not found")
                logging.warning("Input Alpaca Trading Key:")
                alpaca_key = str(input())
                logging.warning("Input Alpaca Trading Security Key:")
                alpaca_sec_key = str(input())
                logging.warning("Input Finnhub Key:")
                finnhub_key = str(input())
                logging.warning("Input Alpaca Brokerage Key:")
                brokerage_key = str(input())
                logging.warning("Input Alpaca Brokerage Security Key:")
                brokerage_sec_key = str(input())

                while True:
                    try:
                        alpaca_api = trade_api.REST(alpaca_key, alpaca_sec_key, URL("https://paper-api.alpaca.markets"),
                                                    api_version='v2')
                        alpaca_api.get_account()
                        break
                    except Exception:
                        logging.warning("Alpaca account credentials were not found!")
                        logging.warning("Input Alpaca Trading Key:")
                        alpaca_key = str(input())
                        logging.warning("Input Alpaca Trading Security Key:")
                        alpaca_sec_key = str(input())

                while True:
                    try:
                        websocket.create_connection(f"wss://ws.finnhub.io?token={finnhub_key}")
                        break
                    except websocket.WebSocketBadStatusException:
                        logging.warning("Finnhub account credentials were not found!")
                        logging.warning("Input Finnhub Key:")
                        finnhub_key = str(input())

                cursor = db.cursor()
                cursor.execute("insert into account_info (alpaca_key, alpaca_security_key, finnhub_key, "
                               "alpaca_brokerage_key, alpaca_brokerage_security_key) values (?, ?, ?, ?, ?)",
                               (alpaca_key, alpaca_sec_key, finnhub_key, brokerage_key, brokerage_sec_key))
                db.commit()

            cur = db.execute("select * from account_info")
            acc_details = cur.fetchall()[0]
            alpaca_api = trade_api.REST(acc_details[0], acc_details[1], URL("https://paper-api.alpaca.markets"),
                                        api_version='v2')
            alpaca_api.get_account()
            logging.debug("A valid Alpaca trading account was found")
        return alpaca_api, (acc_details[0], acc_details[1]), acc_details[2], (acc_details[3], acc_details[4])

    def generation_of_trade_database(self, file):
        if os.path.isfile(self.path + file):
            with sqlite3.connect(self.path + file) as db:
                cursor = db.cursor()
                table_names = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                for element in table_names:
                    stock_split = element[0].split('_')
                    # want to drop all tables that do not concern stocks we are currently tracking
                    if stock_split[1] not in self.stock_tickers:
                        cursor.execute(f"drop table if exists trades_{stock_split[1]}")
                        db.commit()
                        logging.debug(f"Table trades_{stock_split[1]} dropped in trades.db")
                    else:
                        # want to prune existing databases if they are outdated
                        try:
                            cur = db.execute(f"select * from trades_{stock_split[1]}")
                            first_object_time = dt.datetime.strptime(cur.fetchone()[0], "%Y-%m-%d %H:%M:%S.%f")
                            if dt.date.today() != first_object_time.date():
                                cur.execute(f"drop table if exists trades_{stock_split[1]}")
                                db.commit()
                                logging.debug(f"Table trades_{stock_split[1]} dropped in trades.db")
                            return
                        except TypeError:
                            pass

        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                db.execute(f'''create table if not exists trades_{stock} (
                            time TIMESTAMP NOT NULL,
                            price DECIMAL NOT NULL,
                            volume MEDIUMINT NOT NULL,
                            direction TEXT NOT NULL
                            )''')
                db.commit()
                logging.debug(f"Table trades_{stock} created in trades.db")

    def cleanup_of_trade_database(self, file):
        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                cur = db.execute(f"select rowid, * from trades_{stock}")
                for row in cur.fetchall():
                    time = dt.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f')
                    difference = dt.datetime.now() - time
                    # delete trades from 8 hours ago
                    if difference.total_seconds() > 3600:
                        db.execute(f"delete from trades_{stock} where rowid = (?)", (row[0],))
                        db.commit()
                        logging.debug(f"trades_{stock} cleaned in trades.db due to {difference} having elapsed")
            # deletes empty rows
            db.execute("vacuum")
            db.commit()

    def insertion_into_database(self, data, path):
        with sqlite3.connect(self.path + path) as db:
            for stock in self.stock_tickers:
                for element in data[stock]:
                    params = (element['time'], element['price'], element['volume'], 'None')
                    db.execute(f"insert into trades_{stock} values (?, ?, ?, ?)", params)
                    db.commit()
                data[stock] = []

        logging.debug("Trade data saved to DB")
        return data

    def generation_of_quote_database(self, file):
        if os.path.isfile(self.path + file):
            with sqlite3.connect(self.path + file) as db:
                cursor = db.cursor()
                table_names = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                for element in table_names:
                    table_name = element[0].split('_')
                    # want to drop all tables that do not concern stocks we are currently tracking
                    # the last element of every table name list is the stock name, hence why we index -1
                    if table_name[-1] not in self.stock_tickers:
                        if table_name[0] == 'initial':
                            cursor.execute(f"drop table if exists initial_quote_{table_name[-1]}")
                            db.commit()
                            logging.debug(f"table initial_quote_{table_name[-1]} dropped in quotes.db")
                        else:
                            cursor.execute(f"drop table if exists quotes_{table_name[-1]}")
                            db.commit()
                            logging.debug(f"table quotes_{table_name[-1]} dropped in quotes.db")
                    else:
                        try:
                            # want to prune existing databases if they are outdated
                            cur = db.execute(f"select * from quotes_{table_name[-1]}")
                            first_object_time = dt.datetime.strptime(cur.fetchall()[0], "%Y-%m-%d %H:%M:%S")

                            if dt.date.today() != first_object_time.date():
                                cur.execute(f"drop table if exists quotes_{table_name[-1]}")
                                db.commit()
                                logging.debug(f"table quotes_{table_name[-1]} dropped in quotes.db")
                                # safe to assume that if the quote table exists then the initial quote table does too
                                cur.execute(f"drop table if exists initial_quote_{table_name[-1]}")
                                db.commit()
                                logging.debug(f"table initial_quotes_{table_name[-1]} dropped in quotes.db "
                                              f"(may not exist)")
                        except Exception:
                            pass
                db.execute('vacuum')
                db.commit()

        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                db.execute(f'''create table if not exists quotes_{stock} (
                        time TIMESTAMP NOT NULL,
                        price DECIMAL NOT NULL,
                        indicator TEXT NOT NULL,
                        volume TEXT NOT NULL
                        )''')
                db.commit()
                logging.debug(f"table quotes_{stock} added in quotes.db")

    def cleanup_of_quote_database(self, file):
        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                cur = db.execute(f"select rowid, * from quotes_{stock}")
                for row in cur.fetchall():
                    time = dt.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
                    difference = dt.datetime.now() - time
                    # delete quotes from 1 hour ago
                    if difference.total_seconds() > 3600:
                        db.execute(f"delete from quotes_{stock} where rowid = (?)", (row[0],))
                        db.commit()
                        logging.debug(f"table quotes_{stock} cleaned in quotes.db due to {difference} having elapsed")
            db.execute("vacuum")
            db.commit()

    def insertion_into_quote_database(self, data, file):
        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                for element in data[stock]:
                    params = (element['time'], element['current price'], element['indicator'], element['volume'])
                    db.execute(f"insert into quotes_{stock} values (?, ?, ?, ?)", params)
                    db.commit()
                data[stock] = []

        logging.debug("Quote data saved to DB")
        return data

    def generation_of_indicators_database(self, file):
        if os.path.isfile(self.path + file):
            with sqlite3.connect(self.path + file) as db:
                cursor = db.cursor()
                table_names = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

                for element in table_names:
                    stock_split = element[0].split('_')
                    # want to drop all tables that do not concern stocks we are currently tracking
                    if stock_split[-1] not in self.stock_tickers:
                        cursor.execute(f"drop table if exists indicators_{stock_split[-1]}")
                        db.commit()
                        logging.debug(f"table indicators_{stock_split[-1]} dropped in indicators.db")
                    else:
                        try:
                            # want to prune existing databases if they are outdated
                            cur = db.execute(f"select * from indicators_{stock_split[-1]}")
                            first_object_time = dt.datetime.strptime(cur.fetchone()[0], "%Y-%m-%d %H:%M:%S")
                            if dt.date.today() != first_object_time.date():
                                cur.execute(f"drop table if exists indicators_{stock_split[-1]}")
                                db.commit()
                                logging.debug(f"table indicators_{stock_split[-1]} dropped in indicators.db")
                            return
                        except TypeError:
                            pass

        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                db.execute(f'''create table if not exists indicators_{stock} (
                        time TIMESTAMP NOT NULL,
                        buys TEXT NOT NULL,
                        neutrals TEXT NOT NULL,
                        sells TEXT NOT NULL,
                        signal TEXT NOT NULL,
                        adx TEXT NOT NULL,
                        trending TEXT NOT NULL
                        )''')
                db.commit()
                logging.debug(f"table indicators_{stock} created in indicators.db")

    def cleanup_of_indicators_database(self, file):
        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                cur = db.execute(f"select rowid, * from indicators_{stock}")
                for row in cur.fetchall():
                    time = dt.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
                    difference = dt.datetime.now() - time
                    # delete indicators from 1 hour ago
                    if difference.total_seconds() > 3600:
                        db.execute(f"delete from indicators_{stock} where rowid = (?)", (row[0],))
                        db.commit()
                        logging.debug(f"table indicators_{stock} dropped in indicators.db due to "
                                      f"{difference} having elapsed")
            db.execute("vacuum")
            db.commit()

    def insertion_into_indicators_database(self, data, file):
        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                for element in data[stock]:
                    params = (element['time'], element['buy'], element['neutral'], element['sell'], element['signal'],
                              element['adx'], element['trending'])
                    db.execute(f"insert into indicators_{stock} values (?, ?, ?, ?, ?, ?, ?)", params)
                    db.commit()
                data[stock] = []

        logging.debug("Indicator data saved to DB")
        return data

    def initial_quote_insertion(self, initial_data, file):
        # this should not be the case, if there is no initial data then this function shouldn't be entered
        if initial_data is None:
            return
        # normally i would separate the generation of the table in a separate function but since this only gets called
        # once a day it doesn't really make a difference
        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                db.execute(f'''create table if not exists initial_quote_{stock} (
                                    time TIMESTAMP NOT NULL,
                                    beta DECIMAL NOT NULL,
                                    dividend DECIMAL NOT NULL,
                                    days_range TEXT NOT NULL,
                                    one_year_range TEXT NOT NULL,
                                    one_year_target DECIMAL NOT NULL,
                                    previous_close DECIMAL NOT NULL,
                                    DECIMAL TEXT NOT NULL,
                                    P_E_ratio DECIMAL NOT NULL,
                                    average_volume BIGINT NOT NULL
                                    )''')
                db.commit()
                logging.debug(f"table initial_quote_{stock} created in indicators.db")

                for element in initial_data[stock]:
                    params = (element['time'], element['beta'], element['dividend'], element["day's range"],
                              element['52 week range'], element['one year target'], element['previous close'],
                              element['open'], element['P/E ratio'], element['average volume'])
                    db.execute(f"insert into initial_quote_{stock} values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", params)
                    db.commit()

        logging.debug("Initial quote data saved to DB")

    def cleanup_options_database(self, file):
        with sqlite3.connect(f'{self.cwd}\\Databases\\options.db') as db:
            cursor = db.cursor()
            table_names = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

            for element in table_names:
                table_name = element[0].split(' ')
                if table_name[0] == 'timestamp':
                    cursor.execute("select * from timestamp")
                    timestamps = cursor.fetchall()
                    if len(timestamps) > 0:
                        for timestamp in timestamps:
                            if timestamp[0] not in self.stock_tickers:
                                cursor.execute("delete from timestamp where stock = (?)", (timestamp[0],))
                                db.commit()
                    continue

                if table_name[0] not in self.stock_tickers:
                    cursor.execute(f"drop table if exists '{element[0]}';")
                    db.commit()
                    logging.debug(f"Table: {element[0]} was dropped from options.db")

                expiration_date = dt.datetime.strptime(table_name[2], "%Y-%m-%d") + dt.timedelta(hours=15)

                if expiration_date < dt.datetime.today():
                    cursor.execute(f"drop table if exists '{element[0]}';")
                    db.commit()
                    logging.debug(f"Table: {element[0]} was dropped from options.db")

            db.execute('vacuum')
            db.commit()

    # this should check all dbs and should be ran after all dbs have been created
    def verify_db_integrity(self):
        db_directory = self.cwd + r'\Databases'
        dbs = glob.glob(db_directory + r'\*.db')
        troublesome_databases = []
        for db in dbs:
            try:
                cursor = sqlite3.connect(db)
                for r in cursor.execute("PRAGMA integrity_check;"):
                    logging.debug(f"DATABASE INTEGRITY CHECK FOR {db}: {r[0]}")
                    if r[0] != 'ok':
                        troublesome_databases.append(db)
                        os.remove(db)
                        logging.debug(f"FAULT IN {db} DETECTED, FILE REMOVED")
            except Exception as e:
                logging.debug(f"{e} error with verification of database integrity for {db}")
                continue

        return troublesome_databases
