import datetime
import time
import pandas as pd
import ccxt
import schedule
import config
from ta.volatility import BollingerBands,AverageTrueRange

exchange = ccxt.okx({
    'apiKey':config.OKX_API_KEY,
    'secret':config.OKX_SECRET_KEY,
    'password': config.OKX_PASSPHRASE,
})

def _measure_volatility(df,window=14,window_dev=2):
    """添加AverageTrueRange和BollingerBands"""
    # AverageTrueRange衡量市场波动volatility
    atr_indicator = AverageTrueRange(df['high'],df['low'],df['close'],window=window)
    df['atr'] = atr_indicator.average_true_range()

    # BollingerBands衡量波动范围
    bb_indicator = BollingerBands(df['close'],window=window,window_dev=window_dev)
    df['upper_band'] = bb_indicator.bollinger_hband()
    df['lower_band'] = bb_indicator.bollinger_lband()
    df['moving_avg'] = bb_indicator.bollinger_mavg()
    return df


def super_trend(df,window=14,window_dev=2):
    """添加is_uptrend判断趋势"""

    _measure_volatility(df,window=window,window_dev=window_dev)

    # 1. 找到第一个非空的数据行（跳过前面的 NaN）
    first_valid = df['upper_band'].first_valid_index()
    if first_valid is None: return df
    
    # 2. 初始化状态只在第一个有效行设置
    df['is_uptrend'] = True 

    # 3. 从第一个有效行的下一行开始循环
    for i in range(first_valid + 1, len(df)):
        prev = i - 1
        curr_close = df.at[i, 'close']
        prev_upper = df.at[prev, 'upper_band']
        prev_lower = df.at[prev, 'lower_band']
        
        # 趋势翻转逻辑
        if curr_close > prev_upper:
            df.at[i, 'is_uptrend'] = True
        elif curr_close < prev_lower:
            df.at[i, 'is_uptrend'] = False
        else:
            # 继承上一个状态
            df.at[i, 'is_uptrend'] = df.at[prev, 'is_uptrend']
            
            # 递归修正带状线：如果是上升趋势，下轨不能降低
            if df.at[i, 'is_uptrend']:
                if df.at[i, 'lower_band'] < prev_lower:
                    df.at[i, 'lower_band'] = prev_lower
            # 如果是下降趋势，上轨不能升高
            else:
                if df.at[i, 'upper_band'] > prev_upper:
                    df.at[i, 'upper_band'] = prev_upper
    return df

in_position = False

def check_buy_sell_signals(df):
    global in_position

    print("checking for buy and sell signals")
    print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['is_uptrend'][previous_row_index] and df['is_uptrend'][last_row_index]:
        print("changed to uptrend, buy")
        if not in_position:
            order = exchange.create_market_buy_order('ETH/USDT', 0.05)
            print(order)
            in_position = True
        else:
            print("already in position, nothing to do")
    
    elif df['is_uptrend'][previous_row_index] and not df['is_uptrend'][last_row_index]:
        if in_position:
            print("changed to downtrend, sell")
            order = exchange.create_market_sell_order('ETH/USDT', 0.05)
            print(order)
            in_position = False
        else:
            print("You aren't in position, nothing to sell")
    else: print("market is stable,nothing to do")

def run_bot():
    print(f"Fetching new bars for {datetime.datetime.date}")
    bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='1m', limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    supertrend_data = super_trend(df)   
    check_buy_sell_signals(supertrend_data)

if __name__ == '__main__':

    schedule.every(2).seconds.do(run_bot)

    while True:
        schedule.run_pending()
        time.sleep(1)

