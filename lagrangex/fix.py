from termcolor import colored
from threading import Thread, Event
import uuid

SPEED_SLOW = 10.0
SPEED_NORMAL = 5.0
SPEED_FAST = 1.0
SPEED_REALTIME = 0.1

_fix_thread_stop_flag = None
_fix_thread = None

class MyFixThread(Thread):
    
    def __init__(self, event, orderbook_handler_speed, orderbook_handler):
        Thread.__init__(self)
        self.stopped = event
        self._orderbook_handler_speed = orderbook_handler_speed
        self._orderbook_handler = orderbook_handler

    def run(self):
        while not self.stopped.wait(self._orderbook_handler_speed):
            orderbook_update_id = 123
            orderbook_update_data = {
                "SYMBOLS": {
                    "AMZN": {
                        "BID": [
                            {
                                "PRICE": 1234,
                                "QUANTITY": 4567
                            }
                        ],
                        "ASK": [
                            {
                                "PRICE": 1234,
                                "QUANTITY": 4567
                            }
                        ]
                    }
                }
            }
            if self._orderbook_handler is None:
                print(colored("register_orderbook_handler was not used, orderbook_update n. {} lost".format(orderbook_update_id), "magenta"))
            else:
                self._orderbook_handler(orderbook_update_data)

def register_orderbook_handler(handler, speed = SPEED_NORMAL):
    global _fix_thread_stop_flag, _fix_thread
    _fix_thread_stop_flag = Event()
    _fix_thread = MyFixThread(_fix_thread_stop_flag, speed, handler)
    _fix_thread.start()
    return _fix_thread_stop_flag

def buy(symbol, price, quantity):
    print(colored("buy {} at {}$ on {} placed".format(quantity, price/10000, symbol), "green"))
    return uuid.uuid1()

def sell(symbol, price, quantity):
    print(colored("sell {} at {}$ on {} placed".format(quantity, price/10000, symbol), "red"))
    return uuid.uuid1()

def order_status(order_id):
    order_status = "EXECUTED"
    print(colored("order {} status is {}".format(order_id, order_status), "blue"))
    return {
        "status": order_status
    }

def wallet_status(wallet_uuid):
    balance = 10000
    return {
        "balance": balance
    }

def open_wallet(balance):
    wallet_uuid = uuid.uuid1()
    print(colored("opened a {}$ wallet with uuid {}".format(balance, wallet_uuid), "cyan"))
    return wallet_uuid
