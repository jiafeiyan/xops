# -*- coding: UTF-8 -*-

import time
import json

import shfetraderapi

from trader_handler import TraderHandler
from msg_resolver_qry_marketdata import QryMarketDataMsgResolver
from msg_resolver_insert_order import InsertOrderMsgResolver

from trader_msg_resolver import TraderMsgResolver
from xmq import xmq_resolving_puller, xmq_queue_puber
from utils import Configuration, parse_conf_args, log

class TraderWorkerResolver(TraderMsgResolver):
    def __init__(self, handler):
        TraderMsgResolver.__init__(self, handler)

    def resolve_msg(self, msg):
        if msg is None or msg.get("type") is None:
            return -1

        if msg.get("type") == "get_status":
            self.handler.send_status()
            return 0

def start_trader_service(context, conf):
    logger = log.get_logger(category="TraderService")

    logger.info("[start stock trader service with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    exchange_conf = context.get("exchange").get(conf.get("targetExchangeId"))

    exchange_front_addr = str(exchange_conf["frontAddress"])

    user_id = conf["userId"]
    password = conf["password"]

    sec = conf["second_send"].get("sec")
    send = conf["second_send"].get("send")

    # 发送信息【合约状态】
    xmq_target_conf = context.get("xmq").get(conf.get("targetMQ"))
    target_mq_addr = xmq_target_conf["address"]
    target_mq_topic = xmq_target_conf["topic"]
    msg_queue_puber = xmq_queue_puber(target_mq_addr, target_mq_topic)

    trader_api = shfetraderapi.CShfeFtdcTraderApi_CreateFtdcTraderApi()
    trader_handler = TraderHandler(trader_api, user_id, password, conf.get("tradingday"))
    trader_api.RegisterFront(exchange_front_addr)
    trader_api.RegisterSpi(trader_handler)
    trader_api.SubscribePrivateTopic(shfetraderapi.TERT_QUICK)
    trader_api.SubscribePublicTopic(shfetraderapi.TERT_QUICK)

    trader_handler.set_msg_puber(msg_queue_puber)

    trader_api.Init()

    while not trader_handler.is_logined:
        time.sleep(1)

    qry_insstatus_field = shfetraderapi.CShfeFtdcQryInstrumentStatusField()
    trader_api.ReqQryInstrumentStatus(qry_insstatus_field, trader_handler.get_request_id())

    # 拉取报单信息
    xmq_source_conf = context.get("xmq").get(conf.get("sourceMQ"))
    source_mq_addr = xmq_source_conf["address"]
    source_mq_topic = xmq_source_conf["topic"]
    msg_source_puller = xmq_resolving_puller(source_mq_addr, source_mq_topic)

    msg_source_puller.add_resolver(InsertOrderMsgResolver(trader_handler, sec, send))
    msg_source_puller.add_resolver(TraderWorkerResolver(trader_handler))

    trader_api.Join()

def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files,
                                       add_ons=add_ons)

    start_trader_service(context, conf)


if __name__ == "__main__":
    main()
