# -*- coding: UTF-8 -*-

"""
生成CSV文件
"""

import csv
import os

from utils import log
from utils import parse_conf_args
from utils import Configuration
from utils import mysql


class sse_to_csv:
    def __init__(self, context, configs):
        # 初始化settlementGroupID
        settlementGroupID = configs.get("settlementGroupID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="future_to_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning(__file__ + "未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        self.__to_csv()

    def __to_csv(self):
        pass

if __name__ == '__main__':
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql", "csv"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动脚本
    sse_to_csv(context=context, configs=conf)
