# -*- coding: UTF-8 -*-

from xmq import xmq_msg_resolver


class QryInstrumentStatusMsgResolver(xmq_msg_resolver):
    def __init__(self):
        self.status = False
        self.istatus = dict()
        xmq_msg_resolver.__init__(self)

    def resolve_msg(self, msg):
        if msg is None or msg.get("type") is None:
            return

        if msg.get("type") == "istatus":
            data = msg.get("data")
            self.istatus.update(data)
            self.status = True
