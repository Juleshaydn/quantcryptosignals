
from ta.volatility import BollingerBands, AverageTrueRange
import ta
import time
from datetime import datetime
import numpy as np
import warnings
import ccxt
import schedule
import pandas as pd
pd.set_option('display.max_rows', None)
warnings.filterwarnings('ignore')


exchange = ccxt.binanceus()
# market = exchange.load_markets()


# bb_indicator = BollingerBands(df['close'])

# df['upper_band'] = bb_indicator.bollinger_hband()
# df['lower_band'] = bb_indicator.bollinger_lband()
# df['moving_average'] = bb_indicator.bollinger_mavg()

# atr_indicator = AverageTrueRange(df['high'], df['low'], df['close'])


def tr(df):
    # df['atr'] = atr_indicator.average_true_range()
    df['previous_close'] = df['close'].shift(1)
    df['high-low'] = df['high'] - df['low']
    df['high-pc'] = abs(df['high'] - df['previous_close'])
    df['low-pc'] = abs(df['low'] - df['previous_close'])
    tr = df[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr


def atr(df, period=14):
    df['tr'] = tr(df)
    # print("Calculating averave true range")

    the_atr = df['tr'].rolling(period).mean()

    return the_atr
    #df['atr'] = the_atr
    # print(df)


def supertrend(df, period=7, multiplier=3):
    # print("Calculating supertrend")
    # basic upper band = (()high + low / 2) + (multiplier * atr)
    # basic upper band = (()high + low / 2) - (multiplier * atr)
    df['atr'] = atr(df, period=period)
    df['upperband'] = ((df['high'] + df['low']) / 2) + (multiplier * df['atr'])
    df['lowerband'] = ((df['high'] + df['low']) / 2) - (multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previews = current - 1

        if df['close'][current] > df['upperband'][previews]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previews]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previews]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['in_uptrend'][previews]:
                df['lowerband'][current] = df['lowerband'][previews]

            if not df['in_uptrend'][current] and df['upperband'][current] < df['upperband'][previews]:
                df['upperband'][current] = df['upperband'][previews]

    return df


def check_buy_sell_signals(df):
    print("Checking for buys and sells")
    # print(df.tail(5))
    print(df.tail(2))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    print(last_row_index)
    print(previous_row_index)
    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("Changed to uptrend BUY!")

    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        print("Changed to downtrend SELL!")


def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv('BTC/USD', timeframe='1m', limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp',
                      'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    supertrend_data = supertrend(df)
    check_buy_sell_signals(supertrend_data)


schedule.every(2).seconds.do(run_bot)

# supertrend(df)

while True:
    schedule.run_pending()
    time.sleep(1)
