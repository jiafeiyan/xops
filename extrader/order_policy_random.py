# -*- coding: UTF-8 -*-

import json
import time
import csv
import random

from xmq import xmq_puber, xmq_resolving_suber, xmq_msg_resolver
from utils import Configuration, parse_conf_args, log, path

class MarketDataMsgResolver(xmq_msg_resolver):
    def __init__(self):
        self.marketdata = dict()
        xmq_msg_resolver.__init__(self)

    def resolve_msg(self, msg):
        if msg is None or msg.get("type") is None:
            return

        if msg.get("type") == "marketdata":
            data = msg.get("data")
            self.marketdata.update(data)

class InsStatusMsgResolver(xmq_msg_resolver):
    def __init__(self):
        self.istatus = dict()
        xmq_msg_resolver.__init__(self)

    def resolve_msg(self, msg):
        if msg is None or msg.get("type") is None:
            return

        if msg.get("type") == "istatus":
            data = msg.get("data")
            self.istatus.update(data)

def random_order(context, conf):
    logger = log.get_logger(category="OrderPolicyRandom")

    logger.info("[start random order with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    # 下单频率
    order_frequency = conf.get("frequency")
    # 获取数据来源
    file_source = path.convert(conf.get("fileSource"))
    order_source_data = [row for row in csv.DictReader(open(file_source))]
    # 最小下单量
    min_volume = conf.get("minVolume")
    # 最大下单量
    max_volume = conf.get("maxVolume")

    # 发送报单
    xmq_target_conf = context.get("xmq").get(conf.get("targetMQ"))
    target_mq_addr = xmq_target_conf["address"]
    target_mq_topic = xmq_target_conf["topic"]
    msg_target_puber = xmq_puber(target_mq_addr, target_mq_topic)

    # 接收行情信息
    xmq_source_conf = context.get("xmq").get(conf.get("mdSourceMQ"))
    source_mq_addr = xmq_source_conf["address"]
    source_mq_topic = xmq_source_conf["topic"]
    msg_source_suber = xmq_resolving_suber(source_mq_addr, source_mq_topic)

    md_resolver = MarketDataMsgResolver()
    msg_source_suber.add_resolver(md_resolver)

    # 接收行情状态信息
    xmq_source_conf = context.get("xmq").get(conf.get("sourceMQ"))
    source_mq_addr = xmq_source_conf["address"]
    source_mq_topic = xmq_source_conf["topic"]
    msg_source_suber_status = xmq_resolving_suber(source_mq_addr, source_mq_topic)

    md_resolver_status = InsStatusMsgResolver()
    msg_source_suber_status.add_resolver(md_resolver_status)

    count = 0
    while True:
        # 随机选择一只股票
        random_data = order_source_data[random.randint(0, len(order_source_data) - 1)]
        # 查看合约状态
        if random_data.get("InstrumentID") not in md_resolver_status.istatus:
            time.sleep(order_frequency)
            continue
        if '2' == str(md_resolver_status.istatus.get(random_data.get("InstrumentID")).get("InstrumentStatus")):
            digit = get_decimal_digit(float(random_data.get("PriceTick")))
            # 获取报单价格
            limit_price = get_order_price(random_data, md_resolver.marketdata)
            if limit_price is None:
                continue
            input_params = {"InstrumentID": random_data.get("InstrumentID"),
                            "LimitPrice": round(float(limit_price), digit),
                            "VolumeTotalOriginal": random.randint(min_volume, max_volume) *
                                                   (int(random_data.get("VolumeMultiple")) if conf.get("VolumeMultiple") else 1),
                            "Direction": ord(str(random.randint(0, 1))),
                            "ParticipantID": conf.get("ParticipantID"),
                            "ClientID": conf.get("clientId"),
                            "count": count}
            msg_target_puber.send({"type": "order", "data": input_params, "ProductClass": str(random_data.get("ProductClass"))})
            count += 1
            # msg_target_puber.send({"type": "qry_marketdata", "data": {"k1": "v1", "c": count}})
            # count += 1
            time.sleep(order_frequency)

def get_order_price(random_data, marketdata):
    # 1）获取计算涨跌停板价格
    digit = get_decimal_digit(float(random_data.get("PriceTick")))
    if random_data.get("ValueMode") == '1':
        lower = round((1 - float(random_data.get("LowerValue"))) * float(random_data.get("PreClosePrice")), digit)
        upper = round((1 + float(random_data.get("UpperValue"))) * float(random_data.get("PreClosePrice")), digit)
    elif random_data.get("ValueMode") == '2':
        lower = float(random_data.get("PreClosePrice")) - float(random_data.get("LowerValue"))
        upper = float(random_data.get("UpperValue")) + float(random_data.get("PreClosePrice"))
    else:
        return None
    # 3）下单策略
    # 1=>报涨停板价 2=>报跌停板价 3=>涨跌停之间 4=>昨收盘价 5=>最新价和涨跌停板之间
    strategy = get_order_type_by_weight()
    if strategy == 1:
        limit_price = upper
    elif strategy == 2:
        limit_price = lower
    elif strategy == 3:
        limit_price = random.uniform(lower, upper)
    elif strategy == 4:
        limit_price = float(random_data.get("PreClosePrice"))
    elif strategy == 5:
        # 如果没有最新价用昨结算
        if marketdata.get(random_data.get("InstrumentID")) is None:
            return random_data.get("PreClosePrice")
        # 获取最新价附近(浮动 -3% ～ 3%)
        last_price = marketdata.get(random_data.get("InstrumentID")).get("LastPrice")
        last_price = round(float(last_price) * (1.0 + random.uniform(-0.03, 0.03)), digit)
        # 判断涨跌之后是否还在区间内
        if lower <= last_price <= upper:
            limit_price = last_price
        else:
            return random_data.get("PreClosePrice")
    else:
        return None
    return limit_price

def get_order_type_by_weight():
    # 1=>报涨停板价 2=>报跌停板价 3=>涨跌停之间 4=>昨收盘价 5=>最新价和涨跌停板之间
    policy = {1: 10,
              2: 10,
              3: 10,
              4: 10,
              5: 60}
    total = sum(policy.values())
    rad = random.randint(1, total)
    cur_total = 0
    res = ""
    for k, v in policy.items():
            cur_total += v
            if rad <= cur_total:
                res = k
                break
    return res


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
