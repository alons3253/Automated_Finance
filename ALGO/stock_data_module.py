from clr import AddReference
import datetime as dt
import requests
from bs4 import BeautifulSoup


def spy_returns():
    r = requests.get('https://finance.yahoo.com/quote/SPY?p=SPY')
    soup = BeautifulSoup(r.text, 'lxml')
    spy_returns_pct = [entry.text for entry in soup.find_all('span', {'data-reactid': '50'})]
    delimiter1 = '('
    delimiter2 = ')'
    formatted_return = str(spy_returns_pct[0])
    rt = formatted_return[formatted_return.find(delimiter1) + 1: formatted_return.find(delimiter2)]
    return_string = rt.split("%")[0]

    if return_string[0] == '+':
        spy_returns = '{:.2f}'.format(float(return_string.split('+')[1]))
    else:
        spy_returns = float(return_string)

    return spy_returns


class stockDataEngine:
    def __init__(self, stock_tickers, quote_data):
        self.stock_tickers = stock_tickers
        AddReference(r"C:\Users\fabio\source\repos\Webscraper Class Library\Webscraper "
                     r"Class Library\bin\Debug\Webscraper Class Library.dll")
        import CSharpwebscraper
        self.scrape_client = CSharpwebscraper.Webscraper()
        self.quote_data = quote_data

    def initial_quote_data_fetch(self):
        initial_stock_info = self.scrape_client.Initial(self.stock_tickers)
        initial_data = {}
        for stock in self.stock_tickers:
            initial_data[stock] = []

        length_of_information = len(initial_stock_info) // len(self.stock_tickers)

        for stock in self.stock_tickers:
            quote = {}
            for i in range(length_of_information):
                elem = initial_stock_info[i].replace(',', '')
                if i == 1:
                    delimiter1 = '('
                    delimiter2 = ')'
                    div = str(elem)
                    dividend = div[div.find(delimiter1) + 1: div.find(delimiter2)]
                    if dividend == 'N/A':
                        elem = 0.00
                    else:
                        div_string = dividend.split("%")[0]
                        dividend = float(div_string) / 100
                        elem = round(dividend, 4)
                    quote["dividend"] = elem
                if i == 2:
                    quote["day's range"] = elem if not elem == 'N/A' else elem
                if i == 3:
                    quote["52 week range"] = elem if not elem == 'N/A' else elem
                if i == 4:
                    quote["previous close"] = float(elem) if not elem == 'N/A' else elem
                if i == 5:
                    quote["open"] = float(elem) if not elem == 'N/A' else elem
                if i == 6:
                    quote["P/E ratio"] = float(elem) if not elem == 'N/A' else elem
                if i == 7:
                    quote["average volume"] = int(elem) if not elem == 'N/A' else elem
                if i == 8:
                    quote["one year target"] = float(elem) if not elem == 'N/A' else elem
                if i == 9:
                    quote["beta"] = float(elem) if not elem == 'N/A' else elem
                    quote["time"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    initial_data[stock].append(quote)
                    continue
            initial_stock_info = initial_stock_info[length_of_information:]
        return initial_data

    def quote_data_processor(self):
        scraped_stock_info = self.scrape_client.Scraper(self.stock_tickers)
        length_of_information = len(scraped_stock_info) // len(self.stock_tickers)

        for stock in self.stock_tickers:
            quote = {}
            for i in range(length_of_information):
                elem = scraped_stock_info[i].replace(',', '')
                if i == 1:
                    quote['current price'] = float(elem) if not elem == 'N/A' else elem
                if i == 2:
                    quote['indicator'] = elem
                if i == 3:
                    quote['volume'] = int(elem) if not elem == 'N/A' else elem
                if i == 4:
                    quote['bid'] = elem
                if i == 5:
                    quote['ask'] = elem
                    quote['time'] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.quote_data[stock].append(quote)
            scraped_stock_info = scraped_stock_info[length_of_information:]
        return self.quote_data
