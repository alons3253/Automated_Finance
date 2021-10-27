import requests
import time
import finnhub
import datetime
import yfinance as yf
import plotly.graph_objects as go

import re
import csv
import pandas as pd
import requests
from contextlib import closing
import csv
from codecs import iterdecode
import matplotlib as plt
import numpy as np


"""
needs to be expanded and redone with individual tickers instead of the aggregate for a number of reasons
1) i believe the aggregate indicators will be done away with soon
2) i would rather do the math on the indicators by myself and pick and choose which ones will be measured
3) i believe there will be a higher accuracy if i do it this way and plus its a bit more rigorous than
just simply pulling it all from one source.
"""


def ADX(data: pd.DataFrame, period: int):
    """Computes the ADX indicator. """

    df = data.copy()
    alpha = 1 / period

    # TR
    df['H-L'] = df['High'] - df['Low']
    df['H-C'] = np.abs(df['High'] - df['Adj Close'].shift(1))
    df['L-C'] = np.abs(df['Low'] - df['Adj Close'].shift(1))
    df['TR'] = df[['H-L', 'H-C', 'L-C']].max(axis=1)
    del df['H-L'], df['H-C'], df['L-C']

    # ATR
    df['ATR'] = df['TR'].ewm(alpha=alpha, adjust=False).mean()

    # +-DX
    df['H-pH'] = df['High'] - df['High'].shift(1)
    df['pL-L'] = df['Low'].shift(1) - df['Low']
    df['+DX'] = np.where((df['H-pH'] > df['pL-L']) & (df['H-pH'] > 0), df['H-pH'], 0.0)
    df['-DX'] = np.where((df['H-pH'] < df['pL-L']) & (df['pL-L'] > 0), df['pL-L'], 0.0)
    del df['H-pH'], df['pL-L']

    # +- DMI
    df['S+DM'] = df['+DX'].ewm(alpha=alpha, adjust=False).mean()
    df['S-DM'] = df['-DX'].ewm(alpha=alpha, adjust=False).mean()
    df['+DMI'] = (df['S+DM'] / df['ATR']) * 100
    df['-DMI'] = (df['S-DM'] / df['ATR']) * 100
    del df['S+DM'], df['S-DM']

    # ADX
    df['DX'] = (np.abs(df['+DMI'] - df['-DMI']) / (df['+DMI'] + df['-DMI'])) * 100
    df['ADX'] = df['DX'].ewm(alpha=alpha, adjust=False).mean()
    del df['DX'], df['ATR'], df['TR'], df['-DX'], df['+DX'], df['+DMI'], df['-DMI']

    return df


def RSI(dataframe):
    delta = dataframe['Adj Close'].diff()
    up, down = delta.clip(lower=0), delta.clip(upper=0)
    roll_up1 = up.ewm(span=12).mean()
    roll_down1 = down.abs().ewm(span=12).mean()

    # Calculate the RSI based on EWMA
    RS1 = roll_up1 / roll_down1
    return 100.0 - (100.0 / (1.0 + RS1))


class technicalIndicators:
    def __init__(self, stock_tickers, ti_data, finnhub_token):
        self.resolutions = ['1', '5', '15', '30', '60', 'D', 'W', 'M']
        self.stock_tickers = stock_tickers
        self.ti_data = ti_data

    def tech_indicator(self):
        yf.pdr_override()
        data = yf.download(tickers=self.stock_tickers, threads=True, group_by='ticker', period="1d", interval="1m",
                           prepost=True)
        data = data.round(decimals=2)
        for stock in self.stock_tickers:
            dataframe = data[stock].tz_localize(None)
            #ADX > 30 strong trend, 20 < ADX < 30 weak trend, ADX < 20, no trend
            dataframe = ADX(dataframe, 14)

            # simple moving averages
            dataframe['SMA_5'] = dataframe.rolling(5).mean()['Adj Close']
            dataframe['SMA_15'] = dataframe.rolling(15).mean()['Adj Close']
            dataframe['SMA_30'] = dataframe.rolling(30).mean()['Adj Close']

            # get exponential moving averages for MACD
            ema_26 = dataframe['Close'].ewm(span=26, adjust=False).mean()
            ema_12 = dataframe['Close'].ewm(span=12, adjust=False).mean()
            dataframe['MACD'] = ema_12 - ema_26
            dataframe['MACD_SIG'] = dataframe['MACD'].ewm(span=9, adjust=False).mean()

            # RSI
            dataframe['RSI'] = RSI(dataframe)


            dataframe.to_excel(f"{stock} intraday trade data.xlsx", engine='openpyxl')
            print(dataframe)

        """
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
        """
