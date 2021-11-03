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

    return 0.001  # default order size if positions are equal

# TBD REPLACE ORDERS IF FILLED AND PRICE NOT CHANGING ^^


def place(clnt, prc, quantity, command):  # manage buy or sell orders depending on which thread calls
    # attempt to cancel all the orders
    # on this side, as the price has changed
    try:
        order_array = clnt.LinearOrder.LinearOrder_query(symbol="BTCUSDT").result()[0]['result']
        for order in order_array:
            if order['side'] == command:
                print("Cancelling", command, "side order number", order['order_id'], "...", clnt.LinearOrder.
                      LinearOrder_cancel(symbol="BTCUSDT", order_id=order['order_id']).result()[0]['ret_msg'])
    except:
        print("no open orders or cannot cancel")

    # try to place an order at the bid/ask, and a buy/sell to close order at the same price
    try:
        print(command, "order placed ...",
              clnt.LinearOrder.LinearOrder_new(side=command, symbol="BTCUSDT", order_type="Limit",
                                               qty=quantity,
                                               price=prc, time_in_force="PostOnly",
                                               reduce_only=False,
                                               close_on_trigger=False).result()[0]['ret_msg'])
        print(command, "to close placed ...",
              clnt.LinearOrder.LinearOrder_new(side=command, symbol="BTCUSDT", order_type="Limit",
                                               qty=0.001,
                                               price=prc, time_in_force="PostOnly",
                                               reduce_only=True,
                                               close_on_trigger=True).result()[0]['ret_msg'])
    except:
        print("could not place one or both ", command, " side orders")


def bid_ask_intermediary(clnt, array, prc, commnd):
    # if the price has not changed, do nothing. If it has, update my orders
    if prc == Decimal(array[0]['price']):
        return prc
    else:
        prc = Decimal(array[0]['price'])

        # find the balance between open positions and place appropriate order
        amount = check_position_balance(clnt, commnd)
        if amount != 0:
            place(clnt, prc, amount, commnd)
        return prc


def create_bids(client):  # thread for accessing globals bids, loops to place buy orders
    # initial blank price of 0 to place first order
    price = 0
    # loop will place further orders as the price changes
    while 1:
        price = bid_ask_intermediary(client, bids, price, "Buy")


def create_asks(client):  # thread for accessing globals asks, loops to place sell orders
    # initial blank price of 0 to place first order
    price = 0
    # loop will place further orders as the price changes
    while 1:
        price = bid_ask_intermediary(client, asks, price, "Sell")


def sub_menu():
    os.system('cls')
    print("At any time")
    print("Press 1 to begin program")
    print("Press 2 to stop program")
    print("Press any other key to quit")
    ans = input("- - - - - - - -\n")

    if ans == "1":
        os.system('cls')
        # initialise client with keys
        by_client = bybit.bybit(test=False, api_key=api_key, api_secret=api_secret)

        # define threads to keep order book updated and submit orders
        book = threading.Thread(target=update_order_book, args=(by_client,))
        buy = threading.Thread(target=create_bids, args=(by_client,))
        sell = threading.Thread(target=create_asks, args=(by_client,))

        # start threads
        book.start()
        time.sleep(5)  # wait for initial order book fill
        buy.start()
        sell.start()

        # wait for updated input
        while 1:
            new_input = input()
            print(new_input)
    elif ans == "2":
        print("TBD")
    else:
        return


def main_menu():
    print("- - - - - - - -")
    print("Please ensure you have configured your API keys as")
    print("described on https://github.com/mevasi/ByBitBot")
    print("- - - -")
    print("If you have done this, press 1, otherwise press 0 to enter manually")
    print("Please make a selection and press Enter")
    ans = input("- - - - - - - -\n")

    # read user input and take appropriate action
    if ans == "0":
        os.system('cls')
        print("TBD read API keys")
        time.sleep(2)
        sub_menu()
    elif ans == "1":
        sub_menu()


if __name__ == '__main__':
    # initialise main menu
    os.system('cls')
    menu = threading.Thread(target=main_menu)
    menu.start()