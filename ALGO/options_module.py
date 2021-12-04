import datetime as dt
import pandas as pd
import ctypes
import yahooquery
import openpyxl
import concurrent.futures
import os
import sqlite3
import time

from ALGO.excel_formatting_module import ExcelFormatting


class Options:
    def __init__(self, stock_tickers=None, initial_data=None, quote_data=None, rate=None, bbond=None):
        self.stock_tickers = stock_tickers
        self.initial_data = initial_data
        self.quote_data = quote_data
        self.rate = rate
        self.option_value = {}
        self.today = dt.datetime.now()
        self.cwd = os.getcwd()
        self.bond_bootstrapper = bbond
        for ticker in stock_tickers:
            self.option_value[ticker] = []

    def options_fetch(self, initial_quotes):
        max_pain = {}
        for stock in self.stock_tickers:
            max_pain[stock] = 0
            query = yahooquery.Ticker([stock], asynchronous=True)
            options = query.option_chain

            expiration_dates = list(options.index.unique(level=1))
            connection = sqlite3.connect(f'{self.cwd}\\Databases\\options.db')
            for date in expiration_dates:
                expiration = date.to_pydatetime().date()
                exp_time = dt.datetime.combine(expiration, dt.time(15, 0))
                time_diff = exp_time - self.today
                if time_diff.days < 0:
                    continue
                days_till_expiration = round(time_diff.total_seconds() / 86400, 2)
                if days_till_expiration > 7:
                    break

                """
                Underlying theory behind why this is necessary
                Options open interest (and subsequently the total dollar value) is important because options are now the
                predominant driving force behind stock price movements since March of 2020. What I need to do here is
                calculate the value of options that are out of the money (which subsequently will change the stock price
                in that direction) and options that are in the money. We want to assume that the market makers who are 
                selling these options will want to "pin" the stock price to the point where they will profit the most.
                How do I determine this? A large options volume can be a hedge fund trader that is trying to move a 
                stock in the short-term, in which case volume is very important to track throughout the day. However, 
                I will assume that the vast financial resources in institutions is going to eventually push the stock 
                price to the price where the most options contracts will expire.
                """
                call_df = pd.read_sql(f'select * from "{stock} Calls {expiration}"', con=connection).set_index('strike')
                for index, row in call_df.copy().iterrows():
                    call_df.at[index, 'max_pain'] = row['openInterest'] * row['lastPrice']

                put_df = pd.read_sql(f'select * from "{stock} Puts {expiration}"', con=connection).set_index('strike')
                for index, row in put_df.copy().iterrows():
                    put_df.at[index, 'max_pain'] = row['openInterest'] * row['lastPrice']

                reduced_df = call_df['max_pain'].add(put_df['max_pain'], fill_value=0)

                numerator = 0
                denominator = 0
                for index, row in reduced_df.iteritems():
                    numerator += row * index
                    denominator += row

                max_pain_strike = numerator / denominator
                max_pain[stock] = round(max_pain_strike, 2)

        return max_pain

    def thread_marshaller(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.stock_tickers)) as executor:
            for stock in self.stock_tickers:
                #path = f'{self.cwd}\\Daily Stock Analysis\\Options\\{stock} Options Data {self.today.date()}.xlsx'
                #db_path = f'{self.cwd}\\Databases\\options.db'
                # insert a check if we already the initial fetch and pricing
                executor.submit(self.initial_options, stock)

        return self.option_value

    def initial_options(self, stock):
        handle = ctypes.cdll. \
            LoadLibrary(r"C:\Users\fabio\source\repos\CallPricingDll\CallPricingDll\x64\Release\CallPricingDll.dll")

        handle.CallPricing.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        handle.CallPricing.restype = ctypes.c_double
        handle.PutPricing.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        handle.PutPricing.restype = ctypes.c_double

        url = f"{self.cwd}\\Daily Stock Analysis\\Options\\{stock} Options Data {self.today.date()}.xlsx"

        dividend = self.initial_data[stock][-1]['dividend']
        spot = self.quote_data[stock][-1]['current price']

        wb = openpyxl.Workbook()
        wb.save(url)
        book = openpyxl.load_workbook(url)
        writer = pd.ExcelWriter(url, engine='openpyxl')
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)

        i = 0
        query = yahooquery.Ticker([stock], asynchronous=True)
        options = query.option_chain
        expiration_dates = list(options.index.unique(level=1))

        for date in expiration_dates:
            exp = date.to_pydatetime().date()
            # options expire at 3 o'clock CST
            exp_time = dt.datetime.combine(exp, dt.time(15, 0))
            time_diff = exp_time - self.today
            if time_diff.days < 0:
                continue

            days_till_expiration = round(time_diff.total_seconds() / 86400, 2)
            if days_till_expiration > 90:
                continue

            sofr = self.bond_bootstrapper.sofr()
            ois_rate = self.bond_bootstrapper.overnightindexedswaps(days_till_expiration, sofr)

            options_chain = options.loc[stock, date]
            call_table = options_chain.loc['calls']
            put_table = options_chain.loc['puts']

            call_table = call_table.assign(option_value=0.00).set_index('strike')
            put_table = put_table.assign(option_value=0.00).set_index('strike')
            self.option_value[stock].append({str(exp): {'overvalued_call_options': 0, 'undervalued_call_options': 0,
                                                        'overvalued_put_options': 0, 'undervalued_put_options': 0}})

            calls_well_priced = 0
            total_calls = 0
            puts_well_priced = 0
            total_puts = 0
            ois_rate -= dividend  # dividend should be factored in

            for index, row in call_table.iterrows():
                # this means that there have been no trades over the past day
                if row['change'] == 0:
                    continue

                sigma = round(float(row['impliedVolatility']), 6)
                strike = float(index)

                option_price = handle.CallPricing(spot, strike, ois_rate, days_till_expiration, sigma)

                call_table.at[index, 'option_value'] = round(option_price, 3)
                spread = (row['bid'] + row['ask']) / 2
                call_table.at[index, 'lastPrice'] = spread

                error = ((option_price - spread) / spread)
                if -0.05 < error < 0.05:
                    calls_well_priced += 1
                total_calls += 1

                if option_price > spread:
                    self.option_value[stock][i][str(exp)]['undervalued_call_options'] += 1
                if option_price < spread:
                    self.option_value[stock][i][str(exp)]['overvalued_call_options'] += 1

            for index, row in put_table.iterrows():
                # this means that there have been no trades over the past day
                if row['change'] == 0:
                    continue

                sigma = round(float(row['impliedVolatility']), 6)
                strike = float(index)

                option_price = handle.PutPricing(spot, strike, ois_rate, days_till_expiration, sigma)

                put_table.at[index, 'option_value'] = round(option_price, 3)
                spread = (row['bid'] + row['ask']) / 2
                put_table.at[index, 'lastPrice'] = spread

                error = ((option_price - spread) / spread)
                if -0.05 < error < 0.05:
                    puts_well_priced += 1
                total_puts += 1

                if option_price > spread:
                    self.option_value[stock][i][str(exp)]['undervalued_put_options'] += 1
                if option_price < spread:
                    self.option_value[stock][i][str(exp)]['overvalued_put_options'] += 1

            i += 1
            connection = sqlite3.connect(f'{self.cwd}\\Databases\\options.db')

            call_table.to_sql(name=f'{stock} Calls {exp}', con=connection, if_exists='replace')
            put_table.to_sql(name=f'{stock} Puts {exp}', con=connection, if_exists='replace')

            cursor = connection.cursor()
            timestamp = dt.datetime.now()
            cursor.execute("INSERT INTO timestamp (stock, time, expiration) VALUES(?, ?, ?)",
                           (stock, timestamp, exp_time))
            connection.commit()
            connection.close()

            try:
                pct_well_priced = (calls_well_priced / total_calls) * 100
                pct_well_priced_2 = (puts_well_priced / total_puts) * 100
                print(f"{round(pct_well_priced, 2)}% of calls well priced (within 5% of the bid/ask spread) "
                      f"for {stock} options expiring {exp}")
                print(f"{round(pct_well_priced_2, 2)}% of puts well priced (within 5% of the bid/ask spread) "
                      f"for {stock} options expiring {exp}")
            except Exception as e:
                print(e)

            call_table.to_excel(writer, sheet_name=f'{stock} Calls {exp}')
            put_table.to_excel(writer, sheet_name=f'{stock} Puts {exp}')

        try:
            sheet = book['Sheet']
            book.remove(sheet)
        except KeyError:
            pass
        writer.save()
        writer.close()
        book.save(url)
        book.close()

        #ExcelFormatting(file_path=url).formatting()
