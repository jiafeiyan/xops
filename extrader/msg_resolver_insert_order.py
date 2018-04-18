#-*- coding: UTF-8 -*-

from trader_msg_resolver import TraderMsgResolver


class InsertOrderMsgResolver(TraderMsgResolver):
    def __init__(self, handler):
        TraderMsgResolver.__init__(self, handler)

    def resolve_msg(self, msg):
        if msg is None or msg.get("type") is None:
            return -1

        type = msg.get("type")
        if type == "order":
            data = msg.get("data")
            print("********************" + str(data))

            return 0

