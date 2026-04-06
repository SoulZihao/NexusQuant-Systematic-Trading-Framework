import ccxt
import pandas as pd
import config


class DataFetcher:
    """统一的交易所数据获取层。

    管理交易所连接，提供标准化的 OHLCV 数据获取接口，
    支持多币种、多时间框架查询。
    """

    def __init__(self, exchange_id: str = 'okx'):
        self.exchange = self._create_exchange(exchange_id)

    def _create_exchange(self, exchange_id: str) -> ccxt.Exchange:
        exchange_cls = getattr(ccxt, exchange_id)
        return exchange_cls({
            'apiKey': config.OKX_API_KEY,
            'secret': config.OKX_SECRET_KEY,
            'password': config.OKX_PASSPHRASE,
        })

    def fetch_ohlcv(self, symbol: str, timeframe: str = '15m',
                    limit: int = 300) -> pd.DataFrame:
        """获取 OHLCV 数据，返回标准化 DataFrame。

        丢弃最后一根未完成的 K 线，确保数据完整性。
        """
        bars = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe,
                                         limit=limit)
        df = pd.DataFrame(bars[:-1],
                          columns=['timestamp', 'open', 'high', 'low',
                                   'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def fetch_balance(self) -> dict:
        return self.exchange.fetch_balance()

    def fetch_ticker(self, symbol: str) -> dict:
        return self.exchange.fetch_ticker(symbol)

    def create_market_buy_order(self, symbol: str, amount: float):
        return self.exchange.create_market_buy_order(symbol, amount)

    def create_market_sell_order(self, symbol: str, amount: float):
        return self.exchange.create_market_sell_order(symbol, amount)
