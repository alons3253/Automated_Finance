import sqlite3
import os
import datetime as dt
import logging
import alpaca_trade_api as trade_api
from alpaca_trade_api.stream import URL
import websocket


class databaseInitializer:
    def __init__(self, stock_tickers=None):
        self.stock_tickers = stock_tickers
        self.cwd = os.getcwd()
        if not os.path.isdir(fr'{self.cwd}\Databases\\'):
            os.mkdir(fr'{self.cwd}\Databases\\')
        self.path = f'{self.cwd}\\Databases\\'

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
                db.execute("select * from account_info")
            except IndexError:
                logging.critical("Account Information was not found")
                logging.critical("Input Alpaca Trading Key:")
                alpaca_key = str(input())
                logging.critical("Input Alpaca Trading Security Key:")
                alpaca_sec_key = str(input())
                logging.critical("Input Finnhub Key:")
                finnhub_key = str(input())
                logging.critical("Input Alpaca Brokerage Key:")
                brokerage_key = str(input())
                logging.critical("Input Alpaca Brokerage Security Key:")
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
                        logging.warning("Alpaca account credentials were not found!")
                        logging.warning("Input Alpaca Trading Key:")
                        finnhub_key = str(input())

                cursor = db.cursor()
                cursor.execute("insert into account_info (alpaca_key, alpaca_security_key, finnhub_key, "
                               "alpaca_brokerage_key, alpaca_brokerage_security_key) values (?, ?, ?, ?, ?)",
                               (alpaca_key, alpaca_sec_key, finnhub_key, brokerage_key, brokerage_sec_key))
                db.commit()

            cur = db.execute("select * from account_info")
            account_details = cur.fetchall()[0]
            alpaca_api = trade_api.REST(account_details[0], account_details[1], URL("https://paper-api.alpaca.markets"),
                                        api_version='v2')
            alpaca_api.get_account()
            logging.debug("A valid Alpaca trading account was found")
        return alpaca_api, (account_details[0], account_details[1]), account_details[2], (account_details[3], account_details[4])

    def generation_of_trade_database(self, file):
        if os.path.isfile(self.path + file):
            with sqlite3.connect(self.path + file) as db:
                cursor = db.cursor()
                table_names = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                # print(table_names)
                for element in table_names:
                    stock_split = element[0].split('_')
                    # want to drop all tables that do not concern stocks we are currently tracking
                    if stock_split[1] not in self.stock_tickers:
                        cursor.execute(f"drop table if exists trades_{stock_split[1]}")
                        db.commit()
                    else:
                        # want to prune existing databases if they are outdated
                        try:
                            cur = db.execute(f"select * from trades_{stock_split[1]}")
                            first_object_time = dt.datetime.strptime(cur.fetchone()[0], "%Y-%m-%d %H:%M:%S.%f")
                            if dt.date.today() != first_object_time.date():
                                cur.execute(f"drop table if exists trades_{stock_split[1]}")
                                db.commit()
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

    def cleanup_of_trade_database(self, file):
        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                cur = db.execute(f"select rowid, * from trades_{stock}")
                for row in cur.fetchall():
                    # print(row)
                    time = dt.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f')
                    difference = dt.datetime.now() - time
                    # delete trades from 8 hours ago
                    if difference.total_seconds() > 3600:
                        db.execute(f"delete from trades_{stock} where rowid = (?)", (row[0],))
                        db.commit()
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

        print("Trade data saved to DB")
        return data

    def generation_of_quote_database(self, file):
        if os.path.isfile(self.path + file):
            with sqlite3.connect(self.path + file) as db:
                cursor = db.cursor()
                table_names = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                # print(table_names)
                for element in table_names:
                    stock_split = element[0].split('_')
                    # want to drop all tables that do not concern stocks we are currently tracking
                    if stock_split[1] not in self.stock_tickers:
                        cursor.execute(f"drop table if exists quotes_{stock_split[1]}")
                        db.commit()
                    else:
                        try:
                            # want to prune existing databases if they are outdated
                            cur = db.execute(f"select * from quotes_{stock_split[1]}")
                            first_object_time = dt.datetime.strptime(cur.fetchone()[0], "%Y-%m-%d %H:%M:%S")
                            if dt.date.today() != first_object_time.date():
                                cur.execute(f"drop table if exists quotes_{stock_split[1]}")
                                db.commit()
                        except TypeError:
                            pass

        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                db.execute(f'''create table if not exists quotes_{stock} (
                        time TIMESTAMP NOT NULL,
                        price DECIMAL NOT NULL,
                        indicator TEXT NOT NULL,
                        volume TEXT NOT NULL
                        )''')
                db.commit()

    def cleanup_of_quote_database(self, file):
        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                cur = db.execute(f"select rowid, * from quotes_{stock}")
                for row in cur.fetchall():
                    # print(row)
                    time = dt.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
                    difference = dt.datetime.now() - time
                    # delete trades from 8 hours ago
                    if difference.total_seconds() > 3600:
                        db.execute(f"delete from quotes_{stock} where rowid = (?)", (row[0],))
                        db.commit()
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

        print("Quote data saved to DB")
        return data

    def generation_of_indicators_database(self, file):
        if os.path.isfile(self.path + file):
            with sqlite3.connect(self.path + file) as db:
                cursor = db.cursor()
                table_names = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                # print(table_names)
                for element in table_names:
                    stock_split = element[0].split('_')
                    # want to drop all tables that do not concern stocks we are currently tracking
                    if stock_split[1] not in self.stock_tickers:
                        cursor.execute(f"drop table if exists indicators_{stock_split[1]}")
                        db.commit()
                    else:
                        try:
                            # want to prune existing databases if they are outdated
                            cur = db.execute(f"select * from indicators_{stock_split[1]}")
                            first_object_time = dt.datetime.strptime(cur.fetchone()[0], "%Y-%m-%d %H:%M:%S")
                            if dt.date.today() != first_object_time.date():
                                cur.execute(f"drop table if exists indicators_{stock_split[1]}")
                                db.commit()
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

    def cleanup_of_indicators_database(self, file):
        with sqlite3.connect(self.path + file) as db:
            for stock in self.stock_tickers:
                cur = db.execute(f"select rowid, * from indicators_{stock}")
                for row in cur.fetchall():
                    # print(row)
                    time = dt.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
                    difference = dt.datetime.now() - time
                    # delete trades from 1 hour ago
                    if difference.total_seconds() > 3600:
                        db.execute(f"delete from indicators_{stock} where rowid = (?)", (row[0],))
                        db.commit()
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

        print("Indicator data saved to DB")
        return data
