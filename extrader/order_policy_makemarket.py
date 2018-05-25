# -*- coding: UTF-8 -*-

import json
import Queue
import sys
import csv
import os
import time
import threading
from datetime import datetime

from msg_resolver_qry_insstatus import QryInstrumentStatusMsgResolver
from xmq import xmq_pusher, xmq_resolving_suber, xmq_msg_resolver, xmq_resolving_puller
from utils import Configuration, parse_conf_args, log, path


def makemarket_order(context, conf):
    pid = os.getpid()
    logger = log.get_logger(category="OrderMakeMarket")

    logger.info(
        "[start makemarket order order with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    # 发送报单
    xmq_target_conf = context.get("xmq").get(conf.get("targetMQ"))
    target_mq_addr = xmq_target_conf["address"]
    target_mq_topic = xmq_target_conf["topic"]
    msg_target_pusher = xmq_pusher(target_mq_addr, target_mq_topic)

    md_resolver = MakeMarketMsgResolver()
    # 接收实盘行情信息
    xmq_source_conf = context.get("xmq").get(conf.get("tmdSourceMQ"))
    source_mq_addr = xmq_source_conf["address"]
    source_mq_topic = xmq_source_conf["topic"]
    t_msg_source_suber = xmq_resolving_suber(source_mq_addr, source_mq_topic)
    t_msg_source_suber.add_resolver(md_resolver)
    # 接收模拟盘行情信息
    xmq_source_conf = context.get("xmq").get(conf.get("smdSourceMQ"))
    source_mq_addr = xmq_source_conf["address"]
    source_mq_topic = xmq_source_conf["topic"]
    s_msg_source_puller = xmq_resolving_puller(source_mq_addr, source_mq_topic)
    s_msg_source_puller.add_resolver(md_resolver)

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
    load_marketdata(order_source_data, md_resolver)

    # 发送一条获取行情信息
    while not md_resolver_status.status:
        msg_target_pusher.send({"type": "get_status"})
        time.sleep(5)

    count = 0
    while True:
        while not md_resolver.result_queue.empty():
            result = md_resolver.result_queue.get()
            # 查看合约状态
            if result.get("SecurityID") not in md_resolver_status.istatus:
                continue
            if str(md_resolver_status.istatus.get(result.get("SecurityID")).get("InstrumentStatus")) in ('2', '3'):
                input_params = {"InstrumentID": result.get("SecurityID"),
                                "LimitPrice": result.get("LimitPrice"),
                                "VolumeTotalOriginal": int(result.get("VolumeTotalOriginal")),
                                "Direction": ord(result.get("Direction")),
                                "ParticipantID": conf.get("ParticipantID"),
                                "ClientID": conf.get("clientId"),
                                "OrderPriceType": conf.get("OrderPriceType")}
                # logger.info(input_params)
                seq = str(pid) + "_" + str(count)
                msg_target_pusher.send({"type": "order", "data": input_params, "seq": seq})
                logger.info(seq)
                count += 1


def load_marketdata(marketdata, MakeMarketMsgResolver):
    for data in marketdata:
        digit = get_decimal_digit(float(data.get("PriceTick")))
        if data.get("ValueMode") == '1':
            lower = round((1 - float(data.get("LowerValue"))) * float(data.get("PreClosePrice")), digit)
            upper = round((1 + float(data.get("UpperValue"))) * float(data.get("PreClosePrice")), digit)
        elif data.get("ValueMode") == '2':
            lower = float(data.get("PreClosePrice")) - float(data.get("LowerValue"))
            upper = float(data.get("UpperValue")) + float(data.get("PreClosePrice"))
        else:
            continue
        InstrumentID = data.get("InstrumentID")
        PreClosePrice = data.get("PreClosePrice")
        MaxLimitOrderVolume = data.get("MaxLimitOrderVolume")
        one_row = dict({
            InstrumentID: {
                'BidPrice5': 0.00000,
                'BidPrice4': 0.00000,
                'BidPrice1': 0.00000,
                'BidPrice3': 0.00000,
                'BidPrice2': 0.00000,
                'LowerLimitPrice': lower,
                'AskPrice5': 0.00000,
                'AskPrice4': 0.00000,
                'AskPrice3': 0.00000,
                'AskPrice2': 0.00000,
                'AskPrice1': 0.00000,
                'BidVolume5': 0,
                'BidVolume4': 0,
                'BidVolume3': 0,
                'BidVolume2': 0,
                'BidVolume1': 0,
                'Volume': '0',
                'AskVolume1': 0,
                'AskVolume2': 0,
                'AskVolume3': 0,
                'AskVolume4': 0,
                'AskVolume5': 0,
                'UpperLimitPrice': upper,
                'InstrumentID': InstrumentID,
                'LastPrice': PreClosePrice
            }
        })
        # 缓存最大下单量
        MakeMarketMsgResolver.max_volume.update({InstrumentID: int(MaxLimitOrderVolume)})
        MakeMarketMsgResolver.make_target(one_row)


def get_decimal_digit(decimal):
    digit = 0
    while True:
        if decimal == int(decimal):
            break
        else:
            decimal = decimal * 10
            digit = digit + 1
    return digit


class MakeMarketMsgResolver(xmq_msg_resolver):
    def __init__(self):
        self.target_market_context = {}
        self.source_market_context = {}
        self.max_volume = dict()
        self.source_time = dict()
        self.instrument_id = None
        self.result_queue = Queue.Queue()
        self.lock = threading.Lock()
        xmq_msg_resolver.__init__(self)

    def recv_target(self, md_data):
        self.target_market_context.update(md_data)
        self.instrument_id = md_data.keys()[0]

    def make_target(self, md_data):
        if self.max_volume.has_key(md_data.keys()[0]):
            self.source_market_context.update(md_data)
            self.instrument_id = md_data.keys()[0]

    def resolve_msg(self, msg):
        self.lock.acquire()
        try:
            if msg is None or msg.get("type") is None:
                return
            # 获取消息服务器行情信息
            md_data = msg.get("data")
            if msg.get("type") == "marketdata":
                self.make_target(md_data)
                # 模拟盘报单，并且更新时间
                self.req_order()
                self.source_time.update({md_data.keys()[0]: datetime.now()})
            elif msg.get("type") == "makemarket":
                self.recv_target(md_data)
                ins = md_data.keys()[0]
                # 实盘行情与模拟盘缓存时间大于一分钟则报单，并且更新缓存时间
                if not self.source_time.has_key(ins):
                    self.source_time.update({ins: datetime.now()})
                    self.req_order()
                elif (datetime.now() - self.source_time.get(ins)).total_seconds() >= 60:
                    self.source_time.update({ins: datetime.now()})
                    self.market_order()

        finally:
            self.lock.release()

    def req_order(self):
        security_id = self.instrument_id
        if self.source_market_context.has_key(security_id) and self.target_market_context.has_key(security_id):
            source_market = self.source_market_context[security_id]
            target_market = self.target_market_context[security_id]
            orders = self.gen_order(source_market, target_market)
            for order in orders:
                self.result_queue.put(order)

    def market_order(self):
        order = {"SecurityID": self.instrument_id, "Direction": "0", "VolumeTotalOriginal": 100,
                 "LimitPrice": 0, "OrderPriceType": '3'}
        self.result_queue.put(order)

    def gen_order(self, source_market, target_market):
        security_id = str(target_market["InstrumentID"])
        max_volume = self.max_volume.get(security_id)
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

            # 比较五档行情范围
            temp_price = 0
            if self.__check_price_valid(s_a1_p):
                temp_price = s_a1_p
            if self.__check_price_valid(s_a2_p):
                temp_price = s_a2_p
            if self.__check_price_valid(s_a3_p):
                temp_price = s_a3_p
            if self.__check_price_valid(s_a4_p):
                temp_price = s_a4_p
            if self.__check_price_valid(s_a5_p):
                temp_price = s_a5_p
            if target_price > temp_price > 0:
                target_price = temp_price

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

            # 报单量为0修改为100
            if order1["VolumeTotalOriginal"] == 0:
                v = 100 if max_volume > 100 else 1
                order1["VolumeTotalOriginal"] = v
                order2 = {"SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": v,
                          "LimitPrice": target_price}
                # orders.append(order2)
                orders.append(order1)
            else:
                volume_list = []
                quotient = divmod(int(order1["VolumeTotalOriginal"]), int(max_volume))[0] - 1
                remainder = divmod(int(order1["VolumeTotalOriginal"]), int(max_volume))[1]
                while quotient >= 0:
                    quotient -= 1
                    volume_list.append(int(max_volume))
                volume_list.append(remainder)
                # 分段报单
                for vol in volume_list:
                    orders.append({"SecurityID": security_id,
                                   "Direction": "0",
                                   "VolumeTotalOriginal": vol,
                                   "LimitPrice": target_price})
                    break

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

            # 比较五档行情范围
            temp_price = 0
            if self.__check_price_valid(s_b1_p):
                temp_price = s_b1_p
            if self.__check_price_valid(s_b2_p):
                temp_price = s_b2_p
            if self.__check_price_valid(s_b3_p):
                temp_price = s_b3_p
            if self.__check_price_valid(s_b4_p):
                temp_price = s_b4_p
            if self.__check_price_valid(s_b5_p):
                temp_price = s_b5_p
            if target_price < temp_price:
                target_price = temp_price

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
                v = 100 if max_volume > 100 else 1
                order1["VolumeTotalOriginal"] = v
                order2 = {"SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": v,
                          "LimitPrice": target_price}
                # orders.append(order2)
                orders.append(order1)
            else:
                volume_list = []
                quotient = divmod(int(order1["VolumeTotalOriginal"]), int(max_volume))[0] - 1
                remainder = divmod(int(order1["VolumeTotalOriginal"]), int(max_volume))[1]
                while quotient >= 0:
                    quotient -= 1
                    volume_list.append(int(max_volume))
                volume_list.append(remainder)
                # 分段报单
                for vol in volume_list:
                    orders.append({"SecurityID": security_id,
                                   "Direction": "1",
                                   "VolumeTotalOriginal": vol,
                                   "LimitPrice": target_price})
                    break
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
