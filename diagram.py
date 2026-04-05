import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf  # 引入专业金融绘图库
import numpy as np
# 假设你已经从之前的步骤中拿到了 df
from supertrend import df

# ==============================
# 第一步：数据准备（适配 mplfinance）
# ==============================
# mplfinance 要求索引必须是 DatetimeIndex
plot_df = df.copy()
plot_df.set_index('timestamp', inplace=True)

# 确保列名符合 mplfinance 的要求（Open, High, Low, Close, Volume）
# 我们之前的列名已经是小写，这里自动适配，但需确认 open, high, low 数据完整。

# ==============================
# 第二步：生成信号标注数据（软工逻辑点）
# ==============================
# 我们利用 is_uptrend 列的变化来捕获“信号发生点”
# shift(1) 会将整列向下移动一行。对比当前和上一行，就能发现变化。

# 1. 找到买入信号点（昨天是跌，今天是涨）
# (is_uptrend == True) 且 (昨天的 is_uptrend == False)
buy_signals = (plot_df['is_uptrend'] == True) & (plot_df['is_uptrend'].shift(1) == False)

# 2. 找到卖出信号点（昨天是涨，今天是跌）
sell_signals = (plot_df['is_uptrend'] == False) & (plot_df['is_uptrend'].shift(1) == True)

# 创建与 plot_df 等长的数组，用于存储标注价格，默认为 NaN（不显示）
plot_df['buy_price'] = np.nan
plot_df['sell_price'] = np.nan

# 在信号发生的日期，填入相应的价格用于标注
# 买入信号标注在最低价下方，卖出信号标注在最高价上方，避免遮挡 K 线
plot_df.loc[buy_signals, 'buy_price'] = plot_df['low'] * 0.985
plot_df.loc[sell_signals, 'sell_price'] = plot_df['high'] * 1.015

# ==============================
# 第三步：配置 mplfinance (高级可视化设计)
# ==============================

# 1. 定义额外的绘图内容 (Addplot)
apds = [
    # 布林带上轨 (红色虚线)
    mpf.make_addplot(plot_df['upper_band'], color='red', linestyle='--', alpha=0.5, ),
    # 布林带下轨 (绿色虚线)
    mpf.make_addplot(plot_df['lower_band'], color='green', linestyle='--', alpha=0.5, ),
    # 移动平均线 (蓝色实线)
    mpf.make_addplot(plot_df['moving_avg'], color='blue', alpha=0.3, ),
    
    # ATR (在第二个子图中绘制)
    mpf.make_addplot(plot_df['atr'], color='purple', panel=1, ylabel='ATR Value', alpha=0.7),
    
    # 绘制买入标注 (绿色向上三角)
    mpf.make_addplot(plot_df['buy_price'], type='scatter', markersize=100, marker='^', color='lime', ),
    # 绘制卖出标注 (红色向下三角)
    mpf.make_addplot(plot_df['sell_price'], type='scatter', markersize=100, marker='v', color='crimson', )
]

# 2. 自定义 K 线颜色风格 (国际标准：绿涨红跌)
my_color = mpf.make_marketcolors(up='lime', down='crimson', edge='inherit', wick='inherit', volume='in')
my_style = mpf.make_mpf_style(marketcolors=my_color, gridstyle=':', y_on_right=True)

# ==============================
# 第四步：执行绘图并保存
# ==============================

# 注意：mplfinance 有自己的画布管理逻辑，不需要手动 plt.subplots
# 它会自动生成主图（K线）和指定的 panel（这里是 ATR）
# 通过 volume=False 暂时隐藏成交量
mpf.plot(plot_df, 
         type='candle',         # 指定为蜡烛图
         style=my_style,        # 使用自定义风格
         addplot=apds,          # 加入刚才定义的指标和信号
         title='NexusQuant: ETH/USDT Signals & Bollinger Bands',
         ylabel='Price (USDT)',
         volume=False,          # 暂时关闭成交量
         figsize=(12, 10),      # 画布大小
         panel_ratios=(3, 1),   # K线图与 ATR 图的高度比例
         datetime_format='%Y-%m-%d', # x轴时间格式
         savefig='images/NexusQuant_Signals.png') # 保存

print("高性能 K 线信号图已生成并保存为 images/NexusQuant_Signals.png")