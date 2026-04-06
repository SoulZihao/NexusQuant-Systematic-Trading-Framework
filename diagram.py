import mplfinance as mpf
import numpy as np

from data.fetcher import DataFetcher
from factors.supertrend import SuperTrendFactor

# ==============================
# 第一步：数据准备
# ==============================
fetcher = DataFetcher()
df = fetcher.fetch_ohlcv('ETH/USDT', timeframe='15m', limit=300)

# 计算 SuperTrend 因子信号
st_factor = SuperTrendFactor()
signal = st_factor.calculate(df)

df.set_index('timestamp', inplace=True)

# ==============================
# 第二步：生成信号标注数据
# ==============================
buy_signals = (signal > 0.3) & (signal.shift(1) <= 0.3)
sell_signals = (signal < -0.3) & (signal.shift(1) >= -0.3)

buy_price = np.where(buy_signals, df['low'], np.nan)
sell_price = np.where(sell_signals, df['high'], np.nan)

# ==============================
# 第三步：配置 mplfinance
# ==============================
apds = [
    mpf.make_addplot(signal.values, color='blue', panel=1,
                     ylabel='Signal', alpha=0.7),
    mpf.make_addplot(buy_price, type='scatter', markersize=100,
                     marker='^', color='lime'),
    mpf.make_addplot(sell_price, type='scatter', markersize=100,
                     marker='v', color='crimson'),
]

my_style = mpf.make_mpf_style(gridstyle=':', y_on_right=True)

# ==============================
# 第四步：执行绘图并保存
# ==============================
mpf.plot(df,
         type='candle',
         style=my_style,
         addplot=apds,
         title='Multi-Factor: ETH/USDT Signals',
         ylabel='Price (USDT)',
         volume=True,
         figsize=(14, 10),
         panel_ratios=(3, 1),
         datetime_format='%Y-%m-%d %H:%M',
         savefig='images/signals.png')

print("信号图已保存为 images/signals.png")
