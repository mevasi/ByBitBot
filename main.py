import json
import bybit
from decimal import *

api_key = "*"
api_secret = "*"


def trade(b_price, a_price):
    # initialise client with keys
    client = bybit.bybit(test=True, api_key=api_key, api_secret=api_secret)

    # retrieve order book JSON data and sort by price
    btc = client.Market.Market_orderbook(symbol="BTCUSDT").result()[0]['result']
    btc.sort(key=lambda x: x["price"])

    # split buy and sell orders, reverse bids for correct ordering
    bids = [x for x in btc if x['side'] == 'Buy']
    bids.reverse()
    asks = [x for x in btc if x['side'] == 'Sell']

    # do orders
    if b_price == Decimal(bids[0]['price']) and a_price == Decimal(asks[0]['price']):
        pass
        print("passed")
    else:
        print(client.LinearOrder.LinearOrder_cancelAll(symbol="BTCUSDT").result())

        b_price = Decimal(bids[0]['price'])
        a_price = Decimal(asks[0]['price'])

        print(client.LinearOrder.LinearOrder_new(side="Buy", symbol="BTCUSDT", order_type="Limit", qty=0.01,
                                                 price=b_price, time_in_force="PostOnly").result())
        print(client.LinearOrder.LinearOrder_new(side="Sell", symbol="BTCUSDT", order_type="Limit", qty=0.01,
                                                 price=a_price, time_in_force="PostOnly").result())

    return [b_price, a_price]


if __name__ == '__main__':
    [buy, sell] = trade(0, 0)
    while 1:
        [buy, sell] = trade(buy, sell)
