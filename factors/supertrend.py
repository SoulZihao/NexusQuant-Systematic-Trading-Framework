from ta.volatility import BollingerBands,AverageTrueRange
import pandas as pd

def _measure_volatility(df,window=14,window_dev=2):
    """添加AverageTrueRange和BollingerBands"""

    return df


def _super_trend(df,window=14,window_dev=2):
    """添加各种指标判断趋势"""
    # AverageTrueRange衡量市场波动volatility
    atr_indicator = AverageTrueRange(df['high'],df['low'],df['close'],window=window)
    atr = atr_indicator.average_true_range()

    # BollingerBands衡量波动范围
    bb_indicator = BollingerBands(df['close'],window=window,window_dev=window_dev)
    upper_band = pd.Series(bb_indicator.bollinger_hband(), index=df.index, name='is_uptrend')
    lower_band = pd.Series(bb_indicator.bollinger_lband(), index=df.index, name='is_uptrend')
    moving_avg = pd.Series(bb_indicator.bollinger_mavg(), index=df.index, name='is_uptrend')

    # 1. 找到第一个非空的数据行（跳过前面的 NaN）
    first_valid_idx = df.index.get_loc(upper_band.first_valid_index())
    
    # 2. 初始化状态只在第一个有效行设置
    is_uptrend = pd.Series(False, index=df.index, name='is_uptrend')

    # 3. 从第一个有效行的下一行开始循环
    for i in range(first_valid_idx + 1, len(df)):
        prev = i - 1
        curr_close = df.at[i, 'close']
        prev_upper = upper_band.at[prev]
        prev_lower = lower_band.at[prev]
        
        # 趋势翻转逻辑
        if curr_close > prev_upper:
            is_uptrend[i] = True
        elif curr_close < prev_lower:
            is_uptrend[i] = False
        else:
            # 继承上一个状态
            is_uptrend[i] = is_uptrend[prev]
            
            # 递归修正带状线：如果是上升趋势，下轨不能降低
            if is_uptrend[i]:
                if lower_band[i] < prev_lower:
                    lower_band[i] = prev_lower
            # 如果是下降趋势，上轨不能升高
            else:
                if upper_band[i] > prev_upper:
                    upper_band[i] = prev_upper
    plot_data = {
        'upper_band':upper_band,
        'lower_band':lower_band,
        'atr':atr,
        'moving_avg':moving_avg,
        'is_uptrend':is_uptrend
    }
    plot_df = pd.DataFrame(plot_data)
    return plot_df

def calc_super_trend(df)->float:
    plot_df = _super_trend(df)
    score = 0
    print("checking for buy and sell signals")
    print(plot_df.tail(10))
    last_row_index = len(plot_df.index) - 1
    previous_row_index = last_row_index - 1

    if not plot_df['is_uptrend'][previous_row_index] and plot_df['is_uptrend'][last_row_index]:
        print("changed to uptrend, buy")
        score = 1
        in_position = True
    
    elif plot_df['is_uptrend'][previous_row_index] and not plot_df['is_uptrend'][last_row_index]:
        print("changed to downtrend, sell")
        score = -1
    else: print("market is stable,nothing to do")
    return score