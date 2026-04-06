from typing import override

import numpy as np
import pandas as pd
from ta.trend import MACD

from factors.base import BaseFactor


class MACDFactor(BaseFactor):
    """MACD 趋势/动量因子。

    原理：
    - MACD Line = EMA(12) - EMA(26)，衡量短期与长期趋势的差异
    - Signal Line = MACD Line 的 EMA(9)
    - Histogram = MACD Line - Signal Line
    - Histogram > 0 且递增 → 上升动量加速（强看多）
    - Histogram < 0 且递减 → 下降动量加速（强看空）

    信号生成：
    - 用 histogram 除以价格做标准化（消除不同币种价格量级的影响）
    - 再用 tanh 压缩到 [-1, 1] 区间，保证极端值不会溢出
    """

    name = 'macd'
    category = 'trend'

    def __init__(self, window_fast: int = 12, window_slow: int = 26,
                 window_sign: int = 9):
        self.window_fast = window_fast
        self.window_slow = window_slow
        self.window_sign = window_sign
    @override
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        macd = MACD(df['close'],
                     window_fast=self.window_fast,
                     window_slow=self.window_slow,
                     window_sign=self.window_sign)
        histogram = macd.macd_diff()

        # 用价格标准化 histogram，再用 tanh 映射到 [-1, 1]
        # 乘以缩放因子让信号有足够区分度
        normalized = histogram / df['close'] * 100
        signal = pd.Series(np.tanh(normalized), index=df.index)

        return signal.fillna(0)
