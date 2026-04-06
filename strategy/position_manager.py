import logging

logger = logging.getLogger(__name__)


class PositionManager:
    """多币种仓位管理器。

    核心逻辑——固定风险比例法：
    - 每笔交易的最大预期亏损 = 账户净值 × risk_per_trade
    - 仓位大小 = 风险金额 / (入场价 × stop_loss_pct)
    - 这确保了无论价格高低，每笔交易承担的风险金额恒定

    同时跟踪各币种的持仓状态，防止重复开仓。
    """

    def __init__(self, risk_per_trade: float = 0.02,
                 max_position_pct: float = 0.2):
        """
        Args:
            risk_per_trade: 单笔交易最大风险占比（默认 2%）
            max_position_pct: 单币种最大仓位占总资产比例（默认 20%）
        """
        self.risk_per_trade = risk_per_trade
        self.max_position_pct = max_position_pct
        self.positions: dict[str, dict] = {}  # {symbol: {side, amount, entry_price}}

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    def get_position(self, symbol: str) -> dict | None:
        return self.positions.get(symbol)

    def calculate_position_size(self, equity: float, entry_price: float,
                                stop_loss_pct: float) -> float:
        """根据风险预算计算仓位大小。

        Args:
            equity: 当前账户净值（USDT）
            entry_price: 预计入场价格
            stop_loss_pct: 止损百分比（如 0.03 表示 3%）

        Returns:
            应买入的数量（币的数量，非 USDT 金额）
        """
        if stop_loss_pct <= 0 or entry_price <= 0:
            return 0.0

        risk_amount = equity * self.risk_per_trade
        position_value = risk_amount / stop_loss_pct

        # 限制单币种最大仓位
        max_value = equity * self.max_position_pct
        position_value = min(position_value, max_value)

        amount = position_value / entry_price
        return amount

    def open_position(self, symbol: str, side: str, amount: float,
                      entry_price: float):
        if self.has_position(symbol):
            logger.warning(f'已持有 {symbol}，跳过重复开仓')
            return False

        self.positions[symbol] = {
            'side': side,
            'amount': amount,
            'entry_price': entry_price,
        }
        logger.info(f'开仓 {side} {symbol}: {amount} @ {entry_price}')
        return True

    def close_position(self, symbol: str, exit_price: float) -> float | None:
        pos = self.positions.pop(symbol, None)
        if pos is None:
            logger.warning(f'无 {symbol} 持仓可平')
            return None

        if pos['side'] == 'buy':
            pnl = (exit_price - pos['entry_price']) * pos['amount']
        else:
            pnl = (pos['entry_price'] - exit_price) * pos['amount']

        logger.info(f'平仓 {symbol}: PnL = {pnl:.4f} USDT')
        return pnl
