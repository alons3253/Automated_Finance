import datetime as dt


class stockAnalysis:
    def __init__(self, stock_tickers, quote_data, ti_data, trade_data, indicator_votes):
        self.stock_tickers = stock_tickers
        self.quote_data = quote_data
        self.ti_data = ti_data
        self.trade_data = trade_data
        self.indicator_votes = indicator_votes

    def option_analysis(self):
        pass

    def volume_analysis(self, volume_terms):
        for STOCK_TICKER in self.stock_tickers:
            volume_terms_tuple = volume_terms[STOCK_TICKER]

            thirty_seconds = volume_terms_tuple[0]
            one_minute = volume_terms_tuple[1]
            two_minutes = volume_terms_tuple[2]
            five_minutes = volume_terms_tuple[3]

            for pos, ite in enumerate(self.trade_data[STOCK_TICKER]):
                # for now deleting the stock price calculation from this block
                # going to readd a method to classify new trades as buys or sells
                # if the trade is above the current stock price, then its a sell
                # if the trade is below the current stock price, then its a buy
                ##############################################################################
                tradetime = dt.datetime.strptime(ite['time'], "%Y-%m-%d %H:%M:%S.%f")
                if tradetime > dt.datetime.now() - dt.timedelta(seconds=30):
                    thirty_seconds += int(ite['volume'])
                if tradetime > dt.datetime.now() - dt.timedelta(seconds=60):
                    one_minute += int(ite['volume'])
                if tradetime > dt.datetime.now() - dt.timedelta(seconds=120):
                    two_minutes += int(ite['volume'])
                if tradetime > dt.datetime.now() - dt.timedelta(seconds=300):
                    five_minutes += int(ite['volume'])
            ##############################################################################
            volume_terms[STOCK_TICKER] = (thirty_seconds, one_minute, two_minutes, five_minutes)
        print('volume by stock ordered 30sec, 1min, 2min and 5min:', volume_terms)
        return volume_terms

    # working
    def indicator_analysis(self, stock_shortlist, stock_buylist):
        for STOCK_TICKER in self.stock_tickers:
            timestamp = str(dt.datetime.strptime(self.quote_data[STOCK_TICKER][-1]['time'][11::], '%H:%M:%S').time())
            indicator = self.quote_data[STOCK_TICKER][-1]['indicator']
            if len(self.ti_data) > 0:
                self.indicator_votes[STOCK_TICKER]['Bullish Votes'] += int(self.ti_data[STOCK_TICKER][-1]['buy'])
                self.indicator_votes[STOCK_TICKER]['Bearish Votes'] += int(self.ti_data[STOCK_TICKER][-1]['sell'])
                self.indicator_votes[STOCK_TICKER]['Neutral Votes'] += int(self.ti_data[STOCK_TICKER][-1]['neutral'])

            if indicator == 'Bullish':
                self.indicator_votes[STOCK_TICKER]['Bullish Votes'] += 1
            if indicator == 'Bearish':
                self.indicator_votes[STOCK_TICKER]['Bearish Votes'] += 1

            if self.indicator_votes[STOCK_TICKER]['Bullish Votes'] > \
                    self.indicator_votes[STOCK_TICKER]['Bearish Votes'] and \
                    self.indicator_votes[STOCK_TICKER]['Bullish Votes'] > \
                    self.indicator_votes[STOCK_TICKER]['Neutral Votes']:
                stock_buylist[STOCK_TICKER].append({timestamp: 'Very Bullish'})
            elif self.indicator_votes[STOCK_TICKER]['Bullish Votes'] > \
                    self.indicator_votes[STOCK_TICKER]['Bearish Votes']:
                stock_buylist[STOCK_TICKER].append({timestamp: 'Bullish'})

            if self.indicator_votes[STOCK_TICKER]['Bearish Votes'] > \
                    self.indicator_votes[STOCK_TICKER]['Bullish Votes'] and \
                    self.indicator_votes[STOCK_TICKER]['Bearish Votes'] > \
                    self.indicator_votes[STOCK_TICKER]['Neutral Votes']:
                stock_shortlist[STOCK_TICKER].append({timestamp: 'Very Bearish'})
            elif self.indicator_votes[STOCK_TICKER]['Bearish Votes'] > \
                    self.indicator_votes[STOCK_TICKER]['Bullish Votes']:
                stock_shortlist[STOCK_TICKER].append({timestamp: 'Bearish'})

        print('Stocks of interest:', self.stock_tickers)
        print('Buy Side Stocklist:', stock_buylist)
        print('Sell Side Stocklist:', stock_shortlist)
        print('------------------------------------------------------------------------')
        return stock_buylist, stock_shortlist
