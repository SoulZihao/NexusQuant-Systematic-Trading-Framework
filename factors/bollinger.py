from typing import override

import numpy as np
import pandas as pd
from ta.volatility import BollingerBands

from factors.base import BaseFactor


class BollingerFactor(BaseFactor):
    """Bollinger Bands 均值回归因子。

    原理：
    - 用收盘价的移动平均 ± N 倍标准差构建通道
    - 价格触及上轨时倾向回归（偏空），触及下轨时倾向反弹（偏多）
    - %B 指标 = (close - lower) / (upper - lower)，值域 [0, 1]
    - 将 %B 线性映射到 [-1, 1]：%B=0 → -1（超卖/看多），%B=1 → +1（超买/看空）

    注意：作为均值回归因子，信号方向与趋势因子相反——
    超买时信号为负（预期回落），超卖时信号为正（预期反弹）。
    """

    name = 'bollinger'
    category = 'volatility'

    def __init__(self, window: int = 14, window_dev: int = 2):
        self.window = window
        self.window_dev = window_dev
    @override
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        bb = BollingerBands(df['close'], window=self.window,
                            window_dev=self.window_dev)
        pct_b = bb.bollinger_pband()  # (close - lower) / (upper - lower)

        # 均值回归逻辑：%B 高 → 超买 → 看空（负信号），%B 低 → 超卖 → 看多（正信号）
        # 将 %B ∈ [0, 1] 映射到信号 ∈ [+1, -1]（注意反转）
        signal = 1.0 - 2.0 * pct_b

        return signal.clip(-1, 1).fillna(0)
