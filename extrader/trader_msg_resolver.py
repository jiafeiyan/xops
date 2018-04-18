#-*- coding: UTF-8 -*-

from xmq import xmq_msg_resolver


class TraderMsgResolver(xmq_msg_resolver):
    def __init__(self, handler):
        xmq_msg_resolver.__init__(self)

        self.handler = handler

