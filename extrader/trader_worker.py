#-*- coding: UTF-8 -*-

import time
import json
import thread

import shfetraderapi

from trader_handler import TraderHandler
from msg_resolver_qry_marketdata import QryMarketDataMsgResolver
from msg_resolver_insert_order import InsertOrderMsgResolver

from xmq import xmq_resolving_suber, xmq_queue_puber
from utils import Configuration, parse_conf_args, log


def start_trader_service(context, conf):
    logger = log.get_logger(category="TraderService")

    logger.info("[start stock trader service with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    exchange_conf = context.get("exchange").get(conf.get("targetExchangeId"))

    exchange_front_addr = str(exchange_conf["frontAddress"])

    user_id = conf["userId"]
    password = conf["password"]

    xmq_target_conf = context.get("xmq").get(conf.get("targetMQ"))

    target_mq_addr = xmq_target_conf["address"]
    target_mq_topic = xmq_target_conf["topic"]

    msg_queue_puber = xmq_queue_puber(target_mq_addr, target_mq_topic)

    trader_api = shfetraderapi.CShfeFtdcTraderApi_CreateFtdcTraderApi()
    trader_handler = TraderHandler(trader_api, user_id, password)
    trader_api.RegisterFront(exchange_front_addr)
    trader_api.RegisterSpi(trader_handler)
    trader_api.SubscribePrivateTopic(shfetraderapi.TERT_RESUME)
    trader_api.SubscribePublicTopic(shfetraderapi.TERT_RESUME)

    trader_handler.set_msg_puber(msg_queue_puber)

    trader_api.Init()

    while not trader_handler.is_logined:
        time.sleep(1)

    qry_insstatus_field = shfetraderapi.CShfeFtdcQryInstrumentStatusField()
    trader_api.ReqQryInstrumentStatus(qry_insstatus_field, trader_handler.get_request_id())

    xmq_source_conf = context.get("xmq").get(conf.get("sourceMQ"))

    source_mq_addr = xmq_source_conf["address"]
    source_mq_topic = xmq_source_conf["topic"]

    msg_source_suber = xmq_resolving_suber(source_mq_addr, source_mq_topic)

    msg_source_suber.add_resolver(InsertOrderMsgResolver(trader_handler))
    msg_source_suber.add_resolver(QryMarketDataMsgResolver(trader_handler))

    # 定时检查合约交易状态
    thread.start_new(function=check_ins_status(trader_handler))

    trader_api.Join()

def check_ins_status(trader_handler):
    while True:
        print "start check instrument status !"
        trader_handler.ReqQryInstrumentStatus()
        time.sleep(20)

def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    start_trader_service(context, conf)


if __name__ == "__main__":
    main()