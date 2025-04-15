from termcolor import colored
from threading import Thread, Event
import uuid
import csv
import os
import datetime

SPEED_SLOW = 1.0
SPEED_NORMAL = 0.5
SPEED_FAST = 0.01
SPEED_REALTIME = 0.001

_fix_thread_stop_flag = None
_fix_thread = None
_wallet = {
    "wallet_uuid": None,
    "balance": 0,
    "initial_balance": 0,
    "symbols": {"AMZN": 0},
}
_orders = []
_orderbook_update_data = None


class MyFixThread(Thread):

    def __init__(
        self,
        event,
        orderbook_handler_speed,
        orderbook_handler,
        orderbook_depth_level,
    ):
        Thread.__init__(self)
        self.stopped = event
        self._orderbook_handler_speed = orderbook_handler_speed
        self._orderbook_handler = orderbook_handler
        self._orderbook_depth_level = orderbook_depth_level
        csv_file_name = (
            "AMZN_2012-06-21_34200000_57600000_orderbook_{}.csv".format(
                self._orderbook_depth_level
            )
        )
        current_working_directory = os.path.dirname(os.path.realpath(__file__))
        csv_path = "{}/../data/{}".format(current_working_directory, csv_file_name)
        csvfile = open(csv_path, newline="\n")
        self._spamreader = csv.DictReader(csvfile, delimiter=",", quotechar="|")

    def run(self):
        global _orderbook_update_data, _wallet
        while not self.stopped.wait(self._orderbook_handler_speed):
            orderbook_update_id = 123
            try:
                orderbook_update_data_next = self._spamreader.__next__()
                orderbook_update_data = {
                    "SYMBOLS": {
                        "AMZN": {
                            "BID": [
                                {
                                    "PRICE": int(
                                        orderbook_update_data_next["BID_1_PRICE"]
                                    ),
                                    "QUANTITY": int(
                                        orderbook_update_data_next["BID_1_QTY"]
                                    ),
                                }
                            ],
                            "ASK": [
                                {
                                    "PRICE": int(
                                        orderbook_update_data_next["ASK_1_PRICE"]
                                    ),
                                    "QUANTITY": int(
                                        orderbook_update_data_next["ASK_1_QTY"]
                                    ),
                                }
                            ],
                        }
                    }
                }
                if self._orderbook_handler is None:
                    print(
                        colored(
                            "register_orderbook_handler was not used, orderbook_update n. {} lost".format(
                                orderbook_update_id
                            ),
                            "magenta",
                        )
                    )
                else:
                    _orderbook_update_data = orderbook_update_data
                    self._orderbook_handler(orderbook_update_data)
            except StopIteration:
                now = datetime.datetime.now()
                wc = _wallet["balance"]
                wci = _wallet["initial_balance"]
                gain = (wc - wci) / 10000
                if gain > 0:
                    print(
                        colored(
                            "TRADING SESSION ENDED ON {}, you win {}$!!!".format(
                                now, gain
                            ),
                            "yellow",
                            attrs=["reverse", "bold"],
                        ),
                        _wallet,
                    )
                else:
                    print(
                        colored(
                            "TRADING SESSION ENDED ON {}, you lose {}$!!!".format(
                                now, gain
                            ),
                            "yellow",
                            attrs=["reverse", "bold"],
                        ),
                        _wallet,
                    )
                _fix_thread_stop_flag.set()


def register_orderbook_handler(handler, speed=SPEED_NORMAL, level="1-short"):
    global _fix_thread_stop_flag, _fix_thread
    _fix_thread_stop_flag = Event()
    _fix_thread = MyFixThread(_fix_thread_stop_flag, speed, handler, level)
    _fix_thread.start()
    return _fix_thread_stop_flag


