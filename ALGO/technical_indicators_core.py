import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
import time
import os

from ALGO.excel_formatting_module import ExcelFormatting
"""
needs to be expanded and redone with individual tickers instead of the aggregate for a number of reasons
1) i believe the aggregate indicators will be done away with soon
2) i would rather do the math on the indicators by myself and pick and choose which ones will be measured
3) i believe there will be a higher accuracy if i do it this way and plus its a bit more rigorous than
just simply pulling it all from one source.
"""


def STOCH(df):
    df['14-high'] = df.rolling(14).max()['High']
    df['14-low'] = df.rolling(14).min()['Low']
    df['%K'] = (df['Close'] - df['14-low']) * 100 / (df['14-high'] - df['14-low'])
    df['%D'] = df['%K'].rolling(3).mean()
    del df['14-high'], df['14-low']

    return df


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


def bollinger_bands(dataframe):
    dataframe['MA20'] = dataframe['Close'].rolling(window=20).mean()
    dataframe['20dSTD'] = dataframe['Close'].rolling(window=20).std()

    dataframe['Upper'] = dataframe['MA20'] + (dataframe['20dSTD'] * 2)
    dataframe['Lower'] = dataframe['MA20'] - (dataframe['20dSTD'] * 2)
    del dataframe['MA20'], dataframe['20dSTD']

    return dataframe


def ROC(df, n=14):
    M = df['Close'].diff(n - 1)
    N = df['Close'].shift(n - 1)
    df['ROC'] = ((M / N) * 100)
    return df


