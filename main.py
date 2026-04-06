import datetime
import logging
import time
import schedule
import config
import consts
from data.fetcher import DataFetcher
from factors import ALL_FACTORS
from strategy.signal_combiner import SignalCombiner
from strategy.position_manager import PositionManager
from risk.risk_manager import RiskManager
from backtest.engine import BacktestEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ====== 初始化组件 ======
fetcher = DataFetcher()

# factors = [
#     SuperTrendFactor(window=14, multiplier=3.0),
#     BollingerFactor(window=20, window_dev=2),
#     RSIFactor(window=14),
#     MACDFactor(),
#     OBVFactor(window=20),
# ]

combiner = SignalCombiner(ALL_FACTORS)
position_mgr = PositionManager(risk_per_trade=0.02, max_position_pct=0.2)
risk_mgr = RiskManager(max_daily_loss_pct=0.05, atr_stop_multiplier=2.0)


def analyze(symbol: str):
    """获取数据并计算多因子信号（不交易）。"""
    df = fetcher.fetch_ohlcv(symbol, timeframe=consts.TIMEFRAME, limit=300)
    signal_df = combiner.summary(df)

    latest = signal_df.iloc[-1]
    logger.info(f'{symbol} 最新信号:')
    for col in signal_df.columns:
        logger.info(f'  {col}: {latest[col]:.4f}')

    return df, signal_df


def run_bot():
    """定时执行：获取数据 → 计算信号 → 风控检查 → 执行交易。"""
    logger.info(f'=== 运行时间: {datetime.datetime.now()} ===')

    for symbol in consts.SYMBOLS:
        try:
            df = fetcher.fetch_ohlcv(symbol, timeframe=consts.TIMEFRAME, limit=300)
            final_signal = combiner.combine(df).iloc[-1]
            logger.info(f'{symbol} 合成信号: {final_signal:.4f}')

            current_price = df['close'].iloc[-1]

            # ATR 用于止损计算
            from ta.volatility import AverageTrueRange
            atr_val = AverageTrueRange(
                df['high'], df['low'], df['close'], window=14
            ).average_true_range().iloc[-1]

            if final_signal >= consts.SIGNAL_THRESHOLD:
                if position_mgr.has_position(symbol):
                    logger.info(f'{symbol} 已持仓，跳过')
                    continue

                # 计算止损和仓位
                stop_loss = risk_mgr.calculate_stop_loss(
                    current_price, atr_val, 'buy')
                stop_loss_pct = (current_price - stop_loss) / current_price

                # 获取账户余额
                balance = fetcher.fetch_balance()
                equity = float(balance.get('total', {}).get('USDT', 0))
                if equity <= 0:
                    logger.warning('无法获取账户余额')
                    continue

                amount = position_mgr.calculate_position_size(
                    equity, current_price, stop_loss_pct)

                # 风控检查
                order_value = amount * current_price
                current_exposure = sum(
                    p['amount'] * p['entry_price']
                    for p in position_mgr.positions.values()
                )
                passed, reason = risk_mgr.check_order(
                    equity, order_value, current_exposure)
                if not passed:
                    logger.warning(f'{symbol} 风控拒绝: {reason}')
                    continue

                order = fetcher.create_market_buy_order(symbol, amount)
                position_mgr.open_position(
                    symbol, 'buy', amount, current_price)
                logger.info(f'{symbol} 买入 {amount:.6f} @ {current_price}')

            elif final_signal <= -consts.SIGNAL_THRESHOLD:
                if not position_mgr.has_position(symbol):
                    logger.info(f'{symbol} 无持仓，跳过卖出')
                    continue

                pos = position_mgr.get_position(symbol)
                if pos is None:
                    continue
                fetcher.create_market_sell_order(
                    symbol, pos['amount'])
                pnl = position_mgr.close_position(symbol, current_price)
                if pnl is not None:
                    risk_mgr.record_pnl(pnl)
                logger.info(f'{symbol} 卖出，PnL: {pnl}')

        except Exception as e:
            logger.error(f'{symbol} 处理异常: {e}')


def run_backtest():
    """运行所有币种的回测并打印报告。"""
    engine = BacktestEngine(combiner, fee_rate=0.001,
                            signal_threshold=consts.SIGNAL_THRESHOLD)

    for symbol in consts.SYMBOLS:
        df = fetcher.fetch_ohlcv(symbol, timeframe=consts.TIMEFRAME, limit=300)
        metrics = engine.report(df)
        logger.info(f'\n=== {symbol} 回测报告 ===')
        for k, v in metrics.items():
            logger.info(f'  {k}: {v}')


if __name__ == '__main__':
    # 默认运行分析模式（不下单）
    for symbol in consts.SYMBOLS:
        analyze(symbol)

    print('\n--- 回测 ---')
    run_backtest()

    # 取消注释以下代码启动自动交易
    # schedule.every(15).minutes.do(run_bot)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
