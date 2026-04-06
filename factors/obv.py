from typing import override

import numpy as np
import pandas as pd

from factors.base import BaseFactor


class OBVFactor(BaseFactor):
    """OBV（On-Balance Volume）量价因子。

    原理：
    - OBV 通过累加（价格上涨日的成交量）和累减（价格下跌日的成交量）
      构建一条"量能累积线"
    - OBV 的趋势方向比其绝对值更重要：
      - OBV 上升 + 价格上升 → 量价齐升，趋势健康（看多）
      - OBV 下降 + 价格上升 → 量价背离，趋势可能反转（看空）
    - 用 OBV 的短期均线偏离度作为信号

    信号生成：
    - 计算 OBV 相对其移动平均的偏离：(OBV - MA(OBV)) / MA(OBV)
    - 用 tanh 压缩到 [-1, 1]
    """

    name = 'obv'
    category = 'volume'

    def __init__(self, window: int = 14):
        self.window = window
    @override
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        # 计算 OBV
        direction = np.sign(df['close'].diff())
        obv = pd.Series(direction * df['volume']).fillna(0).cumsum()

        # OBV 相对其移动平均的偏离率
        obv_ma = obv.rolling(window=self.window).mean()
        deviation = (obv - obv_ma) / obv_ma.abs().replace(0, np.nan)

        # tanh 压缩到 [-1, 1]
        signal = pd.Series(np.tanh(deviation * 2), index=df.index)

        return signal.fillna(0)
