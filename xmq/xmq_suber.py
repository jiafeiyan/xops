# -*- coding: UTF-8 -*-

import json
import zmq
import thread
import Queue

from utils import log


class xmq_suber:
    def __init__(self, addr, topic):
        logger = log.get_logger(category="XmqSuber")
        logger.info("[init xmq suber with %s] begin" % (
            json.dumps({"addr": addr, "topic": topic}, encoding="UTF-8", ensure_ascii=False)))

        self.addr = addr
        self.topic = topic
        self.topic_length = len(self.topic)

        self.__connect()

    def __connect(self):
        self.context = zmq.Context()
        self.my_xmq = self.context.socket(zmq.SUB)
        self.my_xmq.connect(self.addr)
        self.my_xmq.setsockopt_string(zmq.SUBSCRIBE, self.topic)

    def recv(self):
        data = self.my_xmq.recv()
        data = data[self.topic_length:]

        return data


class xmq_queue_suber:
    def __init__(self, addr, topic):
        self.addr = addr
        self.topic = topic

        self.msg_queue = Queue.Queue()
        self.__start_daemon()

    def recv(self):
        return self.msg_queue.get()

    def __start_daemon(self):
        def loop_msg():
            mqsuber = xmq_suber(self.addr, self.topic)
            while True:
                msg_text = mqsuber.recv()
                msg = json.loads(msg_text, encoding="UTF-8")

                self.msg_queue.put(msg)

        thread.start_new(loop_msg, ())


class xmq_msg_resolver:
    def __init__(self):
        pass

    def resolve_msg(self, msg):
        return -1


class xmq_resolving_suber:
    def __init__(self, addr, topic):
        self.addr = addr
        self.topic = topic
        self.resolvers = []
        self.__start_daemon()

    def add_resolver(self, resolver):
        self.resolvers.append(resolver)

    def __start_daemon(self):
        def loop_msg():
            mqsuber = xmq_suber(self.addr, self.topic)
            while True:
                msg_text = mqsuber.recv()
                msg = json.loads(msg_text, encoding="UTF-8")

                for resolver in self.resolvers:
                    if resolver.resolve_msg(msg) == 0:
                        break

        thread.start_new(loop_msg, ())
