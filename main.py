import datetime
import time
import pandas as pd

from factors.supertrend import _super_trend, calc_super_trend
pd.set_option('display.max_rows', None)
import ccxt
import schedule
import config

crypto='ETH/USDT'
Threshold=0.85

exchange = ccxt.okx({
    'apiKey':config.OKX_API_KEY,
    'secret':config.OKX_SECRET_KEY,
    'password': config.OKX_PASSPHRASE,
})
def fetch_data():
    bars = exchange.fetch_ohlcv(crypto, timeframe='15m', limit=300)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def run_bot():
    print(f"Fetching new bars for {datetime.date}")
    df = fetch_data()
    score = calc_super_trend(df)
    if score >= Threshold:
        order = exchange.create_market_buy_order(crypto, 0.05)
        print(order)
    elif score <=-Threshold:
        order = exchange.create_market_sell_order(crypto, 0.05)
        print(order)

if __name__ == '__main__':
    df = fetch_data()
    scores = {
        'st':calc_super_trend(df)
    }
    final_signal = sum(scores.values())
    print(final_signal)
    print(df)
    # schedule.every(2).seconds.do(run_bot)

    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)

