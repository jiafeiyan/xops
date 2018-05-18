# -*- coding: UTF-8 -*-

import json
import Queue
import sys
import csv
import os
import time

from msg_resolver_qry_insstatus import QryInstrumentStatusMsgResolver
from xmq import xmq_pusher, xmq_resolving_suber, xmq_msg_resolver
from utils import Configuration, parse_conf_args, log, path

def fifth_level(context, conf):
    pid = os.getpid()
    logger = log.get_logger(category="OrderMakeMarket")

    logger.info(
        "[start makemarket order order with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

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

    md_resolver = MakeMarketMsgResolver()
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
    load_marketdata(order_source_data, md_resolver, conf.get("volumeTick"))

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
            if str(md_resolver_status.istatus.get(result.get("SecurityID")).get("InstrumentStatus")) in ('2',):
                input_params = {"InstrumentID": result.get("SecurityID"),
                                "LimitPrice": result.get("LimitPrice"),
                                "VolumeTotalOriginal": int(result.get("VolumeTotalOriginal")),
                                "Direction": ord(result.get("Direction")),
                                "ParticipantID": conf.get("ParticipantID"),
                                "ClientID": conf.get("clientId")}
                logger.info(input_params)
                seq = str(pid) + "_" + str(count)
                msg_target_pusher.send({"type": "order", "data": input_params, "seq": seq})
                logger.info(seq)
                count += 1


def load_marketdata(marketdata, MakeMarketMsgResolver, volume_tick):
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
        VolumeMultiple = data.get("VolumeMultiple")
        PriceTick = data.get("PriceTick")
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
        MakeMarketMsgResolver.make_target(one_row)
        # 缓存数据
        MakeMarketMsgResolver.cache.update({InstrumentID: {
            "MaxLimitOrderVolume": int(MaxLimitOrderVolume),
            "VolumeMultiple": int(VolumeMultiple),
            "volume_tick": int(volume_tick),
            "price_tick": float(PriceTick)
        }})


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
        self.cache = dict()
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
        MaxLimitOrderVolume = self.cache.get(security_id).get("MaxLimitOrderVolume")
        VolumeMultiple = self.cache.get(security_id).get("VolumeMultiple")
        volume_tick = self.cache.get(security_id).get("volume_tick")
        price_tick = self.cache.get(security_id).get("price_tick")

        volume = 1 * volume_tick * VolumeMultiple if MaxLimitOrderVolume > 1 * volume_tick * VolumeMultiple else MaxLimitOrderVolume

        s_a1_p = self.__to_float(source_market["AskPrice1"])
        s_a2_p = self.__to_float(source_market["AskPrice2"])
        s_a3_p = self.__to_float(source_market["AskPrice3"])
        s_a4_p = self.__to_float(source_market["AskPrice4"])
        s_a5_p = self.__to_float(source_market["AskPrice5"])

        t_a1_p = self.__to_float(target_market["AskPrice1"])
        t_a2_p = self.__to_float(target_market["AskPrice2"])
        t_a3_p = self.__to_float(target_market["AskPrice3"])
        t_a4_p = self.__to_float(target_market["AskPrice4"])
        t_a5_p = self.__to_float(target_market["AskPrice5"])

        s_b1_p = self.__to_float(source_market["BidPrice1"])
        s_b2_p = self.__to_float(source_market["BidPrice2"])
        s_b3_p = self.__to_float(source_market["BidPrice3"])
        s_b4_p = self.__to_float(source_market["BidPrice4"])
        s_b5_p = self.__to_float(source_market["BidPrice5"])

        t_b1_p = self.__to_float(target_market["BidPrice1"])
        t_b2_p = self.__to_float(target_market["BidPrice2"])
        t_b3_p = self.__to_float(target_market["BidPrice3"])
        t_b4_p = self.__to_float(target_market["BidPrice4"])
        t_b5_p = self.__to_float(target_market["BidPrice5"])

        orders = []
        ask_price_temp = 0
        buy_price_temp = 0
        # 比较卖一
        if self.__check_price_valid(t_a1_p) and (not self.__check_price_valid(s_a1_p) or s_a1_p > t_a1_p):
            orders.append({
                "SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": volume,
                "LimitPrice": self.__to_float(t_a1_p)
            })
            ask_price_temp = self.__to_float(t_a1_p)
        # 比较卖二
        if self.__check_price_valid(t_a2_p) and (not self.__check_price_valid(s_a2_p) or s_a2_p > t_a2_p):
            orders.append({
                "SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": volume,
                "LimitPrice": self.__to_float(t_a2_p)
            })
            ask_price_temp = self.__to_float(t_a2_p)
        # 比较卖三
        if self.__check_price_valid(t_a3_p) and (not self.__check_price_valid(s_a3_p) or s_a3_p > t_a3_p):
            orders.append({
                "SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": volume,
                "LimitPrice": self.__to_float(t_a3_p)
            })
            ask_price_temp = self.__to_float(t_a3_p)
        # 比较卖四
        if self.__check_price_valid(t_a4_p) and (not self.__check_price_valid(s_a4_p) or s_a4_p > t_a4_p):
            orders.append({
                "SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": volume,
                "LimitPrice": self.__to_float(t_a4_p)
            })
            ask_price_temp = self.__to_float(t_a4_p)
        # 比较卖五
        if self.__check_price_valid(t_a5_p) and (not self.__check_price_valid(s_a5_p) or s_a5_p > t_a5_p):
            orders.append({
                "SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": volume,
                "LimitPrice": self.__to_float(t_a5_p)
            })
            ask_price_temp = self.__to_float(t_a5_p)
        # 比较买一
        if self.__check_price_valid(t_b1_p) and (not self.__check_price_valid(s_b1_p) or s_b1_p < t_b1_p):
            orders.append({
                "SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": volume,
                "LimitPrice": self.__to_float(t_b1_p)
            })
            buy_price_temp = self.__to_float(t_b1_p)
        # 比较买二
        if self.__check_price_valid(t_b2_p) and (not self.__check_price_valid(s_b2_p) or s_b2_p < t_b2_p):
            orders.append({
                "SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": volume,
                "LimitPrice": self.__to_float(t_b2_p)
            })
            buy_price_temp = self.__to_float(t_b2_p)
        # 比较买三
        if self.__check_price_valid(t_b3_p) and (not self.__check_price_valid(s_b3_p) or s_b3_p < t_b3_p):
            orders.append({
                "SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": volume,
                "LimitPrice": self.__to_float(t_b3_p)
            })
            buy_price_temp = self.__to_float(t_b3_p)
        # 比较买四
        if self.__check_price_valid(t_b4_p) and (not self.__check_price_valid(s_b4_p) or s_b4_p < t_b4_p):
            orders.append({
                "SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": volume,
                "LimitPrice": self.__to_float(t_b4_p)
            })
            buy_price_temp = self.__to_float(t_b4_p)
        # 比较买五
        if self.__check_price_valid(t_b5_p) and (not self.__check_price_valid(s_b5_p) or s_b5_p < t_b5_p):
            orders.append({
                "SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": volume,
                "LimitPrice": self.__to_float(t_b5_p)
            })
            buy_price_temp = self.__to_float(t_b5_p)

        # 新增十档
        if ask_price_temp != 0:
            for i in range(1, 6):
                ask_price_temp += price_tick
                orders.append({
                    "SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": VolumeMultiple,
                    "LimitPrice": ask_price_temp
                })
        if buy_price_temp != 0:
            for i in range(1, 6):
                buy_price_temp -= price_tick
                orders.append({
                    "SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": VolumeMultiple,
                    "LimitPrice": buy_price_temp
                })
        return orders

    def __to_float(self, float_str):
        return float(float_str) if float_str else 0

    def __check_price_valid(self, price):
        if float(sys.float_info.max) == price or price == 0:
            return False
        return True


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    fifth_level(context, conf)


if __name__ == "__main__":
    main()
