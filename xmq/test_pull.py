# -*- coding: UTF-8 -*-

import zmq
import time

context = zmq.Context()

topic_length = len("EX:TRADER:")

my_xmq = context.socket(zmq.PULL)
my_xmq.connect("tcp://127.0.0.1:5566")

while True:
    data = my_xmq.recv()
    data = data[topic_length:]
    print data
    time.sleep(0.5)
