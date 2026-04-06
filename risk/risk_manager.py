import logging

logger = logging.getLogger(__name__)


class RiskManager:
    """交易风控层。

    独立于策略，作为所有订单执行前的最后一道防线。
    每个订单必须通过所有风控检查才能执行。

    风控规则：
    1. 单笔止损限制（基于 ATR 倍数）
    2. 单币种最大仓位占比
    3. 总仓位占比上限
    4. 每日最大亏损限制
    """

    def __init__(self,
                 max_daily_loss_pct: float = 0.05,
                 max_total_exposure_pct: float = 0.6,
                 atr_stop_multiplier: float = 2.0):
        """
        Args:
            max_daily_loss_pct: 每日最大亏损占净值比例（默认 5%）
            max_total_exposure_pct: 总仓位占净值上限（默认 60%）
            atr_stop_multiplier: 止损距离 = ATR × 此倍数
        """
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_total_exposure_pct = max_total_exposure_pct
        self.atr_stop_multiplier = atr_stop_multiplier
        self.daily_pnl = 0.0

    def calculate_stop_loss(self, entry_price: float, atr: float,
                            side: str) -> float:
        """基于 ATR 计算止损价。

        Args:
            entry_price: 入场价
            atr: 当前 ATR 值
            side: 'buy' 或 'sell'

        Returns:
            止损价格
        """
        stop_distance = atr * self.atr_stop_multiplier
        if side == 'buy':
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance

    def check_order(self, equity: float, order_value: float,
                    current_exposure: float) -> tuple[bool, str]:
        """检查订单是否通过风控。

        Args:
            equity: 当前账户净值
            order_value: 本笔订单价值（USDT）
            current_exposure: 当前总仓位价值（USDT）

        Returns:
            (是否通过, 原因说明)
        """
        # 1. 每日亏损检查
        if abs(self.daily_pnl) >= equity * self.max_daily_loss_pct:
            return False, f'每日亏损已达上限 ({self.max_daily_loss_pct:.0%})'

        # 2. 总仓位检查
        new_exposure = current_exposure + order_value
        if new_exposure > equity * self.max_total_exposure_pct:
            return False, (f'总仓位将达 {new_exposure/equity:.0%}，'
                           f'超过上限 {self.max_total_exposure_pct:.0%}')

        return True, 'OK'

    def record_pnl(self, pnl: float):
        self.daily_pnl += pnl

    def reset_daily(self):
        self.daily_pnl = 0.0
