# -*- coding: UTF-8 -*-

import json
import time

import shfemdapi
from md_handler import MdHandler

from xmq import xmq_queue_puber
from utils import Configuration, parse_conf_args, log

def start_md_service(context, conf):
    logger = log.get_logger(category="MdService")
    logger.info("[start stock md service with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    exchange_conf = context.get("exchange").get(conf.get("targetExchangeId"))

    exchange_front_addr = str(exchange_conf["mdAddress"])

    user_id = conf["userId"]
    password = conf["password"]
    topic_id = conf["topicId"]

    xmq_target_conf = context.get("xmq").get(conf.get("targetMQ"))

    target_mq_addr = xmq_target_conf["address"]
    target_mq_topic = xmq_target_conf["topic"]

    msg_queue_puber = xmq_queue_puber(target_mq_addr, target_mq_topic)

    md_api = shfemdapi.CShfeFtdcMduserApi_CreateFtdcMduserApi()
    md_handler = MdHandler(md_api, user_id, password)
    md_api.SubscribeMarketDataTopic(topic_id, shfemdapi.TERT_RESTART)
    md_api.RegisterFront(exchange_front_addr)
    md_api.RegisterSpi(md_handler)

    md_handler.set_msg_puber(msg_queue_puber)

    md_api.Init()

    while not md_handler.is_logined:
        time.sleep(1)

    md_api.Join()

def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    start_md_service(context, conf)


if __name__ == "__main__":
    main()
