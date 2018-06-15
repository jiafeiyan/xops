# -*- coding: UTF-8 -*-

import json
import Queue
import sys
import csv
import os
import threading
import time
import random
from datetime import datetime

from msg_resolver_qry_insstatus import QryInstrumentStatusMsgResolver
from xmq import xmq_pusher, xmq_resolving_suber, xmq_msg_resolver, xmq_resolving_puller
from utils import Configuration, parse_conf_args, log, path


def order_union(context, conf):
    pid = os.getpid()
    logger = log.get_logger(category="OrderUnion")

    logger.info(
        "[start union order order with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    order_conf = conf.get("orderConf")
    # 判断股票期货
    market_type = conf.get("type")
    # 接收行情状态信息
    xmq_source_conf = context.get("xmq").get(conf.get("sourceMQ"))
    source_mq_addr = xmq_source_conf["address"]
    source_mq_topic = xmq_source_conf["topic"]
    msg_source_suber_status = xmq_resolving_suber(source_mq_addr, source_mq_topic)
    md_resolver_status = QryInstrumentStatusMsgResolver()
    msg_source_suber_status.add_resolver(md_resolver_status)

    md_resolver = UnionMsgResolver(md_resolver_status, market_type)
    # 获取数据来源
    file_source = path.convert(conf.get("fileSource"))
    order_source_data = [row for row in csv.DictReader(open(file_source))]
    load_marketdata(order_source_data, md_resolver, order_conf)

    # 发送报单
    xmq_target_conf = context.get("xmq").get(conf.get("targetMQ"))
    target_mq_addr = xmq_target_conf["address"]
    target_mq_topic = xmq_target_conf["topic"]
    msg_target_pusher = xmq_pusher(target_mq_addr, target_mq_topic)

    # 发送一条获取行情信息
    while not md_resolver_status.status:
        msg_target_pusher.send({"type": "get_status"})
        logger.info("order_policy_union check marketdata status waiting !!! ")
        time.sleep(5)

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
                                "OrderPriceType": result.get("OrderPriceType"),
                                "order_type": result.get("order_type")}
                # logger.info(input_params)
                seq = str(pid) + "_" + str(count) + "_" + result.get("order_type")
                msg_target_pusher.send({"type": "order", "data": input_params, "seq": seq})
                # logger.info(seq)
                print seq
                count += 1


def load_marketdata(marketdata, UnionMsgResolver, conf):
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
        instrument_id = data.get("InstrumentID")
        pre_close_price = data.get("PreClosePrice")
        max_limit_order_volume = data.get("MaxLimitOrderVolume")
        product_class = str(data.get("ProductClass"))
        price_tick = data.get("PriceTick")
        one_row = dict({
            instrument_id: {
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
                'InstrumentID': instrument_id,
                'LastPrice': pre_close_price
            }
        })
        if conf.has_key('stock'):
            conf['4'] = conf.pop('stock')
        if conf.has_key('etf'):
            conf['2'] = conf.pop('etf')
        if conf.has_key('future'):
            conf['1'] = conf.pop('future')
        if conf.has_key('options'):
            conf['2'] = conf.pop('options')

        # 缓存数据
        UnionMsgResolver.cache.update({instrument_id: {
            "max_limit_order_volume": int(max_limit_order_volume),
            "fifth_level_call_volume": conf.get(product_class).get("fifth_level_call_volume"),
            "normal_volume": conf.get(product_class).get("normal_volume"),
            "price_tick": float(price_tick)
        }})
        UnionMsgResolver.source(one_row)


def get_decimal_digit(decimal):
    digit = 0
    while True:
        if decimal == int(decimal):
            break
        else:
            decimal = decimal * 10
            digit = digit + 1
    return digit


