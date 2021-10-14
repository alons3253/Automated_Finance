import sqlite3
import os


class databaseInitializer:
    def __init__(self, stock_tickers, path):
        self.stock_tickers = stock_tickers
        cwd = os.getcwd()
        if not os.path.isdir(fr'{cwd}\Databases\\'):
            os.mkdir(fr'{cwd}\Databases\\')
        self.path = fr'{cwd}\Databases\\{path}'

    def generation_of_trade_database(self):
        if not os.path.isfile(self.path):
            db_conn = sqlite3.connect(self.path)
            db_conn.close()

        with sqlite3.connect(self.path) as db:
            for stock in self.stock_tickers:
                db.execute(f'''create table if not exists trades_{stock} (
                        time TEXT NOT NULL,
                        price DECIMAL NOT NULL,
                        volume MEDIUMINT NOT NULL
                        )''')
                db.commit()

    def insertion_into_database(self, data):
        with sqlite3.connect(self.path) as db:
            for stock in self.stock_tickers:
                for element in data[stock]:
                    params = (element['time'], element['price'], element['volume'])
                    db.execute(f"insert into trades_{stock} values (?, ?, ?)", params)
                    db.commit()

        print("Trade data saved to DB")
