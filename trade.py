import os
import time
import bybit
import threading
from decimal import *

# globals - i'll remove these eventually
bids = []
asks = []
balance = 0


def update_order_book(client):  # thread to keep global bid and ask arrays updated
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


def check_position_balance(client):  # thread to ensure position remains balanced
    global balance
    while 1:
        time.sleep(1)
        # check my current open positions
        positions = client.LinearPositions.LinearPositions_myPosition(symbol="BTCUSDT").result()[0]['result']
        # split into buy and sell
        buy_position = positions[0]['size']
        sell_position = positions[1]['size']

        # report balance
        balance = round(sell_position - buy_position, 3)


def cancel_other_orders(client, order_a, command):  # thread will remove all the outdated orders
    # attempt to cancel all the other orders
    # on this side, as the price has changed
    try:
        for order in order_a:
            if order['side'] == command:
                print("Cancelling", command, "side order number", order['order_id'], "...", client.LinearOrder.
                      LinearOrder_cancel(symbol="BTCUSDT", order_id=order['order_id']).result()[0]['ret_msg'])
    except:
        print("no open orders or cannot cancel")


def place(clnt, prc, command):  # manage buy or sell orders depending on which thread calls
    # cancel old orders
    order_array = clnt.LinearOrder.LinearOrder_query(symbol="BTCUSDT").result()[0]['result']
    cancel = threading.Thread(target=cancel_other_orders, args=(clnt, order_array, command))
    cancel.start()

    # check balance before placing order
    stagger_price = prc
    if balance == 0:
        pass
    elif command == "Buy":
        if balance > 0:
            stagger_price = prc - 2
        else:
            return
    elif command == "Sell":
        if balance < 0:
            stagger_price = prc + 2
        else:
            return

    # try to place an order around the bid/ask, and a buy/sell to close order at it
    try:
        print(command, "to close placed ...",
              clnt.LinearOrder.LinearOrder_new(side=command, symbol="BTCUSDT", order_type="Limit",
                                               qty=0.001,
                                               price=prc, time_in_force="PostOnly",
                                               reduce_only=True,
                                               close_on_trigger=True).result()[0]['ret_msg'])
        print(command, "order placed ...",
              clnt.LinearOrder.LinearOrder_new(side=command, symbol="BTCUSDT", order_type="Limit",
                                               qty=0.001,
                                               price=stagger_price, time_in_force="PostOnly",
                                               reduce_only=False,
                                               close_on_trigger=False).result()[0]['ret_msg'])
    except:
        print("could not place one or both ", command, " side orders")


def bid_ask_intermediary(clnt, array, prc, bl, commnd):
    # if the price has not changed, do nothing. If it has, update my orders
    if prc == Decimal(array[0]['price']) and bl == balance:
        return [prc, bl]
    else:
        # update price/balance and place order
        prc = Decimal(array[0]['price'])
        bl = balance
        place(clnt, prc, commnd)
        return [prc, bl]


def create_bids(client):  # thread for accessing globals bids, loops to place buy orders
    # initial blank price of 0 to place first order
    price = 0
    bal = 0
    # loop will place further orders as the price changes
    while 1:
        [price, bal] = bid_ask_intermediary(client, bids, price, bal, "Buy")


def create_asks(client):  # thread for accessing globals asks, loops to place sell orders
    # initial blank price of 0 to place first order
    price = 0
    bal = 0
    # loop will place further orders as the price changes
    while 1:
        [price, bal] = bid_ask_intermediary(client, asks, price, bal, "Sell")


def read_api_keys():
    # read from pre-defined file 'API'
    with open('API', 'r') as file:
        data = file.readlines()

    # extract strings with useful data
    api_key = data[0].replace('\n', '')
    api_secret = data[1].replace('\n', '')

    # display and return
    print("your api key is", api_key)
    return [api_key, api_secret]


def sub_menu(api_key, api_secret):
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

        # define threads to keep order book updated, balance sides, review positions and submit orders
        book = threading.Thread(target=update_order_book, args=(by_client,))
        equal = threading.Thread(target=check_position_balance, args=(by_client,))
        buy = threading.Thread(target=create_bids, args=(by_client,))
        sell = threading.Thread(target=create_asks, args=(by_client,))

        # start threads
        book.start()
        equal.start()
        time.sleep(5)  # wait for initial order book fill
        buy.start()
        sell.start()

        # wait for updated input
        while 1:
            new_input = input()
            print(new_input)
    elif ans == "2":
        print("TBD program halting")
        sub_menu(api_key, api_secret)
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
        print("TBD api keys manual input")
        time.sleep(2)
        main_menu()
    elif ans == "1":
        [api_key, api_secret] = read_api_keys()
        sub_menu(api_key, api_secret)


if __name__ == '__main__':
    # initialise main menu
    os.system('cls')
    menu = threading.Thread(target=main_menu)
    menu.start()
