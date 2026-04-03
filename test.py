import ccxt
import config
# import ccxt.async_support as ccxt

# print all exchanges
# for exchange in ccxt.exchanges:
#     print(exchange)
# print('-'*30)
#print(dir(ccxt))

exchange = ccxt.okx({
    'apiKey':config.OKX_API_KEY,
    'secret':config.OKX_SECRET_KEY,
    'password': config.OKX_PASSPHRASE,
})
balances=exchange.fetch_balance()
for key,val in balances.items():
    if key!='info':print(key,val)
print('-'*30)

markets = exchange.load_markets()
for market in markets:
    if 'XRP' in market:
        print(market)
print('-'*30)

ticker = exchange.fetch_ticker('XRP/USDT')
for key, value in ticker.items():
    print(f"{key}---{value}")
print('-'*30)

ohlc = exchange.fetch_ohlcv('XRP/USDT',timeframe='15m',limit=5)
for candle in ohlc:
    print(candle)
print('-'*30)

order_book = exchange.fetch_order_book('XRP/USDT',limit=20)
bids = order_book.get("bids")
asks = order_book.get("asks")
for i, j in zip(bids, asks):
    print(i,j)
print('-'*30)