def buy(wallet_uuid, symbol, price, quantity):
    global _orders, _orderbook_update_data
    order_total = quantity * price
    order = {
        "order_id": uuid.uuid1(),
        "order_total": order_total,
        "order_status": "NOT_EXECUTED",
    }
    if quantity <= 0:
        print(
            colored(
                "BUY ORDER QUANTITY IS <= ZERO({})!!!".format(quantity),
                "red",
                attrs=["reverse", "bold"],
            )
        )
        order["order_status"] = "QUANTITY_LTE_ZERO"
    elif order_total > _wallet["balance"]:
        print(
            colored(
                "CURRENT BALANCE LOWER THAN ORDER TOTAL {}".format(order_total / 10000),
                "red",
                attrs=["reverse", "bold"],
            )
        )
        order["order_status"] = "NOT_ENOUGH_BALANCE"
    else:
        # TODO support partial fill
        # TODO support multi ASK
        p = _orderbook_update_data["SYMBOLS"][symbol]["ASK"][0]["PRICE"]
        q = _orderbook_update_data["SYMBOLS"][symbol]["ASK"][0]["QUANTITY"]
        if price >= p and quantity <= q:
            print(
                colored(
                    "buy {} at {}$ on {} placed".format(
                        quantity, price / 10000, symbol
                    ),
                    "green",
                )
            )
            order["order_status"] = "EXECUTED"
            _wallet["balance"] -= order_total
            if symbol not in _wallet["symbols"]:
                _wallet["symbols"][symbol] = 0
            _wallet["symbols"][symbol] += quantity
        else:
            print(
                colored(
                    "Non vi è sufficiente liquidità per questo ordine",
                    "red",
                    attrs=["reverse", "bold"],
                )
            )
            order["order_status"] = "NOT_ENOUGH_ASK_LIQUIDITY"

    _orders.append(order)
    return order["order_id"]


def sell(wallet_uuid, symbol, price, quantity):
    global _orders, _orderbook_update_data
    order_total = quantity * price
    order = {
        "order_id": uuid.uuid1(),
        "order_total": order_total,
        "order_status": "NOT_EXECUTED",
    }
    sb = _wallet["symbols"][symbol]
    if quantity > sb or sb == 0:
        print(
            colored(
                "CURRENT {} BALANCE({}) LOWER THAN ORDER QUANTITY {}".format(
                    symbol, sb, quantity
                ),
                "red",
                attrs=["reverse", "bold"],
            )
        )
        order["order_status"] = "NOT_ENOUGH_BALANCE"
    else:
        # TODO support partial fill
        # TODO support multi BID
        p = _orderbook_update_data["SYMBOLS"][symbol]["BID"][0]["PRICE"]
        q = _orderbook_update_data["SYMBOLS"][symbol]["BID"][0]["QUANTITY"]
        if price <= p and quantity <= q:
            print(
                colored(
                    "sell {} at {}$ on {} placed".format(
                        quantity, price / 10000, symbol
                    ),
                    "green",
                )
            )
            order["order_status"] = "EXECUTED"
            _wallet["balance"] += order_total
            _wallet["symbols"][symbol] -= quantity
        else:
            print(
                colored(
                    "Non vi è sufficiente liquidità per questo ordine",
                    "red",
                    attrs=["reverse", "bold"],
                )
            )
            order["order_status"] = "NOT_ENOUGH_ASK_LIQUIDITY"

    _orders.append(order)
    return order["order_id"]


def order_status(order_id):
    global _orders
    for o in _orders:
        if o["order_id"] == order_id:
            return o


def wallet_status(wallet_uuid):
    global _wallet
    return {"balance": _wallet["balance"] / 10000}


def open_wallet(balance):
    global _wallet
    wallet_uuid = uuid.uuid1()

    _wallet["wallet_uuid"] = wallet_uuid
    _wallet["balance"] = balance * 10000
    _wallet["initial_balance"] = _wallet["balance"]

    print(
        colored("opened a {}$ wallet with uuid {}".format(balance, wallet_uuid), "cyan")
    )
    return wallet_uuid
