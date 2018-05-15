# -*- coding: UTF-8 -*-

import zmq
import time
import json

topic = "EX:TRADER:"

context = zmq.Context()
my_xmq = context.socket(zmq.PUSH)
my_xmq.connect("tcp://127.0.0.1:5555")


for i in range(1, 16):
    msg_text = topic + json.dumps({"index": i})
    print msg_text
    my_xmq.send_string(msg_text)
    time.sleep(0.5)

