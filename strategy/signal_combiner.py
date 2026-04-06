import pandas as pd
import numpy as np

from factors.base import BaseFactor


class SignalCombiner:
    """多因子信号合成器。

    工作流程：
    1. 对每个因子调用 calculate() 获得原始信号 [-1, 1]
    2. 可选：对信号做滚动 Z-score 标准化（消除不同因子的分布差异）
    3. 按权重加权求和
    4. 最终信号 clip 到 [-1, 1]

    权重设计原则：
    - 默认所有因子等权
    - 可按因子类别或具体因子设置权重
    - 权重会自动归一化（总和为 1）
    """

    def __init__(self, factors: list[BaseFactor],
                 weights: dict[str, float] | None = None,
                 zscore_window: int = 0):
        """
        Args:
            factors: 因子实例列表
            weights: {因子名: 权重} 字典，默认等权
            zscore_window: 滚动 Z-score 窗口。0 表示不做标准化（因子已归一到 [-1,1]）
        """
        self.factors = factors
        self.zscore_window = zscore_window

        if weights is None:
            w = 1.0 / len(factors)
            self.weights = {f.name: w for f in factors}
        else:
            total = sum(weights.values())
            self.weights = {k: v / total for k, v in weights.items()}

    def compute_signals(self, df: pd.DataFrame) -> dict[str, pd.Series]:
        """计算所有因子的原始信号。"""
        return {f.name: f.calculate(df) for f in self.factors}

    def combine(self, df: pd.DataFrame) -> pd.Series:
        """合成最终信号。"""
        raw_signals = self.compute_signals(df)

        combined = pd.Series(0.0, index=df.index)

        for factor_name, signal in raw_signals.items():
            weight = self.weights.get(factor_name, 0.0)

            if self.zscore_window > 0:
                roll_mean = signal.rolling(self.zscore_window).mean()
                roll_std = signal.rolling(self.zscore_window).std()
                signal = (signal - roll_mean) / roll_std.replace(0, np.nan)
                signal = signal.fillna(0).clip(-3, 3) / 3  # Z ∈ [-3,3] → [-1,1]

            combined += weight * signal

        return combined.clip(-1, 1)

    def summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """返回各因子信号及最终合成信号的汇总表。"""
        signals = self.compute_signals(df)
        summary_df = pd.DataFrame(signals)
        summary_df['combined'] = self.combine(df)
        return summary_df
