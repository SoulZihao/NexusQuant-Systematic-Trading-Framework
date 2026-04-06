from typing import override

import numpy as np
import pandas as pd
from ta.volatility import AverageTrueRange

from factors.base import BaseFactor


class SuperTrendFactor(BaseFactor):
    """SuperTrend。

    原理：
    - 以 (high + low) / 2 作为中轴（HL2）
    - 用 ATR × multiplier 构建上下轨
    - 当价格突破上轨时确认上升趋势，突破下轨时确认下降趋势
    - 趋势延续时，轨道只允许朝趋势方向移动（上升趋势中下轨只升不降）

    与 Bollinger Bands 的区别：
    - SuperTrend 用 ATR（true range 的平滑值）度量波动，对跳空和影线更敏感
    - Bollinger Bands 用收盘价标准差度量波动，对价格分布更敏感
    """

    name = 'supertrend'
    category = 'trend'

    def __init__(self, window: int = 14, multiplier: float = 3.0):
        self.window = window
        self.multiplier = multiplier
    @override
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        atr_indicator = AverageTrueRange(
            df['high'], df['low'], df['close'], window=self.window
        )
        atr = atr_indicator.average_true_range()

        hl2 = (df['high'] + df['low']) / 2.0
        basic_upper = hl2 + self.multiplier * atr
        basic_lower = hl2 - self.multiplier * atr

        upper_band = basic_upper.copy()
        lower_band = basic_lower.copy()
        is_uptrend = pd.Series(True, index=df.index)

        first_valid = atr.first_valid_index()
        if first_valid is None:
            return pd.Series(0.0, index=df.index)

        start = int(df.index.get_loc(first_valid)) + 1

        for i in range(start, len(df)):
            prev = i - 1

            # 上升趋势中，下轨只允许上移
            if basic_lower.iloc[i] > lower_band.iloc[prev]:
                lower_band.iloc[i] = basic_lower.iloc[i]
            else:
                lower_band.iloc[i] = lower_band.iloc[prev]

            # 下降趋势中，上轨只允许下移
            if basic_upper.iloc[i] < upper_band.iloc[prev]:
                upper_band.iloc[i] = basic_upper.iloc[i]
            else:
                upper_band.iloc[i] = upper_band.iloc[prev]

            # 趋势翻转判断
            if is_uptrend.iloc[prev]:
                if df['close'].iloc[i] < lower_band.iloc[i]:
                    is_uptrend.iloc[i] = False
                else:
                    is_uptrend.iloc[i] = True
            else:
                if df['close'].iloc[i] > upper_band.iloc[i]:
                    is_uptrend.iloc[i] = True
                else:
                    is_uptrend.iloc[i] = False

        # 生成连续信号：价格距离超势线的远近代表信号强度
        # 上升趋势中，用 (close - lower_band) / (upper_band - lower_band) 映射到 [0, 1]
        # 下降趋势中，用 (close - upper_band) / (upper_band - lower_band) 映射到 [-1, 0]
        band_width = upper_band - lower_band
        band_width = band_width.replace(0, np.nan)

        signal = pd.Series(0.0, index=df.index)
        up_mask = is_uptrend.astype(bool)
        down_mask = ~up_mask

        signal[up_mask] = (
            (df['close'][up_mask] - lower_band[up_mask]) / band_width[up_mask]
        )
        signal[down_mask] = (
            (df['close'][down_mask] - upper_band[down_mask]) / band_width[down_mask]
        )

        return signal.clip(-1, 1).fillna(0)
