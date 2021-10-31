import os
import bybit
from decimal import *
import threading
import time

api_key = "*"
api_secret = "*"

bids = []
asks = []


def update_order_book(client):  # runs as a thread to keep global bid and ask arrays updated
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


def check_position_balance(client, cmmnd):  # ensure difference between position sides is a small as possible
    # check my current open positions
    positions = client.LinearPositions.LinearPositions_myPosition(symbol="BTCUSDT").result()[0]['result']
    # split into buy and sell
    buy_position = positions[0]['size']
    sell_position = positions[1]['size']

    # find the difference between open positions and return appropriate order to rectify
    if cmmnd == "Buy":
        if sell_position > buy_position:
            return round(sell_position - buy_position, 3)
        elif sell_position < buy_position:
            return 0

    if cmmnd == "Sell":
        if buy_position > sell_position:
            return round(buy_position - sell_position, 3)
        elif buy_position < sell_position:
            return 0

    return 0.01  # default order size if positions are equal


def place(clnt, prc, quantity, ordr, command):  # manage buy or sell orders depending on which thread calls
    # attempt to cancel all the orders
    # on this side, as the price has changed
    try:
        for order in ordr:
            print(clnt.LinearOrder.LinearOrder_cancel(symbol="BTCUSDT", order_id=order).result())
        ordr = []
    except:
        print("no open orders or cannot cancel")

    # try to place an order at the bid/ask, and a buy/sell to close order at the same price
    try:
        ord_1 = clnt.LinearOrder.LinearOrder_new(side=command, symbol="BTCUSDT", order_type="Limit", qty=quantity,
                                                 price=prc, time_in_force="PostOnly",
                                                 reduce_only=False).result()[0]['result']['order_id']
        print(ord_1)
        ordr.append(ord_1)  # append new order to orders array
        # ord_2 = clnt.LinearOrder.LinearOrder_new(side=command, symbol="BTCUSDT", order_type="Limit", qty=0.01,
        #                                         price=prc, time_in_force="PostOnly",
        #                                         reduce_only=True).result()[0]['result']['order_id']
        # print(ord_2)
        # ordr.append(ord_2)  # append new order to orders array
    except:
        print("could not place one or both ", command, " side orders")
    return ordr


def create_bids(client):  # thread for accessing globals bids, loops to place buy orders
    # initial blank variables
    price = 0
    orders = []

    # continuous loop in thread
    while 1:
        # if the price has not changed, do nothing. If it has, update my orders
        if price == Decimal(bids[0]['price']):
            pass
        else:
            price = Decimal(bids[0]['price'])
            amount = check_position_balance(client, "Buy")
            if amount != 0:
                orders = place(client, price, amount, orders, "Buy")


def create_asks(client):  # thread for accessing globals asks, loops to place sell orders
    # initial blank variables
    price = 0
    orders = []

    # continuous loop in thread
    while 1:
        # if the price has not changed, do nothing. If it has, update my orders
        if price == Decimal(asks[0]['price']):
            pass
        else:
            price = Decimal(asks[0]['price'])
            amount = check_position_balance(client, "Sell")
            orders = place(client, price, amount, orders, "Sell")


def sub_menu():
    os.system('cls')
    print("At any time")
    print("Press 1 to begin program")
    print("Press 2 to stop program")
    print("Press 0 to quit")
    # ans = input("- - - - - - - -\n")


def main_menu():
    print("- - - - - - - -")
    print("Please ensure you have configured your API keys as")
    print("described on https://github.com/mevasi/ByBitBot")
    print("- - - -")
    print("If you have done this, press 1, otherwise press 0 to enter manually")
    print("Please make a selection and press Enter")
    ans = input("- - - - - - - -\n")

    if ans == "0":
        os.system('cls')
        print("TBD read API keys")
        time.sleep(2)
        sub_menu()
    elif ans == "1":
        sub_menu()


if __name__ == '__main__':
    # initialise main menu
    # os.system('cls')
    # menu = threading.Thread(target=main_menu)
    # menu.start()

    # time.sleep(10)

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
