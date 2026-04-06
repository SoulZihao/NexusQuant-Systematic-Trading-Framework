import numpy as np
import pandas as pd

from strategy.signal_combiner import SignalCombiner
from consts import TIMEFRAME

class BacktestEngine:
    """通用多因子回测引擎。

    支持：
    - 任意因子组合 + 信号合成器
    - 手续费建模（taker fee）
    - 信号延迟一根 K 线执行（模拟真实下单延迟）
    - 输出完整的性能指标
    """

    def __init__(self, combiner: SignalCombiner,
                 fee_rate: float = 0.001,
                 signal_threshold: float = 0.3):
        """
        Args:
            combiner: 信号合成器实例
            fee_rate: 单边手续费率（默认 0.1%）
            signal_threshold: 开仓信号阈值（|signal| > threshold 才开仓）
        """
        self.combiner = combiner
        self.fee_rate = fee_rate
        self.signal_threshold = signal_threshold

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """运行回测。

        Args:
            df: OHLCV DataFrame

        Returns:
            包含信号、仓位、收益等列的 DataFrame
        """
        result = df.copy()
        signal = self.combiner.combine(df)

        # 信号延迟一根 K 线执行（看到信号后的下一根 K 线才入场）
        result['signal'] = signal
        result['position'] = 0.0

        # 基于阈值生成仓位：> threshold 做多（1），< -threshold 做空（-1），否则空仓
        result.loc[signal > self.signal_threshold, 'position'] = 1.0
        result.loc[signal < -self.signal_threshold, 'position'] = -1.0

        # 延迟一根 K 线
        result['position'] = result['position'].shift(1).fillna(0)

        # 计算收益
        market_return = result['close'].pct_change().fillna(0)

        # 检测仓位变动并扣除手续费
        position_change = result['position'].diff().abs().fillna(0)
        fee = position_change * self.fee_rate

        result['strategy_return'] = result['position'] * market_return - fee
        result['cum_return'] = (1 + result['strategy_return']).cumprod()
        result['market_cum_return'] = (1 + market_return).cumprod()

        return result

    def compute_metrics(self, result: pd.DataFrame) -> dict:
        """计算回测性能指标。"""
        returns = result['strategy_return']
        cum_return = result['cum_return']

        # 总收益
        total_return = cum_return.iloc[-1] - 1

        # 年化收益（假设 15 分钟 K 线，一年 ≈ 35040 根）
        n_bars = len(returns)
        bars_per_year = 365 * 24 * 4
        switcher = {
            '1d':365,
            '1h':365 * 24,
            '15m': 365 * 24 * 4,
            '1m':365 * 24 * 60,
        }
        bars_per_year = switcher.get(TIMEFRAME)
        annual_return = (1 + total_return) ** (bars_per_year / max(n_bars, 1)) - 1

        # Sharpe Ratio（年化）
        if returns.std() == 0:
            sharpe = 0.0
        else:
            sharpe = returns.mean() / returns.std() * np.sqrt(bars_per_year)

        # 最大回撤
        rolling_max = cum_return.cummax()
        drawdown = (cum_return - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # 胜率和盈亏比
        trades = returns[returns != 0]
        winning = trades[trades > 0]
        losing = trades[trades < 0]

        win_rate = len(winning) / max(len(trades), 1)

        if len(losing) > 0 and losing.mean() != 0:
            profit_factor = abs(winning.sum() / losing.sum()) if len(winning) > 0 else 0
        else:
            profit_factor = float('inf') if len(winning) > 0 else 0

        return {
            'total_return': f'{total_return:.2%}',
            'annual_return': f'{annual_return:.2%}',
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown': f'{max_drawdown:.2%}',
            'win_rate': f'{win_rate:.2%}',
            'profit_factor': round(profit_factor, 2),
            'total_trades': len(trades),
            'total_bars': n_bars,
        }

    def report(self, df: pd.DataFrame) -> dict:
        """运行回测并输出指标报告。"""
        result = self.run(df)
        metrics = self.compute_metrics(result)
        return metrics
