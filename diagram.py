import mplfinance as mpf
import numpy as np
from main import fetch_data,_super_trend

# ==============================
# 第一步：数据准备（适配 mplfinance）
# ==============================
df = fetch_data()
supertrend_data = _super_trend(df)

plot_df = supertrend_data.copy()
plot_df.set_index('timestamp', inplace=True)

# ==============================
# 第二步：生成信号标注数据
# ==============================
# 我们利用 is_uptrend 列的变化来捕获“信号发生点”
# shift(1) 会将整列向下移动一行。对比当前和上一行，就能发现变化。

# 1. 找到买入信号点（昨天是跌，今天是涨）
buy_signals = (plot_df['is_uptrend'] == True) & (plot_df['is_uptrend'].shift(1) == False)

# 2. 找到卖出信号点（昨天是涨，今天是跌）
sell_signals = (plot_df['is_uptrend'] == False) & (plot_df['is_uptrend'].shift(1) == True)

# 创建与 plot_df 等长的数组，用于存储标注价格，默认为 NaN（不显示）
plot_df['buy_price'] = np.nan
plot_df['sell_price'] = np.nan

# 在信号发生的日期，填入相应的价格用于标注
plot_df.loc[buy_signals, 'buy_price'] = plot_df['low']
plot_df.loc[sell_signals, 'sell_price'] = plot_df['high']

# ==============================
# 第三步：配置 mplfinance
# ==============================

# 定义绘图内容
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

my_color = mpf.make_marketcolors(up='lime', down='crimson', edge='inherit', wick='inherit', volume='in')
my_style = mpf.make_mpf_style( gridstyle=':', y_on_right=True)


# ==============================
# 第四步：执行绘图并保存
# ==============================

mpf.plot(plot_df, 
         type='candle',         # 指定为蜡烛图
         style=my_style,        # 使用自定义风格
         addplot=apds,          # 加入刚才定义的指标和信号
         title='NexusQuant: ETH/USDT Signals & Bollinger Bands',
         ylabel='Price (USDT)',
         volume=True,          # 暂时关闭成交量
         figsize=(12, 10),      # 画布大小
         panel_ratios=(3, 1),   # K线图与 ATR 图的高度比例
         datetime_format='%Y-%m-%d', # x轴时间格式
         savefig='images/NexusQuant_Signals.png') # 保存

print("K 线信号图已生成并保存为 images/NexusQuant_Signals.png")