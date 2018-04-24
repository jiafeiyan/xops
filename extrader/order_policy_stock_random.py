# -*- coding: UTF-8 -*-

import json
import time
import csv
import random
import math

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

    # 获取数据来源，
    file_source = conf.get("fileSource")
    order_source_data = [row for row in csv.DictReader(open(file_source))]
    # 最小下单量
    min_volume = conf.get("minVolume")
    # 最大下单量
    max_volume = conf.get("maxVolume")

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
        # 1）随机选择一只股票
        random_data = order_source_data[random.randint(0, len(order_source_data) - 1)]
        digit = get_decimal_digit(float(random_data.get("PriceTick")))
        # 2）获取计算涨跌停板价格
        if random_data.get("ValueMode") == '1':
            lower = round((1 - float(random_data.get("LowerValue"))) * float(random_data.get("PreClosePrice")), digit)
            upper = round((1 + float(random_data.get("UpperValue"))) * float(random_data.get("PreClosePrice")), digit)
        elif random_data.get("ValueMode") == '2':
            lower = float(random_data.get("PreClosePrice")) - float(random_data.get("LowerValue"))
            upper = float(random_data.get("UpperValue")) + float(random_data.get("PreClosePrice"))
        else:
            continue
        # 3）下单策略
        # 1=>报涨停板价 2=>报跌停板价 3=>随即报单 4=>昨收盘价
        strategy = random.randint(1, 4)
        if strategy == 1:
            limit_price = upper
        elif strategy == 2:
            limit_price = lower
        elif strategy == 3:
            limit_price = random.uniform(lower, upper)
        elif strategy == 4:
            limit_price = float(random_data.get("PreClosePrice"))
        else:
            continue
        input_params = {"InstrumentID": random_data.get("InstrumentID"),
                        "LimitPrice": round(limit_price, digit),
                        "VolumeTotalOriginal": random.randint(min_volume * int(random_data.get("VolumeMultiple")),
                                                              max_volume * int(random_data.get("VolumeMultiple"))),
                        "Direction": ord(str(random.randint(0, 1))),
                        "ParticipantID": conf.get("ParticipantID"),
                        "ClientID": conf.get("clientId"),
                        "count": count}
        msg_target_puber.send({"type": "order", "data": input_params})
        count += 1
        # msg_target_puber.send({"type": "qry_marketdata", "data": {"k1": "v1", "c": count}})
        # count += 1
        time.sleep(3)


def get_decimal_digit(decimal):
    digit = 0
    while True:
        if decimal == int(decimal):
            break
        else:
            decimal = decimal * 10
            digit = digit + 1
    return digit


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    random_order(context, conf)


if __name__ == "__main__":
    main()