class UnionMsgResolver(xmq_msg_resolver):
    def __init__(self, md_resolver_status, market_type):
        xmq_msg_resolver.__init__(self)
        # 类型
        self.market_type = market_type
        # 模拟盘行情
        self.source_market_context = {}
        # 实盘行情
        self.target_market_context = {}
        # 通过order_info.csv初始化缓存数据
        self.cache = dict()
        # 缓存模拟盘行情接受时间o
        self.source_update_time = dict()
        # 合约状态
        self.md_resolver_status = md_resolver_status
        self.instrument_id = None
        self.result_queue = Queue.Queue()
        self.lock = threading.Lock()

    # 模拟盘行情
    def source(self, md_data):
        instrument_id = md_data.keys()[0]
        # 判断是否有缓存数据
        if self.cache.has_key(instrument_id):
            self.source_market_context.update(md_data)
            self.instrument_id = instrument_id

    # 实盘行情
    def target(self, md_data):
        self.target_market_context.update(md_data)
        self.instrument_id = md_data.keys()[0]

    def resolve_msg(self, msg):
        self.lock.acquire()
        try:
            if msg is None or msg.get("type") is None:
                return
            # 获取消息服务器行情信息
            md_data = msg.get("data")
            ins = md_data.keys()[0]
            # 模拟盘行情
            if msg.get("type") == "marketdata":
                self.source(md_data)
                self.req_order()
                # 缓存当前时间
                self.source_update_time.update({ins: datetime.now()})
            # 实盘行情
            elif msg.get("type") == "makemarket":
                self.target(md_data)
                if ins in self.md_resolver_status.istatus:
                    if not self.source_update_time.has_key(ins):
                        self.source_update_time.update({ins: datetime.now()})
                        self.req_order()
                    elif self.md_resolver_status.istatus.get(ins).get("InstrumentStatus") in ('3',) \
                            and (datetime.now() - self.source_update_time.get(ins)).total_seconds() >= 20:
                        # 报五档单
                        self.source_update_time.update({ins: datetime.now()})
                        self.req_order(callmarket=True)
                    elif self.md_resolver_status.istatus.get(ins).get("InstrumentStatus") in ('2',) \
                            and (datetime.now() - self.source_update_time.get(ins)).total_seconds() >= 60:
                        # 大于1s处理
                        self.source_update_time.update({ins: datetime.now()})
                        self.req_order(timeout=True)
        finally:
            self.lock.release()

    def req_order(self, **kwargs):
        instrument_id = self.instrument_id
        if self.source_market_context.has_key(instrument_id) \
                and self.target_market_context.has_key(instrument_id):
            source_market = self.source_market_context[instrument_id]
            target_market = self.target_market_context[instrument_id]
            orders = self.gen_order(source_market, target_market, kwargs)
            for order in orders:
                self.result_queue.put(order)

    def gen_order(self, source_market, target_market, kwargs):
        # 模拟盘价格
        source_price = self.__to_float(source_market["LastPrice"])
        # 实盘价格
        target_price = self.__to_float(target_market["LastPrice"])

        upper_price = self.__to_float(source_market["UpperLimitPrice"])
        lower_price = self.__to_float(source_market["LowerLimitPrice"])

        if target_price > upper_price:
            target_price = upper_price

        if target_price < lower_price:
            target_price = lower_price

        # 判断是否集合竞价
        if kwargs.get("callmarket"):
            return self.policy_fifth_level(source_market, target_market, True)

        # 判断是否大于一分钟
        if kwargs.get("timeout"):
            if source_price != target_price:
                # 价格不同优先撮合
                return self.policy_make_market(source_market, target_market)
            else:
                return self.policy_order_direct()
        else:
            if source_price != target_price:
                # 价格不同优先撮合
                return self.policy_make_market(source_market, target_market)
            elif source_price == target_price:
                # 相同的话报五档
                return self.policy_fifth_level(source_market, target_market)

    # 撮合单
    def policy_make_market(self, source_market, target_market):
        security_id = self.instrument_id
        normal_volume = self.cache.get(security_id).get("normal_volume") * random.randint(1, 10)
        max_volume = self.cache.get(security_id).get("max_limit_order_volume")

        target_price = self.__to_float(target_market["LastPrice"])
        source_price = self.__to_float(source_market["LastPrice"])

        upper_price = self.__to_float(source_market["UpperLimitPrice"])
        lower_price = self.__to_float(source_market["LowerLimitPrice"])

        if target_price > upper_price:
            target_price = upper_price

        if target_price < lower_price:
            target_price = lower_price

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

        orders = []
        if not self.__check_price_valid(source_price):
            order0 = {"SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": normal_volume,
                      "LimitPrice": target_price, "order_type": "make_market_type_1"}
            order1 = {"SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": normal_volume,
                      "LimitPrice": target_price, "order_type": "make_market_type_2"}
            orders.append(order0)
            orders.append(order1)
        elif self.__check_price_valid(s_a1_p) and target_price >= s_a1_p:
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

            order1 = {"SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": 0, "LimitPrice": target_price,
                      "order_type": "make_market_type_3"}
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
                order1["VolumeTotalOriginal"] = normal_volume
                # order2 = {"SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": v,
                #           "LimitPrice": target_price}
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
                                   "LimitPrice": target_price,
                                   "order_type": "make_market_type_4"})
                    break
        elif self.__check_price_valid(s_b1_p) and target_price <= s_b1_p:
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

            order1 = {"SecurityID": security_id, "Direction": "1", "VolumeTotalOriginal": 0, "LimitPrice": target_price,
                      "order_type": "make_market_type_5"}
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
                order1["VolumeTotalOriginal"] = normal_volume
                # order2 = {"SecurityID": security_id, "Direction": "0", "VolumeTotalOriginal": v,
                #           "LimitPrice": target_price}
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
                                   "LimitPrice": target_price,
                                   "order_type": "make_market_type_6"})
                    break
        elif not self.__check_price_valid(s_a1_p):
            order = {"SecurityID": self.instrument_id, "Direction": "1", "VolumeTotalOriginal": normal_volume,
                     "LimitPrice": target_price, "order_type": "order_direct"}
            orders.append(order)
        elif not self.__check_price_valid(s_b1_p):
            order = {"SecurityID": self.instrument_id, "Direction": "0", "VolumeTotalOriginal": normal_volume,
                     "LimitPrice": target_price, "order_type": "order_direct"}
            orders.append(order)
        else:
            order = {"SecurityID": self.instrument_id, "Direction": "1", "VolumeTotalOriginal": normal_volume,
                     "LimitPrice": target_price, "order_type": "order_direct"}
            orders.append(order)
        return orders

    # 五档行情单
    def policy_fifth_level(self, source_market, target_market, callmarket=False):
        security_id = self.instrument_id

        # normal_volume = self.cache.get(security_id).get("normal_volume") * random.randint(1, 10)
        # volume = fifth_level_call_volume if callmarket else normal_volume

        last_price = self.__to_float(source_market["LastPrice"])
        price_tick = self.cache.get(security_id).get("price_tick")

        fifth_level_call_volume = self.cache.get(security_id).get("fifth_level_call_volume")

        upper_price = self.__to_float(source_market["UpperLimitPrice"])
        lower_price = self.__to_float(source_market["LowerLimitPrice"])

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

        t_a1_v = self.__to_float(target_market["AskVolume1"])
        t_a2_v = self.__to_float(target_market["AskVolume2"])
        t_a3_v = self.__to_float(target_market["AskVolume3"])
        t_a4_v = self.__to_float(target_market["AskVolume4"])
        t_a5_v = self.__to_float(target_market["AskVolume5"])

        t_b1_v = self.__to_float(target_market["BidVolume1"])
        t_b2_v = self.__to_float(target_market["BidVolume2"])
        t_b3_v = self.__to_float(target_market["BidVolume3"])
        t_b4_v = self.__to_float(target_market["BidVolume4"])
        t_b5_v = self.__to_float(target_market["BidVolume5"])

        orders = []

        # 定义模拟卖五档行情集合
        s_a_p = [s_a1_p, s_a2_p, s_a3_p, s_a4_p, s_a5_p]
        t_a_p = [t_a1_p, t_a2_p, t_a3_p, t_a4_p, t_a5_p]
        t_a_v = [t_a1_v, t_a2_v, t_a3_v, t_a4_v, t_a5_v]

        # 定义模拟买五档行情集合
        s_b_p = [s_b1_p, s_b2_p, s_b3_p, s_b4_p, s_b5_p]
        t_b_p = [t_b1_p, t_b2_p, t_b3_p, t_b4_p, t_b5_p]
        t_b_v = [t_b1_v, t_b2_v, t_b3_v, t_b4_v, t_b5_v]

        # 定义买卖五档tick后价格
        s_t_a_p = []
        s_t_b_p = []
        for i in range(1, 6):
            s_t_a_p.append(last_price + i * price_tick)
            s_t_b_p.append(last_price - i * price_tick)

        # 判断是否集合竞价
        if callmarket:
            for (index, ap) in enumerate(s_a_p):
                if ap == 0 and t_a_p[index] != 0:
                    orders.append({
                        "SecurityID": security_id,
                        "Direction": "1",
                        "VolumeTotalOriginal": min(t_a_v[index], fifth_level_call_volume),
                        "LimitPrice": t_a_p[index],
                        "level": "a" + str(index + 1),
                        "order_type": "fifth_level_call_market_sell"
                    })
            for (index, bp) in enumerate(s_b_p):
                if bp == 0 and t_b_p[index] != 0:
                    orders.append({
                        "SecurityID": security_id,
                        "Direction": "0",
                        "VolumeTotalOriginal": min(t_b_v[index], fifth_level_call_volume),
                        "LimitPrice": t_b_p[index], "level": "b" + str(index + 1),
                        "order_type": "fifth_level_call_market_buy"
                    })
            return orders

        for (index, ap) in enumerate(s_a_p):
            # 跌停
            if index == 0 and 0 < t_a1_p <= lower_price:
                orders.append({
                    "SecurityID": security_id,
                    "Direction": "1",
                    "VolumeTotalOriginal": t_a_v[index],
                    "LimitPrice": t_a1_p, "level": "a1", "order_type": "fifth_level_type"
                })
                return orders
            # 实盘卖一小于模拟盘卖一
            if index == 0 and 0 < t_a1_p < ap:
                orders.append({
                    "SecurityID": security_id,
                    "Direction": "1",
                    "VolumeTotalOriginal": min(t_a_v[index], fifth_level_call_volume),
                    "LimitPrice": t_a1_p, "level": "a1", "order_type": "fifth_level_type_1"
                })
                return orders
            # 期货补齐五档
            if self.market_type == 'future':
                fifth_add = None
                if s_a_p.count(0) != 0:
                    for value in s_t_a_p:
                        if value not in s_a_p:
                            fifth_add = value
                            break
                if fifth_add is not None:
                    orders.append({
                        "SecurityID": security_id,
                        "Direction": "1",
                        "VolumeTotalOriginal": random.randint(8, 10),
                        "LimitPrice": fifth_add, "level": "a1", "order_type": "fifth_level_type_add_sell"
                    })
                    return orders
            # 股票
            if self.market_type == 'stock':
                if ap == 0 and t_a_p[index] != 0:
                    orders.append({
                        "SecurityID": security_id,
                        "Direction": "1",
                        "VolumeTotalOriginal": min(t_a_v[index], fifth_level_call_volume),
                        "LimitPrice": t_a_p[index], "level": "a" + str(index + 1), "order_type": "fifth_level_type_2"
                    })
                    return orders

        for (index, bp) in enumerate(s_b_p):
            # 涨停
            if index == 0 and t_b1_p >= upper_price:
                orders.append({
                    "SecurityID": security_id,
                    "Direction": "0",
                    "VolumeTotalOriginal": t_b_v[index],
                    "LimitPrice": t_b1_p, "level": "b1", "order_type": "fifth_level_type"
                })
                return orders

            # 实盘买一大于模拟盘买一
            if index == 0 and t_b1_p > bp:
                orders.append({
                    "SecurityID": security_id,
                    "Direction": "0",
                    "VolumeTotalOriginal": min(t_b_v[index], fifth_level_call_volume),
                    "LimitPrice": t_b1_p, "level": "b1", "order_type": "fifth_level_type_3"
                })
                return orders
            # 期货补齐五档
            if self.market_type == 'future':
                fifth_add = None
                if s_b_p.count(0) != 0:
                    for value in s_t_b_p:
                        if value not in s_b_p:
                            fifth_add = value
                            break
                if fifth_add is not None:
                    orders.append({
                        "SecurityID": security_id,
                        "Direction": "0",
                        "VolumeTotalOriginal": random.randint(8, 10),
                        "LimitPrice": fifth_add, "level": "b1", "order_type": "fifth_level_type_add_buy"
                    })
                    return orders
            # 股票
            if self.market_type == 'stock':
                if bp == 0 and t_b_p[index] != 0:
                    orders.append({
                        "SecurityID": security_id,
                        "Direction": "0",
                        "VolumeTotalOriginal": min(t_b_v[index], fifth_level_call_volume),
                        "LimitPrice": t_b_p[index], "level": "b" + str(index + 1), "order_type": "fifth_level_type_4"
                    })
                    return orders
        return orders

    # 市价单
    def policy_order_direct(self):
        normal_volume = self.cache.get(self.instrument_id).get("normal_volume")
        order = {"SecurityID": self.instrument_id, "Direction": "0", "VolumeTotalOriginal": normal_volume,
                 "LimitPrice": 0, "OrderPriceType": '3', "order_type": "order_direct"}
        return [order]

    def __to_float(self, float_str):
        return float(float_str) if float_str and sys.float_info.max != float(float_str) else 0

    def __to_int(self, int_str):
        return int(int_str) if int_str else 0

    def __check_price_valid(self, price):
        if float(sys.float_info.max) == price or price == 0:
            return False
        return True


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files,
                                       add_ons=add_ons)

    order_union(context, conf)


if __name__ == "__main__":
    main()
