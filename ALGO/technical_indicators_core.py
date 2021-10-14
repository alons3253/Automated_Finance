import requests
import time


# this should work properly
class technicalIndicators:
    def __init__(self, stock_tickers, ti_data):
        self.resolutions = ['1', '5', '15', '30', '60', 'D', 'W', 'M']
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.stock_tickers = stock_tickers
        self.ti_data = ti_data

        token_file = open("finnhub_key.txt")
        lines = token_file.readlines()
        self.token = lines[0].rstrip('\n')

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
                technical['time'] = self.timestamp
                self.ti_data[stock].append(technical)
            except KeyError:
                continue
        return self.ti_data
