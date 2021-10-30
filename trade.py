import json
import bybit
from decimal import *
import threading
import time

api_key = "*"
api_secret = "*"

bids = []
asks = []


def update_order_book(client):
    global bids
    global asks
    while 1:
        # retrieve order book JSON data and sort by price
        btc = client.Market.Market_orderbook(symbol="BTCUSDT").result()[0]['result']
        btc.sort(key=lambda x: x["price"])

        # split buy and sell orders, reverse bids for correct ordering
        temp = [x for x in btc if x['side'] == 'Buy']
        temp.reverse()

        # update globals
        bids = temp
        asks = [x for x in btc if x['side'] == 'Sell']


def create_bids(client):
    # initial blank variables
    price = 0
    orders = []

    # continuous loop in thread
    while 1:
        # if the price has not changed, do nothing. If it has, update my orders
        if price == Decimal(bids[0]['price']):
            pass
        else:
            try:
                for order in orders:
                    print(client.LinearOrder.LinearOrder_cancel(symbol="BTCUSDT", order_id=order).result())
                orders = []
            except:
                print("no open orders or cannot cancel")

            price = Decimal(bids[0]['price'])

            try:
                ord_1 = client.LinearOrder.LinearOrder_new(side="Buy", symbol="BTCUSDT", order_type="Limit", qty=0.01,
                                                           price=price, time_in_force="PostOnly",
                                                           reduce_only=False).result()[0]['result']['order_id']
                print(ord_1)
                ord_2 = client.LinearOrder.LinearOrder_new(side="Buy", symbol="BTCUSDT", order_type="Limit", qty=0.01,
                                                           price=price, time_in_force="PostOnly",
                                                           reduce_only=True).result()[0]['result']['order_id']
                print(ord_2)
            except:
                print("could not place one or both buy/close with buy orders")


def create_asks(client):
    # initial blank variables
    price = 0
    orders = []

    # continuous loop in thread
    while 1:
        # if the price has not changed, do nothing. If it has, update my orders
        if price == Decimal(asks[0]['price']):
            pass
        else:
            try:
                for order in orders:
                    print(client.LinearOrder.LinearOrder_cancel(symbol="BTCUSDT", order_id=order).result())
                orders = []
            except:
                print("no open orders or cannot cancel")

            price = Decimal(asks[0]['price'])

            try:
                ord_1 = client.LinearOrder.LinearOrder_new(side="Sell", symbol="BTCUSDT", order_type="Limit", qty=0.01,
                                                           price=price, time_in_force="PostOnly",
                                                           reduce_only=False).result()[0]['result']['order_id']
                print(ord_1)
                orders.append(ord_1)
                ord_2 = client.LinearOrder.LinearOrder_new(side="Sell", symbol="BTCUSDT", order_type="Limit", qty=0.01,
                                                           price=price, time_in_force="PostOnly",
                                                           reduce_only=True).result()[0]['result']['order_id']
                print(ord_2)
                orders.append(ord_2)
            except:
                print("could not place one or both sell/close with sell orders")


if __name__ == '__main__':
    # initialise client with keys
    by_client = bybit.bybit(test=True, api_key=api_key, api_secret=api_secret)

    # define threads to keep order book updated and submit orders
    book = threading.Thread(target=update_order_book, args=(by_client,))
    buy = threading.Thread(target=create_bids, args=(by_client,))
    sell = threading.Thread(target=create_asks, args=(by_client,))

    # start threads
    book.start()
    time.sleep(5)  # wait for initial order book fill
    buy.start()
    sell.start()
