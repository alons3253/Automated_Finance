import requests
import time

"""
needs to be expanded and redone with individual tickers instead of the aggregate for a number of reasons
1) i believe the aggregate indicators will be done away with soon
2) i would rather do the math on the indicators by myself and pick and choose which ones will be measured
3) i believe there will be a higher accuracy if i do it this way and plus its a bit more rigorous than
just simply pulling it all from one source.
"""


class technicalIndicators:
    def __init__(self, stock_tickers, ti_data, finnhub_token):
        self.resolutions = ['1', '5', '15', '30', '60', 'D', 'W', 'M']
        self.stock_tickers = stock_tickers
        self.ti_data = ti_data
        self.token = finnhub_token

    def tech_indicator(self):
        i = 0
        for stock in self.stock_tickers:
            try:
                resolution = self.resolutions[i]
                tech_url = f'https://finnhub.io/api/v1/scan/technical-indicator?symbol={stock}&resolution={resolution}'\
                           f'&token={self.token}'
                r = requests.get(tech_url)
                ti = r.json()
                technical = ti['technicalAnalysis']['count']
                technical['signal'] = ti['technicalAnalysis']['signal']
                technical['adx'] = ti['trend']['adx']
                technical['trending'] = ti['trend']['trending']
                technical['time'] = time.strftime("%Y-%m-%d %H:%M:%S")
                self.ti_data[stock].append(technical)
            except KeyError:
                continue
        return self.ti_data
