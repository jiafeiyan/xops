#-*- coding: UTF-8 -*-

from trader_msg_resolver import TraderMsgResolver


class QryMarketDataMsgResolver(TraderMsgResolver):
    def __init__(self, handler):
        TraderMsgResolver.__init__(self, handler)

    def resolve_msg(self, msg):
        if msg is None or msg.get("type") is None:
            return

        type = msg.get("type")
        if type == "qry_marketdata":
            data = msg.get("data")
            print("++++++" + str(data))
            return 0
