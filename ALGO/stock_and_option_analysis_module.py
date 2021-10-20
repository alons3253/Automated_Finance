import datetime as dt
import sqlite3
import os


class stockAnalysis:
    def __init__(self, stock_tickers, quote_data, ti_data, indicator_votes):
        cwd = os.getcwd()
        self.path = fr'{cwd}\Databases\\'
        self.stock_tickers = stock_tickers
        self.quote_data = quote_data
        self.ti_data = ti_data
        self.indicator_votes = indicator_votes

    def option_analysis(self):
        pass

    # okay for now
    def volume_analysis(self, tick_test, path):
        with sqlite3.connect(self.path + 'quotes.db',
                             detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as db:
            one_minute_ago = dt.datetime.now() - dt.timedelta(minutes=1)
            for stock in self.stock_tickers:
                cur = db.execute(f"select * from quotes_{stock} where time > (?)", (one_minute_ago,))
                self.quote_data[stock] = cur.fetchall()

        volume_terms_dict = {}
        with sqlite3.connect(self.path + path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as db:
            for stock in self.stock_tickers:
                volume_terms_dict[stock] = {"30_seconds": {'shares_bought': 0, 'shares_sold': 0},
                                       "1_minute": {'shares_bought': 0, 'shares_sold': 0},
                                       "2_minutes": {'shares_bought': 0, 'shares_sold': 0},
                                       "4_minutes": {'shares_bought': 0, 'shares_sold': 0},
                                       "8_minutes": {'shares_bought': 0, 'shares_sold': 0},
                                       "15_minutes": {'shares_bought': 0, 'shares_sold': 0}}
                try:
                    cur = db.execute(f"select rowid, * from trades_{stock} where time > (?)",
                                     (self.quote_data[stock][-2][0],))
                    trade_elements = cur.fetchall()
                    cursor = db.cursor()

                    self.quote_data[stock] = []
                    first_trade = trade_elements[0]
                    second_trade = trade_elements[1]

                    uptick = tick_test[stock][0]
                    downtick = tick_test[stock][1]
                    zerotick = tick_test[stock][2]

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
                            # print(row)
                            # print(uptick)
                            # print(downtick)
                            # print(zerotick)
                            if index == 0:
                                previous_trade = first_trade
                                current_trade = second_trade
                                # do reverse tick test for the first item in the series
                                # If the current trade is followed by a trade with a
                                # higher (lower) price, the reverse tick test classifies the current trade as a sell
                                # (buy). This method was used by Hasbrouck (1988) to classify trades at the
                                # midpoint of the bid-ask spread.
                                if first_trade[-1] == 'None':
                                    if second_trade[2] > first_trade[2]:
                                        downtick = True
                                        cursor.execute(f"update trades_{stock} set direction = 'Sell' where rowid = (?)",
                                                       (first_trade[0],))
                                        db.commit()
                                    elif second_trade[2] < first_trade[2]:
                                        uptick = True
                                        cursor.execute(f"update trades_{stock} set direction = 'Buy' where rowid = (?)",
                                                       (first_trade[0],))
                                        db.commit()
                                    elif second_trade[2] == first_trade[2]:
                                        downtick = True
                                        zerotick = True
                                        cursor.execute(f"update trades_{stock} set direction = 'Sell' where rowid = (?)",
                                                       (first_trade[0],))
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
                    # print(row)
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
