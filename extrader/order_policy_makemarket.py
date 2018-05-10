# -*- coding: UTF-8 -*-

import json
import Queue
import sys
import time

from xmq import xmq_puber, xmq_resolving_suber, xmq_msg_resolver
from utils import Configuration, parse_conf_args, log

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


def makemarket_order(context, conf):
    logger = log.get_logger(category="OrderMakeMarket")

    logger.info(
        "[start makemarket order order with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

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

    md_resolver = MakeMarketMsgResolver()
    msg_source_suber.add_resolver(md_resolver)

    # 接收行情状态信息
    xmq_source_conf = context.get("xmq").get(conf.get("sourceMQ"))
    source_mq_addr = xmq_source_conf["address"]
    source_mq_topic = xmq_source_conf["topic"]
    msg_source_suber_status = xmq_resolving_suber(source_mq_addr, source_mq_topic)

    md_resolver_status = InsStatusMsgResolver()
    msg_source_suber_status.add_resolver(md_resolver_status)

    while True:
        while not md_resolver.result_queue.empty():
            result = md_resolver.result_queue.get()
            # 查看合约状态
            if result.get("SecurityID") not in md_resolver_status.istatus:
                continue
            if '2' == str(md_resolver_status.istatus.get(result.get("SecurityID")).get("InstrumentStatus")):
                input_params = {"InstrumentID": result.get("SecurityID"),
                                "LimitPrice": result.get("LimitPrice"),
                                "VolumeTotalOriginal": result.get("VolumeTotalOriginal"),
                                "Direction": ord(result.get("Direction")),
                                "ParticipantID": conf.get("ParticipantID"),
                                "ClientID": conf.get("clientId")}
                logger.info(input_params)
                msg_target_puber.send({"type": "order", "data": input_params, "ProductClass": str(conf.get("ProductClass"))})


class MakeMarketMsgResolver(xmq_msg_resolver):
    def __init__(self):
        self.target_market_context = {}
        self.source_market_context = {}
        self.instrument_id = None
        self.result_queue = Queue.Queue()
        xmq_msg_resolver.__init__(self)

    def recv_target(self, md_data):
        self.target_market_context.update(md_data)
        self.instrument_id = md_data.keys()[0]

    def make_target(self, md_data):
        self.source_market_context.update(md_data)
        self.instrument_id = md_data.keys()[0]

    def resolve_msg(self, msg):
        if msg is None or msg.get("type") is None:
            return
        # 获取消息服务器行情信息
        md_data = msg.get("data")
        if msg.get("type") == "marketdata":
            self.make_target(md_data)
        elif msg.get("type") == "makemarket":
            self.recv_target(md_data)
        self.req_order()

    def req_order(self):
        security_id = self.instrument_id
        if self.source_market_context.has_key(security_id) and self.target_market_context.has_key(security_id):
            source_market = self.source_market_context[security_id]
            target_market = self.target_market_context[security_id]
            orders = self.gen_order(source_market, target_market)
            for order in orders:
                self.result_queue.put(order)

    def gen_order(self, source_market, target_market):
        security_id = str(target_market["InstrumentID"])
        target_price = self.__to_float(target_market["LastPrice"])
        source_price = self.__to_float(source_market["LastPrice"])

        upper_price = self.__to_float(source_market["UpperLimitPrice"])
        lower_price = self.__to_float(source_market["LowerLimitPrice"])

        if target_price > upper_price:
            target_price = upper_price

        if target_price < lower_price:
            target_price = lower_price

        orders = []
        if not self.__check_price_valid(source_price):
            order0 = {"SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": 100,
                      "LimitPrice": target_price}
            order1 = {"SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": 100,
                      "LimitPrice": target_price}
            orders.append(order0)
            orders.append(order1)
        elif target_price > source_price:
            s_a1_p = source_market["AskPrice1"]
            s_a1_v = source_market["AskVolume1"]
            s_a2_p = source_market["AskPrice2"]
            s_a2_v = source_market["AskVolume2"]
            s_a3_p = source_market["AskPrice3"]
            s_a3_v = source_market["AskVolume3"]
            s_a4_p = source_market["AskPrice4"]
            s_a4_v = source_market["AskVolume4"]
            s_a5_p = source_market["AskPrice5"]
            s_a5_v = source_market["AskVolume5"]

            order1 = {"SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": 0, "LimitPrice": target_price}
            if self.__check_price_valid(s_a5_p) and target_price >= s_a5_p:
                order1["VolumeTotalOriginal"] = s_a1_v + s_a2_v + s_a3_v + s_a4_v + s_a5_v
            elif self.__check_price_valid(s_a4_p) and target_price >= s_a4_p:
                order1["VolumeTotalOriginal"] = s_a1_v + s_a2_v + s_a3_v + s_a4_v
            elif self.__check_price_valid(s_a3_p) and target_price >= s_a3_p:
                order1["VolumeTotalOriginal"] = s_a1_v + s_a2_v + s_a3_v
            elif self.__check_price_valid(s_a2_p) and target_price >= s_a2_p:
                order1["VolumeTotalOriginal"] = s_a1_v + s_a2_v
            elif self.__check_price_valid(s_a1_p) and target_price >= s_a1_p:
                order1["VolumeTotalOriginal"] = s_a1_v

            if order1["VolumeTotalOriginal"] == 0:
                order1["VolumeTotalOriginal"] = 100
                order2 = {"SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": 100,
                          "LimitPrice": target_price}
                orders.append(order2)
            orders.append(order1)
        elif target_price < source_price:
            s_b1_p = source_market["BidPrice1"]
            s_b1_v = source_market["BidVolume1"]
            s_b2_p = source_market["BidPrice2"]
            s_b2_v = source_market["BidVolume2"]
            s_b3_p = source_market["BidPrice3"]
            s_b3_v = source_market["BidVolume3"]
            s_b4_p = source_market["BidPrice4"]
            s_b4_v = source_market["BidVolume4"]
            s_b5_p = source_market["BidPrice5"]
            s_b5_v = source_market["BidVolume5"]

            order1 = {"SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": 0, "LimitPrice": target_price}
            if self.__check_price_valid(s_b5_p) and target_price <= s_b5_p:
                order1["VolumeTotalOriginal"] = s_b1_v + s_b2_v + s_b3_v + s_b4_v + s_b5_v
            elif self.__check_price_valid(s_b4_p) and target_price <= s_b4_p:
                order1["VolumeTotalOriginal"] = s_b1_v + s_b2_v + s_b3_v + s_b4_v
            elif self.__check_price_valid(s_b3_p) and target_price <= s_b3_p:
                order1["VolumeTotalOriginal"] = s_b1_v + s_b2_v + s_b3_v
            elif self.__check_price_valid(s_b2_p) and target_price <= s_b2_p:
                order1["VolumeTotalOriginal"] = s_b1_v + s_b2_v
            elif self.__check_price_valid(s_b1_p) and target_price <= s_b1_p:
                order1["VolumeTotalOriginal"] = s_b1_v

            if order1["VolumeTotalOriginal"] == 0:
                order1["VolumeTotalOriginal"] = 100
                order2 = {"SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": 100,
                          "LimitPrice": target_price}
                orders.append(order2)
            orders.append(order1)
        return orders

    def __to_float(self, float_str):
        return float(float_str) if float_str else 0

    def __to_int(self, int_str):
        return int(int_str) if int_str else 0

    def __check_price_valid(self, price):
        if float(sys.float_info.max) == price or price == 0:
            return False
        return True


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    makemarket_order(context, conf)


if __name__ == "__main__":
    main()
