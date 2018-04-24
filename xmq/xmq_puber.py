# -*- coding: UTF-8 -*-

import json
import zmq
import time
import thread
import Queue

from utils import log


class xmq_puber:
    def __init__(self, addr, topic):
        logger = log.get_logger(category="XmqPuber")
        logger.info("[init xmq puber with %s] begin" % (
            json.dumps({"addr": addr, "topic": topic}, encoding="UTF-8", ensure_ascii=False)))

        self.addr = addr
        self.topic = topic

        self.__connect()

    def __connect(self):
        self.context = zmq.Context()
        self.my_xmq = self.context.socket(zmq.PUB)
        self.my_xmq.connect(self.addr)

    def send(self, msg):
        msg_text = self.topic + json.dumps(msg, encoding="UTF-8", ensure_ascii=False)
        print(msg_text)
        self.my_xmq.send_string(msg_text)


class xmq_queue_puber:
    def __init__(self, addr, topic):
        self.addr = addr
        self.topic = topic
        self.msg_queue = Queue.Queue()
        self.__start_daemon()

    def send(self, msg):
        self.msg_queue.put(msg)

    def __start_daemon(self):
        def loop_msg():
            mqpuber = xmq_puber(self.addr, self.topic)
            while True:
                msg = self.msg_queue.get()
                mqpuber.send(msg)

        thread.start_new(loop_msg, ())
