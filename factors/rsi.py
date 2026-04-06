import pandas as pd
from ta.momentum import RSIIndicator

from factors.base import BaseFactor


class RSIFactor(BaseFactor):
    """RSI 动量因子。

    原理：
    - RSI = 100 - 100 / (1 + 平均涨幅 / 平均跌幅)
    - RSI > 70 通常认为超买，RSI < 30 通常认为超卖
    - 将 RSI ∈ [0, 100] 线性映射到信号 ∈ [-1, 1]
    - RSI = 50 对应信号 0（中性），RSI = 30 对应 -0.4（偏空），RSI = 70 对应 +0.4（偏多）

    这里 RSI 作为趋势动量指标使用（高 RSI = 强动量 = 看多），
    而非均值回归指标。两种用法在学术和实战中都有效，
    取决于市场状态和时间框架。加密货币市场趋势性强，
    动量用法通常更合适。
    """

    name = 'rsi'
    category = 'momentum'

    def __init__(self, window: int = 14):
        self.window = window

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        rsi = RSIIndicator(df['close'], window=self.window).rsi()

        # RSI ∈ [0, 100] → signal ∈ [-1, 1]
        signal = (rsi - 50.0) / 50.0

        return signal.clip(-1, 1).fillna(0)
