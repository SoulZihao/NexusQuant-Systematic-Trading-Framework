from ta.volatility import BollingerBands,AverageTrueRange

def _measure_volatility(df,window=14,window_dev=2):
    """添加AverageTrueRange和BollingerBands"""

    return df


def _super_trend(df,window=14,window_dev=2):
    """添加各种指标判断趋势"""
    # AverageTrueRange衡量市场波动volatility
    atr_indicator = AverageTrueRange(df['high'],df['low'],df['close'],window=window)
    df['atr'] = atr_indicator.average_true_range()

    # BollingerBands衡量波动范围
    bb_indicator = BollingerBands(df['close'],window=window,window_dev=window_dev)
    df['upper_band'] = bb_indicator.bollinger_hband()
    df['lower_band'] = bb_indicator.bollinger_lband()
    df['moving_avg'] = bb_indicator.bollinger_mavg()

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

def calc_super_trend(df)->float:
    _super_trend(df)
    score = 0
    print("checking for buy and sell signals")
    print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['is_uptrend'][previous_row_index] and df['is_uptrend'][last_row_index]:
        print("changed to uptrend, buy")
        score = 1
        in_position = True
    
    elif df['is_uptrend'][previous_row_index] and not df['is_uptrend'][last_row_index]:
        print("changed to downtrend, sell")
        score = -1
        in_position = False
    else: print("market is stable,nothing to do")
    return score