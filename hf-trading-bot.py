#!/usr/local/python/current/bin/python
import datetime
from random import randint
from lagrangex.fix import (
    buy,
    open_wallet,
    order_status,
    register_orderbook_handler,
    sell,
    wallet_status,
    SPEED_FAST,
    SPEED_NORMAL,
    SPEED_REALTIME,
    SPEED_SLOW,
)

MY_ORDERS = []
WALLET_UUID = None


def my_orderbook_handler(order_book):
    global MY_ORDERS, WALLET_UUID
    now = datetime.datetime.now()
    print("hf-trading-bot my_orderbook_handler() on {}".format(now), order_book)

    ask_symbol = "AMZN"
    first_ask = order_book["SYMBOLS"][ask_symbol]["ASK"][0]
    first_ask_price = first_ask["PRICE"]
    first_ask_quantity = first_ask["QUANTITY"]

    # best strategy every, 50/50 bet
    chance = randint(0, 1)
    if chance == 1:
        qty = randint(1, first_ask_quantity)
        order_uuid = buy(ask_symbol, first_ask_price, qty)
        print(
            "hf-trading-bot my_orderbook_handler() on {}, buy order_id {}".format(
                now, order_uuid
            ),
            order_book,
        )
        if order_status(order_uuid) == "EXECUTED":
            MY_ORDERS.append(
                {
                    "uuid": order_uuid,
                    "quantity": qty,
                    "price": first_ask_price,
                    "symbol": ask_symbol,
                }
            )

    # sell everything is in profit
    my_order_index = 0
    while my_order_index < len(MY_ORDERS):
        o = MY_ORDERS[my_order_index]
        my_order_symbol = o["symbol"]

        first_bid = order_book["SYMBOLS"][my_order_symbol]["BID"][0]
        first_bid_price = first_bid["PRICE"]
        first_bid_quantity = first_bid["QUANTITY"]

        my_order_price = o["price"]
        if my_order_price < first_bid_price:
            my_order_quantity = o["quantity"]
            if my_order_quantity < first_bid_quantity:
                sell(my_order_symbol, my_order_price, my_order_quantity)
            else:
                sell(my_order_symbol, my_order_price, first_bid_quantity)
                MY_ORDERS[my_order_index]["quantity"] = (
                    my_order_quantity - first_bid_quantity
                )
        my_order_index += 1
    
    # check balance
    wallet_balance = wallet_status(WALLET_UUID)["balance"]
    print("hf-trading-bot my_orderbook_handler() wallet_balance is {}".format(wallet_balance))

def main():
    global WALLET_UUID
    now = datetime.datetime.now()
    print("hf-trading-bot main() on {}".format(now))

    # apertura del wallet con 10000$
    WALLET_UUID = open_wallet(10000)
    print("hf-trading-bot main() wallet_uuid is {}".format(WALLET_UUID))

    # ottenere il saldo del wallet
    wallet_balance = wallet_status(WALLET_UUID)["balance"]
    print("hf-trading-bot main() wallet_balance is {}".format(wallet_balance))

    lagrangex_stopper = register_orderbook_handler(my_orderbook_handler, SPEED_NORMAL)
    # in alternativa a CTRL+C per arrestare il thread dell'order_book
    # lagrangex_stopper.set()


if __name__ == "__main__":
    # Execute when the module is not initialized from an import statement.
    main()
