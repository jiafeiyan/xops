# -*- coding: UTF-8 -*-

import json
import time
import csv
import random
import math
import traceback
import os

from msg_resolver_qry_insstatus import QryInstrumentStatusMsgResolver
from xmq import xmq_resolving_suber, xmq_msg_resolver, xmq_pusher
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

def random_order(context, conf):
    pid = os.getpid()
    logger = log.get_logger(category="OrderPolicyRandom")

    logger.info("[start random order with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    # 下单频率
    order_frequency = conf.get("frequency")

    # 最小下单量
    min_volume = conf.get("minVolume")
    # 最大下单量
    max_volume = conf.get("maxVolume")

    # 发送报单
    xmq_target_conf = context.get("xmq").get(conf.get("targetMQ"))
    target_mq_addr = xmq_target_conf["address"]
    target_mq_topic = xmq_target_conf["topic"]
    msg_target_pusher = xmq_pusher(target_mq_addr, target_mq_topic)


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

    md_resolver_status = QryInstrumentStatusMsgResolver()
    msg_source_suber_status.add_resolver(md_resolver_status)

    # 获取数据来源
    file_source = path.convert(conf.get("fileSource"))
    order_source_data = [row for row in csv.DictReader(open(file_source))]

    # 发送一条获取行情信息
    while not md_resolver_status.status:
        msg_target_pusher.send({"type": "get_status"})
        time.sleep(5)

    count = 0
    while True:
        try:
            # 随机选择一只股票
            # random_data = order_source_data[random.randint(0, len(order_source_data) - 1)]
            # 循环所有报单
            for random_data in order_source_data:
                # 查看合约状态
                if random_data.get("InstrumentID") not in md_resolver_status.istatus:
                    # time.sleep(order_frequency)
                    continue
                # [集合竞价报单]和连续交易
                if str(md_resolver_status.istatus.get(random_data.get("InstrumentID")).get("InstrumentStatus")) in ('2',):
                    price_tick = float(random_data.get("PriceTick"))
                    digit = get_decimal_digit(price_tick)
                    # 获取报单价格
                    price_strategy = get_order_data(random_data, md_resolver.marketdata)
                    if price_strategy is None:
                        continue
                    limit_price = float(price_strategy[0])
                    strategy = price_strategy[1]
                    # 判断价格是否为空
                    if limit_price is None:
                        continue
                    # 通过tick计算报单价格
                    if divmod(limit_price, price_tick)[1] < price_tick / 2:
                        limit_price = math.floor(limit_price / price_tick) * price_tick
                    else:
                        limit_price = math.ceil(limit_price / price_tick) * price_tick
                    if 1 == strategy:
                        # 涨停只报卖
                        direction = "1"
                    elif 2 == strategy:
                        # 跌停只报买
                        direction = "0"
                    else:
                        direction = str(random.randint(0, 1))
                    input_params = {"InstrumentID": random_data.get("InstrumentID"),
                                    "LimitPrice": round(float(limit_price), digit),
                                    "VolumeTotalOriginal": int(random.randint(min_volume, max_volume) *
                                                           (int(random_data.get("VolumeMultiple")) if conf.get("VolumeMultiple") else 1)),
                                    "Direction": ord(direction),
                                    "ParticipantID": conf.get("ParticipantID"),
                                    "ClientID": conf.get("clientId"),
                                    "count": count}
                    seq = str(pid) + "_" + str(count)
                    msg_target_pusher.send({"type": "order", "data": input_params, "seq": seq})
                    logger.info(seq)
                    count += 1
            time.sleep(order_frequency)
        except Exception as err:
            traceback.print_exc()
            print(err)


def get_order_data(random_data, marketdata):
    marketdata = marketdata.get(random_data.get("InstrumentID"))
    # 如果没有最新价用昨收盘
    if marketdata is None:
        marketdata = dict()
    # 1）获取计算涨跌停板价格
    digit = get_decimal_digit(float(random_data.get("PriceTick")))
    # 3）下单策略（1=>报涨停板价 2=>报跌停板价 3=>涨跌停之间 4=>昨收盘价 5=>最新价和涨跌停板之间）
    # 计算权重
    strategy = get_order_type_by_weight()
    # 计算涨停价
    upper = float(0 if marketdata.get("UpperLimitPrice") is None else marketdata.get("UpperLimitPrice"))
    if upper == 0:
        if random_data.get("ValueMode") == '1':
            upper = round((1 + float(random_data.get("UpperValue"))) * float(random_data.get("PreClosePrice")), digit)
        elif random_data.get("ValueMode") == '2':
            upper = float(random_data.get("UpperValue")) + float(random_data.get("PreClosePrice"))
        else:
            return None
    # 计算跌停价
    lower = float(0 if marketdata.get("LowerLimitPrice") is None else marketdata.get("LowerLimitPrice"))
    if lower == 0:
        if random_data.get("ValueMode") == '1':
            lower = round((1 - float(random_data.get("LowerValue"))) * float(random_data.get("PreClosePrice")), digit)
        elif random_data.get("ValueMode") == '2':
            lower = float(random_data.get("PreClosePrice")) - float(random_data.get("LowerValue"))
        else:
            return None
    # 报单价格
    if strategy == 1:
        limit_price = upper
    elif strategy == 2:
        limit_price = lower
    elif strategy == 3:
        limit_price = random.uniform(lower, upper)
    elif strategy == 4:
        limit_price = float(random_data.get("PreClosePrice"))
    elif strategy == 5:
        # 获取最新价附近(浮动 -1% ～ 1%)
        last_price = marketdata.get("LastPrice")
        if last_price is None:
            last_price = random_data.get("PreClosePrice")
        last_price = round(float(last_price) * (1.0 + random.uniform(-0.01, 0.01)), digit)
        # 判断涨跌之后是否还在区间内
        if lower <= last_price <= upper:
            limit_price = last_price
        else:
            return marketdata.get("LastPrice"), strategy
    else:
        return None
    return limit_price, strategy

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
