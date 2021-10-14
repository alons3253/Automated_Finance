import datetime as dt
import pandas as pd
import ctypes
import yahooquery
import openpyxl
import concurrent.futures


class Options:
    def __init__(self, stock_tickers=None, initial_data=None, quote_data=None, rate=None):
        self.stock_tickers = stock_tickers
        self.initial_data = initial_data
        self.quote_data = quote_data
        self.rate = rate
        self.option_value = {}
        for ticker in stock_tickers:
            self.option_value[ticker] = []

    def thread_marshaller(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.stock_tickers)) as executor:
            for stock in self.stock_tickers:
                executor.submit(self.options, stock)
        return self.option_value

    def options(self, stock):
        handle = ctypes.cdll.\
            LoadLibrary(r"C:\Users\fabio\source\repos\CallPricingDll\CallPricingDll\x64\Release\CallPricingDll.dll")

        handle.CallPricing.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        handle.CallPricing.restype = ctypes.c_double
        handle.PutPricing.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        handle.PutPricing.restype = ctypes.c_double

        today = dt.datetime.now()
        url = f"../ALGO/Daily Stock Analysis/Options/{stock} Options Data {today.date()}.xlsx"

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
            time_diff = exp_time - today
            if time_diff.days < 0:
                continue

            days_till_expiration = round(time_diff.total_seconds() / 86400, 2)

            bond_yield = float(self.rate[0])
            if 30 <= days_till_expiration <= 60:
                bond_yield = float(self.rate[1])
            elif 60 < days_till_expiration <= 90:
                bond_yield = float(self.rate[2])
            elif days_till_expiration > 90:
                continue

            options_chain = options.loc[stock, date]
            call_table = options_chain.loc['calls']
            put_table = options_chain.loc['puts']

            call_table = call_table.assign(option_value=0.00).set_index('strike')
            put_table = put_table.assign(option_value=0.00).set_index('strike')

            self.option_value[stock].append({str(exp): {'overvalued_call_options': 0, 'undervalued_call_options': 0,
                                                        'overvalued_put_options': 0, 'undervalued_put_options': 0}})
            # calls_well_priced = 0
            # total_calls = 0
            # puts_well_priced = 0
            # total_puts = 0

            bond_yield -= dividend  # dividend should be factored in

            for index, row in call_table.iterrows():
                # this means that there have been no trades over the past day
                if row['change'] == 0:
                    continue
                if row['inTheMoney'] == 0 and days_till_expiration < 1:
                    continue

                sigma = float(row['impliedVolatility'])
                strike = float(index)

                option_price = handle.CallPricing(spot, strike, bond_yield, days_till_expiration, sigma)

                call_table.at[index, 'option_value'] = round(option_price, 3)
                spread = (row['bid'] + row['ask']) / 2
                call_table.at[strike, 'lastPrice'] = spread

                # error = ((option_price - spread) / spread)
                # if -0.05 < error < 0.05:
                #     calls_well_priced += 1
                # total_calls += 1

                if option_price > spread:
                    self.option_value[stock][i][str(exp)]['undervalued_call_options'] += 1
                if option_price < spread:
                    self.option_value[stock][i][str(exp)]['overvalued_call_options'] += 1

            for index, row in put_table.iterrows():
                # this means that there have been no trades over the past day
                if row['change'] == 0:
                    continue
                if row['inTheMoney'] == 0 and days_till_expiration < 1:
                    continue

                sigma = float(row['impliedVolatility'])
                strike = float(index)
                option_price = handle.PutPricing(spot, strike, bond_yield, days_till_expiration, sigma)

                put_table.at[index, 'option_value'] = round(option_price, 3)
                spread = (row['bid'] + row['ask']) / 2
                put_table.at[index, 'lastPrice'] = spread

                # error = ((option_price - spread) / spread)
                # if -0.05 < error < 0.05:
                #     puts_well_priced += 1
                # total_puts += 1

                if option_price > spread:
                    self.option_value[stock][i][str(exp)]['undervalued_put_options'] += 1
                if option_price < spread:
                    self.option_value[stock][i][str(exp)]['overvalued_put_options'] += 1

            # pct_well_priced = (calls_well_priced / total_calls) * 100
            # pct_well_priced_2 = (puts_well_priced / total_puts) * 100
            # print(f"{round(pct_well_priced, 2)}% of calls well priced (within 5% of the bid/ask spread) "
            #       f"for {stock} options expiring {exp}")
            # print(f"{round(pct_well_priced_2, 2)}% of puts well priced (within 5% of the bid/ask spread) "
            #       f"for {stock} options expiring {exp}")

            i += 1
            call_table.to_excel(writer, sheet_name=f'{stock} Calls {exp}')
            put_table.to_excel(writer, sheet_name=f'{stock} Puts {exp}')
        try:
            sheet = book['Sheet']
            book.remove(sheet)
        except KeyError:
            pass
        book.save(url)
