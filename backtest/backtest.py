def calculate_backtest(df):
    # 1. 计算市场基础收益 (局部变量)
    market_return = df['close'].pct_change()

    # 2. 计算策略每日收益
    # shift(1) 确保我们在看到信号后的“下一根K线”开盘买入
    strategy_return = df['is_uptrend'].shift(1) * market_return

    # 3. 基础累计收益计算
    df['cum_return'] = (1 + strategy_return.fillna(0)).cumprod()

    # 4. 核心逻辑：寻找“由 False 变为 True”的第一个瞬间
    # diff() 会计算当前行减去上一行：1 - 0 = 1 代表由 False 变 True
    change_points = df['is_uptrend'].astype(int).diff()
    first_signal_indices = df.index[change_points == 1]

    if not first_signal_indices.empty:
        # 拿到真正的第一个“金叉”发生的索引
        first_entry_idx = first_signal_indices[0]
        
        # 归一化：让这一点的收益率刚好等于 1.0
        initial_value = df.at[first_entry_idx, 'cum_return']
        df['cum_return'] = df['cum_return'] / initial_value
        
        # 软工细节：在第一次买入之前的日子，收益率应该是 1（因为你还没进场，钱在兜里没动）
        # 我们使用 .loc 将第一个信号之前的索引全部设为 1.0
        df.loc[:first_entry_idx, 'cum_return'] = 1.0
    else:
        # 如果整个数据周期内从来没有从 False 变 True，收益率始终为 1
        df['cum_return'] = 1.0
        
    return df