import pandas as pd
import ccxt
import config
from ta.volatility import BollingerBands,AverageTrueRange
exchange = ccxt.okx({
    'apiKey':config.OKX_API_KEY,
    'secret':config.OKX_SECRET_KEY,
    'password': config.OKX_PASSPHRASE,
})

bars = exchange.fetch_ohlcv('ETH/USDT',timeframe='1d',limit=300)
df = pd.DataFrame(bars[:-1],columns=['timestamp','open','high','low','close','volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

bb_indicator = BollingerBands(df['close'],window=14)
df['upper_band'] = bb_indicator.bollinger_hband()
df['lower_band'] = bb_indicator.bollinger_lband()
df['moving_avg'] = bb_indicator.bollinger_mavg()

atr_indicator = AverageTrueRange(df['high'],df['low'],df['close'],window=14)
df['atr'] = atr_indicator.average_true_range()

if __name__ == '__main__':
    pd.set_option('display.max_rows',None)
    print(df.tail(10))