class technicalIndicators:
    def __init__(self, stock_tickers, ti_data):
        self.resolutions = ['1', '5', '15', '30', '60', 'D', 'W', 'M']
        self.stock_tickers = stock_tickers
        self.ti_data = ti_data
        self.cwd = os.getcwd()

    def tech_indicator(self):
        yf.pdr_override()

        data = yf.download(tickers=self.stock_tickers, threads=True, group_by='ticker', period="1d", interval="1m",
                           prepost=True)
        data = data.round(decimals=2)

        for stock in self.stock_tickers:
            if len(self.stock_tickers) == 1:
                dataframe = data.tz_localize(None)
            else:
                dataframe = data[stock].tz_localize(None)
            # ADX > 30 strong trend, 20 < ADX < 30 weak trend, ADX < 20, no trend
            dataframe = ADX(dataframe, 14)

            # simple moving averages
            dataframe['SMA_7'] = dataframe.rolling(7).mean()['Adj Close']
            dataframe['SMA_14'] = dataframe.rolling(14).mean()['Adj Close']
            dataframe['SMA_28'] = dataframe.rolling(28).mean()['Adj Close']

            # get exponential moving averages for MACD
            ema_26 = dataframe['Close'].ewm(span=26, adjust=False).mean()
            ema_12 = dataframe['Close'].ewm(span=12, adjust=False).mean()
            dataframe['MACD'] = ema_12 - ema_26
            dataframe['MACD_SIG'] = dataframe['MACD'].ewm(span=9, adjust=False).mean()

            # RSI
            dataframe['RSI'] = RSI(dataframe)
            # OBV
            dataframe['OBV'] = (np.sign(dataframe['Close'].diff()) * dataframe['Volume']).fillna(0).cumsum()
            # stochastic oscillator
            # if %K is above %d, then that signals a buy, reverse signals a sell
            dataframe = STOCH(dataframe)
            # Aroon Indicator
            dataframe['AR-UP'] = 100 * dataframe['High'].rolling(15).apply(lambda x: x.argmax()) / 14
            dataframe['AR-DN'] = 100 * dataframe['Low'].rolling(15).apply(lambda x: x.argmin()) / 14
            # bollinger range
            dataframe = bollinger_bands(dataframe)
            # Rate of Change (momentum)
            dataframe = ROC(dataframe)

            dataframe = dataframe.round(decimals=2)
            dataframe = dataframe.dropna()
            # probably get 4:00 am as the time
            four_am = dt.datetime.combine(dt.date.today(), dt.time(4, 0))
            adx = np.argmax(abs(dataframe['ADX'].index - four_am))

            last_valid_row = dataframe.loc[dataframe.index[adx]]
            b = 0
            n = 0
            s = 0

            directional_index = last_valid_row['ADX']
            if directional_index < 20:
                TREND = 'none'
                n += 1
            elif 20 < directional_index < 30:
                TREND = 'weak'
            else:
                TREND = 'strong'

            rate_of_change = last_valid_row['ROC']
            if rate_of_change > 0.2:
                momentum = 'strong positive'
                b += 1
            elif rate_of_change < -0.2:
                momentum = 'strong negative'
                s += 1
            else:
                momentum = 'neutral'
                n += 1

            relative_strength = last_valid_row['RSI']
            if relative_strength > 70:
                b += 1
            elif relative_strength < 30:
                s += 1
            else:
                n += 1

            K = last_valid_row['%K']
            D = last_valid_row['%D']
            if K >= D:
                b += 1
                if K > D and (K-D) > 10:
                    b += 1
            elif K < D:
                s += 1
                if K < D and (D-K) > 10:
                    s += 1

            ARUP = last_valid_row['AR-UP']
            ARDN = last_valid_row['AR-DN']
            if ARUP >= 80:
                b += 1
                if ARUP == 100:
                    b += 1
                if ARDN == 0:
                    b += 1
                if ARUP - ARDN >= 50:
                    b += 1
                else:
                    n += 1

            if ARDN >= 80:
                s += 1
                if ARDN == 100:
                    s += 1
                if ARUP == 0:
                    s += 1
                if ARDN - ARDN >= 50:
                    s += 1
                else:
                    n += 1

            BUpper = last_valid_row['Upper']
            BLower = last_valid_row['Lower']
            Close = last_valid_row['Close']
            if Close > 1.05 * ((BUpper + BLower) / 2):
                b += 1
            elif Close < .95 * ((BUpper + BLower) / 2):
                s += 1
            if BLower * 1.05 > Close:
                b += 1
            elif BUpper * .95 < Close:
                s += 1

            if .95 * ((BUpper + BLower) / 2) < Close < 1.05 * ((BUpper + BLower) / 2):
                n += 1

            MACD = last_valid_row['MACD']
            MACD_SIG = last_valid_row['MACD_SIG']
            if MACD > MACD_SIG:
                b += 1
                if MACD_SIG < 0 and MACD > 0:
                    b += 1

            if MACD < 0 and MACD_SIG < 0:
                n += 1
            if abs(MACD - MACD_SIG) < 0.2:
                n += 1

            if MACD < MACD_SIG:
                s += 1
                if MACD_SIG > 0 and MACD < 0:
                    s += 1

            simple_ma7 = last_valid_row['SMA_7']
            simple_ma14 = last_valid_row['SMA_14']
            simple_ma28 = last_valid_row['SMA_28']

            if Close >= simple_ma7:
                s += 1
            else:
                b += 1
            if Close >= simple_ma14:
                s += 1
            else:
                b += 1
            if Close >= simple_ma28:
                s += 1
            else:
                b += 1

            # future expansion is necessary but this is good for now
            # a look at the inflection and rate of change between the indicators from 5-10 minutes ago to now is useful
            sig = 'Neutral'
            if b > n > s:
                sig = 'Strong Buy'
            elif b > s:
                sig = 'Buy'
            elif b < s:
                sig = 'Sell'
            elif b < n < s:
                sig = 'Strong Sell'

            if abs(b-s) < 2:
                sig = 'Neutral'

            technical = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "buy": b, 'neutral': n, 'sell': s, 'signal': sig,
                         'trending': TREND, 'adx': directional_index, "momentum": momentum,
                         "rate of change": rate_of_change}
            self.ti_data[stock].append(technical)

            url = f"{self.cwd}\\Daily Stock Analysis\\Trades\\{stock} Intraday {dt.date.today()}.xlsx"
            with pd.ExcelWriter(url, engine='openpyxl') as writer:
                dataframe.to_excel(writer, sheet_name=f'{stock} Intraday Trades')

            ExcelFormatting(file_path=url).formatting()

        return self.ti_data
