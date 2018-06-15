# -*- coding: UTF-8 -*-

import json
import time
import thread
import pandas as pd

from pandas import DataFrame
from xmq import xmq_resolving_suber, xmq_msg_resolver, xmq_queue_pusher
from utils import Configuration, parse_conf_args, log


class RtnOrderTradeResolver(xmq_msg_resolver):
    def __init__(self, pusher, conf):
        xmq_msg_resolver.__init__(self)
        self.pusher = pusher
        self.sec = conf.get("sec")
        self.send = conf.get("send")
        # order结构
        self.order_header = ["TradingDay", "OrderSysID", "ParticipantID", "ClientID", "OrderStatus"]
        # self.order_header = ["TradingDay", "SettlementGroupID", "SettlementID", "OrderSysID", "ParticipantID",
        #               "ClientID", "UserID", "InstrumentID", "OrderPriceType", "Direction", "CombOffsetFlag",
        #               "CombHedgeFlag", "LimitPrice", "VolumeTotalOriginal", "TimeCondition", "GTDDate",
        #               "VolumeCondition", "MinVolume", "ContingentCondition", "StopPrice", "ForceCloseReason",
        #               "OrderLocalID", "IsAutoSuspend", "OrderSource", "OrderStatus", "OrderType", "VolumeTraded",
        #               "VolumeTotal", "InsertDate", "InsertTime", "ActiveTime", "SuspendTime", "UpdateTime",
        #               "CancelTime", "ActiveUserID", "Priority", "TimeSortID", "ClearingPartID", "BusinessUnit",
        #               "BusinessLocalID", "ActionDay"]
        # trade结构
        self.trade_header = ["TradingDay", "OrderSysID", "ParticipantID", "ClientID"]
        # self.trade_header = ["TradingDay", "SettlementGroupID", "SettlementID", "TradeID", "Direction", "OrderSysID",
        #                      "ParticipantID", "ClientID", "TradingRole", "AccountID", "InstrumentID", "OffsetFlag",
        #                      "HedgeFlag", "Price", "Volume", "TradeTime", "TradeType", "PriceSource", "UserID",
        #                      "OrderLocalID", "ClearingPartID", "BusinessUnit", "BusinessLocalID", "ActionDay"]
        # 初始化order空数据集
        self.order = DataFrame(columns=self.order_header)
        # 初始化trade空数据集
        self.trade = DataFrame(columns=self.trade_header)
        # 全局缓冲区
        self.order_cache = []
        self.trade_cache = []
        self.handle_order_action()

    def resolve_msg(self, msg):
        if msg is None or msg.get("type") is None:
            return
        if msg.get("type") == "rtnOrder":
            self.handle_order(data=msg.get("data"))
        elif msg.get("type") == "rtnTrade":
            self.handle_trade(data=msg.get("data"))

    def handle_order(self, data):
        # 0 全部成交
        # 1 部分成交还在队列中
        # 2 部分成交不在队列中
        # 3 未成交还在队列中
        # 4 未成交不在队列中
        # 5 撤单
        if data[4] == '3':
            self.order_cache.append(data)

    def handle_trade(self, data):
        self.trade_cache.append(data)

    def handle_order_action(self):
        # 撤单策略
        def loop():
            while True:
                self.full_gc()
                _head = self.order.head(self.send)
                for index, row in _head.iterrows():
                    data = row.to_dict()
                    self.pusher.send({"type": "withdrawal", "data": data})
                time.sleep(self.sec)
        # 启动线程
        thread.start_new(loop, ())

    def full_gc(self):
        # 刷新缓冲区
        _order = self.order.append(DataFrame(data=self.order_cache, columns=self.order_header), sort=True)
        _trade = self.trade.append(DataFrame(data=self.trade_cache, columns=self.trade_header), sort=True)
        self.order_cache = []
        self.trade_cache = []
        # 重建索引
        _order = _order.set_index("OrderSysID")
        _trade = _trade.set_index("OrderSysID")

        # 获取交集
        merge = pd.merge(left=_order, right=_trade, how='inner', on=["OrderSysID"])
        # 删除子集
        _order.drop(merge.index, inplace=True)
        # 恢复索引
        _order.reset_index(inplace=True)
        # 清空trade
        self.trade = DataFrame(columns=self.trade_header)
        self.order = _order

def order_record(context, conf):
    logger = log.get_logger(category="OrderRecord")

    logger.info(
        "[start action order with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    second_action = conf["second_action"]

    # 发送报单
    xmq_target_conf = context.get("xmq").get(conf.get("targetMQ"))
    target_mq_addr = xmq_target_conf["address"]
    target_mq_topic = xmq_target_conf["topic"]
    msg_target_pusher = xmq_queue_pusher(target_mq_addr, target_mq_topic)

    # 接收保单回报
    resolver = RtnOrderTradeResolver(msg_target_pusher, second_action)
    xmq_source_conf = context.get("xmq").get(conf.get("sourceMQ"))
    source_mq_addr = xmq_source_conf["address"]
    source_mq_topic = xmq_source_conf["topic"]
    msg_source_suber_status = xmq_resolving_suber(source_mq_addr, source_mq_topic)
    msg_source_suber_status.add_resolver(resolver)

    while True:
        time.sleep(60)

def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files,
                                       add_ons=add_ons)

    order_record(context, conf)


if __name__ == "__main__":
    main()
