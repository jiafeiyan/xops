# -*- coding: UTF-8 -*-

import json
import time

from xmq import xmq_puber, xmq_resolving_suber, xmq_msg_resolver
from utils import Configuration, parse_conf_args, log


class InstrumentStatusMsgResolver(xmq_msg_resolver):
    def __init__(self):
        xmq_msg_resolver.__init__(self)

    def resolve_msg(self, msg):
        print(msg)


def random_order(context, conf):
    logger = log.get_logger(category="OrderPolicyRandom")

    logger.info("[start random order with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    xmq_target_conf = context.get("xmq").get(conf.get("targetMQ"))

    target_mq_addr = xmq_target_conf["address"]
    target_mq_topic = xmq_target_conf["topic"]

    msg_target_puber = xmq_puber(target_mq_addr, target_mq_topic)

    xmq_source_conf = context.get("xmq").get(conf.get("sourceMQ"))

    source_mq_addr = xmq_source_conf["address"]
    source_mq_topic = xmq_source_conf["topic"]

    msg_source_suber = xmq_resolving_suber(source_mq_addr, source_mq_topic)

    msg_source_suber.add_resolver(InstrumentStatusMsgResolver())

    count = 0
    while True:
        # 随机报单
        input_params= {"InstrumentID": "600000",
                       "LimitPrice": 12,
                       "VolumeTotalOriginal": 1,
                       "Direction": 1,
                       "count": count}
        msg_target_puber.send({"type": "order", "data": input_params})
        count += 1
        # msg_target_puber.send({"type": "qry_marketdata", "data": {"k1": "v1", "c": count}})
        # count += 1
        time.sleep(3)


def load_marked_data():
    pass


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    random_order(context, conf)


if __name__ == "__main__":
    main()
