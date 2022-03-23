import datetime as dt
import sqlite3
import yahooquery
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class stockAnalysis:
    def __init__(self, stock_tickers, quote_data, ti_data, indicator_votes, cwd):
        self.cwd = cwd
        self.path = fr'{self.cwd}\Databases\\'
        self.stock_tickers = stock_tickers
        self.quote_data = quote_data
        self.ti_data = ti_data
        self.indicator_votes = indicator_votes

    # fixed on 3/17/2022
    def option_analysis(self):
        logging.debug("Entering options analysis function (untested as of 2/14/2022)")
        change_in_options_volume = {}

        with sqlite3.connect(f'{self.cwd}\\Databases\\options.db') as db:
            for stock in self.stock_tickers:
                query = yahooquery.Ticker([stock], asynchronous=True)
                options = query.option_chain
                expiration_dates = []

                old_options_tables = db.execute(f"SELECT name from sqlite_master where name like '{stock}%'").fetchall()
                cursor = db.cursor()
                cursor.execute(f'select * from timestamp where stock = (?)', (stock,))
                timestamps = cursor.fetchall()

                # we need to analyze the change in options, do it in about 5 minute increments because of resources
                # calculations that shouldnt be ran every 30 seconds for example
                # once we have done this, replace the options chains and timestamps in the existing options.db
                for element in old_options_tables:
                    date = element[0].split(' ')[-1]
                    if date not in expiration_dates:
                        expiration_dates.append(date)

                time = dt.datetime.strptime(timestamps[-1][1], "%Y-%m-%d %H:%M:%S.%f")
                if time + dt.timedelta(minutes=5) < dt.datetime.now():
                    for date in expiration_dates:
                        change_in_options_volume[stock] = []
                        dictionary_of_options_volume = {'calls': [], 'puts': []}

                        options_chain = options.loc[stock, date]
                        # new and updated options chains
                        new_call_table = options_chain.loc['calls']
                        new_put_table = options_chain.loc['puts']

                        # old options chain in the database
                        old_call_table = pd.read_sql(f'select * from "{stock} Calls {date}"', con=db).set_index('strike')
                        old_put_table = pd.read_sql(f'select * from "{stock} Puts {date}"',  con=db).set_index('strike')

                        for index, row in new_call_table.iterrows():
                            strike = row['strike']
                            change_in_volume = row['volume'] - old_call_table.loc[strike]['volume']
                            change_in_price = row['lastPrice'] - old_call_table.loc[strike]['lastPrice']
                            if change_in_volume != 0:
                                # if volume increase and price goes down, we can assume investors are bailing from
                                # this strike, if volume increase and price goes up, we can assume movement into
                                # the specific strike
                                dictionary_of_options_volume['calls'].append(
                                    [strike, change_in_volume, change_in_price])

                        for index, row in new_put_table.iterrows():
                            strike = row['strike']
                            change_in_volume = row['volume'] - old_put_table.loc[strike]['volume']
                            change_in_price = round(row['lastPrice'] - old_put_table.loc[strike]['lastPrice'], 6)
                            if change_in_volume != 0:
                                dictionary_of_options_volume['puts'].append(
                                    [strike, change_in_volume, change_in_price])

                        print(dictionary_of_options_volume)
                        change_in_options_volume[stock].append(dictionary_of_options_volume)

        # begin analysis of the change in options volume
        logging.debug("Exiting experimental options update function")
        return change_in_options_volume

    # okay for now
    def trade_analysis(self, tick_test, path):
        logging.debug("entering experimental trade analysis function (as of 2/14/2022)")

        volume_terms_dict = {}
        with sqlite3.connect(self.path + path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as db:
            for stock in self.stock_tickers:
                volume_terms_dict[stock] = {"30_seconds": {'shares_bought': 0, 'shares_sold': 0},
                                            "1_minute": {'shares_bought': 0, 'shares_sold': 0},
                                            "2_minutes": {'shares_bought': 0, 'shares_sold': 0},
                                            "4_minutes": {'shares_bought': 0, 'shares_sold': 0},
                                            "8_minutes": {'shares_bought': 0, 'shares_sold': 0},
                                            "15_minutes": {'shares_bought': 0, 'shares_sold': 0}}

                uptick = tick_test[stock][0]
                downtick = tick_test[stock][1]
                zerotick = tick_test[stock][2]
                try:
                    # select all unclassified trades
                    cur = db.execute(f"select rowid, * from trades_{stock} where direction = (?)", ('None',))
                    trade_elements = cur.fetchall()

                    cursor = db.cursor()
                    self.quote_data[stock] = []
                    first_trade = trade_elements[0]
                    second_trade = trade_elements[1]
                    for index, row in enumerate(trade_elements.copy()):
                        # https://hashingit.com/elements/research-resources/1991-06-inferring-trade-direction.pdf
                        # The tick test is a technique which infers the direction of a trade by
                        # comparing its price to the price of the preceding trade(s). The test classifies
                        # each trade into four categories: an uptick, a downtick, a zero-uptick, and a
                        # zero-downtick. A trade is an uptick (downtick) if the price is higher (lower)
                        # than the price of the previous trade. When the price is the same as the
                        # previous trade (a zero tick), if the last price change was an uptick, then the
                        # trade is a zero-uptick. Similarly, if the last price change was a downtick, then
                        # the trade is a zero-downtick. A trade is classified as a buy if it occurs on an
                        # uptick or a zero-uptick; otherwise it is classified as a sell.
                        try:
                            if index == 0:
                                previous_trade = first_trade
                                current_trade = second_trade

                                if first_trade[-1] == 'None':
                                    if second_trade[2] > first_trade[2]:
                                        downtick = True
                                        cursor.execute(f"update trades_{stock} set direction = 'Sell' where rowid = (?)", (first_trade[0],))
                                        db.commit()
                                    elif second_trade[2] < first_trade[2]:
                                        uptick = True
                                        cursor.execute(f"update trades_{stock} set direction = 'Buy' where rowid = (?)", (first_trade[0],))
                                        db.commit()
                                    elif second_trade[2] == first_trade[2]:
                                        downtick = True
                                        zerotick = True
                                        cursor.execute(f"update trades_{stock} set direction = 'Sell' where rowid = (?)", (first_trade[0],))
                                        db.commit()

                            elif index < len(trade_elements):
                                previous_trade = trade_elements[index]
                                current_trade = trade_elements[index+1]

                            price_preceding = previous_trade[2]
                            price_current = current_trade[2]

                            if float(price_current) > float(price_preceding):
                                uptick = True
                                downtick = False
                                zerotick = False
                            if float(price_current) < float(price_preceding):
                                downtick = True
                                uptick = False
                                zerotick = False
                            if float(price_current) == float(price_preceding):
                                zerotick = True

                            if (zerotick and uptick) or uptick:
                                cursor.execute(f"update trades_{stock} set direction = 'Buy' where rowid = (?)",
                                               (current_trade[0],))
                                db.commit()
                            if (zerotick and downtick) or downtick:
                                cursor.execute(f"update trades_{stock} set direction = 'Sell' where rowid = (?)",
                                               (current_trade[0],))
                                db.commit()
                        except IndexError:
                            pass
                except IndexError:
                    pass

                tick_test[stock] = [uptick, downtick, zerotick]
                cur = db.execute(f"select * from trades_{stock}")
                trade_data = cur.fetchall()
                for row in trade_data:
                    # since we have already classified all of the trades as buys or sells, here we will analyze them
                    tradetime = row[0]
                    if tradetime > dt.datetime.now() - dt.timedelta(seconds=30):
                        if row[-1] == 'Buy':
                            volume_terms_dict[stock]['30_seconds']['shares_bought'] += int(row[2])
                        elif row[-1] == 'Sell':
                            volume_terms_dict[stock]['30_seconds']['shares_sold'] += int(row[2])
                    if tradetime > dt.datetime.now() - dt.timedelta(seconds=60):
                        if row[-1] == 'Buy':
                            volume_terms_dict[stock]['1_minute']['shares_bought'] += int(row[2])
                        elif row[-1] == 'Sell':
                            volume_terms_dict[stock]['1_minute']['shares_sold'] += int(row[2])
                    if tradetime > dt.datetime.now() - dt.timedelta(seconds=120):
                        if row[-1] == 'Buy':
                            volume_terms_dict[stock]['2_minutes']['shares_bought'] += int(row[2])
                        elif row[-1] == 'Sell':
                            volume_terms_dict[stock]['2_minutes']['shares_sold'] += int(row[2])
                    if tradetime > dt.datetime.now() - dt.timedelta(seconds=240):
                        if row[-1] == 'Buy':
                            volume_terms_dict[stock]['4_minutes']['shares_bought'] += int(row[2])
                        elif row[-1] == 'Sell':
                            volume_terms_dict[stock]['4_minutes']['shares_sold'] += int(row[2])
                    if tradetime > dt.datetime.now() - dt.timedelta(seconds=480):
                        if row[-1] == 'Buy':
                            volume_terms_dict[stock]['8_minutes']['shares_bought'] += int(row[2])
                        elif row[-1] == 'Sell':
                            volume_terms_dict[stock]['8_minutes']['shares_sold'] += int(row[2])
                    if tradetime > dt.datetime.now() - dt.timedelta(seconds=900):
                        if row[-1] == 'Buy':
                            volume_terms_dict[stock]['15_minutes']['shares_bought'] += int(row[2])
                        elif row[-1] == 'Sell':
                            volume_terms_dict[stock]['15_minutes']['shares_sold'] += int(row[2])
            ##############################################################################
        print('volume by stock ordered 30sec, 1min, 2min, 4min, 8min and 15min:', volume_terms_dict)
        return volume_terms_dict

    # ok for now
    def indicator_analysis(self, stock_shortlist, stock_buylist, path):
        with sqlite3.connect(self.path + path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as db:
            for stock in self.stock_tickers:
                bullish_votes = 0
                bearish_votes = 0
                neutral_votes = 0

                five_minutes_ago = dt.datetime.now() - dt.timedelta(minutes=5)
                cur = db.execute(f"select * from indicators_{stock} where time > (?)", (five_minutes_ago,))
                ti_data = cur.fetchall()
                for row in ti_data:
                    timestamp = row[0].strftime('%H:%M:%S')
                    if len(self.ti_data) > 0:
                        bullish_votes += int(row[1])
                        bearish_votes += int(row[2])
                        neutral_votes += int(row[3])

                self.indicator_votes[stock]['Bullish Votes'] = int(bullish_votes) / len(ti_data)
                self.indicator_votes[stock]['Bearish Votes'] = int(bearish_votes) / len(ti_data)
                self.indicator_votes[stock]['Neutral Votes'] = int(neutral_votes) / len(ti_data)

                if self.indicator_votes[stock]['Bullish Votes'] > self.indicator_votes[stock]['Bearish Votes'] and \
                        self.indicator_votes[stock]['Bullish Votes'] > self.indicator_votes[stock]['Neutral Votes']:
                    stock_buylist[stock].append({timestamp: 'Very Bullish'})
                elif self.indicator_votes[stock]['Bullish Votes'] > self.indicator_votes[stock]['Bearish Votes']:
                    stock_buylist[stock].append({timestamp: 'Bullish'})

                if self.indicator_votes[stock]['Bearish Votes'] > self.indicator_votes[stock]['Bullish Votes'] and \
                        self.indicator_votes[stock]['Bearish Votes'] > self.indicator_votes[stock]['Neutral Votes']:
                    stock_shortlist[stock].append({timestamp: 'Very Bearish'})
                elif self.indicator_votes[stock]['Bearish Votes'] > self.indicator_votes[stock]['Bullish Votes']:
                    stock_shortlist[stock].append({timestamp: 'Bearish'})

                self.ti_data[stock] = []

        print('Buy Side Stocklist:', stock_buylist)
        print('Sell Side Stocklist:', stock_shortlist)
        print('------------------------------------------------------------------------')
        return stock_buylist, stock_shortlist
