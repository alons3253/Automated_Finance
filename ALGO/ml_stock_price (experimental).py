import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import Dense, LSTM
import math
from sklearn.preprocessing import MinMaxScaler
import yfinance as yf


if __name__ == '__main__':
    stock_tickers = ['FITB', 'GILD', 'MO']

    yf.pdr_override()

    data = yf.download(tickers=stock_tickers, threads=True, group_by='ticker', period="5d", interval="1m",
                       prepost=False)
    data = data.round(decimals=2)

    for stock in stock_tickers:
        df = data[stock]
        #output_var = pd.DataFrame(df['Adj Close'])
        #df = pd.read_excel(f'Daily Stock Analysis/Trades/{stock} Intraday {dt.date.today()}.xlsx', index_col=0)
        df = df.dropna()
        df.head()
