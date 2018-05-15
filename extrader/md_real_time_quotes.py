# -*- coding: UTF-8 -*-

import json
import time

from xmq import xmq_queue_puber
from utils import Configuration, parse_conf_args, log, path


def start_get_md_quotes(context, conf):
    # 偏移量跳过csv文件的表头区域
    HEAD_OFF_SET = 502

    logger = log.get_logger(category="MdService")
    logger.info("[start real time quotes with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    # 获取实盘行情文件路径
    md_source = path.convert(conf.get("mdSource"))
    # 获取刷新频率
    frequency = conf.get("frequency")

    xmq_target_conf = context.get("xmq").get(conf.get("targetMQ"))
    target_mq_addr = xmq_target_conf["address"]
    target_mq_topic = xmq_target_conf["topic"]
    msg_queue_puber = xmq_queue_puber(target_mq_addr, target_mq_topic)

    # 处理文件并且发送实盘行情消息
    # 定义指针记录当前行
    # pointer = 1
    step = conf.get("msg_step")
    f = open(md_source, 'r')
    f.seek(HEAD_OFF_SET)
    count = 0
    while True:
        line = f.readline()
        if len(line) == 0:
            logger.info("real time quotes had send %s messages", str(count))
            count = 0
            pos = f.tell()
            f.close()
            f = open(md_source, 'r')
            f.seek(pos)
            # 设置是否循环
            if conf.get("is_loop"):
                logger.info("读到文件末尾，重新循环")
                f.seek(HEAD_OFF_SET)
        else:
            handle_file(line, msg_queue_puber)
            count += 1
            if count == step:
                logger.info("real time quotes had send %s messages", str(count))
                time.sleep(frequency)
                count = 0

def handle_file(read_line, pub):
        row = read_line
        # 判断是否存在换行符，表示一行行情结束
        row = row.replace("\n", "").split(",")
        md_info = dict({"InstrumentID": row[21],
                        "LastPrice": row[3],
                        "UpperLimitPrice": row[15],
                        "LowerLimitPrice": row[16],
                        "Volume": row[10],
                        "BidPrice1": row[23],
                        "BidVolume1": row[24],
                        "AskPrice1": row[25],
                        "AskVolume1": row[26],
                        "BidPrice2": row[27],
                        "BidVolume2": row[28],
                        "AskPrice2": row[29],
                        "AskVolume2": row[30],
                        "BidPrice3": row[31],
                        "BidVolume3": row[32],
                        "AskPrice3": row[33],
                        "AskVolume3": row[34],
                        "BidPrice4": row[35],
                        "BidVolume4": row[36],
                        "AskPrice4": row[37],
                        "AskVolume4": row[38],
                        "BidPrice5": row[39],
                        "BidVolume5": row[40],
                        "AskPrice5": row[41],
                        "AskVolume5": row[42]})
        msg = {"type": "makemarket",
               "data": {row[21]: md_info}}
        pub.send(msg)

def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    start_get_md_quotes(context, conf)


if __name__ == "__main__":
    main()
