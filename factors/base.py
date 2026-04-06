from abc import ABC, abstractmethod
import pandas as pd


class BaseFactor(ABC):
    """多因子模型的因子基类。

    所有因子必须继承此类并实现 calculate() 方法。
    calculate() 必须返回一个值域为 [-1, 1] 的 pd.Series：
      - 接近 +1 表示强烈看多
      - 接近 -1 表示强烈看空
      - 接近 0 表示无明确方向
    """

    name: str = ''
    category: str = ''  # trend, momentum, volume, volatility

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """根据 OHLCV 数据计算因子信号。

        Args:
            df: 包含 open, high, low, close, volume 列的 DataFrame

        Returns:
            pd.Series: 值域 [-1, 1] 的信号序列，index 与 df 一致
        """
        ...

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name}, category={self.category})'
